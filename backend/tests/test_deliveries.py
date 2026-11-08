from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4, uuid5

import pytest

from backend.app.models import Membership, utcnow
from .test_accounts import post, signup
from .test_inventory import detail as stock_detail, movement, reviewed_request, setup_stock
from .test_relief import transition


def issued_stock(client,auth):
    item,location,body,_=setup_stock(client,auth,'100.125')
    request=reviewed_request(client,auth)
    reservation=movement(client,auth,body,kind='reserve',quantity='40',request_id=request['id']).json()['record']
    issue=movement(client,auth,body,kind='issue',quantity='30.125',parent_id=reservation['id']).json()['record']
    return item,location,body,request,issue


def draft_payload(issue,**changes):
    return {'reference':'SHIP-001','submission_key':str(uuid4()),'issue_id':issue['id'],'quantity':'20.125',
        'receiving_organisation':'Fictional community relief desk','destination':'Fictional Riverside Ward',
        'note':'Fictional tracking example.',**changes}


def create(client,auth,issue,**changes):
    response=post(client,'/api/deliveries',auth,json=draft_payload(issue,**changes))
    assert response.status_code==201,response.text
    return response.json()['shipment']


def action_payload(item,kind,**changes):
    return {'kind':kind,'reference':'EVIDENCE-'+uuid4().hex[:14],'submission_key':str(uuid4()),
        'expected_version':item['version'],'source_name':'Fictional signed logistics log',
        'observed_at':utcnow().isoformat(),'reason':'Fictional source evidence checked and recorded.',**changes}


def action(client,auth,item,kind,**changes):
    return post(client,'/api/deliveries/'+item['id']+'/events',auth,json=action_payload(item,kind,**changes))


def dispatch(client,auth,item):
    approved=action(client,auth,item,'approved')
    assert approved.status_code==201,approved.text
    dispatched=action(client,auth,approved.json()['shipment'],'dispatched')
    assert dispatched.status_code==201,dispatched.text
    return dispatched.json()['shipment']


def test_shipment_partial_delivery_return_closes_and_updates_stock_atomically(client):
    auth=signup(client);item,location,body,request,issue=issued_stock(client,auth)
    ship=create(client,auth,issue)
    assert ship['status']=='draft' and ship['delivered']=='0' and ship['unit']=='packs'
    assert stock_detail(client,item,location)['position']['on_hand']=='70'
    ship=dispatch(client,auth,ship)
    result=action(client,auth,ship,'delivery',quantity='12.125')
    assert result.status_code==201,result.text
    ship=result.json()['shipment']
    assert ship['status']=='partially_delivered' and ship['unresolved']=='8'
    need=client.get('/api/deliveries/needs').json()['items'][0]
    assert need['delivered']=='12.125' and need['remaining']=='27.875'
    returned=action(client,auth,ship,'return',quantity='8',expected_stock_version=ship['stock_version'])
    assert returned.status_code==201,returned.text
    ship=returned.json()['shipment']
    assert ship['status']=='closed' and ship['returned']=='8' and ship['delivered']=='12.125' and ship['unresolved']=='0'
    assert stock_detail(client,item,location)['position']['on_hand']=='78'
    history=client.get('/api/deliveries/'+ship['id']).json()['events']
    assert len(history)==5 and history[0]['stock_reference'].startswith('SRET-') and history[0]['stock_record_id']
    assert '@cedar-owner' in history[0]['actor']
    assert history[0]['after']['delivered']=='12.125'


def test_delivered_is_derived_from_evidence_and_correction_preserves_original(client):
    auth=signup(client);item,location,body,request,issue=issued_stock(client,auth)
    ship=dispatch(client,auth,create(client,auth,issue))
    result=action(client,auth,ship,'delivery',quantity='20.125');ship=result.json()['shipment'];arrival=result.json()['event']
    assert ship['status']=='delivered'
    assert action(client,auth,ship,'return',quantity='1',expected_stock_version=ship['stock_version']).status_code==409
    corrected=action(client,auth,ship,'delivery_correction',quantity='2.125',parent_event_id=arrival['id'])
    assert corrected.status_code==201,corrected.text
    ship=corrected.json()['shipment']
    assert ship['status']=='partially_delivered' and ship['delivered']=='18' and ship['unresolved']=='2.125'
    history=client.get('/api/deliveries/'+ship['id']).json()['events']
    assert history[0]['parent_reference']==arrival['reference']
    original=next(event for event in history if event['id']==arrival['id'])
    assert original['quantity']=='20.125' and original['correctable_quantity']=='18'
    assert stock_detail(client,item,location)['position']['on_hand']=='70'
    assert action(client,auth,ship,'delivery_correction',quantity='18.001',parent_event_id=arrival['id']).status_code==409


@pytest.mark.parametrize('changes',[
    {'quantity':True},{'quantity':'0'},{'quantity':'-1'},{'quantity':'0.0001'},
    {'quantity':'NaN'},{'quantity':'Infinity'},{'quantity':'1000000001'},
    {'receiving_organisation':' '},{'destination':' '},{'status':'delivered'},{'workspace_id':'other'},{'unit':'litres'},
])
def test_draft_validation_is_atomic(client,changes):
    auth=signup(client);item,location,body,request,issue=issued_stock(client,auth)
    response=post(client,'/api/deliveries',auth,json=draft_payload(issue,**changes))
    assert response.status_code==422,response.text
    assert client.get('/api/deliveries').json()['total']==0


def test_evidence_fields_and_source_chronology_are_enforced(client):
    auth=signup(client);item,location,body,request,issue=issued_stock(client,auth)
    ship=create(client,auth,issue)
    assert action(client,auth,ship,'delivery',quantity='1').status_code==409
    for changes in ({'reason':' '},{'source_name':' '},{'observed_at':'2026-11-08T10:00:00'},
        {'expected_version':True},{'quantity':'1'},{'workspace_id':'other'},{'status':'delivered'}):
        assert action(client,auth,ship,'approved',**changes).status_code==422
    assert action(client,auth,ship,'approved',observed_at=(utcnow()+timedelta(days=1)).isoformat()).status_code==422
    approved=action(client,auth,ship,'approved').json()['shipment']
    assert action(client,auth,approved,'dispatched',observed_at=(utcnow()-timedelta(days=1)).isoformat()).status_code==409
    ship=action(client,auth,approved,'dispatched').json()['shipment']
    assert action(client,auth,ship,'delivery',quantity='1',observed_at=(utcnow()-timedelta(days=1)).isoformat()).status_code==409


def test_shipment_and_event_retries_are_safe_after_commit_and_later_changes(client):
    auth=signup(client);item,location,body,request,issue=issued_stock(client,auth)
    payload=draft_payload(issue);response=post(client,'/api/deliveries',auth,json=payload);ship=response.json()['shipment']
    duplicate=post(client,'/api/deliveries',auth,json={**payload,'reference':'ship-001','quantity':'20.1250'})
    assert duplicate.status_code==200 and duplicate.json()['duplicate']
    assert post(client,'/api/deliveries',auth,json={**payload,'quantity':'19'}).status_code==409
    evidence=action_payload(ship,'approved');approved=post(client,'/api/deliveries/'+ship['id']+'/events',auth,json=evidence).json()['shipment']
    ship=action(client,auth,approved,'dispatched').json()['shipment']
    repeat=post(client,'/api/deliveries/'+ship['id']+'/events',auth,json=evidence)
    assert repeat.status_code==200 and repeat.json()['duplicate'] and repeat.json()['shipment']['status']=='in_transit'
    assert action(client,auth,approved,'cancelled').status_code==409
    assert post(client,'/api/deliveries/'+ship['id']+'/events',auth,json={**evidence,'reason':'Different source.'}).status_code==409
    assert len(client.get('/api/deliveries/'+ship['id']).json()['events'])==3


def test_assignment_cancellation_and_direct_stock_returns_share_issue_limit(client):
    auth=signup(client);item,location,body,request,issue=issued_stock(client,auth)
    ship=create(client,auth,issue)
    assert post(client,'/api/deliveries',auth,json=draft_payload(issue,reference='SECOND',quantity='11')).status_code==409
    assert movement(client,auth,body,kind='return',quantity='10.001',parent_id=issue['id']).status_code==409
    assert movement(client,auth,body,kind='return',quantity='10',parent_id=issue['id']).status_code==201
    cancelled=action(client,auth,ship,'cancelled').json()['shipment']
    assert cancelled['status']=='cancelled'
    assert movement(client,auth,body,kind='return',quantity='20.125',parent_id=issue['id']).status_code==201
    assert action(client,auth,cancelled,'approved').status_code==409


def test_failed_stock_return_leaves_delivery_and_stock_history_unchanged(client):
    auth=signup(client);item,location,body,request,issue=issued_stock(client,auth)
    ship=dispatch(client,auth,create(client,auth,issue))
    before=stock_detail(client,item,location)
    assert action(client,auth,ship,'return',quantity='2',expected_stock_version=ship['stock_version']-1).status_code==409
    assert stock_detail(client,item,location)==before
    actual=client.get('/api/deliveries/'+ship['id']).json()
    assert actual['shipment']['returned']=='0' and len(actual['events'])==3


def test_return_response_retry_does_not_restock_twice(client):
    auth=signup(client);item,location,body,request,issue=issued_stock(client,auth)
    ship=dispatch(client,auth,create(client,auth,issue))
    evidence=action_payload(ship,'return',quantity='2.125',expected_stock_version=ship['stock_version'])
    url='/api/deliveries/'+ship['id']+'/events'
    assert post(client,url,auth,json=evidence).status_code==201
    repeat=post(client,url,auth,json=evidence)
    assert repeat.status_code==200 and repeat.json()['duplicate']
    assert stock_detail(client,item,location)['position']['on_hand']=='72.125'
    assert len([record for record in stock_detail(client,item,location)['records'] if record['kind']=='return'])==1


def test_request_cancellation_keeps_actual_delivery_recording_but_blocks_new_dispatch(client):
    auth=signup(client);item,location,body,request,issue=issued_stock(client,auth)
    ship=dispatch(client,auth,create(client,auth,issue))
    second=create(client,auth,issue,reference='SECOND',quantity='10')
    transition(client,auth,request,'cancelled')
    assert action(client,auth,second,'approved').status_code==409
    assert action(client,auth,ship,'delivery',quantity='1').status_code==201
    assert client.get('/api/deliveries/needs').json()['total']==0


def test_request_corrections_cannot_invalidate_active_or_confirmed_shipments(client):
    auth=signup(client);item,location,body,request,issue=issued_stock(client,auth)
    ship=create(client,auth,issue)
    draft=transition(client,auth,request,'draft').json()['request']
    fields={key:draft[key] for key in ('requesting_organisation','locality','category','item_name','quantity','unit','needed_by','source_name','note')}
    def edit(**changes):
        return client.patch('/api/relief-requests/'+request['id'],headers={'X-CSRF-Token':auth['csrf_token']},json={**fields,'expected_version':draft['version'],'reason':'Fictional source correction.',**changes})
    assert edit(quantity='20').status_code==409
    assert edit(unit='litres').status_code==409
    action(client,auth,ship,'cancelled')
    assert edit(unit='litres').status_code==200


def test_delivery_roles_csrf_demo_and_foreign_ids(client):
    assert client.get('/api/deliveries').status_code==401
    assert client.get('/api/demo/deliveries').status_code==200
    auth=signup(client);item,location,body,request,issue=issued_stock(client,auth);ship=create(client,auth,issue)
    assert client.post('/api/deliveries/'+ship['id']+'/events',json=action_payload(ship,'approved')).status_code==403
    with client.test_sessions.begin() as session:
        session.get(Membership,(auth['user']['id'],auth['workspace']['id'])).role='viewer'
    assert client.get('/api/deliveries/'+ship['id']).status_code==200 and not client.get('/api/deliveries').json()['can_edit']
    assert action(client,auth,ship,'approved').status_code==403
    with client.test_sessions.begin() as session:
        session.get(Membership,(auth['user']['id'],auth['workspace']['id'])).role='editor'
    assert action(client,auth,ship,'approved').status_code==201
    other=signup(client,username='other-owner')
    assert client.get('/api/deliveries/'+ship['id']).status_code==404
    assert post(client,'/api/deliveries',other,json=draft_payload(issue)).status_code==404
    assert client.get('/api/deliveries/issues').json()['items']==[]


def test_concurrent_shipments_cannot_assign_same_issue_twice(client):
    auth=signup(client);item,location,body,request,issue=issued_stock(client,auth)
    def save(index):
        return post(client,'/api/deliveries',auth,json=draft_payload(issue,reference=f'RACE-{index}'))
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(save,[1,2]))
    assert sorted(result.status_code for result in results)==[201,409]


def test_concurrent_confirmations_have_one_winner_and_no_over_delivery(client):
    auth=signup(client);item,location,body,request,issue=issued_stock(client,auth)
    ship=dispatch(client,auth,create(client,auth,issue))
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda index:action(client,auth,ship,'delivery',quantity='12'),[1,2]))
    assert sorted(result.status_code for result in results)==[201,409]
    assert client.get('/api/deliveries/'+ship['id']).json()['shipment']['delivered']=='12'


def test_delivery_search_paging_and_needs_are_exact(client):
    auth=signup(client);item,location,body,request,issue=issued_stock(client,auth)
    for index in range(22):
        create(client,auth,issue,reference=f'SHIP-{index:03}',quantity='1',destination='Fictional 100% Valley' if index==0 else 'Fictional Hill')
    assert client.get('/api/deliveries').json()['total']==22
    assert len(client.get('/api/deliveries?page=2').json()['items'])==2
    assert client.get('/api/deliveries?q=%').json()['total']==1
    assert client.get('/api/deliveries?status=in_transit').json()['total']==0
    need=client.get('/api/deliveries/needs?only_remaining=true').json()['items'][0]
    assert need['allocated']=='22' and need['delivered']=='0' and need['remaining']=='40'


def test_new_shipment_respects_a_request_quantity_corrected_after_issue(client):
    auth=signup(client);item,location,body,request,issue=issued_stock(client,auth)
    draft=transition(client,auth,request,'draft').json()['request']
    fields={key:draft[key] for key in ('requesting_organisation','locality','category','item_name','quantity','unit','needed_by','source_name','note')}
    response=client.patch('/api/relief-requests/'+request['id'],headers={'X-CSRF-Token':auth['csrf_token']},json={**fields,'quantity':'20','expected_version':draft['version'],'reason':'Fictional need corrected before shipment.'})
    assert response.status_code==200,response.text
    current=transition(client,auth,response.json()['request'],'submitted').json()['request']
    transition(client,auth,current,'reviewed')
    assert post(client,'/api/deliveries',auth,json=draft_payload(issue)).status_code==409
    assert create(client,auth,issue,quantity='20')['quantity']=='20'


def test_return_and_arrival_race_cannot_resolve_same_supplies_twice(client):
    auth=signup(client);item,location,body,request,issue=issued_stock(client,auth)
    ship=dispatch(client,auth,create(client,auth,issue))
    def save(kind):
        return action(client,auth,ship,kind,quantity='12',**({'expected_stock_version':ship['stock_version']} if kind=='return' else {}))
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(save,['delivery','return']))
    assert sorted(result.status_code for result in results)==[201,409]
    actual=client.get('/api/deliveries/'+ship['id']).json()['shipment']
    assert float(actual['delivered'])+float(actual['returned'])==12 and actual['unresolved']=='8.125'


def test_delivery_action_validation_cannot_spoof_links_or_quantities(client):
    auth=signup(client);item,location,body,request,issue=issued_stock(client,auth)
    ship=dispatch(client,auth,create(client,auth,issue))
    for changes in ({'quantity':True},{'quantity':'0'},{'quantity':'0.0001'},{'quantity':'NaN'},
        {'quantity':None},{'quantity':'1','expected_stock_version':ship['stock_version']},{'quantity':'1','parent_event_id':str(uuid4())}):
        assert action(client,auth,ship,'delivery',**changes).status_code==422
    assert movement(client,auth,body,kind='return',quantity='1',parent_id=issue['id'],return_for_shipment_id=ship['id']).status_code==422


def test_fully_returned_shipment_closes_without_claiming_delivery(client):
    auth=signup(client);item,location,body,request,issue=issued_stock(client,auth)
    ship=dispatch(client,auth,create(client,auth,issue))
    response=action(client,auth,ship,'return',quantity=ship['quantity'],expected_stock_version=ship['stock_version'])
    assert response.status_code==201,response.text
    actual=response.json()['shipment']
    assert actual['status']=='closed' and actual['delivered']=='0' and actual['unresolved']=='0'
    need=client.get('/api/deliveries/needs').json()['items'][0]
    assert need['remaining']=='40' and need['allocated']=='0'


def test_history_pages_retain_corrected_arrival_evidence(client):
    auth=signup(client);item,location,body,request,issue=issued_stock(client,auth)
    ship=dispatch(client,auth,create(client,auth,issue))
    for index in range(25):
        result=action(client,auth,ship,'delivery',quantity='1').json()
        ship=action(client,auth,result['shipment'],'delivery_correction',quantity='1',parent_event_id=result['event']['id']).json()['shipment']
    first=client.get('/api/deliveries/'+ship['id']).json()
    assert len(first['events'])==50 and first['next_before_version']==4
    older=client.get('/api/deliveries/'+ship['id']+'?before_version=4').json()
    assert [event['version'] for event in older['events']]==[3,2,1] and older['next_before_version'] is None


def test_existing_stock_identifier_cannot_be_counted_as_a_new_shipment_return(client):
    auth=signup(client);item,location,body,request,issue=issued_stock(client,auth)
    key=uuid4();observed=(utcnow()+timedelta(minutes=1)).isoformat()
    evidence=action_payload({'version':1},'return',quantity='1',expected_stock_version=3)
    evidence.update(submission_key=str(key),observed_at=observed)
    existing=movement(client,auth,body,kind='return',quantity='1',parent_id=issue['id'],
        reference='SRET-'+key.hex,submission_key=str(uuid5(key,'shipment-return')),
        observed_at=observed,source_name=evidence['source_name'],reason=evidence['reason'])
    assert existing.status_code==201,existing.text
    ship=dispatch(client,auth,create(client,auth,issue))
    evidence.update(expected_version=ship['version'],expected_stock_version=ship['stock_version'])
    response=post(client,'/api/deliveries/'+ship['id']+'/events',auth,json=evidence)
    assert response.status_code==409,response.text
    actual=client.get('/api/deliveries/'+ship['id']).json()
    assert actual['shipment']['returned']=='0' and len(actual['events'])==3
    assert stock_detail(client,item,location)['position']['on_hand']=='71'
