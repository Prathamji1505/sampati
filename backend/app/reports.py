from collections import Counter, defaultdict
from datetime import timezone
import json
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .auth import Context
from .config import settings
from .database import get_session
from .files import csv_bytes, spreadsheet_bytes
from .imports import snapshot
from .models import Aircraft, AutomationReceipt, ImportBatch, Incident, ReliefRequest, Shipment, StockPosition, Workspace, utcnow
from .relief import quantity_text

router = APIRouter(tags=['Reports and exports'])
DB = Annotated[Session, Depends(get_session)]


@router.get('/overview/relief')
def relief_overview(session: DB, context: Context):
    """One consistent, scoped view of recorded relief work. Quantities stay per request."""
    with session.begin():
        session.scalar(select(Workspace).where(Workspace.id == context.workspace_id).with_for_update(read=True))
        scope = context.workspace_id
        now = utcnow()
        def count(model, *conditions):
            return session.scalar(select(func.count()).select_from(model).where(model.workspace_id == scope, *conditions))
        delivered = select(Shipment.request_id, func.sum(Shipment.delivered).label('quantity')).where(
            Shipment.workspace_id == scope, Shipment.status != 'cancelled').group_by(Shipment.request_id).subquery()
        remaining = ReliefRequest.quantity - func.coalesce(delivered.c.quantity, 0)
        base = [ReliefRequest.workspace_id == scope, ReliefRequest.status == 'reviewed', remaining > 0]
        query = select(ReliefRequest, remaining.label('remaining')).outerjoin(delivered, delivered.c.request_id == ReliefRequest.id).where(*base)
        total = session.scalar(select(func.count()).select_from(query.subquery()))
        rows = session.execute(query.order_by(ReliefRequest.needed_by, ReliefRequest.id).limit(20)).all()
        return {'generated_at': now, 'needs_total': total, 'needs': [{'id': request.id, 'reference': request.reference,
            'locality': request.locality, 'item_name': request.item_name, 'unit': request.unit, 'quantity': quantity_text(request.quantity),
            'remaining': quantity_text(amount), 'needed_by': request.needed_by, 'overdue': request.needed_by < now} for request, amount in rows],
            'attention': {'incidents': count(Incident, Incident.status == 'pending'),
                'requests': count(ReliefRequest, ReliefRequest.status.in_(['draft', 'submitted'])),
                'intake': count(AutomationReceipt, AutomationReceipt.state.in_(['pending', 'blocked'])),
                'shipments': count(Shipment, Shipment.status.in_(['draft', 'approved', 'in_transit', 'partially_delivered'])),
                'stock_positions': count(StockPosition)},
            'method': 'Recorded source confirmations reduce remaining needs. Counts and rules are computed locally; quantities stay in each request’s unit.'}


def report_freshness(item):
    age = (utcnow() - item.source_updated_at).total_seconds()
    return 'future' if age < -300 else 'stale' if age > settings.freshness_hours * 3600 else 'current'


@router.get('/overview')
def overview(session: DB, context: Context):
    records = session.scalars(select(Aircraft).where(Aircraft.workspace_id == context.workspace_id).order_by(Aircraft.aircraft_id)).all()
    statuses, freshness = Counter(item.reported_status for item in records), Counter(report_freshness(item) for item in records)
    by_source = defaultdict(lambda: {'count': 0, 'needs_review': 0, 'last_report': None})
    attention, daily = [], Counter()
    for item in records:
        state = report_freshness(item)
        source = by_source[item.source_name]
        source['count'] += 1
        source['needs_review'] += state != 'current'
        source['last_report'] = max(source['last_report'] or item.source_updated_at, item.source_updated_at)
        daily[item.source_updated_at.astimezone(timezone.utc).date().isoformat()] += 1
        if state != 'current' or item.reported_status == 'unknown' or not item.display_name:
            attention.append({'aircraft_id': item.aircraft_id, 'reason': 'Timestamp is in the future' if state == 'future' else 'Report needs a refresh' if state == 'stale' else 'Source reports unknown status' if item.reported_status == 'unknown' else 'Display name is missing'})
    total = len(records)
    statements = [f'{total} accepted aircraft {"record is" if total == 1 else "records are"} visible in this workspace.']
    if total:
        statements += [f"{freshness['stale']} reports are older than the {settings.freshness_hours}-hour demo threshold; {freshness['future']} have future timestamps.", f"{statuses['unknown']} aircraft have a source-reported unknown status."]
    else:
        statements.append('Import a sample or a dataset to begin. No availability can be inferred from an empty register.')
    return {'total': total, 'statuses': dict(statuses), 'freshness': dict(freshness), 'sources': [{'name': name, **values} for name, values in sorted(by_source.items())],
        'attention': attention[:100], 'report_dates': [{'date': key, 'count': value} for key, value in sorted(daily.items())],
        'summary': statements, 'summary_method': 'Computed from accepted records. No predictive model or external AI service.', 'generated_at': utcnow()}


@router.get('/exports/register.{format}')
def export_register(format: Literal['csv', 'xlsx', 'json'], session: DB, context: Context,
    q: str = Query(default='', max_length=200), status: Literal['all', 'available', 'unavailable', 'unknown'] = 'all',
    freshness: Literal['all', 'current', 'review'] = 'all'):
    records = session.scalars(select(Aircraft).where(Aircraft.workspace_id == context.workspace_id).order_by(Aircraft.aircraft_id)).all()
    rows = [snapshot(item) for item in records if (status == 'all' or item.reported_status == status)
        and (freshness == 'all' or (report_freshness(item) == 'current') == (freshness == 'current'))
        and q.lower() in f'{item.aircraft_id} {item.display_name} {item.source_name}'.lower()]
    if format == 'xlsx':
        content, media = spreadsheet_bytes(rows), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    elif format == 'csv':
        content, media = csv_bytes(rows), 'text/csv; charset=utf-8'
    else:
        content, media = json.dumps({'exported_at': utcnow().isoformat(), 'workspace_id': context.workspace_id, 'records': rows}, ensure_ascii=False, indent=2), 'application/json'
    return Response(content=content, media_type=media, headers={'Content-Disposition': f'attachment; filename="sampati-register.{format}"'})
