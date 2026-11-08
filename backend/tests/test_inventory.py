from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from backend.app.models import Membership, StockRecord, utcnow
from .test_accounts import post, signup
from .test_relief import create as create_request, payload as request_payload, transition


def setup_stock(client,auth,quantity='100'):
    item=post(client,'/api/inventory/items',auth,json={'code':'WATER-PACK','name':'Fictional water packs','category':'water','unit':'packs'}).json()['entry']
    location=post(client,'/api/inventory/locations',auth,json={'code':'STORE-A','name':'Fictional store','locality':'Fictional Riverside'}).json()['entry']
    body={'item_id':item['id'],'location_id':location['id'],'reference':'RECEIPT-001','submission_key':str(uuid4()),'expected_version':0,
        'kind':'receipt','quantity':quantity,'source_name':'Fictional signed store log','observed_at':utcnow().isoformat(),'reason':'Fictional supplies received and recorded.'}
    response=post(client,'/api/inventory/records',auth,json=body)
    assert response.status_code==201,response.text
    return item,location,body,response.json()['record']


def detail(client,item,location,**params):
    return client.get('/api/inventory/position',params={'item_id':item['id'],'location_id':location['id'],**params}).json()


def movement(client,auth,body,**changes):
    return post(client,'/api/inventory/records',auth,json={**body,'reference':'MOVE-'+uuid4().hex[:12],
        'submission_key':str(uuid4()),'expected_version':detail(client,{'id':body['item_id']},{'id':body['location_id']})['position']['version'],**changes})


def reviewed_request(client,auth,**changes):
    item=create_request(client,auth,request_payload(quantity='40',**changes))
    item=transition(client,auth,item,'submitted').json()['request']
    return transition(client,auth,item,'reviewed').json()['request']


def test_inventory_lifecycle_exact_quantities_and_append_only_history(client):
    auth=signup(client);before=client.get('/api/workspace').json()
    item,location,body,receipt=setup_stock(client,auth,'100.125')
    request=reviewed_request(client,auth)
    reserve=movement(client,auth,body,kind='reserve',quantity='30.125',request_id=request['id']).json()['record']
    issue=movement(client,auth,body,kind='issue',quantity='20.125',parent_id=reserve['id']).json()['record']
    assert movement(client,auth,body,kind='release',quantity='10',parent_id=reserve['id']).status_code==201
    assert movement(client,auth,body,kind='return',quantity='5.125',parent_id=issue['id']).status_code==201
    data=detail(client,item,location)
    assert {key:data['position'][key] for key in ('on_hand','reserved','available','version')}=={'on_hand':'85.125','reserved':'0','available':'85.125','version':5}
    assert len(data['records'])==5 and data['records'][-1]['id']==receipt['id']
    assert data['records'][-1]['after']['on_hand']=='100.125'
    assert data['records'][0]['request_reference']==request['reference']
    assert '@cedar-owner' in data['records'][0]['actor']
    eligible=client.get('/api/inventory/requests',params={'item_id':item['id']}).json()['items'][0]
    assert eligible['remaining']=='25'
    assert client.patch('/api/inventory/records/'+receipt['id'],json={}).status_code==404
    after=client.get('/api/workspace').json()
    assert {key:after[key] for key in ('aircraft','imports','revision')}=={key:before[key] for key in ('aircraft','imports','revision')}


def test_reports_are_separate_and_old_source_does_not_replace_newer_count(client):
    auth=signup(client);item,location,body,_=setup_stock(client,auth)
    assert movement(client,auth,body,kind='report',quantity='0',observed_at=(utcnow()-timedelta(hours=1)).isoformat()).status_code==201
    assert movement(client,auth,body,kind='report',quantity='50',observed_at=(utcnow()-timedelta(days=2)).isoformat()).status_code==201
    data=detail(client,item,location)
    assert data['position']['on_hand']=='100' and data['position']['available']=='100'
    assert data['position']['latest_report']['quantity']=='0'
    assert len(data['records'])==3


@pytest.mark.parametrize('changes',[
    {'quantity':True},{'quantity':'-1'},{'quantity':'0'},{'quantity':'0.0001'},{'quantity':'NaN'},
    {'quantity':'Infinity'},{'quantity':'1000000001'},{'observed_at':'2026-11-08T10:00:00'},
    {'observed_at':(utcnow()+timedelta(days=1)).isoformat()},{'source_name':' '},{'reason':' '},
    {'unit':'litres'},{'workspace_id':'other'},{'kind':'issue'},{'kind':'return'},
    {'kind':'reserve'},{'expected_version':True},{'on_hand':'200'},
])
def test_invalid_stock_event_is_atomic(client,changes):
    auth=signup(client);item,location,body,_=setup_stock(client,auth)
    response=movement(client,auth,body,**changes)
    assert response.status_code==422,response.text
    data=detail(client,item,location)
    assert data['position']['version']==1 and len(data['records'])==1


def test_duplicate_retry_reference_and_version_behavior(client):
    auth=signup(client);item,location,body,record=setup_stock(client,auth)
    repeat=post(client,'/api/inventory/records',auth,json={**body,'quantity':'100.000'})
    assert repeat.status_code==200 and repeat.json()['duplicate'] and repeat.json()['record']['id']==record['id']
    new_key=post(client,'/api/inventory/records',auth,json={**body,'submission_key':str(uuid4()),'reference':'receipt-001'})
    assert new_key.status_code==200
    assert post(client,'/api/inventory/records',auth,json={**body,'quantity':'99'}).status_code==409
    assert movement(client,auth,body,expected_version=0).status_code==409
    assert len(detail(client,item,location)['records'])==1


def test_reservation_issue_return_and_adjustment_limits(client):
    auth=signup(client);item,location,body,_=setup_stock(client,auth,'10')
    request=reviewed_request(client,auth)
    assert movement(client,auth,body,kind='reserve',quantity='11',request_id=request['id']).status_code==409
    reserve=movement(client,auth,body,kind='reserve',quantity='8',request_id=request['id']).json()['record']
    assert movement(client,auth,body,kind='adjustment_out',quantity='3').status_code==409
    assert movement(client,auth,body,kind='issue',quantity='9',parent_id=reserve['id']).status_code==409
    issue=movement(client,auth,body,kind='issue',quantity='7',parent_id=reserve['id']).json()['record']
    assert movement(client,auth,body,kind='release',quantity='2',parent_id=reserve['id']).status_code==409
    assert movement(client,auth,body,kind='return',quantity='8',parent_id=issue['id']).status_code==409
    assert movement(client,auth,body,kind='return',quantity='7',parent_id=issue['id']).status_code==201
    assert movement(client,auth,body,kind='return',quantity='0.001',parent_id=issue['id']).status_code==409
    assert movement(client,auth,body,kind='adjustment_out',quantity='2').status_code==201
    assert movement(client,auth,body,kind='adjustment_in',quantity='0.125').status_code==201
    data=detail(client,item,location)
    assert data['position']['on_hand']=='8.125' and data['position']['reserved']=='1'


def test_request_scope_review_units_categories_and_changed_needs(client):
    auth=signup(client);item,location,body,_=setup_stock(client,auth)
    draft=create_request(client,auth)
    assert movement(client,auth,body,kind='reserve',quantity='1',request_id=draft['id']).status_code==409
    wrong_unit=reviewed_request(client,auth,reference='OTHER-UNIT',unit='litres')
    assert movement(client,auth,body,kind='reserve',quantity='1',request_id=wrong_unit['id']).status_code==409
    wrong_category=reviewed_request(client,auth,reference='OTHER-CATEGORY',category='food')
    assert movement(client,auth,body,kind='reserve',quantity='1',request_id=wrong_category['id']).status_code==409
    request=reviewed_request(client,auth,reference='RIGHT')
    reserve=movement(client,auth,body,kind='reserve',quantity='40',request_id=request['id']).json()['record']
    assert movement(client,auth,body,kind='reserve',quantity='0.001',request_id=request['id']).status_code==409
    transition(client,auth,request,'cancelled')
    assert movement(client,auth,body,kind='issue',quantity='1',parent_id=reserve['id']).status_code==409
    assert movement(client,auth,body,kind='release',quantity='40',parent_id=reserve['id']).status_code==201


def test_allocation_limit_is_shared_across_storage_locations(client):
    auth=signup(client);item,location,body,_=setup_stock(client,auth)
    request=reviewed_request(client,auth)
    other=post(client,'/api/inventory/locations',auth,json={'code':'B','name':'Other store','locality':'Fictional Hill'}).json()['entry']
    other_body={**body,'location_id':other['id'],'reference':'OTHER-RECEIPT','submission_key':str(uuid4())}
    assert post(client,'/api/inventory/records',auth,json=other_body).status_code==201
    assert movement(client,auth,body,kind='reserve',quantity='30',request_id=request['id']).status_code==201
    assert movement(client,auth,other_body,kind='reserve',quantity='11',request_id=request['id']).status_code==409
    assert movement(client,auth,other_body,kind='reserve',quantity='10',request_id=request['id']).status_code==201


def test_catalog_is_scoped_immutable_and_retry_safe(client):
    auth=signup(client);item,location,body,_=setup_stock(client,auth)
    same={'code':'water-pack','name':item['name'],'category':'water','unit':'packs'}
    assert post(client,'/api/inventory/items',auth,json=same).status_code==200
    assert post(client,'/api/inventory/items',auth,json={**same,'unit':'litres'}).status_code==409
    for changes in ({'unit':'loads'},{'name':' '},{'category':'invalid'}):
        assert post(client,'/api/inventory/items',auth,json={**same,'code':'NEW',**changes}).status_code==422
    other=signup(client,username='other-owner')
    assert client.get('/api/inventory/catalog').json()['items']==[]
    assert client.get('/api/inventory/position',params={'item_id':item['id'],'location_id':location['id']}).status_code==404
    assert post(client,'/api/inventory/records',other,json={**body,'submission_key':str(uuid4())}).status_code==404
    assert post(client,'/api/inventory/items',other,json=same).status_code==201


def test_stock_roles_csrf_and_demo(client):
    assert client.get('/api/inventory').status_code==401
    assert client.get('/api/demo/inventory/catalog').status_code==200
    assert client.post('/api/demo/inventory/items',json={'code':'A','name':'Example','category':'water','unit':'packs'}).status_code==403
    auth=signup(client);item,location,body,_=setup_stock(client,auth)
    assert client.post('/api/inventory/records',json=body).status_code==403
    with client.test_sessions.begin() as session:
        session.get(Membership,(auth['user']['id'],auth['workspace']['id'])).role='viewer'
    assert client.get('/api/inventory').status_code==200 and not client.get('/api/inventory/catalog').json()['can_edit']
    assert movement(client,auth,body).status_code==403
    with client.test_sessions.begin() as session:
        session.get(Membership,(auth['user']['id'],auth['workspace']['id'])).role='editor'
    assert movement(client,auth,body,quantity='1').status_code==201


def test_stock_search_and_pagination(client):
    auth=signup(client);item,location,body,_=setup_stock(client,auth)
    for index in range(21):
        target=post(client,'/api/inventory/locations',auth,json={'code':f'EXTRA-{index}','name':'100% Store' if index==0 else 'Other store','locality':'Fictional Hill'}).json()['entry']
        assert post(client,'/api/inventory/records',auth,json={**body,'location_id':target['id'],'reference':f'RECEIPT-{index+2}','submission_key':str(uuid4())}).status_code==201
    assert client.get('/api/inventory').json()['total']==22
    assert len(client.get('/api/inventory?page=2').json()['items'])==2
    assert client.get('/api/inventory?q=%').json()['total']==1


def test_concurrent_stock_reservations_have_one_winner(client):
    auth=signup(client);item,location,body,_=setup_stock(client,auth,'10')
    request=reviewed_request(client,auth)
    def reserve(index):
        return post(client,'/api/inventory/records',auth,json={**body,'reference':f'RACE-{index}',
            'submission_key':str(uuid4()),'expected_version':1,'kind':'reserve','quantity':'8','request_id':request['id']})
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(reserve,[1,2]))
    assert sorted(result.status_code for result in results)==[201,409]
    position=detail(client,item,location)['position']
    assert position['reserved']=='8' and position['available']=='2'


def test_stock_history_pages_and_ceiling(client):
    auth=signup(client);item,location,body,_=setup_stock(client,auth,'1000000000')
    assert movement(client,auth,body,quantity='0.001').status_code==409
    for index in range(51):
        assert movement(client,auth,body,kind='report',quantity='0').status_code==201
    first=detail(client,item,location);older=detail(client,item,location,before_sequence=first['next_before_sequence'])
    assert len(first['records'])==50 and [record['sequence'] for record in older['records']]==[2,1]
    assert older['next_before_sequence'] is None


def test_concurrent_issues_cannot_take_the_same_reserved_stock_twice(client):
    auth=signup(client);item,location,body,_=setup_stock(client,auth,'10')
    request=reviewed_request(client,auth)
    reserve=movement(client,auth,body,kind='reserve',quantity='8',request_id=request['id']).json()['record']
    def issue(index):
        return post(client,'/api/inventory/records',auth,json={**body,'reference':f'ISSUE-RACE-{index}',
            'submission_key':str(uuid4()),'expected_version':2,'kind':'issue','quantity':'6','parent_id':reserve['id']})
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(issue,[1,2]))
    assert sorted(result.status_code for result in results)==[201,409]
    position=detail(client,item,location)['position']
    assert position['on_hand']=='4' and position['reserved']=='2' and position['available']=='2'
    assert movement(client,auth,body,kind='issue',quantity='6',parent_id=reserve['id']).status_code==409


def test_concurrent_reservations_at_different_stores_share_request_limit(client):
    auth=signup(client);item,location,body,_=setup_stock(client,auth)
    request=reviewed_request(client,auth)
    other=post(client,'/api/inventory/locations',auth,json={'code':'B','name':'Other store','locality':'Fictional Hill'}).json()['entry']
    other_body={**body,'location_id':other['id'],'reference':'B-RECEIPT','submission_key':str(uuid4())}
    assert post(client,'/api/inventory/records',auth,json=other_body).status_code==201
    def reserve(pair):
        index,source=pair
        return post(client,'/api/inventory/records',auth,json={**source,'reference':f'SHARED-RACE-{index}',
            'submission_key':str(uuid4()),'expected_version':1,'kind':'reserve','quantity':'30','request_id':request['id']})
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(reserve,[(1,body),(2,other_body)]))
    assert sorted(result.status_code for result in results)==[201,409]
    assert client.get('/api/inventory/requests',params={'item_id':item['id']}).json()['items'][0]['remaining']=='10'


def test_request_unit_correction_requires_resolving_old_allocations(client):
    auth=signup(client);item,location,body,_=setup_stock(client,auth)
    request=reviewed_request(client,auth)
    reserve=movement(client,auth,body,kind='reserve',quantity='8',request_id=request['id']).json()['record']
    draft=transition(client,auth,request,'draft').json()['request']
    editable={key:draft[key] for key in ('requesting_organisation','locality','category','item_name','quantity','unit','needed_by','source_name','note')}
    corrected=client.patch('/api/relief-requests/'+request['id'],headers={'X-CSRF-Token':auth['csrf_token']},
        json={**editable,'unit':'litres','expected_version':draft['version'],'reason':'Fictional source corrected its unit.'}).json()['request']
    corrected=transition(client,auth,corrected,'submitted').json()['request']
    transition(client,auth,corrected,'reviewed')
    litres=post(client,'/api/inventory/items',auth,json={'code':'WATER-LITRES','name':'Fictional drinking water','category':'water','unit':'litres'}).json()['entry']
    litre_body={**body,'item_id':litres['id'],'reference':'LITRE-RECEIPT','submission_key':str(uuid4())}
    assert post(client,'/api/inventory/records',auth,json=litre_body).status_code==201
    assert movement(client,auth,body,kind='issue',quantity='1',parent_id=reserve['id']).status_code==409
    assert movement(client,auth,litre_body,kind='reserve',quantity='1',request_id=request['id']).status_code==409
    assert movement(client,auth,body,kind='release',quantity='8',parent_id=reserve['id']).status_code==201
    assert movement(client,auth,litre_body,kind='reserve',quantity='1',request_id=request['id']).status_code==201


def test_parent_records_cannot_cross_item_or_storage_boundaries(client):
    auth=signup(client);item,location,body,_=setup_stock(client,auth)
    request=reviewed_request(client,auth)
    reserve=movement(client,auth,body,kind='reserve',quantity='8',request_id=request['id']).json()['record']
    other=post(client,'/api/inventory/locations',auth,json={'code':'B','name':'Other store','locality':'Fictional Hill'}).json()['entry']
    other_body={**body,'location_id':other['id'],'reference':'B-RECEIPT','submission_key':str(uuid4())}
    assert post(client,'/api/inventory/records',auth,json=other_body).status_code==201
    assert movement(client,auth,other_body,kind='issue',quantity='1',parent_id=reserve['id']).status_code==409
    assert movement(client,auth,body,kind='return',quantity='1',parent_id=reserve['id']).status_code==409
    assert len(detail(client,item,other)['records'])==1
