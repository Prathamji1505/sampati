"""Source-scoped relief intake. Rules create drafts; people confirm needs and logistics."""
from datetime import timezone
import hmac
import json
import secrets
from typing import Annotated, Literal
from uuid import UUID, uuid4, uuid5

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .auth import AccessContext, Context, token_digest
from .automation_files import CONTRACT, HEADERS, MAX_FILE, IntakeRow, example_payload, parse_file, stable_hash
from .config import settings
from .database import get_session
from .imports import safe_filename
from .models import (AutomationReceipt, AutomationReceiptEvent, AutomationSourceEvent, DataSource,
    InventoryItem, Membership, ReliefRequest, StockPosition, StorageLocation, utcnow)
from .relief import EDITABLE, NewRequest, create_locked, quantity_text, snapshot as request_snapshot, writer
from .services import require_workspace

router = APIRouter(prefix='/automation', tags=['Automation inbox'])
ingest_router = APIRouter(tags=['Relief connector uploads'])
DB = Annotated[Session, Depends(get_session)]
RULE_VERSION = 'relief-drafts.v1'


class SourceInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=100)


class Decision(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    expected_version: int = Field(ge=1, strict=True)
    reason: str = Field(min_length=1, max_length=500)


class Policy(Decision):
    enabled: bool = Field(strict=True)
    automation_mode: Literal['review', 'new_drafts']


class Apply(Decision):
    plan_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    acknowledge_warnings: bool = Field(default=False, strict=True)


def source_snapshot(source):
    return {key: getattr(source, key) for key in ('id', 'name', 'enabled', 'automation_mode', 'policy_version')}


def source_description(source):
    return {**source_snapshot(source), 'created_at': source.created_at, 'last_received_at': source.last_received_at,
        'ingest_path': f'/api/automation/ingest/{source.id}'}


def source_event(session, source, context, action, reason, before=None):
    session.add(AutomationSourceEvent(id=str(uuid4()), workspace_id=source.workspace_id, source_id=source.id,
        version=source.policy_version, action=action, actor_id=context.actor_id, actor=context.actor,
        created_at=utcnow(), reason=reason, before=before, after=source_snapshot(source)))


def require_owner(session, context):
    writer(session, context)
    if session.get(Membership, (context.actor_id, context.workspace_id)).role != 'owner':
        raise HTTPException(403, 'Only an organisation owner can manage trusted sources and automation rules.')


def find_source(session, context, source_id, lock=False):
    query = select(DataSource).where(DataSource.workspace_id == context.workspace_id,
        DataSource.id == str(source_id), DataSource.purpose == 'relief')
    source = session.scalar(query.with_for_update() if lock else query)
    if source is None:
        raise HTTPException(404, 'This relief source was not found in the selected organisation.')
    return source


def find_receipt(session, context, receipt_id, lock=False):
    query = select(AutomationReceipt).where(AutomationReceipt.workspace_id == context.workspace_id,
        AutomationReceipt.id == str(receipt_id))
    item = session.scalar(query.with_for_update() if lock else query)
    if item is None:
        raise HTTPException(404, 'This intake file was not found in the selected organisation.')
    return item


def receipt_snapshot(item):
    return {'id': item.id, 'state': item.state, 'version': item.version, 'automatic': item.automatic,
        'results': item.results, 'reviewed_at': item.reviewed_at.astimezone(timezone.utc).isoformat() if item.reviewed_at else None,
        'source_policy_version': item.source_policy_version, 'source_policy_mode': item.source_policy_mode,
        'rule_version': RULE_VERSION}


def receipt_event(session, item, context, action, reason):
    session.add(AutomationReceiptEvent(id=str(uuid4()), workspace_id=item.workspace_id, receipt_id=item.id,
        version=item.version, action=action, actor_id=context.actor_id, actor=context.actor,
        created_at=item.reviewed_at or item.received_at, reason=reason, after=receipt_snapshot(item)))


def warnings_for(session, source, item):
    warnings = []
    if item.observed_at and (utcnow() - item.observed_at).total_seconds() > settings.freshness_hours * 3600:
        warnings.append({'code': 'stale', 'message': f'This source observation is older than {settings.freshness_hours} hours. Check whether the needs are still current.'})
    if not source.enabled:
        warnings.append({'code': 'disabled', 'message': 'This source is disabled. Verify the saved evidence before accepting this file.'})
    member = session.get(Membership, (source.created_by, source.workspace_id))
    if member is None or member.role not in {'owner', 'editor'}:
        warnings.append({'code': 'issuer_access', 'message': 'The source key issuer no longer has write access. An owner must rotate the key before new files can arrive.'})
    return warnings


def plan_for(session, item, source):
    keys = [row['reference'] for row in item.rows]
    existing = {request.reference_key: request for request in session.scalars(select(ReliefRequest).where(
        ReliefRequest.workspace_id == item.workspace_id, ReliefRequest.reference_key.in_(keys))).all()} if keys else {}
    proposals = []
    for row in item.rows:
        target = existing.get(row['reference'])
        values = {key: row[key] for key in EDITABLE}
        before = request_snapshot(target) if target else None
        differences = [{'field': key, 'accepted': before[key], 'incoming': values[key]} for key in EDITABLE
            if before is not None and before[key] != values[key]]
        proposals.append({'row': row['row'], 'reference': row['reference'], 'values': values,
            'action': 'new_draft' if target is None else 'conflict' if differences else 'duplicate',
            'request_id': target.id if target else None, 'request_version': target.version if target else None,
            'request_status': target.status if target else None, 'differences': differences})
    warnings = warnings_for(session, source, item)
    counts = {key: sum(row['action'] == key for row in proposals) for key in ('new_draft', 'duplicate', 'conflict')}
    digest = stable_hash({'receipt_id': item.id, 'version': item.version, 'rows': proposals,
        'source': source_snapshot(source), 'warnings': [warning['code'] for warning in warnings], 'rule_version': RULE_VERSION})
    return {'proposals': proposals, 'counts': counts, 'warnings': warnings, 'plan_hash': digest,
        'can_apply': not item.errors and counts['conflict'] == 0 and bool(proposals) and item.state == 'pending'}


def stock_hints(session, item):
    pairs = {(row['category'], row['unit']) for row in item.rows}
    if not pairs:
        return []
    available = StockPosition.on_hand - StockPosition.reserved
    ranked = select(StockPosition.id.label('position_id'), InventoryItem.name.label('item_name'), InventoryItem.category,
        InventoryItem.unit, StorageLocation.name.label('store_name'), available.label('available'),
        func.row_number().over(partition_by=(InventoryItem.category, InventoryItem.unit), order_by=(available.desc(), StockPosition.id)).label('rank'))\
        .join(InventoryItem, InventoryItem.id == StockPosition.item_id).join(StorageLocation, StorageLocation.id == StockPosition.location_id)\
        .where(StockPosition.workspace_id == item.workspace_id, available > 0,
            or_(*[(InventoryItem.category == category) & (InventoryItem.unit == unit) for category, unit in pairs])).subquery()
    return [{**dict(row), 'available': quantity_text(row.available)} for row in session.execute(select(ranked).where(ranked.c.rank <= 3)).mappings()]


def summary(item, source):
    return {**receipt_snapshot(item), 'source_id': source.id, 'source_name': source.name,
        'filename': item.filename, 'report_reference': item.report_reference, 'observed_at': item.observed_at,
        'observed_at_raw': item.observed_at_raw, 'received_at': item.received_at, 'received_actor': item.received_actor,
        'row_count': len(item.rows), 'error_count': len(item.errors)}


def detail(session, item, source):
    return {**summary(item, source), 'raw_text': item.raw_text, 'errors': item.errors,
        'plan': plan_for(session, item, source), 'stock_hints': stock_hints(session, item)}


def apply_locked(session, item, source, context, reason, automatic=False):
    plan = plan_for(session, item, source)
    if not plan['can_apply']:
        raise HTTPException(409, 'This file has invalid rows, conflicting references, or has already been decided. Inspect the preview before trying again.')
    results = []
    for row in plan['proposals']:
        if row['action'] == 'new_draft':
            body = NewRequest.model_validate({**row['values'], 'reference': row['reference'],
                'submission_key': uuid5(UUID(item.id), row['reference'])})
            saved = create_locked(body, context, session, intake_id=item.id,
                reason=f'Draft from intake {item.report_reference}; {"trusted source rule" if automatic else "file reviewed"}.')
            results.append({'reference': row['reference'], 'request_id': saved['request']['id'], 'action': 'created_draft'})
        else:
            results.append({'reference': row['reference'], 'request_id': row['request_id'], 'action': 'unchanged_duplicate'})
    item.state, item.version, item.reviewed_at = 'applied', item.version + 1, utcnow()
    item.results, item.automatic = results, automatic
    receipt_event(session, item, context, 'auto_applied' if automatic else 'applied', reason)


def queue_locked(session, source, content, filename, context):
    parsed = parse_file(content, filename)
    previous = session.scalar(select(AutomationReceipt).where(AutomationReceipt.source_id == source.id,
        AutomationReceipt.fingerprint == parsed['fingerprint']))
    if previous:
        return previous, True
    unresolved = session.scalar(select(func.count()).select_from(AutomationReceipt).where(
        AutomationReceipt.workspace_id == source.workspace_id, AutomationReceipt.state.in_(['pending', 'blocked'])))
    if unresolved >= 100:
        raise HTTPException(409, 'There are 100 files awaiting a decision. Accept or dismiss some before sending another file.')
    item = AutomationReceipt(id=str(uuid4()), workspace_id=source.workspace_id, source_id=source.id,
        filename=filename, **parsed, state='blocked' if parsed['errors'] else 'pending', version=1,
        source_policy_version=source.policy_version, source_policy_mode=source.automation_mode,
        received_actor_id=context.actor_id, received_actor=context.actor, received_at=utcnow(), automatic=False, results=[])
    source.last_received_at = item.received_at
    session.add(item)
    session.flush()
    receipt_event(session, item, context, 'received', 'Source text saved; validation and draft proposals are rule-based.')
    if source.automation_mode == 'new_drafts':
        plan = plan_for(session, item, source)
        if plan['can_apply'] and not plan['warnings']:
            robot = AccessContext(source.workspace_id, None, f'Automation · {source.name}'[:120], 'automation')
            apply_locked(session, item, source, robot, f'Trusted-source policy v{source.policy_version}: create new drafts only.', automatic=True)
    return item, False


def read_upload(file):
    try:
        return file.file.read(MAX_FILE + 1), safe_filename(file.filename or 'relief.json')
    finally:
        file.file.close()


@router.get('/contract')
def contract(context: Context):
    return {'schema_version': CONTRACT, 'max_bytes': MAX_FILE, 'max_rows': 200, 'csv_headers': HEADERS,
        'request_schema': IntakeRow.model_json_schema(), 'example': example_payload(),
        'instructions': 'Use one report reference and timezone-bearing observation time per file. References identify requests within this organisation. Existing requests are never overwritten. New requests remain drafts.'}


@router.get('/sources')
def list_sources(context: Context, session: DB):
    sources = session.scalars(select(DataSource).where(DataSource.workspace_id == context.workspace_id,
        DataSource.purpose == 'relief').order_by(DataSource.created_at, DataSource.id)).all()
    return {'items': [source_description(source) for source in sources], 'can_manage': context.actor_id is not None and context.role == 'owner',
        'can_upload': context.actor_id is not None and context.role in {'owner', 'editor'}}


@router.post('/sources', status_code=201)
def create_source(body: SourceInput, context: Context, session: DB):
    with session.begin():
        require_owner(session, context)
        if session.scalar(select(func.count()).select_from(DataSource).where(DataSource.workspace_id == context.workspace_id, DataSource.purpose == 'relief')) >= 20:
            raise HTTPException(409, 'This organisation already has 20 relief sources. Reuse an existing source.')
        token = secrets.token_urlsafe(32)
        source = DataSource(id=str(uuid4()), workspace_id=context.workspace_id, created_by=context.actor_id,
            name=body.name, token_hash=token_digest(token), enabled=True, purpose='relief', automation_mode='review', policy_version=1)
        session.add(source)
        session.flush()
        source_event(session, source, context, 'created', 'New relief source starts with manual review.')
        return {**source_description(source), 'token': token}


@router.get('/sources/{source_id}')
def source_detail(source_id: UUID, context: Context, session: DB, before_version: int | None = Query(default=None, ge=1)):
    source = find_source(session, context, source_id)
    conditions = [AutomationSourceEvent.source_id == source.id, AutomationSourceEvent.workspace_id == context.workspace_id]
    if before_version:
        conditions.append(AutomationSourceEvent.version < before_version)
    events = session.scalars(select(AutomationSourceEvent).where(*conditions).order_by(AutomationSourceEvent.version.desc()).limit(50)).all()
    return {'source': source_description(source), 'events': [{key: getattr(event, key) for key in
        ('id', 'version', 'action', 'actor', 'created_at', 'reason', 'before', 'after')} for event in events],
        'next_before_version': events[-1].version if events and events[-1].version > 1 else None}


@router.patch('/sources/{source_id}')
def change_policy(source_id: UUID, body: Policy, context: Context, session: DB):
    with session.begin():
        require_owner(session, context)
        source = find_source(session, context, source_id, lock=True)
        if source.policy_version != body.expected_version:
            raise HTTPException(409, 'This source policy changed. Refresh the source before saving a new rule.')
        if source.enabled == body.enabled and source.automation_mode == body.automation_mode:
            return {**source_description(source), 'unchanged': True}
        before = source_snapshot(source)
        source.enabled, source.automation_mode = body.enabled, body.automation_mode
        source.policy_version += 1
        source_event(session, source, context, 'policy_changed', body.reason, before)
        return {**source_description(source), 'unchanged': False}


@router.post('/sources/{source_id}/rotate')
def rotate_key(source_id: UUID, body: Decision, context: Context, session: DB):
    with session.begin():
        require_owner(session, context)
        source = find_source(session, context, source_id, lock=True)
        if source.policy_version != body.expected_version:
            raise HTTPException(409, 'This source changed. Refresh before replacing the key.')
        before = source_snapshot(source)
        token = secrets.token_urlsafe(32)
        source.token_hash, source.created_by = token_digest(token), context.actor_id
        source.policy_version += 1
        source_event(session, source, context, 'key_rotated', body.reason, before)
        return {**source_description(source), 'token': token}


@router.post('/sources/{source_id}/upload', status_code=202)
def upload(source_id: UUID, context: Context, session: DB, file: UploadFile = File(...)):
    content, filename = read_upload(file)
    with session.begin():
        writer(session, context)
        source = find_source(session, context, source_id, lock=True)
        if not source.enabled:
            raise HTTPException(409, 'Enable this source before uploading a file.')
        item, duplicate = queue_locked(session, source, content, filename, context)
        return {'receipt': detail(session, item, source), 'duplicate': duplicate}


@router.post('/sources/{source_id}/example', status_code=202)
def simulate(source_id: UUID, context: Context, session: DB):
    with session.begin():
        writer(session, context)
        source = find_source(session, context, source_id, lock=True)
        if not source.enabled:
            raise HTTPException(409, 'Enable this source before creating a fictional example.')
        content = json.dumps(example_payload()).encode()
        item, duplicate = queue_locked(session, source, content, 'fictional-relief-example.json', context)
        return {'receipt': detail(session, item, source), 'duplicate': duplicate}


@ingest_router.post('/api/automation/ingest/{source_id}', status_code=202)
def receive(source_id: UUID, request: Request, session: DB, file: UploadFile = File(...)):
    authorization = request.headers.get('authorization', '')
    token = authorization[7:] if authorization.startswith('Bearer ') else ''
    with session.begin():
        # Look up the workspace, then use the same workspace -> source lock order as every mutation.
        initial = session.get(DataSource, str(source_id))
        if initial is None or initial.purpose != 'relief':
            raise HTTPException(401, 'The relief source key is invalid or inactive.')
        require_workspace(session, initial.workspace_id, lock=True)
        session.expire(initial)
        source = session.scalar(select(DataSource).where(DataSource.id == str(source_id)).with_for_update())
        if not source.enabled or not token or not hmac.compare_digest(source.token_hash, token_digest(token)):
            raise HTTPException(401, 'The relief source key is invalid or inactive.')
        membership = session.get(Membership, (source.created_by, source.workspace_id))
        if membership is None or membership.role not in {'owner', 'editor'}:
            raise HTTPException(403, 'The key issuer no longer has write access. An owner must rotate the source key.')
        content, filename = read_upload(file)
        context = AccessContext(source.workspace_id, None, f'Connector · {source.name}'[:120], 'connector')
        item, duplicate = queue_locked(session, source, content, filename, context)
        return {'id': item.id, 'state': item.state, 'automatic': item.automatic, 'duplicate': duplicate,
            'message': 'Relief file recorded. Only the configured new-draft rule can change request records.'}


@router.get('/inbox')
def inbox(context: Context, session: DB, state: Literal['all', 'pending', 'blocked', 'applied', 'dismissed'] = 'all',
    source_id: UUID | None = None, q: str = Query(default='', max_length=200), page: int = Query(default=1, ge=1, le=100000)):
    with session.begin():
        require_workspace(session, context.workspace_id)
        base = [AutomationReceipt.workspace_id == context.workspace_id]
        counts = dict(session.execute(select(AutomationReceipt.state, func.count()).where(*base).group_by(AutomationReceipt.state)).all())
        conditions = list(base)
        if state != 'all': conditions.append(AutomationReceipt.state == state)
        if source_id: conditions.append(AutomationReceipt.source_id == str(source_id))
        if q.strip(): conditions.append(or_(*[func.lower(field).contains(q.strip().lower(), autoescape=True) for field in
            (AutomationReceipt.filename, AutomationReceipt.report_reference, DataSource.name)]))
        query = select(AutomationReceipt, DataSource).join(DataSource, DataSource.id == AutomationReceipt.source_id).where(*conditions)
        total = session.scalar(select(func.count()).select_from(query.subquery()))
        pages = max(1, (total + 19) // 20); current = min(page, pages)
        records = session.execute(query.order_by(AutomationReceipt.received_at.desc(), AutomationReceipt.id).offset((current - 1) * 20).limit(20)).all()
        return {'items': [summary(item, source) for item, source in records], 'total': total, 'page': current, 'total_pages': pages,
            'counts': {'all': sum(counts.values()), **{key: counts.get(key, 0) for key in ('pending', 'blocked', 'applied', 'dismissed')}},
            'can_edit': context.actor_id is not None and context.role in {'owner', 'editor'}, 'freshness_hours': settings.freshness_hours}


@router.get('/inbox/{receipt_id}')
def receipt_detail(receipt_id: UUID, context: Context, session: DB):
    with session.begin():
        require_workspace(session, context.workspace_id, lock=True)
        item = find_receipt(session, context, receipt_id)
        source = find_source(session, context, item.source_id)
        events = session.scalars(select(AutomationReceiptEvent).where(AutomationReceiptEvent.workspace_id == context.workspace_id,
            AutomationReceiptEvent.receipt_id == item.id).order_by(AutomationReceiptEvent.version.desc())).all()
        return {'receipt': detail(session, item, source), 'events': [{key: getattr(event, key) for key in
            ('id', 'version', 'action', 'actor', 'created_at', 'reason', 'after')} for event in events]}


@router.post('/inbox/{receipt_id}/apply')
def apply_receipt(receipt_id: UUID, body: Apply, context: Context, session: DB):
    with session.begin():
        writer(session, context)
        item = find_receipt(session, context, receipt_id, lock=True)
        source = find_source(session, context, item.source_id)
        if item.state == 'applied':
            return {'receipt': detail(session, item, source), 'duplicate': True}
        plan = plan_for(session, item, source)
        if item.version != body.expected_version or plan['plan_hash'] != body.plan_hash:
            raise HTTPException(409, 'The file preview or accepted records changed. Refresh the preview and inspect the current proposals before applying.')
        if plan['warnings'] and not body.acknowledge_warnings:
            raise HTTPException(409, 'Check the source warnings and acknowledge them before accepting this file.')
        apply_locked(session, item, source, context, body.reason)
        return {'receipt': detail(session, item, source), 'duplicate': False}


@router.post('/inbox/{receipt_id}/dismiss')
def dismiss_receipt(receipt_id: UUID, body: Decision, context: Context, session: DB):
    with session.begin():
        writer(session, context)
        item = find_receipt(session, context, receipt_id, lock=True)
        source = find_source(session, context, item.source_id)
        if item.state == 'dismissed':
            return {'receipt': detail(session, item, source), 'duplicate': True}
        if item.version != body.expected_version or item.state not in {'pending', 'blocked'}:
            raise HTTPException(409, 'This file has already changed or been applied. Refresh before deciding.')
        item.state, item.version, item.reviewed_at = 'dismissed', item.version + 1, utcnow()
        receipt_event(session, item, context, 'dismissed', body.reason)
        return {'receipt': detail(session, item, source), 'duplicate': False}
