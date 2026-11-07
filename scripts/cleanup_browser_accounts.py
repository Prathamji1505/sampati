"""Remove only explicitly named, generated browser-QA accounts after verification."""
import argparse

from sqlalchemy import delete, select

from backend.app.database import SessionLocal
from backend.app.models import Aircraft, AircraftChange, DataSource, IncomingDataset, ImportBatch, Invitation, Membership, User, Workspace


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
        for workspace_id in workspace_ids:
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
