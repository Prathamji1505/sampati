from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from backend.app.models import Membership, utcnow
from .test_accounts import post, signup
from .test_relief import payload as request_payload


def payload(**changes):
    return {'schema_version':'sampati.incident.v1', 'external_reference':'FLOOD-001',
        'title':'Fictional flood observation', 'hazard':'flood', 'assessment_kind':'impact_observation',
        'locality':'Fictional Riverside', 'observed_at':(utcnow()-timedelta(hours=2)).isoformat(),
        'generated_at':(utcnow()-timedelta(hours=1)).isoformat(), 'source_name':'Fictional assessment desk',
        'source_url':'https://example.org/fictional-evidence', 'summary':'Fictional report of water around access roads.',
        'uncertainty':'Cloud cover and local access have not been verified.',
        'extent':{'west':85.1,'south':25.4,'east':85.2,'north':25.5}, 'reported_affected_people':None, **changes}


def create(client, auth, body=None):
    response=post(client,'/api/incidents',auth,json=body or payload())
    assert response.status_code==201, response.text
    return response.json()['incident']


def review(client, auth, item, status, reason='Fictional evidence checked with its limitations.'):
    return post(client,f"/api/incidents/{item['id']}/review",auth,
        json={'status':status,'expected_version':item['version'],'reason':reason})


def test_incident_intake_and_idempotency_preserve_original_evidence(client):
    auth=signup(client); body=payload()
    before=client.get('/api/workspace').json()
    item=create(client,auth,body)
    assert item['status']=='pending' and item['version']==1 and item['assessment']==body
    same=post(client,'/api/incidents',auth,json={**body,'external_reference':'flood-001'})
    assert same.status_code==200 and same.json()['duplicate']
    assert same.json()['incident']['assessment']['external_reference']=='FLOOD-001'
    assert post(client,'/api/incidents',auth,json={**body,'summary':'Different report with the same reference.'}).status_code==409
    detail=client.get('/api/incidents/'+item['id']).json()
    assert len(detail['events'])==1 and detail['events'][0]['before_status'] is None
    assert '@cedar-owner' in detail['events'][0]['actor']
    after=client.get('/api/workspace').json()
    assert {key:before[key] for key in ('revision','aircraft','imports')}=={key:after[key] for key in ('revision','aircraft','imports')}


@pytest.mark.parametrize('changes',[
    {'schema_version':'unknown'}, {'assessment_kind':'forecast'}, {'hazard':'war'},
    {'observed_at':'2026-11-08T10:00:00'}, {'generated_at':'2000-01-01T00:00:00Z'},
    {'observed_at':(utcnow()+timedelta(days=1)).isoformat(),'generated_at':(utcnow()+timedelta(days=2)).isoformat()},
    {'uncertainty':'  '}, {'summary':'short'}, {'reported_affected_people':True},
    {'reported_affected_people':-1}, {'reported_affected_people':1.5},
    {'extent':{'west':90,'south':20,'east':85,'north':21}},
    {'extent':{'west':85,'south':20,'east':86,'north':20}},
    {'extent':{'west':True,'south':20,'east':86,'north':21}},
    {'extent':{'west':-181,'south':20,'east':86,'north':21}},
    {'source_url':'javascript:alert(1)'}, {'source_url':'http://example.org'},
    {'source_url':'https://user:password@example.org'}, {'status':'reviewed'}, {'workspace_id':'other'},
])
def test_incident_contract_rejects_invalid_and_server_owned_input(client,changes):
    auth=signup(client)
    assert post(client,'/api/incidents',auth,json=payload(**changes)).status_code==422
    assert client.get('/api/incidents').json()['total']==0


def test_incident_review_graph_version_noop_and_audit(client):
    auth=signup(client); item=create(client,auth)
    assert review(client,auth,item,'reviewed','  ').status_code==422
    same=review(client,auth,item,'pending')
    assert same.json()['unchanged'] and same.json()['incident']['version']==1
    current=review(client,auth,item,'reviewed').json()['incident']
    assert current['version']==2
    assert review(client,auth,item,'dismissed').status_code==409
    dismissed=review(client,auth,current,'dismissed').json()['incident']
    assert review(client,auth,dismissed,'reviewed').status_code==409
    reopened=review(client,auth,dismissed,'pending').json()['incident']
    detail=client.get('/api/incidents/'+item['id']).json()
    assert reopened['version']==4 and [event['version'] for event in detail['events']]==[4,3,2,1]
    assert detail['incident']['assessment']==item['assessment']


def test_link_requires_reviewed_same_organisation_and_survives_reopen(client):
    auth=signup(client); incident=create(client,auth)
    body=request_payload(incident_id=incident['id'])
    assert post(client,'/api/relief-requests',auth,json=body).status_code==409
    incident=review(client,auth,incident,'reviewed').json()['incident']
    response=post(client,'/api/relief-requests',auth,json=body)
    assert response.status_code==201
    request=response.json()['request']
    assert request['incident_id']==incident['id'] and request['incident_reference']=='FLOOD-001'
    assert client.get('/api/relief-requests/'+request['id']).json()['events'][0]['after']['incident_id']==incident['id']
    assert post(client,'/api/relief-requests',auth,json=body).json()['duplicate']
    review(client,auth,incident,'pending')
    detail=client.get('/api/incidents/'+incident['id']).json()
    assert detail['linked_request_count']==1 and detail['linked_requests'][0]['id']==request['id']
    assert post(client,'/api/relief-requests',auth,json=request_payload(reference='REL-002',incident_id=incident['id'])).status_code==409
    other=signup(client,username='other-owner')
    assert client.get('/api/incidents/'+incident['id']).status_code==404
    assert post(client,'/api/relief-requests',other,json=request_payload(incident_id=incident['id'])).status_code==404
    assert client.get('/api/incidents').json()['total']==0
    assert create(client,other)['assessment']['external_reference']=='FLOOD-001'


def test_incident_roles_csrf_and_demo_are_enforced(client):
    assert client.get('/api/incidents').status_code==401
    assert client.post('/api/demo/incidents',json=payload()).status_code==403
    assert client.get('/api/demo/incidents/contract').json()['properties']['schema_version']['const']=='sampati.incident.v1'
    auth=signup(client); item=create(client,auth)
    assert client.post('/api/incidents',json=payload(external_reference='NO-CSRF')).status_code==403
    with client.test_sessions.begin() as session:
        session.get(Membership,(auth['user']['id'],auth['workspace']['id'])).role='viewer'
    assert client.get('/api/incidents/'+item['id']).status_code==200
    assert review(client,auth,item,'reviewed').status_code==403
    assert post(client,'/api/incidents',auth,json=payload(external_reference='VIEWER')).status_code==403
    assert not client.get('/api/incidents').json()['can_edit']
    with client.test_sessions.begin() as session:
        session.get(Membership,(auth['user']['id'],auth['workspace']['id'])).role='editor'
    assert review(client,auth,item,'reviewed').status_code==200


def test_incident_search_paging_and_old_observation_are_explicit(client):
    auth=signup(client)
    for index in range(22):
        create(client,auth,payload(external_reference=f'FLOOD-{index:03}',locality='Fictional 100% Valley' if index==0 else 'Other Ward',
            observed_at=(utcnow()-timedelta(days=3)).isoformat()))
    first=client.get('/api/incidents').json(); second=client.get('/api/incidents?page=2').json()
    assert first['total']==22 and len(first['items'])==20 and len(second['items'])==2
    assert len({item['id'] for item in first['items']+second['items']})==22
    assert first['items'][0]['older_than_24h']
    assert client.get('/api/incidents?q=%').json()['total']==1
    assert client.get('/api/incidents?status=reviewed').json()['total']==0
    assert client.get('/api/incidents?page=999').json()['page']==2


def test_concurrent_incident_review_has_one_winner(client):
    auth=signup(client); item=create(client,auth)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda status:review(client,auth,item,status),['reviewed','dismissed']))
    assert sorted(response.status_code for response in results)==[200,409]
    assert len(client.get('/api/incidents/'+item['id']).json()['events'])==2


def test_incident_history_pagination(client):
    auth=signup(client); item=create(client,auth)
    for index in range(51):
        item=review(client,auth,item,'reviewed' if item['status']=='pending' else 'pending').json()['incident']
    first=client.get('/api/incidents/'+item['id']).json()
    assert len(first['events'])==50 and first['next_before_version']==3
    older=client.get('/api/incidents/'+item['id']+'?before_version=3').json()
    assert [event['version'] for event in older['events']]==[2,1] and older['next_before_version'] is None
