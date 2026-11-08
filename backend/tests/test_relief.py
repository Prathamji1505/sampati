from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4

import pytest

from backend.app.auth import COOKIE
from backend.app.models import Membership, ReliefRequest, ReliefRequestEvent, utcnow
from .test_accounts import FORM_HEADERS, post, signup
from .test_workspace_tools import use_cookie


def payload(**changes):
    return {'reference': 'REL-001', 'submission_key': str(uuid4()), 'requesting_organisation': 'Fictional Community Desk',
        'locality': 'Fictional River Ward', 'category': 'water', 'item_name': 'Drinking-water packs', 'quantity': '10.500',
        'unit': 'packs', 'needed_by': (utcnow() + timedelta(days=1)).isoformat(), 'source_name': 'Fictional desk register',
        'note': 'Fictional relief supplies only.', **changes}


def create(client, auth, body=None):
    response = post(client, '/api/relief-requests', auth, json=body or payload())
    assert response.status_code == 201, response.text
    return response.json()['request']


def transition(client, auth, item, status, reason='Request details checked.'):
    return post(client, f"/api/relief-requests/{item['id']}/status", auth,
        json={'status': status, 'expected_version': item['version'], 'reason': reason})


def test_relief_creation_is_attributable_and_separate_from_aircraft_revision(client):
    auth = signup(client)
    before = client.get('/api/workspace').json()
    item = create(client, auth)
    assert item['status'] == 'draft' and item['version'] == 1 and item['quantity'] == '10.5'
    assert '@cedar-owner' in item['created_actor']
    detail = client.get('/api/relief-requests/' + item['id']).json()
    assert len(detail['events']) == 1 and detail['events'][0]['before'] is None
    assert detail['events'][0]['after']['quantity'] == '10.5'
    after = client.get('/api/workspace').json()
    assert {key: after[key] for key in ('aircraft', 'imports', 'revision')} == {key: before[key] for key in ('aircraft', 'imports', 'revision')}


@pytest.mark.parametrize('changes', [
    {'quantity': '0'}, {'quantity': '-1'}, {'quantity': '0.0001'}, {'quantity': 'NaN'}, {'quantity': 'Infinity'},
    {'quantity': True}, {'quantity': '1000000001'}, {'needed_by': '2026-11-08T10:00:00'},
    {'requesting_organisation': '  '}, {'unit': 'loads'}, {'status': 'reviewed'}, {'workspace_id': 'other'},
])
def test_relief_validation_rejects_invalid_or_server_owned_fields(client, changes):
    auth = signup(client)
    response = post(client, '/api/relief-requests', auth, json=payload(**changes))
    assert response.status_code == 422
    assert client.get('/api/relief-requests').json()['total'] == 0


def test_relief_duplicate_reference_and_retry_semantics(client):
    auth = signup(client)
    body = payload(reference='Rel-001')
    item = create(client, auth, body)
    repeat = post(client, '/api/relief-requests', auth, json={**body, 'quantity': '10.5', 'reference': 'rel-001'})
    assert repeat.status_code == 200 and repeat.json()['duplicate'] and repeat.json()['request']['id'] == item['id']
    changed = post(client, '/api/relief-requests', auth, json={**body, 'quantity': '11'})
    assert changed.status_code == 409
    duplicate_ref = post(client, '/api/relief-requests', auth, json=payload(reference='REL-001'))
    assert duplicate_ref.status_code == 409
    assert len(client.get('/api/relief-requests/' + item['id']).json()['events']) == 1


def test_relief_review_correction_and_terminal_cancellation_are_audited(client):
    auth = signup(client)
    item = create(client, auth)
    assert transition(client, auth, item, 'reviewed').status_code == 409
    submitted = transition(client, auth, item, 'submitted').json()['request']
    assert submitted['version'] == 2
    assert transition(client, auth, item, 'cancelled').status_code == 409
    assert transition(client, auth, submitted, 'reviewed', reason='   ').status_code == 422
    reviewed = transition(client, auth, submitted, 'reviewed').json()['request']
    assert reviewed['version'] == 3
    assert transition(client, auth, reviewed, 'fulfilled').status_code == 422
    draft = transition(client, auth, reviewed, 'draft', 'Return for corrected quantity.').json()['request']
    edit_body = {key: draft[key] for key in ('requesting_organisation', 'locality', 'category', 'item_name', 'quantity', 'unit', 'needed_by', 'source_name', 'note')}
    edited = client.patch('/api/relief-requests/' + item['id'], headers={'X-CSRF-Token': auth['csrf_token']},
        json={**edit_body, 'quantity': '12.125', 'expected_version': draft['version'], 'reason': 'Corrected the source quantity.'})
    assert edited.status_code == 200 and edited.json()['request']['quantity'] == '12.125'
    cancelled = transition(client, auth, edited.json()['request'], 'cancelled').json()['request']
    assert cancelled['version'] == 6 and cancelled['allowed_transitions'] == []
    assert transition(client, auth, cancelled, 'draft').status_code == 409
    events = client.get('/api/relief-requests/' + item['id']).json()['events']
    assert [event['version'] for event in events] == [6, 5, 4, 3, 2, 1]
    assert events[1]['before']['quantity'] == '10.5' and events[1]['after']['quantity'] == '12.125'


def test_relief_edit_noop_and_wrong_state_do_not_rewrite_history(client):
    auth = signup(client)
    body = payload()
    item = create(client, auth, body)
    edit = {key: body[key] for key in ('requesting_organisation', 'locality', 'category', 'item_name', 'quantity', 'unit', 'needed_by', 'source_name', 'note')}
    response = client.patch('/api/relief-requests/' + item['id'], headers={'X-CSRF-Token': auth['csrf_token']},
        json={**edit, 'expected_version': 1, 'reason': 'Rechecked the same details.'})
    assert response.status_code == 200 and response.json()['unchanged'] and response.json()['request']['version'] == 1
    submitted = transition(client, auth, item, 'submitted').json()['request']
    response = client.patch('/api/relief-requests/' + item['id'], headers={'X-CSRF-Token': auth['csrf_token']},
        json={**edit, 'quantity': '4', 'expected_version': submitted['version'], 'reason': 'Correction.'})
    assert response.status_code == 409


def test_relief_organisation_isolation_demo_readonly_and_csrf(client):
    assert client.get('/api/relief-requests').status_code == 401
    assert client.get('/api/demo/relief-requests').status_code == 200
    assert client.post('/api/demo/relief-requests', json=payload()).status_code == 403
    first = signup(client, 'first-owner')
    assert client.post('/api/relief-requests', json=payload()).status_code == 403
    item = create(client, first)
    client.cookies.clear()
    second = signup(client, 'second-owner')
    assert client.get('/api/relief-requests', params={'workspace_id': first['workspace']['id']}).json()['items'] == []
    assert client.get('/api/relief-requests/' + item['id']).status_code == 404
    assert transition(client, second, item, 'submitted').status_code == 404
    assert create(client, second)['reference'] == item['reference']


def test_relief_viewer_reads_and_editor_writes(client):
    auth = signup(client)
    item = create(client, auth)
    with client.test_sessions.begin() as session:
        session.get(Membership, (auth['user']['id'], auth['workspace']['id'])).role = 'viewer'
    assert client.get('/api/relief-requests/' + item['id']).status_code == 200
    assert not client.get('/api/relief-requests').json()['can_edit']
    assert post(client, '/api/relief-requests', auth, json=payload(reference='REL-002')).status_code == 403
    assert transition(client, auth, item, 'submitted').status_code == 403
    with client.test_sessions.begin() as session:
        session.get(Membership, (auth['user']['id'], auth['workspace']['id'])).role = 'editor'
    assert transition(client, auth, item, 'submitted').status_code == 200


def test_relief_search_is_literal_and_filters_pages_and_deadlines_are_explicit(client):
    auth = signup(client)
    overdue = create(client, auth, payload(locality='Fictional 100% ward', needed_by=(utcnow() - timedelta(days=1)).isoformat()))
    assert overdue['past_deadline']
    for index in range(1, 22):
        create(client, auth, payload(reference=f'REL-{index+1:03}', category='food'))
    first = client.get('/api/relief-requests').json()
    second = client.get('/api/relief-requests', params={'page': 2}).json()
    assert first['total'] == 22 and len(first['items']) == 20 and len(second['items']) == 2
    assert client.get('/api/relief-requests', params={'q': '%'}).json()['total'] == 1
    assert client.get('/api/relief-requests', params={'category': 'food'}).json()['total'] == 21
    assert client.get('/api/relief-requests', params={'status': 'submitted'}).json()['total'] == 0
    cancelled = transition(client, auth, overdue, 'cancelled').json()['request']
    assert not cancelled['past_deadline']


def test_relief_audit_pagination_and_optimistic_edit_protection(client):
    auth = signup(client)
    item = create(client, auth)
    for index in range(51):
        target = 'submitted' if item['status'] == 'draft' else 'draft'
        response = transition(client, auth, item, target, f'Fictional review cycle {index}.')
        assert response.status_code == 200
        item = response.json()['request']
    first = client.get('/api/relief-requests/' + item['id']).json()
    assert len(first['events']) == 50 and first['next_before_version'] == 3
    older = client.get('/api/relief-requests/' + item['id'], params={'before_version': 3}).json()
    assert [event['version'] for event in older['events']] == [2, 1] and older['next_before_version'] is None


def test_concurrent_relief_updates_have_only_one_winner(client):
    auth = signup(client)
    item = create(client, auth)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda status: transition(client, auth, item, status), ['submitted', 'cancelled']))
    assert sorted(result.status_code for result in results) == [200, 409]
    events = client.get('/api/relief-requests/' + item['id']).json()['events']
    assert len(events) == 2 and events[0]['version'] == 2
