import csv
import hmac
from datetime import datetime, timedelta, timezone
import io
import os
import time
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .config import ROOT, settings
from .auth import Context, router as auth_router
from .database import get_session
from .imports import compare_rows, existing_import, fingerprint, read_preview, safe_filename, snapshot
from .files import parse_dataset, spreadsheet_bytes
from .services import build_preview, incoming_for_confirmation, accept_incoming
from .accounts import router as account_router
from .reports import router as report_router
from .sources import router as source_router, ingest_router
from .quality import router as quality_router
from .relief import router as relief_router
from .incidents import router as incident_router
from .inventory import router as inventory_router
from .deliveries import router as delivery_router
from .automation import router as automation_router, ingest_router as automation_ingest_router
from .models import Aircraft, AircraftChange, ImportBatch, Workspace, utcnow
from .schemas import ConfirmRequest, HEADERS, MAX_BYTES, parse_timestamp

app = FastAPI(title='Sampati', version='0.4.0', description='Civilian disaster response: reviewed evidence, relief needs, stock, delivery records and draft intake automation.')
data_router = APIRouter(tags=['Aircraft reports'])
DB = Annotated[Session, Depends(get_session)]


@app.middleware('http')
async def local_request_limits(request: Request, call_next):
    if request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
        origin = request.headers.get('origin')
        if origin and origin not in {'http://127.0.0.1:5173', 'http://localhost:5173', 'http://127.0.0.1:8000', 'http://localhost:8000'}:
            return JSONResponse({'detail': 'Use the local Sampati application for changes.'}, status_code=403)
        size = request.headers.get('content-length', '0')
        if not size.isdigit() or int(size) > 8 * MAX_BYTES:
            return JSONResponse({'detail': 'This request is too large.'}, status_code=413)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-store'
    return response


def require_workspace(session: Session, workspace_id: str, lock=False) -> Workspace:
    query = select(Workspace).where(Workspace.id == workspace_id)
    if lock:
        query = query.with_for_update()
    workspace = session.scalar(query)
    if workspace is None:
        raise HTTPException(503, 'The database needs its initial migration. Run the setup command.')
    return workspace


def serialize_aircraft(item: Aircraft) -> dict:
    age = (utcnow() - item.source_updated_at).total_seconds()
    freshness = 'future' if age < -300 else 'stale' if age > settings.freshness_hours * 3600 else 'current'
    return {**snapshot(item), 'received_at': item.received_at.isoformat(), 'source_timestamp_raw': item.source_timestamp_raw, 'last_import_id': item.last_import_id, 'freshness': freshness}


def serialize_import(item: ImportBatch) -> dict:
    return {key: getattr(item, key) for key in ('id', 'filename', 'actor', 'received_at', 'confirmed_at', 'row_count', 'new_count', 'updated_count', 'unchanged_count', 'revision')}


@app.get('/api/health')
def health(session: DB):
    session.execute(text('SELECT 1'))
    return {'status': 'ok', 'mode': 'local-fictional-demo'}


@data_router.get('/workspace')
def workspace(session: DB, context: Context):
    record = require_workspace(session, context.workspace_id)
    items = session.scalars(select(Aircraft).where(Aircraft.workspace_id == context.workspace_id).order_by(Aircraft.aircraft_id)).all()
    batches = session.scalars(select(ImportBatch).where(ImportBatch.workspace_id == context.workspace_id).order_by(ImportBatch.confirmed_at.desc()).limit(50)).all()
    return {
        'id': record.id, 'name': record.name, 'is_demo': record.is_demo, 'revision': record.revision, 'freshness_hours': settings.freshness_hours,
        'aircraft': [serialize_aircraft(item) for item in items],
        'imports': [serialize_import(item) for item in batches],
        'server_time': utcnow().isoformat(),
    }


@data_router.post('/imports/preview')
def preview(session: DB, context: Context, file: UploadFile = File(...)):
    if len(settings.preview_secret) < 32:
        raise HTTPException(503, 'The local preview signing key has not been configured. Run setup first.')
    received_at = utcnow().isoformat()
    filename = safe_filename(file.filename or 'aircraft.csv')
    try:
        content = file.file.read(MAX_BYTES + 1)
    finally:
        file.file.close()
    rows, errors = parse_dataset(content, filename)
    return build_preview(session, context, rows, errors, filename, received_at)


@data_router.post('/imports/confirm')
def confirm(body: ConfirmRequest, session: DB, context: Context):
    try:
        payload = read_preview(body.token, settings.preview_secret, context.workspace_id, context.actor_id)
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    digest = fingerprint(body.rows)
    if not hmac.compare_digest(digest, payload['fingerprint']):
        raise HTTPException(400, 'The preview content changed. Upload the original file again.')
    if len({row.aircraft_id for row in body.rows}) != len(body.rows):
        raise HTTPException(400, 'The confirmation contains duplicate aircraft IDs.')
    # Every accepted import serializes on this workspace row. The preview itself writes nothing.
    with session.begin():
        current = require_workspace(session, context.workspace_id, lock=True)
        incoming = incoming_for_confirmation(session, payload, context)
        duplicate = existing_import(session, digest, context.workspace_id)
        if duplicate:
            accept_incoming(incoming, duplicate.id, context)
            return {'import': serialize_import(duplicate), 'duplicate': True}
        if current.revision != payload['revision']:
            raise HTTPException(409, 'The register changed after this preview. Review the file again before confirming.')
        changes, errors = compare_rows(session, body.rows, context.workspace_id)
        if errors:
            raise HTTPException(409, 'The source reports no longer match this preview. Review the file again.')
        now = utcnow()
        new_count = sum(change['action'] == 'new' for change in changes)
        updated_count = sum(change['action'] == 'updated' for change in changes)
        unchanged_count = sum(change['action'] == 'unchanged' for change in changes)
        current.revision += 1
        batch = ImportBatch(id=str(uuid.uuid4()), workspace_id=context.workspace_id, fingerprint=digest,
            filename=payload['filename'], received_at=parse_timestamp(payload['received_at']), confirmed_at=now,
            actor=context.actor, actor_id=context.actor_id, row_count=len(body.rows), new_count=new_count,
            updated_count=updated_count, unchanged_count=unchanged_count, revision=current.revision)
        session.add(batch)
        session.flush()
        existing = {item.aircraft_id: item for item in session.scalars(select(Aircraft).where(Aircraft.workspace_id == context.workspace_id))}
        for row, change in zip(body.rows, changes):
            if change['action'] == 'unchanged':
                continue
            item = existing.get(row.aircraft_id)
            if item is None:
                item = Aircraft(workspace_id=context.workspace_id, aircraft_id=row.aircraft_id)
                session.add(item)
            for field in ('display_name', 'reported_status', 'source_name', 'note'):
                setattr(item, field, getattr(row, field))
            item.source_updated_at = parse_timestamp(row.source_updated_at)
            item.source_timestamp_raw = row.source_updated_at
            item.received_at, item.last_import_id = parse_timestamp(payload['received_at']), batch.id
            session.add(AircraftChange(workspace_id=context.workspace_id, import_id=batch.id, aircraft_id=row.aircraft_id,
                action=change['action'], before=change['before'], after={**change['after'], 'source_timestamp_raw': row.source_updated_at}))
        session.flush()
        result = serialize_import(batch)
        accept_incoming(incoming, batch.id, context)
    return {'import': result, 'duplicate': False}


@data_router.get('/imports/{import_id}')
def import_detail(import_id: str, session: DB, context: Context):
    batch = session.scalar(select(ImportBatch).where(ImportBatch.workspace_id == context.workspace_id, ImportBatch.id == import_id))
    if batch is None:
        raise HTTPException(404, 'This import was not found in the local workspace.')
    changes = session.scalars(select(AircraftChange).where(AircraftChange.workspace_id == context.workspace_id, AircraftChange.import_id == import_id).order_by(AircraftChange.aircraft_id)).all()
    return {'import': serialize_import(batch), 'changes': [{'aircraft_id': change.aircraft_id, 'action': change.action, 'before': change.before, 'after': change.after} for change in changes]}


def sample_rows() -> list[dict]:
    now = utcnow().replace(microsecond=0)
    names = ['Cedar', 'Willow', 'Birch', 'Maple', 'Aspen', 'Alder', 'Juniper', 'Elm', 'Hazel', 'Pine', 'Oak', 'Ash']
    statuses = ['available', 'available', 'unavailable', 'available', 'unknown', 'available', 'unavailable', 'available', 'available', 'unknown', 'available', 'unavailable']
    notes = {'available': 'Fictional civilian transport report.', 'unavailable': 'Fictional maintenance hold reported by the source.', 'unknown': 'Fictional record awaiting a confirmed source update.'}
    return [{
        'aircraft_id': f'DEMO-{index + 1:03}', 'display_name': name,
        'reported_status': statuses[index],
        'source_updated_at': (now - timedelta(minutes=(index + 1) * 17, hours=30 if index in (4, 9) else 0)).isoformat(),
        'source_name': 'Fictional civil fleet register', 'note': notes[statuses[index]],
    } for index, name in enumerate(names)]


@app.get('/api/examples/{example}')
def example_file(example: str):
    if example not in {'sample.csv', 'template.csv', 'template.xlsx', 'invalid.csv'}:
        raise HTTPException(404, 'This example does not exist.')
    rows = sample_rows()
    if example.startswith('template.'):
        rows = rows[:1]
    if example == 'template.xlsx':
        return Response(content=spreadsheet_bytes(rows), media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': 'attachment; filename="sampati-template.xlsx"'})
    if example == 'invalid.csv':
        rows = [rows[0], {**rows[1], 'reported_status': 'ready', 'source_updated_at': '2026-11-07 10:00'}]
    buffer = io.StringIO(newline='')
    writer = csv.DictWriter(buffer, fieldnames=HEADERS)
    writer.writeheader()
    writer.writerows(rows)
    return Response(content=buffer.getvalue(), media_type='text/csv', headers={'Content-Disposition': f'attachment; filename="sampati-{example}"'})


app.include_router(auth_router)
app.include_router(account_router)
app.include_router(ingest_router)
app.include_router(automation_ingest_router)
app.include_router(automation_router, prefix='/api/demo')
app.include_router(automation_router, prefix='/api')
app.include_router(delivery_router, prefix='/api/demo')
app.include_router(delivery_router, prefix='/api')
app.include_router(inventory_router, prefix='/api/demo')
app.include_router(inventory_router, prefix='/api')
app.include_router(incident_router, prefix='/api/demo')
app.include_router(incident_router, prefix='/api')
app.include_router(relief_router, prefix='/api/demo')
app.include_router(relief_router, prefix='/api')
app.include_router(quality_router, prefix='/api/demo')
app.include_router(quality_router, prefix='/api')
app.include_router(report_router, prefix='/api/demo')
app.include_router(report_router, prefix='/api')
app.include_router(source_router, prefix='/api/demo')
app.include_router(source_router, prefix='/api')
app.include_router(data_router, prefix='/api/demo')
app.include_router(data_router, prefix='/api')

# Packaged local mode serves the compiled interface after all API routes.
if os.environ.get('SAMPATI_SERVE_FRONTEND') == 'true':
    app.mount('/', StaticFiles(directory=ROOT / 'frontend' / 'dist', html=True), name='interface')
