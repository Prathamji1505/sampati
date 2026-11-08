"""Add fictional, read-only flood assessments once without refreshing old evidence."""
from datetime import timedelta
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.incidents import Assessment, add_event, assessment_digest
from backend.app.models import Incident, Workspace, WORKSPACE_ID, utcnow


def main():
    added = 0
    with SessionLocal.begin() as session:
        workspace = session.scalar(select(Workspace).where(Workspace.id == WORKSPACE_ID).with_for_update())
        if workspace is None or not workspace.is_demo:
            raise RuntimeError('The fictional demo workspace must exist before seeding incidents.')
        now = utcnow().replace(microsecond=0)
        for reference, locality, hours, reviewed in [
            ('DEMO-FLOOD-001', 'Fictional Riverside Ward', 3, False),
            ('DEMO-FLOOD-002', 'Fictional Meadow Ward', 30, True),
        ]:
            if session.scalar(select(Incident.id).where(Incident.workspace_id == workspace.id, Incident.reference_key == reference)):
                continue
            body = Assessment(schema_version='sampati.incident.v1', external_reference=reference,
                title='Fictional flood assessment · ' + locality, hazard='flood', assessment_kind='impact_observation',
                locality=locality, observed_at=(now - timedelta(hours=hours)).isoformat(),
                generated_at=(now - timedelta(hours=hours-1)).isoformat(), source_name='Fictional assessment desk',
                source_url=None, summary='Illustrative report of water around access roads. A local needs check is required before recording supply requests.',
                uncertainty='Fictional learning example. Extent is illustrative and local conditions have not been verified.',
                extent={'west':85.1,'south':25.4,'east':85.2,'north':25.5}, reported_affected_people=None)
            item = Incident(id=str(uuid5(NAMESPACE_URL,'sampati/incident/' + reference)), workspace_id=workspace.id,
                reference_key=reference, digest=assessment_digest(body), assessment=body.model_dump(mode='json'),
                status='pending', version=1, created_by=None, created_actor='Fictional example', received_at=now, updated_at=now)
            session.add(item)
            session.flush()
            add_event(session,item,'Fictional example',None,'Fictional example received; human review required.',None)
            if reviewed:
                item.status, item.version = 'reviewed', 2
                add_event(session,item,'Fictional example',None,'Fictional source and limitations reviewed. No needs or dispatch approval is implied.','pending')
            added += 1
    print(f'Added {added} fictional incident examples; existing evidence was retained.')


if __name__ == '__main__':
    main()
