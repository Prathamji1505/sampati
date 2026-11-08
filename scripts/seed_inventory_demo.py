"""Add stable, fictional read-only aid-stock examples; never overwrite existing records."""
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select

from backend.app.auth import AccessContext
from backend.app.database import SessionLocal
from backend.app.inventory import RecordInput, record_locked
from backend.app.models import InventoryItem, ReliefRequest, StockPosition, StockRecord, StorageLocation, Workspace, WORKSPACE_ID, utcnow


def identifier(label):
    return str(uuid5(NAMESPACE_URL,'sampati/inventory/demo/'+label))


def main():
    added=0
    with SessionLocal.begin() as session:
        workspace=session.scalar(select(Workspace).where(Workspace.id==WORKSPACE_ID).with_for_update())
        if workspace is None or not workspace.is_demo:
            raise RuntimeError('The fictional demo workspace must exist before seeding inventory.')
        now=utcnow().replace(microsecond=0)
        context=AccessContext(workspace.id,None,'Fictional example','demo')
        items=[]
        for code,name,category,unit in [('DEMO-WATER','Fictional drinking-water packs','water','packs'),('DEMO-SHELTER','Fictional shelter kits','shelter','kits')]:
            item=session.scalar(select(InventoryItem).where(InventoryItem.workspace_id==workspace.id,InventoryItem.code_key==code))
            if item is None:
                item=InventoryItem(id=identifier(code),workspace_id=workspace.id,code=code,code_key=code,name=name,category=category,unit=unit,created_actor=context.actor,created_at=now)
                session.add(item)
            items.append(item)
        location=session.scalar(select(StorageLocation).where(StorageLocation.workspace_id==workspace.id,StorageLocation.code_key=='DEMO-STORE'))
        if location is None:
            location=StorageLocation(id=identifier('STORE'),workspace_id=workspace.id,code='DEMO-STORE',code_key='DEMO-STORE',name='Fictional community store',locality='Fictional Riverside Ward',created_actor=context.actor,created_at=now)
            session.add(location)
        session.flush()
        def add(reference,item,kind,quantity,**links):
            nonlocal added
            existing=session.scalar(select(StockRecord).where(StockRecord.workspace_id==workspace.id,StockRecord.reference_key==reference))
            if existing:
                return existing
            position=session.scalar(select(StockPosition).where(StockPosition.workspace_id==workspace.id,StockPosition.item_id==item.id,StockPosition.location_id==location.id))
            body=RecordInput(item_id=item.id,location_id=location.id,reference=reference,submission_key=identifier(reference),
                expected_version=position.version if position else 0,kind=kind,quantity=quantity,source_name='Fictional community store log',
                observed_at=now.isoformat(),reason='Fictional learning example. No real stock movement or delivery is represented.',**links)
            record,duplicate=record_locked(body,context,session)
            added+=not duplicate
            return record
        add('DEMO-STOCK-001',items[0],'receipt','120')
        add('DEMO-STOCK-002',items[0],'report','113')
        add('DEMO-STOCK-003',items[1],'receipt','50')
        request=session.scalar(select(ReliefRequest).where(ReliefRequest.workspace_id==workspace.id,ReliefRequest.reference_key=='DEMO-REL-003'))
        if request and request.status=='reviewed' and request.unit=='kits' and request.category=='shelter' and request.quantity>=40:
            reserve=add('DEMO-STOCK-004',items[1],'reserve','40',request_id=request.id)
            issue=add('DEMO-STOCK-005',items[1],'issue','15',parent_id=reserve.id)
            add('DEMO-STOCK-006',items[1],'return','2',parent_id=issue.id)
    print(f'Added {added} fictional stock events. Existing catalog entries, balances and evidence were retained.')


if __name__=='__main__':
    main()
