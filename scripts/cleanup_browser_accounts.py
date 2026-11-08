"""Remove only explicitly named, generated browser-QA accounts after verification."""
import argparse

from sqlalchemy import delete, select

from backend.app.database import SessionLocal
from backend.app.models import Aircraft, AircraftChange, AutomationReceipt, AutomationReceiptEvent, AutomationSourceEvent, DataSource, IncomingDataset, ImportBatch, Incident, IncidentEvent, InventoryItem, Invitation, Membership, ReliefRequest, ReliefRequestEvent, Shipment, ShipmentEvent, StockPosition, StockRecord, StorageLocation, User, Workspace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('user_ids', nargs='+')
    args = parser.parse_args()
    with SessionLocal.begin() as session:
        selected = []
        workspace_ids = set()
        requested = set(args.user_ids)
        for user_id in args.user_ids:
            user = session.get(User, user_id)
            if user is None:
                continue
            memberships = session.scalars(select(Membership).where(Membership.user_id == user.id)).all()
            if not user.username.startswith('qa-browser-') or not user.display_name.startswith('Browser QA ') or not memberships:
                raise RuntimeError('An account did not match the generated browser-QA fixture. Nothing was removed.')
            for membership in memberships:
                workspace = session.get(Workspace, membership.workspace_id)
                if workspace.is_demo or not workspace.name.startswith('Browser QA organisation '):
                    raise RuntimeError('The workspace is not a generated browser-QA fixture. Nothing was removed.')
                others = session.scalars(select(Membership).where(Membership.workspace_id == workspace.id)).all()
                if any(item.user_id not in requested for item in others):
                    raise RuntimeError('The fixture has other members. Nothing was removed.')
                workspace_ids.add(workspace.id)
            selected.append(user)
        # Refuse foreign references; deleting these fixtures must never affect another organisation.
        if session.scalar(select(Invitation.id).where((Invitation.target_user_id.in_(requested) | Invitation.issuer_id.in_(requested)), ~Invitation.workspace_id.in_(workspace_ids)).limit(1)):
            raise RuntimeError('A fixture has invitations in another organisation. Nothing was removed.')
        if session.scalar(select(ReliefRequest.id).where(ReliefRequest.created_by.in_(requested), ~ReliefRequest.workspace_id.in_(workspace_ids)).limit(1)) or session.scalar(select(ReliefRequestEvent.id).where(ReliefRequestEvent.actor_id.in_(requested), ~ReliefRequestEvent.workspace_id.in_(workspace_ids)).limit(1)):
            raise RuntimeError('A fixture has relief records in another organisation. Nothing was removed.')
        for workspace_id in workspace_ids:
            for model, actor_field in [(DataSource, DataSource.created_by), (AutomationReceipt, AutomationReceipt.received_actor_id), (AutomationReceiptEvent, AutomationReceiptEvent.actor_id), (AutomationSourceEvent, AutomationSourceEvent.actor_id)]:
                if session.scalar(select(model.id).where(actor_field.in_(requested), ~model.workspace_id.in_(workspace_ids)).limit(1)):
                    raise RuntimeError('A fixture has source or automation evidence in another organisation. Nothing was removed.')
            if session.scalar(select(Shipment.id).where(Shipment.created_by.in_(requested), ~Shipment.workspace_id.in_(workspace_ids)).limit(1)) or session.scalar(select(ShipmentEvent.id).where(ShipmentEvent.actor_id.in_(requested), ~ShipmentEvent.workspace_id.in_(workspace_ids)).limit(1)):
                raise RuntimeError('A fixture has delivery records in another organisation. Nothing was removed.')
            if session.scalar(select(StockRecord.id).where(StockRecord.actor_id.in_(requested), ~StockRecord.workspace_id.in_(workspace_ids)).limit(1)):
                raise RuntimeError('A fixture has stock records in another organisation. Nothing was removed.')
            if session.scalar(select(Incident.id).where(Incident.created_by.in_(requested), ~Incident.workspace_id.in_(workspace_ids)).limit(1)) or session.scalar(select(IncidentEvent.id).where(IncidentEvent.actor_id.in_(requested), ~IncidentEvent.workspace_id.in_(workspace_ids)).limit(1)):
                raise RuntimeError('A fixture has incident records in another organisation. Nothing was removed.')
            session.execute(delete(Shipment).where(Shipment.workspace_id == workspace_id))
            session.execute(delete(StockPosition).where(StockPosition.workspace_id == workspace_id))
            session.execute(delete(InventoryItem).where(InventoryItem.workspace_id == workspace_id))
            session.execute(delete(StorageLocation).where(StorageLocation.workspace_id == workspace_id))
            session.execute(delete(ReliefRequest).where(ReliefRequest.workspace_id == workspace_id))
            session.execute(delete(AutomationReceipt).where(AutomationReceipt.workspace_id == workspace_id))
            session.execute(delete(Incident).where(Incident.workspace_id == workspace_id))
            session.execute(delete(IncomingDataset).where(IncomingDataset.workspace_id == workspace_id))
            session.execute(delete(DataSource).where(DataSource.workspace_id == workspace_id))
            session.execute(delete(Invitation).where(Invitation.workspace_id == workspace_id))
            session.execute(delete(AircraftChange).where(AircraftChange.workspace_id == workspace_id))
            session.execute(delete(Aircraft).where(Aircraft.workspace_id == workspace_id))
            session.execute(delete(ImportBatch).where(ImportBatch.workspace_id == workspace_id))
            session.execute(delete(Membership).where(Membership.workspace_id == workspace_id))
            session.delete(session.get(Workspace, workspace_id))
        for user in selected:
            session.delete(user)
    print(f'Removed {len(selected)} generated browser-QA account fixtures; demo records were not changed.')


if __name__ == '__main__':
    main()
