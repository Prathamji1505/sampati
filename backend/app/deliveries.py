"""Human-reviewed civilian shipments and source-backed delivery evidence."""
from datetime import timedelta, timezone
from decimal import Decimal
import hashlib
import json
from typing import Annotated, Literal
from uuid import UUID, uuid4, uuid5

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import Field, field_validator, model_validator
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .auth import Context
from .database import get_session
from .inventory import CleanInput, RecordInput, consumed, record_locked, scoped, workspace_lock
from .models import InventoryItem, ReliefRequest, Shipment, ShipmentEvent, StockPosition, StockRecord, StorageLocation, utcnow
from .relief import quantity_text
from .schemas import parse_timestamp

router=APIRouter(prefix='/deliveries',tags=['Civilian delivery tracking'])
DB=Annotated[Session,Depends(get_session)]
Status=Literal['all','draft','approved','in_transit','partially_delivered','delivered','closed','cancelled']
Action=Literal['approved','dispatched','delivery','return','cancelled','delivery_correction']
STATES=('draft','approved','in_transit','partially_delivered','delivered','closed','cancelled')


class ExactInput(CleanInput):
    @field_validator('quantity',mode='before',check_fields=False)
    @classmethod
    def no_bool(cls,value):
        if isinstance(value,bool):
            raise ValueError('Use an exact supply quantity.')
        return value


class NewShipment(ExactInput):
    reference:str=Field(min_length=1,max_length=64,pattern=r'^[A-Za-z0-9][A-Za-z0-9._/-]*$')
    submission_key:UUID
    issue_id:UUID
    quantity:Decimal=Field(gt=0,le=Decimal('1000000000'),max_digits=13,decimal_places=3,allow_inf_nan=False)
    receiving_organisation:str=Field(min_length=2,max_length=120)
    destination:str=Field(min_length=2,max_length=160)
    note:str=Field(default='',max_length=1000)


class DeliveryAction(ExactInput):
    kind:Action
    reference:str=Field(min_length=1,max_length=64,pattern=r'^[A-Za-z0-9][A-Za-z0-9._/-]*$')
    submission_key:UUID
    expected_version:int=Field(ge=1,strict=True)
    quantity:Decimal|None=Field(default=None,gt=0,le=Decimal('1000000000'),max_digits=13,decimal_places=3,allow_inf_nan=False)
    parent_event_id:UUID|None=None
    expected_stock_version:int|None=Field(default=None,ge=0,strict=True)
    source_name:str=Field(min_length=2,max_length=120)
    observed_at:str=Field(min_length=1,max_length=64)
    reason:str=Field(min_length=1,max_length=500)

    @field_validator('observed_at')
    @classmethod
    def dated(cls,value):
        parse_timestamp(value)
        return value

    @model_validator(mode='after')
    def quantities_and_links(self):
        if (self.kind in {'delivery','return','delivery_correction'})!=(self.quantity is not None):
            raise ValueError('Only arrival, return and correction events supply a quantity.')
        if (self.kind=='delivery_correction')!=(self.parent_event_id is not None):
            raise ValueError('A correction must reference its original delivery confirmation.')
        if (self.kind=='return')!=(self.expected_stock_version is not None):
            raise ValueError('A stock return requires the current stock-position version.')
        return self


def fingerprint(body,shipment_id=None):
    value=body.model_dump(mode='json',exclude={'submission_key','expected_version','expected_stock_version'})
    value['reference']=body.reference.upper()
    if value.get('quantity') is not None:
        value['quantity']=quantity_text(body.quantity)
    if 'observed_at' in value:
        value['observed_at']=parse_timestamp(body.observed_at).isoformat()
    if shipment_id:
        value['shipment_id']=shipment_id
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def allocated(session,issue_id):
    return session.scalar(select(func.coalesce(func.sum(Shipment.quantity-Shipment.returned),0)).where(Shipment.issue_id==issue_id,Shipment.status!='cancelled'))


def issue_details(session,context,issue_id):
    issue=scoped(session,StockRecord,context,issue_id)
    if issue.kind!='issue':
        raise HTTPException(409,'Choose an actual inventory issue, not a receipt or reservation.')
    position=scoped(session,StockPosition,context,issue.position_id)
    item=scoped(session,InventoryItem,context,position.item_id)
    location=scoped(session,StorageLocation,context,position.location_id)
    request=scoped(session,ReliefRequest,context,issue.request_id)
    return issue,position,item,location,request


def reviewed_need(request,item):
    if request.status!='reviewed' or request.unit!=item.unit or request.category!=item.category:
        raise HTTPException(409,'Review the matching relief request before creating, approving or recording dispatch for a shipment.')


def summary(item):
    return {'status':item.status,'quantity':quantity_text(item.quantity),'delivered':quantity_text(item.delivered),
        'returned':quantity_text(item.returned),'unresolved':quantity_text(item.quantity-item.delivered-item.returned),'version':item.version}


def describe(session,context,item):
    issue,position,supply,location,request=issue_details(session,context,item.issue_id)
    actions={'draft':['approved','cancelled'],'approved':['dispatched','cancelled'],
        'in_transit':['delivery','return'],'partially_delivered':['delivery','return'],'delivered':[],'closed':[],'cancelled':[]}[item.status][:]
    if item.delivered>0:
        actions.append('delivery_correction')
    return {**{key:getattr(item,key) for key in ('id','reference','issue_id','request_id','receiving_organisation','destination','note','created_actor','created_at','updated_at','approved_at','dispatched_at')},
        **summary(item),'issue_reference':issue.reference,'request_reference':request.reference,'request_status':request.status,
        'item_code':supply.code,'item_name':supply.name,'unit':supply.unit,'store_name':location.name,'stock_version':position.version,
        'allowed_actions':actions}


def event_view(event,remaining=None):
    return {**{key:getattr(event,key) for key in ('id','version','kind','reference','parent_event_id','parent_reference','stock_record_id','stock_reference','source_name','observed_at','observed_at_raw','received_at','actor','reason','after')},
        'quantity':quantity_text(event.quantity) if event.quantity is not None else None,
        'correctable_quantity':quantity_text(remaining) if remaining is not None else None}


@router.get('/issues')
def issues(context:Context,session:DB,q:str=Query(default='',max_length=200)):
    with session.begin():
        workspace_lock(session,context)
        query=select(StockRecord).join(ReliefRequest,StockRecord.request_id==ReliefRequest.id).where(StockRecord.workspace_id==context.workspace_id,StockRecord.kind=='issue',ReliefRequest.status=='reviewed')
        if q.strip():
            query=query.where(or_(*(func.lower(field).contains(q.strip().lower(),autoescape=True) for field in (StockRecord.reference,StockRecord.request_reference))))
        total=session.scalar(select(func.count()).select_from(query.subquery()))
        records=session.scalars(query.order_by(StockRecord.received_at.desc(),StockRecord.id).limit(20)).all()
        items=[]
        for issue in records:
            _,position,item,location,request=issue_details(session,context,issue.id)
            free=issue.quantity-consumed(session,issue.id)-allocated(session,issue.id)
            items.append({'id':issue.id,'reference':issue.reference,'request_reference':request.reference,'item_name':item.name,'unit':item.unit,
                'store_name':location.name,'available':quantity_text(max(Decimal(0),free)),
                'receiving_organisation':request.requesting_organisation,'destination':request.locality,
                'compatible':request.unit==item.unit and request.category==item.category})
        return {'items':items,'total':total}


@router.get('/needs')
def needs(context:Context,session:DB,q:str=Query(default='',max_length=200),only_remaining:bool=False,page:int=Query(default=1,ge=1,le=100000)):
    with session.begin():
        workspace_lock(session,context)
        totals=select(Shipment.request_id,func.sum(Shipment.delivered).label('delivered'),func.sum(Shipment.quantity-Shipment.returned).label('allocated')).where(Shipment.status!='cancelled').group_by(Shipment.request_id).subquery()
        confirmed=func.coalesce(totals.c.delivered,0)
        query=select(ReliefRequest,confirmed,func.coalesce(totals.c.allocated,0)).outerjoin(totals,totals.c.request_id==ReliefRequest.id).where(ReliefRequest.workspace_id==context.workspace_id,ReliefRequest.status=='reviewed')
        if only_remaining:
            query=query.where(ReliefRequest.quantity>confirmed)
        if q.strip():
            query=query.where(or_(*(func.lower(field).contains(q.strip().lower(),autoescape=True) for field in (ReliefRequest.reference,ReliefRequest.requesting_organisation,ReliefRequest.locality))))
        total=session.scalar(select(func.count()).select_from(query.subquery()));pages=max(1,(total+19)//20);page=min(page,pages)
        rows=session.execute(query.order_by(ReliefRequest.updated_at.desc(),ReliefRequest.id).offset((page-1)*20).limit(20)).all()
        return {'items':[{'id':request.id,'reference':request.reference,'organisation':request.requesting_organisation,'locality':request.locality,
            'quantity':quantity_text(request.quantity),'delivered':quantity_text(delivered),'remaining':quantity_text(max(Decimal(0),request.quantity-delivered)),
            'allocated':quantity_text(committed),'unit':request.unit} for request,delivered,committed in rows],
            'page':page,'total_pages':pages,'total':total}


@router.get('')
def list_shipments(context:Context,session:DB,q:str=Query(default='',max_length=200),status:Status='all',page:int=Query(default=1,ge=1,le=100000)):
    with session.begin():
        workspace=workspace_lock(session,context)
        filters=[Shipment.workspace_id==context.workspace_id]
        if status!='all':
            filters.append(Shipment.status==status)
        if q.strip():
            filters.append(or_(*(func.lower(field).contains(q.strip().lower(),autoescape=True) for field in (Shipment.reference,Shipment.receiving_organisation,Shipment.destination))))
        counts=dict(session.execute(select(Shipment.status,func.count()).where(Shipment.workspace_id==context.workspace_id).group_by(Shipment.status)).all())
        total=session.scalar(select(func.count()).select_from(Shipment).where(*filters));pages=max(1,(total+19)//20);page=min(page,pages)
        items=session.scalars(select(Shipment).where(*filters).order_by(Shipment.updated_at.desc(),Shipment.id).offset((page-1)*20).limit(20)).all()
        return {'items':[describe(session,context,item) for item in items],'counts':{'all':sum(counts.values()),**{key:counts.get(key,0) for key in STATES}},
            'page':page,'total_pages':pages,'total':total,'can_edit':not workspace.is_demo and context.role in {'owner','editor'}}


def create_locked(body,context,session):
    digest=fingerprint(body)
    old=session.scalar(select(Shipment).where(Shipment.workspace_id==context.workspace_id,Shipment.submission_key==str(body.submission_key)))
    if old is None:
        old=session.scalar(select(Shipment).where(Shipment.workspace_id==context.workspace_id,Shipment.reference_key==body.reference.upper()))
    if old:
        if old.create_digest!=digest:
            raise HTTPException(409,'That shipment reference or save identifier already records different details. Inspect it before creating another draft.')
        return old,True
    issue,position,item,location,request=issue_details(session,context,body.issue_id)
    reviewed_need(request,item)
    request_claims=session.scalar(select(func.coalesce(func.sum(Shipment.quantity-Shipment.returned),0)).where(Shipment.request_id==request.id,Shipment.status!='cancelled'))
    if request_claims+body.quantity>request.quantity:
        raise HTTPException(409,'Shipment allocations exceed the request’s remaining quantity. Resolve earlier shipments before assigning more supplies.')
    if body.quantity>issue.quantity-consumed(session,issue.id)-allocated(session,issue.id):
        raise HTTPException(409,'This quantity exceeds the issue’s unreturned stock that is not already assigned to shipments.')
    now=utcnow()
    shipment=Shipment(id=str(uuid4()),workspace_id=context.workspace_id,reference=body.reference,reference_key=body.reference.upper(),
        submission_key=str(body.submission_key),create_digest=digest,position_id=position.id,issue_id=issue.id,request_id=request.id,
        quantity=body.quantity,delivered=Decimal(0),returned=Decimal(0),receiving_organisation=body.receiving_organisation,
        destination=body.destination,note=body.note,status='draft',version=1,created_by=context.actor_id,created_actor=context.actor,created_at=now,updated_at=now)
    session.add(shipment);session.flush()
    session.add(ShipmentEvent(id=str(uuid4()),workspace_id=context.workspace_id,shipment_id=shipment.id,version=1,kind='created',
        source_name=issue.source_name,observed_at=issue.observed_at,observed_at_raw=issue.observed_at_raw,received_at=now,actor_id=context.actor_id,
        actor=context.actor,reason='Draft linked to the recorded inventory issue. Arrival is not confirmed.',after=summary(shipment)))
    return shipment,False


@router.post('',status_code=201)
def create(body:NewShipment,context:Context,session:DB,response:Response):
    with session.begin():
        workspace_lock(session,context,write=True)
        item,duplicate=create_locked(body,context,session)
        if duplicate:response.status_code=200
        return {'shipment':describe(session,context,item),'duplicate':duplicate}


@router.get('/{shipment_id}')
def detail(shipment_id:UUID,context:Context,session:DB,before_version:int|None=Query(default=None,ge=1)):
    with session.begin():
        workspace_lock(session,context)
        item=scoped(session,Shipment,context,shipment_id)
        filters=[ShipmentEvent.shipment_id==item.id]
        if before_version is not None:filters.append(ShipmentEvent.version<before_version)
        events=session.scalars(select(ShipmentEvent).where(*filters).order_by(ShipmentEvent.version.desc()).limit(50)).all()
        parents=[event.id for event in events if event.kind=='delivery']
        corrected=dict(session.execute(select(ShipmentEvent.parent_event_id,func.sum(ShipmentEvent.quantity)).where(ShipmentEvent.parent_event_id.in_(parents)).group_by(ShipmentEvent.parent_event_id)).all()) if parents else {}
        return {'shipment':describe(session,context,item),'events':[event_view(event,event.quantity-corrected.get(event.id,Decimal(0)) if event.kind=='delivery' else None) for event in events],
            'next_before_version':events[-1].version if events and events[-1].version>1 else None}


def settled_status(item):
    if item.delivered==item.quantity:return 'delivered'
    if item.delivered+item.returned==item.quantity:return 'closed'
    return 'partially_delivered' if item.delivered>0 else 'in_transit'


def action_locked(item,body,context,session):
    digest=fingerprint(body,item.id)
    old=session.scalar(select(ShipmentEvent).where(ShipmentEvent.workspace_id==context.workspace_id,ShipmentEvent.submission_key==str(body.submission_key)))
    if old is None:
        old=session.scalar(select(ShipmentEvent).where(ShipmentEvent.workspace_id==context.workspace_id,ShipmentEvent.reference_key==body.reference.upper()))
    if old:
        if old.digest!=digest:
            raise HTTPException(409,'This event reference or save identifier already records different evidence. Use a new reference for a new event.')
        return old,True
    if item.version!=body.expected_version:
        raise HTTPException(409,'This shipment changed after you opened it. Refresh its details before recording another event.')
    if body.kind not in describe(session,context,item)['allowed_actions']:
        raise HTTPException(409,'That action is not available in this shipment state. Refresh its details.')
    observed=parse_timestamp(body.observed_at)
    if observed>utcnow()+timedelta(minutes=5):
        raise HTTPException(422,'Use a source time that is not in the future.')
    issue,position,supply,location,request=issue_details(session,context,item.issue_id)
    parent=None;stock=None
    if body.kind in {'approved','dispatched'}:
        reviewed_need(request,supply)
        if body.kind=='dispatched' and observed<item.approved_at:
            raise HTTPException(409,'Dispatch evidence cannot precede the recorded approval source time.')
        if body.kind=='approved':item.approved_at=observed
        else:item.dispatched_at=observed
        item.status='approved' if body.kind=='approved' else 'in_transit'
    elif body.kind=='cancelled':
        item.status='cancelled'
    else:
        if item.dispatched_at is None or observed<item.dispatched_at:
            raise HTTPException(409,'Arrival, return and correction evidence cannot precede the recorded dispatch time.')
        if body.kind=='delivery':
            delivered=session.scalar(select(func.coalesce(func.sum(Shipment.delivered),0)).where(Shipment.request_id==request.id))
            if body.quantity>item.quantity-item.delivered-item.returned or delivered+body.quantity>request.quantity:
                raise HTTPException(409,'This exceeds the shipment’s unresolved quantity or the request’s remaining need.')
            item.delivered+=body.quantity
        elif body.kind=='return':
            if body.quantity>item.quantity-item.delivered-item.returned:
                raise HTTPException(409,'Only unresolved, undelivered supplies can be returned from this shipment.')
            stock_body=RecordInput(item_id=position.item_id,location_id=position.location_id,reference='SRET-'+body.submission_key.hex,
                submission_key=uuid5(body.submission_key,'shipment-return'),expected_version=body.expected_stock_version,
                kind='return',quantity=body.quantity,parent_id=issue.id,source_name=body.source_name,observed_at=body.observed_at,reason=body.reason)
            stock,stock_duplicate=record_locked(stock_body,context,session,return_for_shipment_id=item.id)
            if stock_duplicate:
                raise HTTPException(409,'That inventory return identifier was already used outside this shipment event. Inspect the histories and use a fresh evidence save action.')
            item.returned+=body.quantity
        else:
            parent=scoped(session,ShipmentEvent,context,body.parent_event_id)
            if parent.shipment_id!=item.id or parent.kind!='delivery':
                raise HTTPException(409,'Choose the original delivery confirmation from this shipment.')
            previous=session.scalar(select(func.coalesce(func.sum(ShipmentEvent.quantity),0)).where(ShipmentEvent.parent_event_id==parent.id))
            if body.quantity>parent.quantity-previous or observed<parent.observed_at:
                raise HTTPException(409,'This correction exceeds the original uncorrected confirmation or precedes its source time.')
            item.delivered-=body.quantity
        item.status=settled_status(item)
    now=utcnow();item.version+=1;item.updated_at=now
    event=ShipmentEvent(id=str(uuid4()),workspace_id=context.workspace_id,shipment_id=item.id,version=item.version,kind=body.kind,
        reference=body.reference,reference_key=body.reference.upper(),submission_key=str(body.submission_key),digest=digest,quantity=body.quantity,
        parent_event_id=parent.id if parent else None,parent_reference=parent.reference if parent else None,
        stock_position_id=position.id if stock else None,stock_record_id=stock.id if stock else None,stock_reference=stock.reference if stock else None,
        source_name=body.source_name,observed_at=observed,observed_at_raw=body.observed_at,received_at=now,actor_id=context.actor_id,
        actor=context.actor,reason=body.reason,after=summary(item))
    session.add(event);session.flush()
    return event,False


@router.post('/{shipment_id}/events',status_code=201)
def record_action(shipment_id:UUID,body:DeliveryAction,context:Context,session:DB,response:Response):
    with session.begin():
        workspace_lock(session,context,write=True)
        item=session.scalar(select(Shipment).where(Shipment.workspace_id==context.workspace_id,Shipment.id==str(shipment_id)).with_for_update())
        if item is None:raise HTTPException(404,'This shipment was not found in the selected organisation.')
        event,duplicate=action_locked(item,body,context,session)
        if duplicate:response.status_code=200
        return {'shipment':describe(session,context,item),'event':event_view(event),'duplicate':duplicate}
