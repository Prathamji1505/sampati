"""Warning evidence -> explained civilian preparation -> current human review."""
from datetime import timedelta
from decimal import Decimal
import hmac
import secrets
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from .auth import AccessContext, Context, token_digest
from .automation import require_owner
from .config import settings
from .database import get_session
from .inventory import scoped, workspace_lock
from .models import Aircraft, DataSource, InventoryItem, Membership, ReliefRequest, StockPosition, StockRecord, StorageLocation, utcnow
from .response_models import AircraftSupport, ResponseEvent, ResponsePlan, ResponseSignal
from .response_rules import LIMITS, RULE_VERSION, evaluate_response, fresh, instant, quantity, stable_hash

router = APIRouter(prefix='/response', tags=['Civilian response preparation'])
ingest_router = APIRouter(tags=['Warning connector uploads'])
DB = Annotated[Session, Depends(get_session)]
Check = Literal['confirmed', 'hold', 'unknown']


class CleanInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

    @field_validator('*', mode='before')
    @classmethod
    def reject_bool_numbers(cls, value, info):
        if isinstance(value, bool) and info.field_name in {'cargo_allowance_kg', 'unit_weight_kg'}:
            raise ValueError('Enter an exact positive weight in kilograms.')
        return value


class DatedInput(CleanInput):
    source_name: str = Field(min_length=2, max_length=120)
    observed_at: str = Field(min_length=1, max_length=64)

    @field_validator('observed_at')
    @classmethod
    def dated(cls, value):
        date = instant(value)
        if date > utcnow() + timedelta(minutes=5):
            raise ValueError('The source timestamp is in the future.')
        return date.isoformat()


class SignalInput(DatedInput):
    reference: str = Field(min_length=1, max_length=64, pattern=r'^[A-Za-z0-9][A-Za-z0-9._/-]*$')
    kind: Literal['warning', 'news']
    title: str = Field(min_length=3, max_length=160)
    locality: str = Field(min_length=2, max_length=160)
    severity: Literal['extreme', 'severe', 'moderate', 'minor', 'unknown']
    certainty: Literal['observed', 'likely', 'possible', 'unlikely', 'unknown']
    expires_at: str = Field(min_length=1, max_length=64)
    source_url: str = Field(default='', max_length=1000)
    description: str = Field(min_length=3, max_length=3000)

    @field_validator('source_url')
    @classmethod
    def safe_url(cls, value):
        # Stored reference only. The application never fetches user-provided URLs.
        from urllib.parse import urlsplit
        url = urlsplit(value)
        if value and (url.scheme not in {'http', 'https'} or not url.hostname or url.username or url.password):
            raise ValueError('Use an HTTP(S) source link without embedded credentials, or leave it empty.')
        return value

    @field_validator('expires_at')
    @classmethod
    def expiry(cls, value):
        return instant(value).isoformat()

    @model_validator(mode='after')
    def valid_window(self):
        if instant(self.expires_at) <= instant(self.observed_at):
            raise ValueError('Expiry must follow the source observation.')
        return self


class Decision(CleanInput):
    expected_version: int = Field(ge=1, strict=True)
    reason: str = Field(min_length=3, max_length=500)


class SignalReview(Decision):
    state: Literal['verified', 'dismissed']


class SupportInput(DatedInput):
    expected_version: int = Field(ge=0, strict=True)
    cargo_allowance_kg: Decimal = Field(gt=0, le=1000000, max_digits=12, decimal_places=3, allow_inf_nan=False)
    crew: Check
    maintenance: Check
    fuel: Check
    reason: str = Field(min_length=3, max_length=500)


class Conditions(DatedInput):
    weather: Check
    destination_access: Check


class NeedInput(CleanInput):
    request_id: UUID
    item_id: UUID
    location_id: UUID
    unit_weight_kg: Decimal = Field(gt=0, le=1000000, max_digits=12, decimal_places=3, allow_inf_nan=False)
    item_name_confirmed: bool = Field(strict=True)
    weight_source: str = Field(min_length=2, max_length=120)


class PlanInput(CleanInput):
    title: str = Field(min_length=3, max_length=160)
    signal_id: UUID
    needs: list[NeedInput] = Field(min_length=1, max_length=LIMITS['requests'])
    conditions: Conditions

    @model_validator(mode='after')
    def unique_needs(self):
        if len({row.request_id for row in self.needs}) != len(self.needs):
            raise ValueError('Select each supply request once.')
        return self


class SavePlan(PlanInput):
    submission_key: UUID
    evaluation_hash: str = Field(pattern=r'^[a-f0-9]{64}$')


class ReviewPlan(Decision):
    evaluation_hash: str = Field(pattern=r'^[a-f0-9]{64}$')


class SourceInput(CleanInput):
    name: str = Field(min_length=2, max_length=100)


class SourcePolicy(Decision):
    enabled: bool = Field(strict=True)


def journal(session, context, kind, identifier, version, action, reason, after):
    session.add(ResponseEvent(id=str(uuid4()), workspace_id=context.workspace_id, entity_kind=kind,
        entity_id=identifier, version=version, actor=context.actor, action=action, reason=reason,
        created_at=utcnow(), after=after))


def signal_view(item):
    return {**item.payload, 'id': item.id, 'state': item.state, 'version': item.version, 'received_at': item.received_at.isoformat()}


def source_view(item):
    return {'id': item.id, 'name': item.name, 'enabled': item.enabled, 'version': item.policy_version,
        'last_received_at': item.last_received_at.isoformat() if item.last_received_at else None,
        'ingest_path': '/api/response/ingest/' + item.id}


def receive_signal(session, context, body, origin):
    payload = body.model_dump(mode='json')
    digest = stable_hash(payload)
    identity = stable_hash([origin, body.reference.casefold()])
    existing = session.scalar(select(ResponseSignal).where(ResponseSignal.workspace_id == context.workspace_id,
        ResponseSignal.identity_key == identity))
    if existing:
        if existing.digest != digest:
            raise HTTPException(409, 'This source reference has different evidence. Send a new revision reference; the original stays intact.')
        return {'signal': signal_view(existing), 'duplicate': True}
    pending = session.scalar(select(func.count()).select_from(ResponseSignal).where(
        ResponseSignal.workspace_id == context.workspace_id, ResponseSignal.state == 'unreviewed'))
    if pending >= 1000:
        raise HTTPException(409, 'Review pending warnings before adding more; this workspace has 1,000 unreviewed reports.')
    item = ResponseSignal(id=str(uuid4()), workspace_id=context.workspace_id, identity_key=identity, digest=digest,
        payload=payload, state='unreviewed', version=1, received_at=utcnow())
    session.add(item)
    journal(session, context, 'signal', item.id, 1, 'received', 'Source evidence received; human verification required.', signal_view(item))
    session.flush()
    return {'signal': signal_view(item), 'duplicate': False}


def events(session, context, kind, identifier):
    rows = session.scalars(select(ResponseEvent).where(ResponseEvent.workspace_id == context.workspace_id,
        ResponseEvent.entity_kind == kind, ResponseEvent.entity_id == identifier).order_by(ResponseEvent.version.desc()).limit(100)).all()
    return [{key: getattr(row, key) for key in ('version', 'actor', 'action', 'reason', 'created_at', 'after')} for row in rows]


@router.get('/catalog')
def catalog(context: Context, session: DB):
    with session.begin():
        workspace_lock(session, context)
        aircraft = session.scalars(select(Aircraft).where(Aircraft.workspace_id == context.workspace_id).order_by(Aircraft.aircraft_id).limit(LIMITS['aircraft'] + 1)).all()
        profiles = {row.aircraft_id: row for row in session.scalars(select(AircraftSupport).where(AircraftSupport.workspace_id == context.workspace_id))}
        return {'aircraft': [{'aircraft_id': row.aircraft_id, 'display_name': row.display_name,
            'reported_status': row.reported_status, 'source_updated_at': row.source_updated_at.isoformat(),
            'support': {**profiles[row.aircraft_id].payload, 'version': profiles[row.aircraft_id].version} if row.aircraft_id in profiles else None}
            for row in aircraft[:LIMITS['aircraft']]], 'aircraft_limit_exceeded': len(aircraft) > LIMITS['aircraft'],
            'rule_version': RULE_VERSION, 'freshness_hours': settings.freshness_hours,
            'can_edit': not context.role == 'demo' and context.role in {'owner', 'editor'}, 'can_manage_sources': context.role == 'owner'}


@router.get('/signals')
def signals(context: Context, session: DB, page: int = Query(1, ge=1, le=100000)):
    with session.begin():
        workspace_lock(session, context)
        base = ResponseSignal.workspace_id == context.workspace_id
        total = session.scalar(select(func.count()).select_from(ResponseSignal).where(base))
        rows = session.scalars(select(ResponseSignal).where(base).order_by(ResponseSignal.received_at.desc(), ResponseSignal.id).offset((page - 1) * 20).limit(20)).all()
        return {'items': [signal_view(row) for row in rows], 'total': total, 'page': page, 'total_pages': max(1, (total + 19) // 20)}


@router.post('/signals', status_code=201)
def add_signal(body: SignalInput, context: Context, session: DB, response: Response):
    with session.begin():
        workspace_lock(session, context, write=True)
        result = receive_signal(session, context, body, 'manual:' + body.source_name.casefold())
        if result['duplicate']:
            response.status_code = 200
        return result


@router.get('/signals/{identifier}')
def signal_detail(identifier: UUID, context: Context, session: DB):
    with session.begin():
        workspace_lock(session, context)
        item = scoped(session, ResponseSignal, context, identifier)
        return {'signal': signal_view(item), 'events': events(session, context, 'signal', item.id)}


@router.post('/signals/{identifier}/review')
def review_signal(identifier: UUID, body: SignalReview, context: Context, session: DB):
    with session.begin():
        workspace_lock(session, context, write=True)
        item = scoped(session, ResponseSignal, context, identifier)
        if item.version != body.expected_version:
            raise HTTPException(409, 'The warning changed. Open it again before reviewing.')
        if item.state != body.state:
            item.state, item.version = body.state, item.version + 1
            journal(session, context, 'signal', item.id, item.version, body.state, body.reason, signal_view(item))
        return {'signal': signal_view(item)}


@router.put('/aircraft/{aircraft_id}')
def support(aircraft_id: str, body: SupportInput, context: Context, session: DB):
    with session.begin():
        workspace_lock(session, context, write=True)
        aircraft = session.scalar(select(Aircraft).where(Aircraft.workspace_id == context.workspace_id, Aircraft.aircraft_id == aircraft_id))
        if aircraft is None:
            raise HTTPException(404, 'Import this aircraft into your organisation register first.')
        item = session.get(AircraftSupport, (context.workspace_id, aircraft_id))
        payload = body.model_dump(mode='json', exclude={'expected_version', 'reason'})
        payload['cargo_allowance_kg'] = quantity(body.cargo_allowance_kg)
        if item and item.payload == payload:
            return {'support': {**item.payload, 'version': item.version}, 'duplicate': True}
        if (item.version if item else 0) != body.expected_version:
            raise HTTPException(409, 'The support report changed. Reload it before saving.')
        if item and instant(payload['observed_at']) < instant(item.payload['observed_at']):
            raise HTTPException(409, 'An older support observation cannot replace the current report.')
        if item is None:
            item = AircraftSupport(workspace_id=context.workspace_id, aircraft_id=aircraft_id, version=0)
            session.add(item)
        item.payload, item.version = payload, item.version + 1
        journal(session, context, 'aircraft', aircraft_id, item.version, 'support_recorded', body.reason, payload)
        return {'support': {**payload, 'version': item.version}, 'duplicate': False}


@router.get('/aircraft/{aircraft_id}/history')
def support_history(aircraft_id: str, context: Context, session: DB):
    with session.begin():
        workspace_lock(session, context)
        return {'events': events(session, context, 'aircraft', aircraft_id)}


def load_facts(session, context, body):
    signal = scoped(session, ResponseSignal, context, body.signal_id)
    ids = [str(row.request_id) for row in body.needs]
    requests = {row.id: row for row in session.scalars(select(ReliefRequest).where(ReliefRequest.workspace_id == context.workspace_id, ReliefRequest.id.in_(ids)))}
    item_ids = [str(row.item_id) for row in body.needs]
    location_ids = [str(row.location_id) for row in body.needs]
    items = {row.id: row for row in session.scalars(select(InventoryItem).where(InventoryItem.workspace_id == context.workspace_id, InventoryItem.id.in_(item_ids)))}
    locations = set(session.scalars(select(StorageLocation.id).where(StorageLocation.workspace_id == context.workspace_id, StorageLocation.id.in_(location_ids))))
    positions = {(row.item_id, row.location_id): row for row in session.scalars(select(StockPosition).where(StockPosition.workspace_id == context.workspace_id, StockPosition.item_id.in_(item_ids), StockPosition.location_id.in_(location_ids)))}
    signed = case((StockRecord.kind == 'reserve', StockRecord.quantity), (StockRecord.kind.in_(['release', 'return']), -StockRecord.quantity), else_=Decimal(0))
    claims = session.execute(select(StockRecord.request_id, InventoryItem.unit, InventoryItem.category, func.sum(signed)).join(StockPosition, StockPosition.id == StockRecord.position_id).join(InventoryItem, InventoryItem.id == StockPosition.item_id).where(StockRecord.workspace_id == context.workspace_id, StockRecord.request_id.in_(ids)).group_by(StockRecord.request_id, InventoryItem.unit, InventoryItem.category)).all()
    observed = dict(session.execute(select(StockRecord.position_id, func.max(StockRecord.observed_at)).where(StockRecord.workspace_id == context.workspace_id, StockRecord.position_id.in_([p.id for p in positions.values()]), StockRecord.kind != 'report').group_by(StockRecord.position_id)).all())
    needs = []
    for line in body.needs:
        request = requests.get(str(line.request_id)); item = items.get(str(line.item_id)); location_id = str(line.location_id)
        if request is None or item is None or location_id not in locations:
            raise HTTPException(404, 'A selected need, item or store was not found in your organisation.')
        position = positions.get((item.id, location_id))
        compatible = [(unit, category, amount) for rid, unit, category, amount in claims if rid == request.id]
        needs.append({'request_id': request.id, 'reference': request.reference, 'status': request.status, 'version': request.version,
            'locality': request.locality, 'needed_by': request.needed_by.isoformat(), 'quantity': quantity(request.quantity),
            'unit': request.unit, 'category': request.category, 'item_id': item.id, 'item_unit': item.unit, 'item_category': item.category,
            'committed': quantity(sum((amount for unit, category, amount in compatible if unit == request.unit and category == request.category), Decimal(0))),
            'incompatible_commitments': any(amount > 0 and (unit != request.unit or category != request.category) for unit, category, amount in compatible),
            'location_id': location_id, 'on_hand': quantity(position.on_hand) if position else '0', 'reserved': quantity(position.reserved) if position else '0',
            'stock_version': position.version if position else 0, 'stock_updated_at': observed[position.id].isoformat() if position and position.id in observed else '1970-01-01T00:00:00+00:00',
            'unit_weight_kg': quantity(line.unit_weight_kg), 'item_name_confirmed': line.item_name_confirmed, 'weight_source': line.weight_source})
    aircraft = session.scalars(select(Aircraft).where(Aircraft.workspace_id == context.workspace_id).order_by(Aircraft.aircraft_id).limit(LIMITS['aircraft'] + 1)).all()
    if len(aircraft) > LIMITS['aircraft']:
        raise HTTPException(409, 'This planner supports up to 500 aircraft per organisation; narrow the register before evaluating.')
    profiles = {row.aircraft_id: row for row in session.scalars(select(AircraftSupport).where(AircraftSupport.workspace_id == context.workspace_id))}
    return {'signal': signal_view(signal), 'conditions': body.conditions.model_dump(mode='json'), 'needs': needs,
        'aircraft': [{'aircraft_id': row.aircraft_id, 'display_name': row.display_name, 'reported_status': row.reported_status,
            'source_updated_at': row.source_updated_at.isoformat(), 'support': {**profiles[row.aircraft_id].payload,
                'version': profiles[row.aircraft_id].version} if row.aircraft_id in profiles else None} for row in aircraft]}


def evaluate(session, context, body):
    return evaluate_response(load_facts(session, context, body), now=utcnow(), freshness_hours=settings.freshness_hours)


@router.post('/evaluate')
def preview(body: PlanInput, context: Context, session: DB):
    with session.begin():
        workspace_lock(session, context)
        return evaluate(session, context, body)


@router.post('/plans', status_code=201)
def save(body: SavePlan, context: Context, session: DB, response: Response):
    with session.begin():
        workspace_lock(session, context, write=True)
        inputs = body.model_dump(mode='json', exclude={'submission_key', 'evaluation_hash'})
        digest = stable_hash(inputs)
        existing = session.scalar(select(ResponsePlan).where(ResponsePlan.workspace_id == context.workspace_id, ResponsePlan.submission_key == str(body.submission_key)))
        if existing:
            if existing.input_digest != digest:
                raise HTTPException(409, 'This save key belongs to a different workflow. Use a new draft.')
            response.status_code = 200
            return {'plan': plan_view(existing), 'duplicate': True}
        facts = load_facts(session, context, body)
        decision = evaluate_response(facts, now=utcnow(), freshness_hours=settings.freshness_hours)
        if decision['evaluation_hash'] != body.evaluation_hash:
            raise HTTPException(409, 'The evidence or its freshness changed. Evaluate the workflow again before saving.')
        item = ResponsePlan(id=str(uuid4()), workspace_id=context.workspace_id, signal_id=str(body.signal_id),
            submission_key=str(body.submission_key), input_digest=digest, inputs=inputs,
            snapshot={'decision': decision, 'facts': facts}, state='draft', version=1, created_at=utcnow())
        session.add(item)
        journal(session, context, 'plan', item.id, 1, 'draft_saved', 'Explained preparation workflow saved without reserving resources.', item.snapshot)
        return {'plan': plan_view(item), 'duplicate': False}


def plan_view(item):
    return {'id': item.id, 'title': item.inputs['title'], 'state': item.state, 'version': item.version,
        'created_at': item.created_at.isoformat(), 'snapshot': item.snapshot, 'inputs': item.inputs}


@router.get('/plans')
def plans(context: Context, session: DB, page: int = Query(1, ge=1, le=100000)):
    with session.begin():
        workspace_lock(session, context)
        base = ResponsePlan.workspace_id == context.workspace_id
        total = session.scalar(select(func.count()).select_from(ResponsePlan).where(base))
        rows = session.scalars(select(ResponsePlan).where(base).order_by(ResponsePlan.created_at.desc(), ResponsePlan.id).offset((page - 1) * 20).limit(20)).all()
        return {'items': [{'id': r.id, 'title': r.inputs['title'], 'state': r.state, 'version': r.version,
            'created_at': r.created_at, 'snapshot_status': r.snapshot['decision']['status']} for r in rows],
            'total': total, 'page': page, 'total_pages': max(1, (total + 19) // 20)}


@router.get('/plans/{identifier}')
def plan_detail(identifier: UUID, context: Context, session: DB):
    with session.begin():
        workspace_lock(session, context)
        item = scoped(session, ResponsePlan, context, identifier)
        current = evaluate(session, context, PlanInput.model_validate(item.inputs))
        unchanged = current['evaluation_hash'] == item.snapshot['decision']['evaluation_hash']
        return {'plan': plan_view(item), 'current': current, 'is_current': unchanged,
            'effective_state': item.state if unchanged else 'recheck_required', 'events': events(session, context, 'plan', item.id)}


@router.post('/plans/{identifier}/review')
def review_plan(identifier: UUID, body: ReviewPlan, context: Context, session: DB):
    with session.begin():
        workspace_lock(session, context, write=True)
        item = scoped(session, ResponsePlan, context, identifier)
        current = evaluate(session, context, PlanInput.model_validate(item.inputs))
        if current['status'] != 'reviewable' or current['evaluation_hash'] != body.evaluation_hash or current['evaluation_hash'] != item.snapshot['decision']['evaluation_hash']:
            raise HTTPException(409, 'This workflow is blocked or its evidence changed. Evaluate and save a new draft.')
        if item.state == 'reviewed':
            return {'plan': plan_view(item), 'duplicate': True}
        if item.version != body.expected_version:
            raise HTTPException(409, 'The workflow changed. Open the latest draft.')
        item.state, item.version = 'reviewed', item.version + 1
        journal(session, context, 'plan', item.id, item.version, 'coordinator_review', body.reason, {'evaluation_hash': current['evaluation_hash'], 'state': item.state})
        return {'plan': plan_view(item), 'duplicate': False}


@router.get('/sources')
def sources(context: Context, session: DB):
    with session.begin():
        workspace_lock(session, context)
        return {'items': [source_view(r) for r in session.scalars(select(DataSource).where(DataSource.workspace_id == context.workspace_id, DataSource.purpose == 'response').order_by(DataSource.created_at))]}


@router.post('/sources', status_code=201)
def create_source(body: SourceInput, context: Context, session: DB):
    token = secrets.token_urlsafe(32)
    with session.begin():
        require_owner(session, context)
        if session.scalar(select(func.count()).select_from(DataSource).where(DataSource.workspace_id == context.workspace_id, DataSource.purpose == 'response')) >= 50:
            raise HTTPException(409, 'This workspace already has 50 warning connectors.')
        item = DataSource(id=str(uuid4()), workspace_id=context.workspace_id, created_by=context.actor_id,
            name=body.name, token_hash=token_digest(token), enabled=True, purpose='response', automation_mode='review', policy_version=1)
        session.add(item); session.flush()
        journal(session, context, 'source', item.id, 1, 'created', 'Warning-only source created. Reports require human verification.', source_view(item))
        return {**source_view(item), 'token': token}


@router.patch('/sources/{identifier}')
def policy(identifier: UUID, body: SourcePolicy, context: Context, session: DB):
    with session.begin():
        require_owner(session, context)
        item = scoped(session, DataSource, context, identifier)
        if item.purpose != 'response':
            raise HTTPException(404, 'Warning connector not found.')
        if body.expected_version != item.policy_version:
            raise HTTPException(409, 'The connector changed. Reload its policy.')
        item.enabled, item.policy_version = body.enabled, item.policy_version + 1
        journal(session, context, 'source', item.id, item.policy_version, 'policy_changed', body.reason, source_view(item))
        return source_view(item)


@router.post('/sources/{identifier}/rotate')
def rotate(identifier: UUID, body: Decision, context: Context, session: DB):
    token = secrets.token_urlsafe(32)
    with session.begin():
        require_owner(session, context)
        item = scoped(session, DataSource, context, identifier)
        if item.purpose != 'response':
            raise HTTPException(404, 'Warning connector not found.')
        if body.expected_version != item.policy_version:
            raise HTTPException(409, 'The connector changed. Reload its policy.')
        item.token_hash, item.created_by, item.policy_version = token_digest(token), context.actor_id, item.policy_version + 1
        journal(session, context, 'source', item.id, item.policy_version, 'key_rotated', body.reason, source_view(item))
        return {**source_view(item), 'token': token}


@ingest_router.post('/api/response/ingest/{identifier}', status_code=202)
def ingest(identifier: UUID, body: SignalInput, request: Request, session: DB):
    authorization = request.headers.get('authorization', '')
    token = authorization[7:] if authorization.startswith('Bearer ') else ''
    with session.begin():
        item = session.get(DataSource, str(identifier))
        if item is None or item.purpose != 'response' or not item.enabled or not token or not hmac.compare_digest(item.token_hash, token_digest(token)):
            raise HTTPException(401, 'The warning-only source key is invalid or disabled.')
        context = AccessContext(item.workspace_id, item.created_by, 'Warning connector: ' + item.name[:95], 'editor')
        workspace_lock(session, context, write=True)
        # Re-read after the shared workspace lock: disable/rotation may have won.
        session.refresh(item)
        if not item.enabled or not hmac.compare_digest(item.token_hash, token_digest(token)):
            raise HTTPException(401, 'The warning source key changed or was disabled.')
        result = receive_signal(session, context, body, 'source:' + item.id)
        item.last_received_at = utcnow()
        return result
