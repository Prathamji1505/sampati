"""Add three stable, fictional intake examples; never apply drafts or freshen old reports."""
import json
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select

from backend.app.auth import AccessContext, token_digest
from backend.app.automation import queue_locked, source_event
from backend.app.automation_files import example_payload
from backend.app.database import SessionLocal
from backend.app.models import AutomationReceipt, DataSource, ReliefRequest, User, Workspace, WORKSPACE_ID, utcnow
from backend.app.relief import snapshot


def main():
    source_id = str(uuid5(NAMESPACE_URL, 'sampati/automation/demo/paused-source'))
    with SessionLocal.begin() as session:
        workspace = session.scalar(select(Workspace).where(Workspace.id == WORKSPACE_ID).with_for_update())
        if workspace is None or not workspace.is_demo:
            raise RuntimeError('The fictional demo workspace must already exist.')
        # Stable source ID is the seed marker. Existing evidence is never rewritten.
        if session.get(DataSource, source_id):
            print('Fictional intake examples already exist; their original dates and decisions were retained.')
            return
        issuer = session.scalar(select(User).order_by(User.created_at).limit(1))
        request = session.scalar(select(ReliefRequest).where(ReliefRequest.workspace_id == workspace.id).order_by(ReliefRequest.reference).limit(1))
        if issuer is None:
            print('No account exists yet; relief intake examples can be tried from a private source after signup.')
            return
        if request is None:
            raise RuntimeError('Seed the earlier learning examples before intake examples.')
        now = utcnow()
        source = DataSource(id=source_id, workspace_id=workspace.id, created_by=issuer.id, name='Fictional relief desk · paused demo source',
            token_hash=token_digest(str(uuid5(NAMESPACE_URL, 'sampati/unusable/fictional/relief-source'))),
            enabled=False, purpose='relief', automation_mode='review', policy_version=1, created_at=now)
        session.add(source); session.flush()
        context = AccessContext(workspace.id, None, 'Fictional example', 'demo')
        source_event(session, source, context, 'created', 'Paused, fictional learning source. No live file watcher is connected.')
        fresh = example_payload(reference='DEMO-INTAKE-NEW', now=now); fresh['report_reference'] = 'DEMO-INTAKE-001'
        conflicting = example_payload(now=now); conflicting['report_reference'] = 'DEMO-INTAKE-002'
        original = snapshot(request)
        conflicting['requests'] = [{key: original[key] for key in ('reference', 'requesting_organisation', 'locality', 'category', 'item_name', 'quantity', 'unit', 'needed_by', 'source_name', 'note')}]
        conflicting['requests'][0]['quantity'] = '999'
        invalid = example_payload(reference='DEMO-INTAKE-INVALID', now=now); invalid['report_reference'] = 'DEMO-INTAKE-003'
        invalid['requests'][0]['quantity'] = '0'
        for payload in (fresh, conflicting, invalid):
            queue_locked(session, source, json.dumps(payload).encode(), payload['report_reference'].lower() + '.json', context)
    print('Added three fictional intake files. Existing requests, stock, deliveries and aircraft records were retained.')


if __name__ == '__main__':
    main()
