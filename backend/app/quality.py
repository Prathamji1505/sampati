"""Explain source-record quality without inferring aircraft condition or readiness."""
from collections import Counter
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import Context
from .config import settings
from .database import get_session
from .models import Aircraft, IncomingDataset, Workspace, utcnow
from .schemas import parse_timestamp

router = APIRouter(tags=['Report data checks'])
DB = Annotated[Session, Depends(get_session)]
RULE_VERSION = 'report-data-v1'
CHECKS = [
    {'code': 'stale_report', 'label': 'Old report', 'description': 'Source time exceeds the configured demo freshness threshold.'},
    {'code': 'future_report', 'label': 'Future timestamp', 'description': 'Source time is more than five minutes ahead of the check time.'},
    {'code': 'unknown_status', 'label': 'Unknown status', 'description': 'The source explicitly reports unknown.'},
    {'code': 'missing_name', 'label': 'Missing display name', 'description': 'The accepted record has no display name.'},
    {'code': 'incoming_update', 'label': 'Incoming update', 'description': 'A newer report for this ID is waiting for human review.'},
    {'code': 'incoming_conflict', 'label': 'Incoming conflict', 'description': 'A pending report has the same source time but different values.'},
    {'code': 'incoming_older', 'label': 'Older incoming report', 'description': 'A pending report predates the accepted record.'},
]


def classify_incoming(accepted, row):
    """Compare validated source facts; never interpret meaning from free-text notes."""
    timestamp = parse_timestamp(row['source_updated_at'])
    if timestamp < accepted.source_updated_at:
        return 'incoming_older'
    if timestamp > accepted.source_updated_at:
        return 'incoming_update'
    if any(row[field] != getattr(accepted, field) for field in ('display_name', 'reported_status', 'source_name', 'note')):
        return 'incoming_conflict'
    return None


def inspect_report(item, now, freshness_hours, pending=None):
    age = (now - item.source_updated_at).total_seconds()
    freshness = 'future' if age < -300 else 'stale' if age > freshness_hours * 3600 else 'current'
    findings = []
    def add(code, message, next_step):
        findings.append({'code': code, 'message': message, 'next_step': next_step, 'count': 1, 'examples': []})
    if freshness == 'future':
        add('future_report', 'The source timestamp is more than five minutes in the future.', 'Check the source clock and timezone, then submit a corrected report.')
    elif freshness == 'stale':
        add('stale_report', f'The source report is older than the {freshness_hours}-hour demo threshold.', 'Request a newer report from the source.')
    if item.reported_status == 'unknown':
        add('unknown_status', 'The source reports an unknown status.', 'Ask the source to confirm the reported status.')
    if not item.display_name.strip():
        add('missing_name', 'The record has no display name.', 'Provide a display name in a newer source report if one is known.')
    messages = {
        'incoming_update': ('A newer report is waiting in the incoming inbox.', 'Review the proposed changes in Data connections.'),
        'incoming_conflict': ('An incoming report disagrees at the same source timestamp.', 'Ask the source to resolve the conflict before confirming an import.'),
        'incoming_older': ('An incoming report is older than this accepted record.', 'Review or reject the old file; it cannot replace this newer record.'),
    }
    for code, group in sorted((pending or {}).items()):
        message, next_step = messages[code]
        findings.append({'code': code, 'message': message, 'next_step': next_step, **group})
    return {
        'aircraft_id': item.aircraft_id, 'display_name': item.display_name,
        'reported_status': item.reported_status, 'source_name': item.source_name,
        'source_updated_at': item.source_updated_at.isoformat(), 'source_timestamp_raw': item.source_timestamp_raw,
        'last_import_id': item.last_import_id, 'freshness': freshness,
        'result': 'review' if findings else 'complete', 'findings': findings,
    }


@router.get('/report-checks')
def report_checks(context: Context, session: DB):
    with session.begin():
        # Imports/inbox decisions take an exclusive workspace lock. This shared lock
        # keeps the reported revision, accepted rows and pending evidence coherent.
        workspace = session.scalar(select(Workspace).where(Workspace.id == context.workspace_id).with_for_update(read=True))
        if workspace is None:
            raise HTTPException(503, 'The workspace needs its database setup.')
        now = utcnow()
        accepted = session.scalars(select(Aircraft).where(Aircraft.workspace_id == context.workspace_id).order_by(Aircraft.aircraft_id)).all()
        by_id = {item.aircraft_id: item for item in accepted}
        pending, new_ids, pending_files = {}, set(), 0
        incoming = session.scalars(select(IncomingDataset).where(IncomingDataset.workspace_id == context.workspace_id,
            IncomingDataset.state == 'pending').order_by(IncomingDataset.received_at.desc(), IncomingDataset.id).execution_options(yield_per=5))
        for dataset in incoming:
            pending_files += 1
            for row in dataset.rows:
                item = by_id.get(row['aircraft_id'])
                if item is None:
                    new_ids.add(row['aircraft_id'])
                    continue
                code = classify_incoming(item, row)
                if code is None:
                    continue
                group = pending.setdefault(item.aircraft_id, {}).setdefault(code, {'count': 0, 'examples': []})
                group['count'] += 1
                if len(group['examples']) < 3:
                    group['examples'].append({'incoming_id': dataset.id, 'filename': dataset.filename,
                        'source_updated_at': row['source_updated_at'], 'reported_status': row['reported_status']})
        records = [inspect_report(item, now, settings.freshness_hours, pending.get(item.aircraft_id)) for item in accepted]
        counts = Counter(finding['code'] for item in records for finding in item['findings'])
        review = sum(item['result'] == 'review' for item in records)
        return {'workspace_id': context.workspace_id, 'workspace_revision': workspace.revision, 'generated_at': now,
            'rule_version': RULE_VERSION, 'freshness_hours': settings.freshness_hours, 'checks': CHECKS,
            'summary': {'records': len(records), 'needs_review': review, 'complete': len(records) - review,
                'pending_files': pending_files, 'pending_new_ids': len(new_ids)},
            'counts_by_code': dict(counts), 'records': records,
            'meaning': 'Checks source-record quality only. A complete report does not establish aircraft condition, availability or flight clearance.'}
