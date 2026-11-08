"""Add read-only fictional relief examples once; never overwrite existing requests."""
from datetime import timedelta
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models import ReliefRequest, Workspace, WORKSPACE_ID, utcnow
from backend.app.relief import NewRequest, add_event, create_digest, snapshot
from backend.app.schemas import parse_timestamp


def main():
    added = 0
    with SessionLocal.begin() as session:
        workspace = session.scalar(select(Workspace).where(Workspace.id == WORKSPACE_ID).with_for_update())
        if workspace is None or not workspace.is_demo:
            raise RuntimeError('The fictional demo workspace must exist before seeding relief examples.')
        now = utcnow().replace(microsecond=0)
        examples = [
            ('DEMO-REL-001', 'food', 'Dry-food boxes', '120', 'boxes', 'Fictional Hill Community Desk', 'Fictional Hill Ward', 24, 'draft'),
            ('DEMO-REL-002', 'water', 'Drinking-water packs', '250', 'packs', 'Fictional Riverside Relief Desk', 'Fictional Riverside Ward', -2, 'submitted'),
            ('DEMO-REL-003', 'shelter', 'Shelter supply kits', '40', 'kits', 'Fictional Meadow Community Desk', 'Fictional Meadow Ward', 48, 'reviewed'),
        ]
        for reference, category, item_name, quantity, unit, organisation, locality, hours, target in examples:
            if session.scalar(select(ReliefRequest.id).where(ReliefRequest.workspace_id == workspace.id, ReliefRequest.reference_key == reference)):
                continue
            body = NewRequest(reference=reference, submission_key=uuid5(NAMESPACE_URL, 'sampati/relief/example/' + reference),
                requesting_organisation=organisation, locality=locality, category=category, item_name=item_name,
                quantity=quantity, unit=unit, needed_by=(now + timedelta(hours=hours)).isoformat(),
                source_name='Fictional community desk register', note='Illustrative civilian-welfare example. No real request, stock or delivery is represented.')
            item = ReliefRequest(id=str(uuid5(NAMESPACE_URL, 'sampati/relief/request/' + reference)), workspace_id=workspace.id,
                reference=reference, reference_key=reference, submission_key=str(body.submission_key), create_digest=create_digest(body),
                requesting_organisation=organisation, locality=locality, category=category, item_name=item_name,
                quantity=body.quantity, unit=unit, needed_by=parse_timestamp(body.needed_by), needed_by_raw=body.needed_by,
                source_name=body.source_name, note=body.note, status='draft', version=1,
                created_by=None, created_actor='Fictional example', created_at=now, updated_at=now)
            session.add(item)
            session.flush()
            add_event(session, item, 'Fictional example', None, 'created', 'Fictional example recorded as a draft.', None)
            if target != 'draft':
                before = snapshot(item)
                item.status, item.version = 'submitted', 2
                add_event(session, item, 'Fictional example', None, 'status_changed', 'Fictional submission for demonstrating review.', before)
            if target == 'reviewed':
                before = snapshot(item)
                item.status, item.version = 'reviewed', 3
                add_event(session, item, 'Fictional example', None, 'status_changed', 'Fictional details reviewed; no delivery is implied.', before)
            added += 1
    print(f'Added {added} fictional read-only relief examples; existing records were retained.')


if __name__ == '__main__':
    main()
