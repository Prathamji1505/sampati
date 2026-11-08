"""Exact, scoped civilian aid stock records. Reports never change ledger balances."""
from datetime import timedelta, timezone
from decimal import Decimal
import hashlib
import json
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from .auth import Context
from .database import get_session
from .models import InventoryItem, Membership, ReliefRequest, Shipment, StockPosition, StockRecord, StorageLocation, Workspace, utcnow
from .relief import Category, Unit, quantity_text
from .schemas import parse_timestamp

router = APIRouter(prefix='/inventory', tags=['Civilian aid inventory'])
DB = Annotated[Session, Depends(get_session)]
Kind = Literal['receipt','reserve','release','issue','return','report','adjustment_in','adjustment_out']
MAX_QUANTITY = Decimal('1000000000')


class CleanInput(BaseModel):
    model_config = ConfigDict(extra='forbid')

    @field_validator('*', mode='before')
    @classmethod
    def trim(cls, value):
        return value.strip() if isinstance(value, str) else value


class ItemInput(CleanInput):
    code: str = Field(min_length=1, max_length=64, pattern=r'^[A-Za-z0-9][A-Za-z0-9._/-]*$')
    name: str = Field(min_length=2, max_length=160)
    category: Category
    unit: Unit


class LocationInput(CleanInput):
    code: str = Field(min_length=1, max_length=64, pattern=r'^[A-Za-z0-9][A-Za-z0-9._/-]*$')
    name: str = Field(min_length=2, max_length=120)
    locality: str = Field(min_length=2, max_length=160)


class RecordInput(CleanInput):
    item_id: UUID
    location_id: UUID
    reference: str = Field(min_length=1, max_length=64, pattern=r'^[A-Za-z0-9][A-Za-z0-9._/-]*$')
    submission_key: UUID
    expected_version: int = Field(ge=0, strict=True)
    kind: Kind
    quantity: Decimal = Field(ge=0, le=MAX_QUANTITY, max_digits=13, decimal_places=3, allow_inf_nan=False)
    parent_id: UUID | None = None
    request_id: UUID | None = None
    source_name: str = Field(min_length=2, max_length=120)
    observed_at: str = Field(min_length=1, max_length=64)
    reason: str = Field(min_length=1, max_length=500)

    @field_validator('quantity', mode='before')
    @classmethod
    def no_bool(cls, value):
        if isinstance(value, bool):
            raise ValueError('Enter an exact supply quantity.')
        return value

    @field_validator('observed_at')
    @classmethod
    def dated(cls, value):
        parse_timestamp(value)
        return value

    @model_validator(mode='after')
    def relationships(self):
        if self.kind != 'report' and self.quantity <= 0:
            raise ValueError('Movements require a positive quantity; count reports may be zero.')
        if (self.kind in {'release','issue','return'}) != (self.parent_id is not None):
            raise ValueError('Release/issue must reference a reservation; returns must reference an issue.')
        if (self.kind == 'reserve') != (self.request_id is not None):
            raise ValueError('Only a new reservation supplies a reviewed relief-request ID. Other links are inherited.')
        return self


def workspace_lock(session, context, write=False):
    query = select(Workspace).where(Workspace.id == context.workspace_id)
    workspace = session.scalar(query.with_for_update(read=not write))
    if workspace is None:
        raise HTTPException(503, 'The workspace needs its database setup.')
    if write:
        member = session.get(Membership,(context.actor_id,context.workspace_id)) if context.actor_id else None
        if workspace.is_demo or member is None or member.role not in {'owner','editor'}:
            raise HTTPException(403, 'An organisation owner or editor can record stock. Demo examples are read-only.')
    return workspace


def scoped(session, model, context, identifier):
    item = session.scalar(select(model).where(model.workspace_id == context.workspace_id, model.id == str(identifier)))
    if item is None:
        raise HTTPException(404, 'That inventory item, location or reference was not found in this organisation.')
    return item


def catalog_entry(item):
    fields = ('id','code','name','category','unit','created_actor','created_at') if isinstance(item,InventoryItem) else ('id','code','name','locality','created_actor','created_at')
    return {key:getattr(item,key) for key in fields}


@router.get('/catalog')
def catalog(context: Context, session: DB):
    with session.begin():
        workspace = workspace_lock(session,context)
        return {'items':[catalog_entry(item) for item in session.scalars(select(InventoryItem).where(InventoryItem.workspace_id==context.workspace_id).order_by(InventoryItem.code_key))],
            'locations':[catalog_entry(item) for item in session.scalars(select(StorageLocation).where(StorageLocation.workspace_id==context.workspace_id).order_by(StorageLocation.code_key))],
            'can_edit':not workspace.is_demo and context.role in {'owner','editor'},'catalog_limit':500}


def create_catalog(body, context, session, model, response):
    with session.begin():
        workspace_lock(session,context,write=True)
        existing = session.scalar(select(model).where(model.workspace_id==context.workspace_id,model.code_key==body.code.upper()))
        fields = body.model_dump()
        if existing:
            if any(getattr(existing,key) != value for key,value in fields.items() if key != 'code'):
                raise HTTPException(409, 'That code already describes different details. Use a new code; catalog units and identities remain fixed.')
            response.status_code=200
            return {'entry':catalog_entry(existing),'duplicate':True}
        if session.scalar(select(func.count()).select_from(model).where(model.workspace_id==context.workspace_id)) >= 500:
            raise HTTPException(409, 'This local prototype supports 500 entries per catalog. Existing entries are retained.')
        item=model(id=str(uuid4()),workspace_id=context.workspace_id,code_key=body.code.upper(),**fields,created_actor=context.actor,created_at=utcnow())
        session.add(item)
        return {'entry':catalog_entry(item),'duplicate':False}


@router.post('/items',status_code=201)
def create_item(body:ItemInput,context:Context,session:DB,response:Response):
    return create_catalog(body,context,session,InventoryItem,response)


@router.post('/locations',status_code=201)
def create_location(body:LocationInput,context:Context,session:DB,response:Response):
    return create_catalog(body,context,session,StorageLocation,response)


def balances(position):
    on_hand = position.on_hand if position else Decimal(0)
    reserved = position.reserved if position else Decimal(0)
    return {'on_hand':quantity_text(on_hand),'reserved':quantity_text(reserved),'available':quantity_text(on_hand-reserved)}


def position_view(session,position,item,location):
    report = session.scalar(select(StockRecord).where(StockRecord.position_id==position.id,StockRecord.kind=='report')
        .order_by(StockRecord.observed_at.desc(),StockRecord.sequence.desc()).limit(1)) if position else None
    return {'id':position.id if position else None,'item':catalog_entry(item),'location':catalog_entry(location),
        **balances(position),'version':position.version if position else 0,'updated_at':position.updated_at if position else None,
        'latest_report':{'reference':report.reference,'quantity':quantity_text(report.quantity),'source_name':report.source_name,
            'observed_at':report.observed_at,'received_at':report.received_at} if report else None}


def consumed(session,parent_id):
    return session.scalar(select(func.coalesce(func.sum(StockRecord.quantity),0)).where(StockRecord.parent_id==parent_id))


def record_view(item,remaining=None):
    return {**{key:getattr(item,key) for key in ('id','sequence','reference','kind','parent_id','parent_reference','request_id','request_reference','source_name','observed_at_raw','observed_at','received_at','actor','reason','after')},
        'quantity':quantity_text(item.quantity),'remaining_quantity':quantity_text(remaining) if remaining is not None else None}


@router.get('/position')
def detail(context:Context,session:DB,item_id:UUID,location_id:UUID,before_sequence:int | None=Query(default=None,ge=1)):
    with session.begin():
        workspace_lock(session,context)
        item,location=scoped(session,InventoryItem,context,item_id),scoped(session,StorageLocation,context,location_id)
        position=session.scalar(select(StockPosition).where(StockPosition.workspace_id==context.workspace_id,StockPosition.item_id==str(item_id),StockPosition.location_id==str(location_id)))
        records=[]
        if position:
            filters=[StockRecord.position_id==position.id]
            if before_sequence is not None:
                filters.append(StockRecord.sequence<before_sequence)
            records=session.scalars(select(StockRecord).where(*filters).order_by(StockRecord.sequence.desc()).limit(50)).all()
        parent_ids=[record.id for record in records if record.kind in {'reserve','issue'}]
        used=dict(session.execute(select(StockRecord.parent_id,func.sum(StockRecord.quantity)).where(StockRecord.parent_id.in_(parent_ids)).group_by(StockRecord.parent_id)).all()) if parent_ids else {}
        return {'position':position_view(session,position,item,location),
            'records':[record_view(record,record.quantity-used.get(record.id,Decimal(0)) if record.id in parent_ids else None) for record in records],
            'next_before_sequence':records[-1].sequence if records and records[-1].sequence>1 else None}


@router.get('')
def list_positions(context:Context,session:DB,q:str=Query(default='',max_length=200),page:int=Query(default=1,ge=1,le=100000)):
    with session.begin():
        workspace_lock(session,context)
        query=select(StockPosition,InventoryItem,StorageLocation).join(InventoryItem,StockPosition.item_id==InventoryItem.id).join(StorageLocation,StockPosition.location_id==StorageLocation.id).where(StockPosition.workspace_id==context.workspace_id)
        if q.strip():
            query=query.where(or_(*(func.lower(field).contains(q.strip().lower(),autoescape=True) for field in
                (InventoryItem.code,InventoryItem.name,StorageLocation.code,StorageLocation.name,StorageLocation.locality))))
        total=session.scalar(select(func.count()).select_from(query.subquery()))
        pages=max(1,(total+19)//20);page=min(page,pages)
        rows=session.execute(query.order_by(StockPosition.updated_at.desc(),StockPosition.id).offset((page-1)*20).limit(20)).all()
        return {'items':[position_view(session,*row) for row in rows],'total':total,'page':page,'total_pages':pages,'page_size':20,'server_time':utcnow()}


def commitments(session,request):
    signed=case((StockRecord.kind=='reserve',StockRecord.quantity),
        (StockRecord.kind.in_(['release','return']),-StockRecord.quantity),else_=Decimal(0))
    rows=session.execute(select(InventoryItem.unit,InventoryItem.category,func.sum(signed)).join(StockPosition,StockRecord.position_id==StockPosition.id)
        .join(InventoryItem,StockPosition.item_id==InventoryItem.id).where(StockRecord.request_id==request.id).group_by(InventoryItem.unit,InventoryItem.category)).all()
    incompatible=any(amount>0 and (unit!=request.unit or category!=request.category) for unit,category,amount in rows)
    total=sum((amount for unit,category,amount in rows if unit==request.unit and category==request.category),Decimal(0))
    return total,incompatible


@router.get('/requests')
def eligible_requests(context:Context,session:DB,item_id:UUID,q:str=Query(default='',max_length=200)):
    with session.begin():
        workspace_lock(session,context);item=scoped(session,InventoryItem,context,item_id)
        query=select(ReliefRequest).where(ReliefRequest.workspace_id==context.workspace_id,ReliefRequest.status=='reviewed',ReliefRequest.category==item.category,ReliefRequest.unit==item.unit)
        if q.strip():
            query=query.where(or_(func.lower(ReliefRequest.reference).contains(q.strip().lower(),autoescape=True),func.lower(ReliefRequest.requesting_organisation).contains(q.strip().lower(),autoescape=True)))
        total=session.scalar(select(func.count()).select_from(query.subquery()))
        requests=session.scalars(query.order_by(ReliefRequest.updated_at.desc(),ReliefRequest.id).limit(20)).all()
        values=[]
        for request in requests:
            committed,incompatible=commitments(session,request)
            values.append({'id':request.id,'reference':request.reference,'organisation':request.requesting_organisation,
                'quantity':quantity_text(request.quantity),'remaining':quantity_text(max(Decimal(0),request.quantity-committed)),
                'allocation_warning':incompatible,'unit':request.unit})
        return {'items':values,'total':total}


def digest(body):
    value=body.model_dump(mode='json',exclude={'submission_key','expected_version'})
    value.update(reference=body.reference.upper(),quantity=quantity_text(body.quantity),observed_at=parse_timestamp(body.observed_at).isoformat())
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def check_request(session,context,request_id,item,extra=Decimal(0)):
    request=scoped(session,ReliefRequest,context,request_id)
    if request.status!='reviewed':
        raise HTTPException(409,'The relief request must currently be reviewed. Release reservations or return stock if the request has changed.')
    if request.unit!=item.unit or request.category!=item.category:
        raise HTTPException(409,'The item and request must have the same category and unit. No automatic unit conversion is performed.')
    committed,incompatible=commitments(session,request)
    if incompatible or committed+extra>request.quantity:
        raise HTTPException(409,'This exceeds the request quantity or conflicts with earlier allocations. Release or return the affected stock before allocating again.')
    return request


def record_locked(body,context,session,return_for_shipment_id=None):
    """Caller must hold the workspace write lock. Shared with the fictional seed."""
    fingerprint=digest(body)
    previous=session.scalar(select(StockRecord).where(StockRecord.workspace_id==context.workspace_id,StockRecord.submission_key==str(body.submission_key)))
    if previous is None:
        previous=session.scalar(select(StockRecord).where(StockRecord.workspace_id==context.workspace_id,StockRecord.reference_key==body.reference.upper()))
    if previous:
        if previous.digest!=fingerprint:
            raise HTTPException(409,'This save identifier or reference already records different details. Inspect the stock history; use a new reference for a new event.')
        return previous,True
    item,location=scoped(session,InventoryItem,context,body.item_id),scoped(session,StorageLocation,context,body.location_id)
    position=session.scalar(select(StockPosition).where(StockPosition.workspace_id==context.workspace_id,StockPosition.item_id==item.id,StockPosition.location_id==location.id).with_for_update())
    if (position.version if position else 0)!=body.expected_version:
        raise HTTPException(409,'This stock position changed after you opened it. Refresh its details before recording another event.')
    if parse_timestamp(body.observed_at)>utcnow()+timedelta(minutes=5):
        raise HTTPException(422,'Use a source time that is not in the future. This ledger records reported events, not planned movements.')
    if position is None:
        position=StockPosition(id=str(uuid4()),workspace_id=context.workspace_id,item_id=item.id,location_id=location.id,on_hand=Decimal(0),reserved=Decimal(0),version=0,updated_at=utcnow())
        session.add(position);session.flush()
    request=None;parent=None
    if body.kind=='reserve':
        request=check_request(session,context,body.request_id,item,extra=body.quantity)
    if body.parent_id:
        parent=scoped(session,StockRecord,context,body.parent_id)
        expected_kind='issue' if body.kind=='return' else 'reserve'
        if parent.position_id!=position.id or parent.kind!=expected_kind:
            raise HTTPException(409,'Choose the original reservation or issue from this same item and location.')
        if body.quantity>parent.quantity-consumed(session,parent.id):
            raise HTTPException(409,'This exceeds the original record’s remaining quantity. Refresh the history before retrying.')
        if body.kind=='return':
            claims=select(func.coalesce(func.sum(Shipment.quantity-Shipment.returned),0)).where(Shipment.issue_id==parent.id,Shipment.status!='cancelled')
            if return_for_shipment_id:
                claims=claims.where(Shipment.id!=return_for_shipment_id)
            if body.quantity>parent.quantity-consumed(session,parent.id)-session.scalar(claims):
                raise HTTPException(409,'This issue is assigned to shipment records. Record an undelivered return through Delivery tracking, or cancel an unstarted shipment first.')
        request=scoped(session,ReliefRequest,context,parent.request_id)
        if body.kind=='issue':
            request=check_request(session,context,parent.request_id,item)
    quantity=body.quantity
    if body.kind in {'receipt','return','adjustment_in'}:
        position.on_hand+=quantity
    elif body.kind=='reserve':
        position.reserved+=quantity
    elif body.kind=='release':
        position.reserved-=quantity
    elif body.kind=='issue':
        position.on_hand-=quantity;position.reserved-=quantity
    elif body.kind=='adjustment_out':
        position.on_hand-=quantity
    if not (Decimal(0)<=position.reserved<=position.on_hand<=MAX_QUANTITY):
        raise HTTPException(409,'Insufficient unreserved stock, or the stock limit would be exceeded. Refresh balances and check the quantity.')
    now=utcnow();position.version+=1;position.updated_at=now
    record=StockRecord(id=str(uuid4()),workspace_id=context.workspace_id,position_id=position.id,sequence=position.version,
        reference=body.reference,reference_key=body.reference.upper(),submission_key=str(body.submission_key),digest=fingerprint,
        kind=body.kind,quantity=quantity,parent_id=str(body.parent_id) if body.parent_id else None,
        parent_reference=parent.reference if parent else None,
        request_id=request.id if request else None,request_reference=request.reference if request else None,
        source_name=body.source_name,observed_at=parse_timestamp(body.observed_at),observed_at_raw=body.observed_at,
        received_at=now,actor_id=context.actor_id,actor=context.actor,reason=body.reason,after=balances(position))
    session.add(record);session.flush()
    return record,False


@router.post('/records',status_code=201)
def create_record(body:RecordInput,context:Context,session:DB,response:Response):
    with session.begin():
        workspace_lock(session,context,write=True)
        record,duplicate=record_locked(body,context,session)
        if duplicate:
            response.status_code=200
        return {'record':record_view(record),'duplicate':duplicate}
