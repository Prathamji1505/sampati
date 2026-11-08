"""Human-reviewed civilian supply requests; no stock, dispatch or delivery inference."""
from decimal import Decimal
from datetime import timezone
import hashlib
import json
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .auth import Context
from .database import get_session
from .models import Incident, Membership, ReliefRequest, ReliefRequestEvent, Workspace, utcnow
from .schemas import parse_timestamp
from .services import require_workspace

router = APIRouter(tags=['Civilian relief requests'])
DB = Annotated[Session, Depends(get_session)]
Status = Literal['draft', 'submitted', 'reviewed', 'cancelled']
Category = Literal['food', 'water', 'medicine', 'shelter', 'other']
Unit = Literal['items', 'boxes', 'kits', 'litres', 'kilograms', 'packs']
TRANSITIONS = {'draft': ['submitted', 'cancelled'], 'submitted': ['reviewed', 'draft', 'cancelled'],
    'reviewed': ['draft', 'cancelled'], 'cancelled': []}
EDITABLE = ('requesting_organisation', 'locality', 'category', 'item_name', 'quantity', 'unit', 'needed_by', 'source_name', 'note')


class RequestFields(BaseModel):
    model_config = ConfigDict(extra='forbid')
    requesting_organisation: str = Field(min_length=2, max_length=120)
    locality: str = Field(min_length=2, max_length=160)
    category: Category
    item_name: str = Field(min_length=2, max_length=160)
    quantity: Decimal = Field(gt=0, le=Decimal('1000000000'), max_digits=13, decimal_places=3, allow_inf_nan=False)
    unit: Unit
    needed_by: str = Field(min_length=1, max_length=64)
    source_name: str = Field(min_length=2, max_length=120)
    note: str = Field(default='', max_length=1000)

    @field_validator('*', mode='before')
    @classmethod
    def trim(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator('quantity', mode='before')
    @classmethod
    def no_boolean_quantity(cls, value):
        if isinstance(value, bool):
            raise ValueError('Enter a positive supply quantity.')
        return value

    @field_validator('needed_by')
    @classmethod
    def timezone_required(cls, value):
        parse_timestamp(value)
        return value


class NewRequest(RequestFields):
    reference: str = Field(min_length=1, max_length=64, pattern=r'^[A-Za-z0-9][A-Za-z0-9._/-]*$')
    submission_key: UUID
    incident_id: UUID | None = None


class EditRequest(RequestFields):
    expected_version: int = Field(ge=1, strict=True)
    reason: str = Field(min_length=1, max_length=500)


class StatusChange(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: Status
    expected_version: int = Field(ge=1, strict=True)
    reason: str = Field(min_length=1, max_length=500)

    @field_validator('reason')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Explain the status change.')
        return value.strip()


def quantity_text(value):
    text = format(value, 'f')
    return text.rstrip('0').rstrip('.') if '.' in text else text


def normalized(body):
    values = {field: getattr(body, field) for field in EDITABLE}
    values['quantity'] = quantity_text(body.quantity)
    values['needed_by'] = parse_timestamp(body.needed_by).isoformat()
    return values


def create_digest(body):
    values = {**normalized(body), 'reference': body.reference.upper()}
    if body.incident_id is not None:
        values['incident_id'] = str(body.incident_id)
    return hashlib.sha256(json.dumps(values, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def snapshot(item):
    return {'id': item.id, 'reference': item.reference,
        'incident_id': item.incident_id, 'incident_reference': item.incident_reference,
        **{field: getattr(item, field) for field in EDITABLE if field not in {'quantity', 'needed_by'}},
        'quantity': quantity_text(item.quantity), 'needed_by': item.needed_by.astimezone(timezone.utc).isoformat(), 'needed_by_raw': item.needed_by_raw,
        'status': item.status, 'version': item.version, 'created_actor': item.created_actor,
        'created_at': item.created_at.astimezone(timezone.utc).isoformat(), 'updated_at': item.updated_at.astimezone(timezone.utc).isoformat()}


def describe(item, now=None):
    return {**snapshot(item), 'past_deadline': item.status != 'cancelled' and item.needed_by < (now or utcnow()),
        'allowed_transitions': TRANSITIONS[item.status]}


def add_event(session, item, actor, actor_id, action, reason, before):
    session.add(ReliefRequestEvent(id=str(uuid4()), workspace_id=item.workspace_id, request_id=item.id,
        version=item.version, action=action, actor_id=actor_id, actor=actor, created_at=item.updated_at,
        reason=reason, before=before, after=snapshot(item)))


def writer(session, context):
    if context.actor_id is None or context.role not in {'owner', 'editor'}:
        raise HTTPException(403, 'Sign in to an organisation as an owner or editor to manage relief requests. Demo examples are read-only.')
    require_workspace(session, context.workspace_id, lock=True)
    membership = session.get(Membership, (context.actor_id, context.workspace_id))
    if membership is None or membership.role not in {'owner', 'editor'}:
        raise HTTPException(403, 'This account no longer has permission to change requests.')


def find_request(session, context, request_id, lock=False):
    query = select(ReliefRequest).where(ReliefRequest.workspace_id == context.workspace_id, ReliefRequest.id == str(request_id))
    item = session.scalar(query.with_for_update() if lock else query)
    if item is None:
        raise HTTPException(404, 'This relief request was not found in the selected organisation.')
    return item


@router.get('/relief-requests')
def list_requests(context: Context, session: DB, q: str = Query(default='', max_length=200),
    status: Literal['all', 'draft', 'submitted', 'reviewed', 'cancelled'] = 'all',
    category: Literal['all', 'food', 'water', 'medicine', 'shelter', 'other'] = 'all', page: int = Query(default=1, ge=1, le=100000)):
    with session.begin():
        workspace = session.scalar(select(Workspace).where(Workspace.id == context.workspace_id).with_for_update(read=True))
        if workspace is None:
            raise HTTPException(503, 'The workspace needs its database setup.')
        counts = dict(session.execute(select(ReliefRequest.status, func.count()).where(ReliefRequest.workspace_id == context.workspace_id).group_by(ReliefRequest.status)).all())
        filters = [ReliefRequest.workspace_id == context.workspace_id]
        if status != 'all':
            filters.append(ReliefRequest.status == status)
        if category != 'all':
            filters.append(ReliefRequest.category == category)
        if q.strip():
            filters.append(or_(*(func.lower(getattr(ReliefRequest, field)).contains(q.strip().lower(), autoescape=True)
                for field in ('reference', 'requesting_organisation', 'locality', 'item_name', 'source_name'))))
        total = session.scalar(select(func.count()).select_from(ReliefRequest).where(*filters))
        pages = max(1, (total + 19) // 20)
        current_page = min(page, pages)
        items = session.scalars(select(ReliefRequest).where(*filters).order_by(ReliefRequest.updated_at.desc(), ReliefRequest.id).offset((current_page - 1) * 20).limit(20)).all()
        now = utcnow()
        return {'items': [describe(item, now) for item in items], 'total': total,
            'counts': {'all': sum(counts.values()), **{key: counts.get(key, 0) for key in TRANSITIONS}},
            'page': current_page, 'page_size': 20, 'total_pages': pages, 'server_time': now,
            'can_edit': context.actor_id is not None and context.role in {'owner', 'editor'} and not workspace.is_demo, 'is_demo': workspace.is_demo}


@router.post('/relief-requests', status_code=201)
def create_request(body: NewRequest, context: Context, session: DB, response: Response):
    with session.begin():
        writer(session, context)
        digest = create_digest(body)
        previous = session.scalar(select(ReliefRequest).where(ReliefRequest.workspace_id == context.workspace_id, ReliefRequest.submission_key == str(body.submission_key)))
        if previous:
            if previous.create_digest != digest:
                raise HTTPException(409, 'This save identifier was already used for different details. Refresh the list to inspect the saved request.')
            response.status_code = 200
            return {'request': describe(previous), 'duplicate': True}
        if session.scalar(select(ReliefRequest.id).where(ReliefRequest.workspace_id == context.workspace_id, ReliefRequest.reference_key == body.reference.upper())):
            raise HTTPException(409, 'That request reference already exists in this organisation. Search for it in the request list.')
        incident = None
        if body.incident_id is not None:
            incident = session.scalar(select(Incident).where(Incident.workspace_id == context.workspace_id, Incident.id == str(body.incident_id)))
            if incident is None:
                raise HTTPException(404, 'The linked incident was not found in this organisation.')
            if incident.status != 'reviewed':
                raise HTTPException(409, 'Review the incident evidence before linking a new relief request.')
        now = utcnow()
        item = ReliefRequest(id=str(uuid4()), workspace_id=context.workspace_id, reference=body.reference,
            incident_id=incident.id if incident else None,
            incident_reference=incident.assessment['external_reference'] if incident else None,
            reference_key=body.reference.upper(), submission_key=str(body.submission_key), create_digest=digest,
            **{field: getattr(body, field) for field in EDITABLE if field != 'needed_by'},
            needed_by=parse_timestamp(body.needed_by), needed_by_raw=body.needed_by,
            status='draft', version=1, created_by=context.actor_id, created_actor=context.actor,
            created_at=now, updated_at=now)
        session.add(item)
        session.flush()
        add_event(session, item, context.actor, context.actor_id, 'created', 'Request recorded as a draft.', None)
        return {'request': describe(item), 'duplicate': False}


@router.get('/relief-requests/{request_id}')
def request_detail(request_id: UUID, context: Context, session: DB, before_version: int | None = Query(default=None, ge=1)):
    with session.begin():
        workspace = session.scalar(select(Workspace).where(Workspace.id == context.workspace_id).with_for_update(read=True))
        if workspace is None:
            raise HTTPException(503, 'The workspace needs its database setup.')
        item = find_request(session, context, request_id)
        conditions = [ReliefRequestEvent.workspace_id == context.workspace_id, ReliefRequestEvent.request_id == item.id]
        if before_version is not None:
            conditions.append(ReliefRequestEvent.version < before_version)
        events = session.scalars(select(ReliefRequestEvent).where(*conditions).order_by(ReliefRequestEvent.version.desc()).limit(50)).all()
        return {'request': describe(item), 'events': [{key: getattr(event, key) for key in
            ('id', 'version', 'action', 'actor', 'created_at', 'reason', 'before', 'after')} for event in events],
            'next_before_version': events[-1].version if events and events[-1].version > 1 else None}


def check_version(item, expected):
    if item.version != expected:
        raise HTTPException(409, 'This request changed after you opened it. Refresh its details before trying again.')


@router.patch('/relief-requests/{request_id}')
def edit_request(request_id: UUID, body: EditRequest, context: Context, session: DB):
    with session.begin():
        writer(session, context)
        item = find_request(session, context, request_id, lock=True)
        check_version(item, body.expected_version)
        if item.status != 'draft':
            raise HTTPException(409, 'Return this request to draft before changing its details.')
        if not body.reason.strip():
            raise HTTPException(422, 'Explain the correction before saving.')
        before = snapshot(item)
        if normalized(body) == {key: before[key] for key in EDITABLE}:
            return {'request': describe(item), 'unchanged': True}
        for field in EDITABLE:
            setattr(item, field, parse_timestamp(body.needed_by) if field == 'needed_by' else getattr(body, field))
        item.needed_by_raw = body.needed_by
        item.version += 1
        item.updated_at = utcnow()
        add_event(session, item, context.actor, context.actor_id, 'edited', body.reason.strip(), before)
        return {'request': describe(item), 'unchanged': False}


@router.post('/relief-requests/{request_id}/status')
def change_status(request_id: UUID, body: StatusChange, context: Context, session: DB):
    with session.begin():
        writer(session, context)
        item = find_request(session, context, request_id, lock=True)
        check_version(item, body.expected_version)
        if body.status == item.status:
            return {'request': describe(item), 'unchanged': True}
        if body.status not in TRANSITIONS[item.status]:
            raise HTTPException(409, 'That status change is not allowed. Refresh the request and choose an available action.')
        before = snapshot(item)
        item.status, item.version, item.updated_at = body.status, item.version + 1, utcnow()
        add_event(session, item, context.actor, context.actor_id, 'status_changed', body.reason, before)
        return {'request': describe(item), 'unchanged': False}
