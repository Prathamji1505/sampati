"""Add stable, fictional delivery evidence without altering existing stock events."""
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select

from backend.app.auth import AccessContext
from backend.app.database import SessionLocal
from backend.app.deliveries import DeliveryAction, NewShipment, action_locked, create_locked
from backend.app.models import ShipmentEvent, StockRecord, Workspace, WORKSPACE_ID


def identifier(label):
    return uuid5(NAMESPACE_URL,'sampati/delivery/demo/'+label)


def main():
    added=0
    with SessionLocal.begin() as session:
        workspace=session.scalar(select(Workspace).where(Workspace.id==WORKSPACE_ID).with_for_update())
        if workspace is None or not workspace.is_demo:
            raise RuntimeError('The fictional demo workspace must exist before seeding delivery examples.')
        issue=session.scalar(select(StockRecord).where(StockRecord.workspace_id==workspace.id,StockRecord.reference_key=='DEMO-STOCK-005'))
        if issue is None:
            raise RuntimeError('Seed the fictional inventory examples before delivery examples.')
        context=AccessContext(workspace.id,None,'Fictional example','demo')
        for reference,quantity,delivered in [('DEMO-SHIP-001','8','5'),('DEMO-SHIP-002','5','5')]:
            item,duplicate=create_locked(NewShipment(reference=reference,submission_key=identifier(reference),issue_id=issue.id,
                quantity=quantity,receiving_organisation='Fictional Meadow Community Desk',destination='Fictional Meadow Ward',
                note='Fictional learning example. No actual dispatch, delivery or beneficiary is represented.'),context,session)
            added+=not duplicate
            for kind,suffix in [('approved','APPROVAL'),('dispatched','DISPATCH'),('delivery','ARRIVAL')]:
                event_reference=reference+'-'+suffix
                if session.scalar(select(ShipmentEvent.id).where(ShipmentEvent.workspace_id==workspace.id,ShipmentEvent.reference_key==event_reference)):
                    continue
                body=DeliveryAction(kind=kind,reference=event_reference,submission_key=identifier(event_reference),expected_version=item.version,
                    quantity=delivered if kind=='delivery' else None,source_name='Fictional signed relief tracking log',
                    observed_at=item.created_at.isoformat(),reason='Fictional evidence for the learning walkthrough. No real-world outcome is claimed.')
                action_locked(item,body,context,session)
    print(f'Added {added} fictional shipments. Existing stock, source evidence and shipment history were retained.')


if __name__=='__main__':
    main()
