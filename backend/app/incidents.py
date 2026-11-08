"""Versioned assessment intake and human review, independent of dispatch decisions."""
from datetime import timedelta, timezone
import hashlib
import json
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .auth import Context
from .database import get_session
from .models import Incident, IncidentEvent, Membership, ReliefRequest, Workspace, utcnow
from .schemas import parse_timestamp
from .services import require_workspace

router = APIRouter(tags=['Civilian incidents'])
DB = Annotated[Session, Depends(get_session)]
Status = Literal['pending', 'reviewed', 'dismissed']
TRANSITIONS = {'pending': ['reviewed', 'dismissed'], 'reviewed': ['pending', 'dismissed'], 'dismissed': ['pending']}


class Extent(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    west: float = Field(ge=-180, le=180)
    south: float = Field(ge=-90, le=90)
    east: float = Field(ge=-180, le=180)
    north: float = Field(ge=-90, le=90)

    @field_validator('*', mode='before')
    @classmethod
    def coordinates_are_numbers(cls, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError('Coordinates must be finite JSON numbers.')
        return value

    @model_validator(mode='after')
    def ordered(self):
        if self.west >= self.east or self.south >= self.north:
            raise ValueError('Extent requires west < east and south < north. Split antimeridian areas into separate assessments.')
        return self


class Assessment(BaseModel):
    model_config = ConfigDict(extra='forbid')
    schema_version: Literal['sampati.incident.v1']
    external_reference: str = Field(min_length=1, max_length=64, pattern=r'^[A-Za-z0-9][A-Za-z0-9._/-]*$')
    title: str = Field(min_length=2, max_length=160)
    hazard: Literal['flood']
    assessment_kind: Literal['impact_observation']
    locality: str = Field(min_length=2, max_length=160)
    observed_at: str = Field(min_length=1, max_length=64)
    generated_at: str = Field(min_length=1, max_length=64)
    source_name: str = Field(min_length=2, max_length=120)
    source_url: HttpUrl | None = Field(default=None, max_length=2000)
    summary: str = Field(min_length=10, max_length=2000)
    uncertainty: str = Field(min_length=2, max_length=1000)
    extent: Extent
    reported_affected_people: int | None = Field(default=None, ge=0, le=1000000000, strict=True)

    @field_validator('*', mode='before')
    @classmethod
    def trim(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator('source_url')
    @classmethod
    def secure_source(cls, value):
        if value is not None and (value.scheme != 'https' or value.username or value.password):
            raise ValueError('Use an HTTPS evidence link without credentials.')
        return value

    @model_validator(mode='after')
    def dated_observation(self):
        observed, generated = parse_timestamp(self.observed_at), parse_timestamp(self.generated_at)
        if generated < observed:
            raise ValueError('Generation time cannot precede observation time.')
        return self


class Review(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: Status
    expected_version: int = Field(ge=1, strict=True)
    reason: str = Field(min_length=1, max_length=500)

    @field_validator('reason')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Explain the review decision.')
        return value.strip()


def canonical(body):
    value = body.model_dump(mode='json')
    value['external_reference'] = value['external_reference'].upper()
    for field in ('observed_at', 'generated_at'):
        value[field] = parse_timestamp(value[field]).isoformat()
    return value


def assessment_digest(body):
    return hashlib.sha256(json.dumps(canonical(body), sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def describe(item):
    age = (utcnow() - parse_timestamp(item.assessment['observed_at'])).total_seconds()
    return {'id': item.id, 'assessment': item.assessment, 'status': item.status, 'version': item.version,
        'created_actor': item.created_actor, 'received_at': item.received_at.astimezone(timezone.utc).isoformat(),
        'updated_at': item.updated_at.astimezone(timezone.utc).isoformat(),
        'observation_age_hours': round(age / 3600, 1), 'older_than_24h': age > 86400,
        'allowed_transitions': TRANSITIONS[item.status]}


def writer(session, context):
    if context.actor_id is None or context.role not in {'owner', 'editor'}:
        raise HTTPException(403, 'An organisation owner or editor can record and review incidents. Demo examples are read-only.')
    workspace = require_workspace(session, context.workspace_id, lock=True)
    member = session.get(Membership, (context.actor_id, context.workspace_id))
    if workspace.is_demo or member is None or member.role not in {'owner', 'editor'}:
        raise HTTPException(403, 'This account no longer has permission to change incidents.')


def find_incident(session, context, incident_id, lock=False):
    query = select(Incident).where(Incident.workspace_id == context.workspace_id, Incident.id == str(incident_id))
    item = session.scalar(query.with_for_update() if lock else query)
    if item is None:
        raise HTTPException(404, 'This incident was not found in the selected organisation.')
    return item


def add_event(session, item, actor, actor_id, reason, before):
    session.add(IncidentEvent(id=str(uuid4()), workspace_id=item.workspace_id, incident_id=item.id,
        version=item.version, actor=actor, actor_id=actor_id, created_at=item.updated_at,
        reason=reason, before_status=before, after_status=item.status))


@router.get('/incidents/contract')
def contract():
    return Assessment.model_json_schema()


@router.get('/incidents')
def list_incidents(context: Context, session: DB, q: str = Query(default='', max_length=200),
    status: Literal['all', 'pending', 'reviewed', 'dismissed'] = 'all', page: int = Query(default=1, ge=1, le=100000)):
    with session.begin():
        require_workspace(session, context.workspace_id, lock=False)
        session.scalar(select(Workspace.id).where(Workspace.id == context.workspace_id).with_for_update(read=True))
        counts = dict(session.execute(select(Incident.status, func.count()).where(Incident.workspace_id == context.workspace_id).group_by(Incident.status)).all())
        filters = [Incident.workspace_id == context.workspace_id]
        if status != 'all':
            filters.append(Incident.status == status)
        if q.strip():
            filters.append(or_(Incident.reference_key.contains(q.strip().upper(), autoescape=True),
                *(func.lower(Incident.assessment[field].as_string()).contains(q.strip().lower(), autoescape=True)
                    for field in ('title', 'locality', 'source_name'))))
        total = session.scalar(select(func.count()).select_from(Incident).where(*filters))
        pages = max(1, (total + 19) // 20)
        page = min(page, pages)
        items = session.scalars(select(Incident).where(*filters).order_by(Incident.received_at.desc(), Incident.id).offset((page - 1) * 20).limit(20)).all()
        return {'items': [describe(item) for item in items], 'total': total, 'page': page, 'total_pages': pages,
            'counts': {'all': sum(counts.values()), **{key: counts.get(key, 0) for key in TRANSITIONS}},
            'can_edit': context.actor_id is not None and context.role in {'owner', 'editor'}, 'server_time': utcnow()}


@router.post('/incidents', status_code=201)
def create_incident(body: Assessment, context: Context, session: DB, response: Response):
    with session.begin():
        writer(session, context)
        digest = assessment_digest(body)
        previous = session.scalar(select(Incident).where(Incident.workspace_id == context.workspace_id, Incident.reference_key == body.external_reference.upper()))
        if previous:
            if previous.digest != digest:
                raise HTTPException(409, 'This assessment reference already has different evidence. Use a new reference for a revised assessment; the original is retained.')
            response.status_code = 200
            return {'incident': describe(previous), 'duplicate': True}
        if max(parse_timestamp(body.observed_at), parse_timestamp(body.generated_at)) > utcnow() + timedelta(minutes=5):
            raise HTTPException(422, 'This intake accepts dated impact observations. Future observations or forecasts need a separate contract.')
        now = utcnow()
        item = Incident(id=str(uuid4()), workspace_id=context.workspace_id, reference_key=body.external_reference.upper(),
            digest=digest, assessment=body.model_dump(mode='json'), status='pending', version=1,
            created_by=context.actor_id, created_actor=context.actor, received_at=now, updated_at=now)
        session.add(item)
        session.flush()
        add_event(session, item, context.actor, context.actor_id, 'Assessment received; human review required.', None)
        return {'incident': describe(item), 'duplicate': False}


@router.get('/incidents/{incident_id}')
def detail(incident_id: UUID, context: Context, session: DB, before_version: int | None = Query(default=None, ge=1)):
    with session.begin():
        require_workspace(session, context.workspace_id)
        session.scalar(select(Workspace.id).where(Workspace.id == context.workspace_id).with_for_update(read=True))
        item = find_incident(session, context, incident_id)
        conditions = [IncidentEvent.workspace_id == context.workspace_id, IncidentEvent.incident_id == item.id]
        if before_version is not None:
            conditions.append(IncidentEvent.version < before_version)
        events = session.scalars(select(IncidentEvent).where(*conditions).order_by(IncidentEvent.version.desc()).limit(50)).all()
        links = session.scalars(select(ReliefRequest).where(ReliefRequest.workspace_id == context.workspace_id, ReliefRequest.incident_id == item.id).order_by(ReliefRequest.created_at.desc()).limit(20)).all()
        linked_count = session.scalar(select(func.count()).select_from(ReliefRequest).where(ReliefRequest.workspace_id == context.workspace_id, ReliefRequest.incident_id == item.id))
        return {'incident': describe(item), 'events': [{key: getattr(event, key) for key in
            ('id', 'version', 'actor', 'created_at', 'reason', 'before_status', 'after_status')} for event in events],
            'next_before_version': events[-1].version if events and events[-1].version > 1 else None,
            'linked_requests': [{'id': request.id, 'reference': request.reference, 'status': request.status} for request in links], 'linked_request_count': linked_count}


@router.post('/incidents/{incident_id}/review')
def review(incident_id: UUID, body: Review, context: Context, session: DB):
    with session.begin():
        writer(session, context)
        item = find_incident(session, context, incident_id, lock=True)
        if item.version != body.expected_version:
            raise HTTPException(409, 'This incident changed after you opened it. Refresh its details before reviewing again.')
        if item.status == body.status:
            return {'incident': describe(item), 'unchanged': True}
        if body.status not in TRANSITIONS[item.status]:
            raise HTTPException(409, 'Choose an available review action.')
        before = item.status
        item.status, item.version, item.updated_at = body.status, item.version + 1, utcnow()
        add_event(session, item, context.actor, context.actor_id, body.reason, before)
        return {'incident': describe(item), 'unchanged': False}
