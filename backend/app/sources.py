"""Inbound, organisation-scoped datasets. Acceptance is always a separate user action."""
import hmac
import secrets
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .accounts import owner
from .auth import Context, token_digest
from .database import get_session
from .files import parse_dataset
from .imports import fingerprint, safe_filename, snapshot
from .models import Aircraft, DataSource, IncomingDataset, Membership, utcnow
from .schemas import CsvRow, MAX_BYTES
from .services import build_preview, require_workspace

router = APIRouter(tags=['Data connections'])
ingest_router = APIRouter(tags=['Connector uploads'])
DB = Annotated[Session, Depends(get_session)]


class SourceInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=2, max_length=100)


class SourceState(BaseModel):
    model_config = ConfigDict(extra='forbid')
    enabled: bool


def describe(source):
    return {'id': source.id, 'name': source.name, 'enabled': source.enabled, 'created_at': source.created_at, 'last_received_at': source.last_received_at}


def find_source(session, source_id, workspace_id, lock=False):
    query = select(DataSource).where(DataSource.id == source_id, DataSource.workspace_id == workspace_id, DataSource.purpose == 'aircraft')
    if lock:
        query = query.with_for_update()
    record = session.scalar(query)
    if record is None:
        raise HTTPException(404, 'Data source not found in this organisation.')
    return record


def queue_rows(session, source, rows, filename):
    require_workspace(session, source.workspace_id, lock=True)
    digest = fingerprint(rows)
    previous = session.scalar(select(IncomingDataset).where(IncomingDataset.source_id == source.id,
        IncomingDataset.fingerprint == digest, IncomingDataset.state.in_(['pending', 'accepted'])).order_by(IncomingDataset.received_at.desc()))
    if previous:
        return previous, True
    pending = session.scalar(select(func.count()).select_from(IncomingDataset).where(IncomingDataset.workspace_id == source.workspace_id, IncomingDataset.state == 'pending'))
    if pending >= 100:
        raise HTTPException(409, 'The organisation has 100 pending files. Review or reject some before submitting more.')
    record = IncomingDataset(id=str(uuid.uuid4()), workspace_id=source.workspace_id, source_id=source.id,
        fingerprint=digest, filename=filename, rows=[row.model_dump() for row in rows], state='pending')
    source.last_received_at = utcnow()
    session.add(record)
    session.flush()
    return record, False


@router.get('/sources')
def sources(context: Context, session: DB):
    records = session.scalars(select(DataSource).where(DataSource.workspace_id == context.workspace_id, DataSource.purpose == 'aircraft').order_by(DataSource.created_at)).all()
    incoming = session.execute(select(IncomingDataset, DataSource.name).join(DataSource, DataSource.id == IncomingDataset.source_id)
        .where(IncomingDataset.workspace_id == context.workspace_id).order_by(IncomingDataset.received_at.desc()).limit(100)).all()
    return {'sources': [describe(record) for record in records], 'incoming': [{'id': item.id, 'source_name': name, 'filename': item.filename,
        'state': item.state, 'row_count': len(item.rows), 'received_at': item.received_at, 'reviewed_at': item.reviewed_at, 'import_id': item.import_id} for item, name in incoming]}


@router.post('/sources', status_code=201)
def create_source(body: SourceInput, context: Context, session: DB):
    owner(context)
    if not body.name.strip():
        raise HTTPException(422, 'Give the data source a name.')
    token = secrets.token_urlsafe(32)
    with session.begin():
        record = DataSource(id=str(uuid.uuid4()), workspace_id=context.workspace_id, created_by=context.actor_id,
            name=body.name.strip(), token_hash=token_digest(token), enabled=True)
        session.add(record)
        session.flush()
        result = describe(record)
    return {**result, 'token': token, 'ingest_path': f'/api/ingest/{record.id}'}


@router.patch('/sources/{source_id}')
def set_source_state(source_id: str, body: SourceState, context: Context, session: DB):
    owner(context)
    with session.begin():
        record = find_source(session, source_id, context.workspace_id, lock=True)
        record.enabled = body.enabled
    return describe(record)


@router.post('/sources/{source_id}/rotate')
def rotate_source(source_id: str, context: Context, session: DB):
    owner(context)
    token = secrets.token_urlsafe(32)
    with session.begin():
        record = find_source(session, source_id, context.workspace_id, lock=True)
        record.token_hash, record.created_by, record.enabled = token_digest(token), context.actor_id, True
    return {**describe(record), 'token': token, 'ingest_path': f'/api/ingest/{record.id}'}


@ingest_router.post('/api/ingest/{source_id}', status_code=202)
def receive(source_id: str, request: Request, session: DB, file: UploadFile = File(...)):
    authorization = request.headers.get('authorization', '')
    token = authorization[7:] if authorization.startswith('Bearer ') else ''
    with session.begin():
        source = session.scalar(select(DataSource).where(DataSource.id == source_id).with_for_update())
        if source is None or source.purpose != 'aircraft' or not source.enabled or not token or not hmac.compare_digest(source.token_hash, token_digest(token)):
            raise HTTPException(401, 'The source key is invalid or inactive.')
        membership = session.get(Membership, (source.created_by, source.workspace_id))
        if membership is None or membership.role not in {'owner', 'editor'}:
            raise HTTPException(403, 'The account that created this key no longer has import access. Ask an owner to rotate the key.')
        try:
            content = file.file.read(MAX_BYTES + 1)
        finally:
            file.file.close()
        filename = safe_filename(file.filename or 'source.csv')
        rows, errors = parse_dataset(content, filename)
        if errors:
            raise HTTPException(422, {'message': 'The incoming file was rejected.', 'errors': errors})
        record, duplicate = queue_rows(session, source, rows, filename)
        return {'id': record.id, 'state': record.state, 'duplicate': duplicate, 'message': 'Dataset received for human review. Accepted aircraft records were not changed.'}


@router.post('/sources/{source_id}/simulate')
def simulate(source_id: str, context: Context, session: DB):
    with session.begin():
        source = find_source(session, source_id, context.workspace_id, lock=True)
        if not source.enabled:
            raise HTTPException(409, 'Enable the source before generating a fictional update.')
        records = session.scalars(select(Aircraft).where(Aircraft.workspace_id == context.workspace_id).order_by(Aircraft.aircraft_id).limit(3)).all()
        now = utcnow().replace(microsecond=0).isoformat()
        rows = [CsvRow.model_validate({**snapshot(item), 'reported_status': 'unknown' if item.reported_status != 'unknown' else 'available',
            'source_updated_at': now, 'source_name': f'Simulated: {source.name}'[:120], 'note': 'Fictional connector update for reviewing the workflow.'}) for item in records]
        if not rows:
            rows = [CsvRow(aircraft_id='SIM-001', display_name='Fictional source aircraft', reported_status='unknown', source_updated_at=now,
                source_name=f'Simulated: {source.name}'[:120], note='Fictional connector update for reviewing the workflow.')]
        record, duplicate = queue_rows(session, source, rows, 'fictional-source-update.csv')
    return {'id': record.id, 'duplicate': duplicate, 'state': record.state}


@router.post('/sources/inbox/{incoming_id}/preview')
def incoming_preview(incoming_id: str, context: Context, session: DB):
    record = session.scalar(select(IncomingDataset).where(IncomingDataset.id == incoming_id, IncomingDataset.workspace_id == context.workspace_id))
    if record is None:
        raise HTTPException(404, 'Incoming dataset not found.')
    if record.state != 'pending':
        raise HTTPException(409, 'This dataset has already been reviewed.')
    rows = [CsvRow.model_validate(row) for row in record.rows]
    return build_preview(session, context, rows, [], record.filename, record.received_at.isoformat(), record.id)


@router.post('/sources/inbox/{incoming_id}/reject')
def reject_incoming(incoming_id: str, context: Context, session: DB):
    with session.begin():
        require_workspace(session, context.workspace_id, lock=True)
        record = session.scalar(select(IncomingDataset).where(IncomingDataset.id == incoming_id, IncomingDataset.workspace_id == context.workspace_id).with_for_update())
        if record is None:
            raise HTTPException(404, 'Incoming dataset not found.')
        if record.state != 'pending':
            raise HTTPException(409, 'This dataset has already been reviewed.')
        record.state, record.reviewed_at, record.reviewer_id = 'rejected', utcnow(), context.actor_id
    return {'rejected': True}
