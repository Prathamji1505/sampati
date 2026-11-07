import time

from fastapi import HTTPException
from sqlalchemy import select

from .config import settings
from .imports import compare_rows, existing_import, fingerprint, sign_preview, snapshot
from .models import IncomingDataset, Workspace, utcnow


def require_workspace(session, workspace_id, lock=False):
    query = select(Workspace).where(Workspace.id == workspace_id)
    if lock:
        query = query.with_for_update()
    record = session.scalar(query)
    if record is None:
        raise HTTPException(503, 'The workspace database needs its migrations. Run setup first.')
    return record


def build_preview(session, context, rows, errors, filename, received_at=None, incoming_id=None):
    if len(settings.preview_secret) < 32:
        raise HTTPException(503, 'The preview signing key has not been configured.')
    current = require_workspace(session, context.workspace_id)
    received_at = received_at or utcnow().isoformat()
    changes, duplicate = [], None
    errors = list(errors)
    if not errors:
        duplicate = existing_import(session, fingerprint(rows), context.workspace_id)
        if duplicate is None:
            changes, comparison_errors = compare_rows(session, rows, context.workspace_id)
            errors.extend(comparison_errors)
        else:
            changes = [{'row': row._csv_row or index, 'aircraft_id': row.aircraft_id, 'action': 'unchanged', 'before': None, 'after': row.normalized()} for index, row in enumerate(rows, start=2)]
    counts = {action: sum(change['action'] == action for change in changes) for action in ('new', 'updated', 'unchanged', 'blocked')}
    token = None
    if not errors:
        token = sign_preview({'workspace': context.workspace_id, 'actor_id': context.actor_id, 'revision': current.revision,
            'fingerprint': fingerprint(rows), 'filename': filename, 'received_at': received_at, 'incoming_id': incoming_id,
            'expires': int(time.time()) + 1800}, settings.preview_secret)
    return {'valid': not errors, 'filename': filename, 'row_count': len(rows), 'rows': [row.model_dump() for row in rows],
        'errors': errors, 'changes': changes, 'counts': counts, 'already_imported': duplicate is not None, 'token': token}


def incoming_for_confirmation(session, payload, context):
    incoming_id = payload.get('incoming_id')
    if not incoming_id:
        return None
    record = session.scalar(select(IncomingDataset).where(IncomingDataset.id == incoming_id, IncomingDataset.workspace_id == context.workspace_id).with_for_update())
    if record is None or record.state == 'rejected':
        raise HTTPException(409, 'This incoming dataset is no longer available for confirmation.')
    return record


def accept_incoming(record, batch_id, context):
    # A repeated confirmation is a no-op, including its original review attribution.
    if record and record.state == 'pending':
        record.state, record.import_id, record.reviewed_at, record.reviewer_id = 'accepted', batch_id, utcnow(), context.actor_id
