from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import timedelta
from decimal import Decimal
import random
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from backend.app.models import Membership, StockRecord, utcnow
from backend.app.response_models import ResponseEvent, ResponsePlan, ResponseSignal
from backend.app.response_rules import evaluate_response
from .test_accounts import post, save, signup, upload
from .test_imports import row
from .test_inventory import detail, movement, reviewed_request, setup_stock


def facts():
    timestamp = '2026-11-22T08:00:00+00:00'
    return {'signal': {'state': 'verified', 'observed_at': timestamp, 'expires_at': '2026-11-23T08:00:00+00:00',
        'certainty': 'observed', 'locality': 'River Ward'},
        'conditions': {'observed_at': timestamp, 'weather': 'confirmed', 'destination_access': 'confirmed'},
        'needs': [{'request_id': 'r1', 'reference': 'R1', 'status': 'reviewed', 'needed_by': timestamp,
            'locality': 'River Ward', 'quantity': '10.125', 'committed': '0', 'unit': 'packs', 'item_unit': 'packs',
            'category': 'water', 'item_category': 'water', 'item_name_confirmed': True, 'incompatible_commitments': False,
            'item_id': 'i1', 'location_id': 'l1', 'on_hand': '100', 'reserved': '0', 'stock_version': 1,
            'stock_updated_at': timestamp, 'unit_weight_kg': '2', 'weight_source': 'Synthetic packing sheet'}],
        'aircraft': [{'aircraft_id': 'CIV-1', 'display_name': 'Fictional civil aircraft', 'reported_status': 'available',
            'source_updated_at': timestamp, 'support': {'observed_at': timestamp, 'cargo_allowance_kg': '21',
                'crew': 'confirmed', 'maintenance': 'confirmed', 'fuel': 'confirmed'}}]}


def run(value):
    from datetime import datetime
    return evaluate_response(value, now=datetime.fromisoformat('2026-11-22T09:00:00+00:00'))


@pytest.mark.parametrize('path,value,code', [
    (['signal', 'state'], 'unreviewed', 'signal_unverified'),
    (['signal', 'state'], 'dismissed', 'signal_unverified'),
    (['signal', 'certainty'], 'unknown', 'signal_uncertain'),
    (['signal', 'expires_at'], '2026-11-22T09:00:00+00:00', 'signal_outdated'),
    (['conditions', 'weather'], 'hold', 'conditions_weather'),
    (['conditions', 'destination_access'], 'unknown', 'conditions_destination_access'),
    (['conditions', 'observed_at'], '2026-11-20T08:00:00+00:00', 'conditions_outdated'),
    (['needs', 0, 'status'], 'draft', 'request_unreviewed'),
    (['needs', 0, 'locality'], 'Different ward', 'locality_mismatch'),
    (['needs', 0, 'item_unit'], 'boxes', 'item_mismatch'),
    (['needs', 0, 'item_category'], 'medicine', 'item_mismatch'),
    (['needs', 0, 'item_name_confirmed'], False, 'item_confirmation'),
    (['needs', 0, 'incompatible_commitments'], True, 'commitment_mismatch'),
    (['needs', 0, 'reserved'], '95', 'stock_shortfall'),
    (['needs', 0, 'committed'], '10.125', 'already_allocated'),
    (['needs', 0, 'stock_updated_at'], '2026-11-20T08:00:00+00:00', 'stock_outdated'),
    (['aircraft', 0, 'reported_status'], 'unavailable', 'no_aircraft_candidate'),
    (['aircraft', 0, 'reported_status'], 'unknown', 'no_aircraft_candidate'),
    (['aircraft', 0, 'source_updated_at'], '2026-11-20T08:00:00+00:00', 'no_aircraft_candidate'),
    (['aircraft', 0, 'support'], None, 'no_aircraft_candidate'),
    (['aircraft', 0, 'support', 'crew'], 'hold', 'no_aircraft_candidate'),
    (['aircraft', 0, 'support', 'maintenance'], 'unknown', 'no_aircraft_candidate'),
    (['aircraft', 0, 'support', 'fuel'], 'hold', 'no_aircraft_candidate'),
    (['aircraft', 0, 'support', 'cargo_allowance_kg'], '20.249', 'no_aircraft_candidate'),
])
def test_missing_or_negative_evidence_never_becomes_reviewable(path, value, code):
    data = facts(); target = data
    for key in path[:-1]: target = target[key]
    target[path[-1]] = value
    result = run(data)
    assert result['status'] == 'blocked'
    assert code in {item['code'] for item in result['blockers']}


def test_exact_weights_stable_candidates_and_freshness_boundaries():
    value = facts(); original = deepcopy(value)
    assert run(value)['cargo_kg'] == '20.25'
    assert run(value)['status'] == 'reviewable'
    assert run(value)['workflow'][5]['state'] == 'awaiting_review'
    assert run(value)['workflow'][6]['state'] == 'human_action'
    assert value == original
    value['aircraft'].append({**deepcopy(value['aircraft'][0]), 'aircraft_id': 'CIV-0'})
    assert run(value)['selected_aircraft'] == 'CIV-0'
    value['aircraft'].reverse()
    assert run(value)['selected_aircraft'] == 'CIV-0'
    value['signal']['observed_at'] = '2026-11-21T09:00:00+00:00'
    assert run(value)['status'] == 'reviewable'
    value['signal']['observed_at'] = '2026-11-21T08:59:59+00:00'
    assert run(value)['status'] == 'blocked'
    value['signal']['observed_at'] = '2026-11-22T09:05:00+00:00'
    assert run(value)['status'] == 'reviewable'
    value['signal']['observed_at'] = '2026-11-22T09:05:01+00:00'
    assert run(value)['status'] == 'blocked'


def test_shared_stock_deadline_priority_and_mass_units():
    value = facts(); first = value['needs'][0]
    first.update(on_hand='15', quantity='10', unit_weight_kg='1')
    value['needs'].append({**first, 'request_id': 'r2', 'reference': 'R2', 'needed_by': '2026-11-23T08:00:00+00:00'})
    result = run(value)
    assert [r['proposed'] for r in result['allocations']] == ['10', '5']
    assert result['allocations'][1]['shortfall'] == '5'
    first.update(unit='kilograms', item_unit='kilograms', unit_weight_kg='0.5')
    assert 'weight_unit_mismatch' in {b['code'] for b in run(value)['blockers']}


def test_generated_resource_invariants_under_1000_permutations():
    rng = random.Random(26250)
    for _ in range(1000):
        value = facts(); count = rng.randint(1, 50); stock = Decimal(rng.randint(0, 10000)) / 1000
        template = value['needs'][0]; value['needs'] = []
        for i in range(count):
            value['needs'].append({**template, 'request_id': str(i), 'reference': str(i), 'quantity': str(rng.randint(1, 20000) / 1000), 'on_hand': str(stock)})
        before = deepcopy(value)
        result = run(value)
        assert sum(Decimal(r['proposed']) for r in result['allocations']) <= stock
        assert all(Decimal(r['proposed']) >= 0 and Decimal(r['shortfall']) >= 0 for r in result['allocations'])
        rng.shuffle(value['needs'])
        assert run(value) == result
        assert sorted(before['needs'], key=lambda x:x['request_id']) == sorted(value['needs'], key=lambda x:x['request_id'])


def signal_body(**changes):
    return {'reference': 'WARN-1', 'kind': 'warning', 'title': 'Fictional flood warning', 'locality': 'Fictional River Ward',
        'severity': 'severe', 'certainty': 'observed', 'source_name': 'Fictional district desk', 'source_url': '',
        'observed_at': utcnow().isoformat(), 'expires_at': (utcnow() + timedelta(hours=4)).isoformat(),
        'description': 'Fictional warning for software testing only.', **changes}


def setup_plan(client, username='cedar-owner'):
    auth = signup(client, username)
    assert save(client, auth, upload(client, auth, [row(source_updated_at=utcnow().isoformat())])).status_code == 200
    aircraft_id = client.get('/api/workspace').json()['aircraft'][0]['aircraft_id']
    support = {'expected_version': 0, 'cargo_allowance_kg': '100', 'crew': 'confirmed', 'maintenance': 'confirmed',
        'fuel': 'confirmed', 'observed_at': utcnow().isoformat(), 'source_name': 'Fictional operator sheet', 'reason': 'Synthetic support evidence.'}
    response = client.put('/api/response/aircraft/' + aircraft_id, json=support, headers={'X-CSRF-Token': auth['csrf_token']})
    assert response.status_code == 200, response.text
    item, location, stock_body, _ = setup_stock(client, auth)
    need = reviewed_request(client, auth)
    signal = post(client, '/api/response/signals', auth, json=signal_body()).json()['signal']
    signal = post(client, '/api/response/signals/' + signal['id'] + '/review', auth,
        json={'state': 'verified', 'expected_version': 1, 'reason': 'Checked fictional primary source.'}).json()['signal']
    inputs = {'title': 'Fictional ward response', 'signal_id': signal['id'], 'needs': [{'request_id': need['id'],
        'item_id': item['id'], 'location_id': location['id'], 'unit_weight_kg': '2', 'weight_source': 'Fictional packing sheet', 'item_name_confirmed': True}],
        'conditions': {'weather': 'confirmed', 'destination_access': 'confirmed', 'observed_at': utcnow().isoformat(), 'source_name': 'Fictional context log'}}
    return auth, inputs, item, location, stock_body, aircraft_id


def test_plan_preview_snapshot_review_and_stock_changes_require_recheck(client):
    auth, inputs, item, location, body, _ = setup_plan(client)
    before = detail(client, item, location)
    preview = post(client, '/api/response/evaluate', auth, json=inputs)
    assert preview.status_code == 200, preview.text
    preview = preview.json()
    assert preview['status'] == 'reviewable' and preview['cargo_kg'] == '80'
    saved_input = {**inputs, 'submission_key': str(uuid4()), 'evaluation_hash': preview['evaluation_hash']}
    saved = post(client, '/api/response/plans', auth, json=saved_input)
    assert saved.status_code == 201, saved.text
    plan = saved.json()['plan']
    assert post(client, '/api/response/plans', auth, json=saved_input).json()['duplicate']
    review = {'expected_version': 1, 'evaluation_hash': preview['evaluation_hash'], 'reason': 'Coordinator checked preparation evidence.'}
    with ThreadPoolExecutor(max_workers=8) as pool:
        reviews = list(pool.map(lambda _:post(client, '/api/response/plans/' + plan['id'] + '/review', auth, json=review), range(8)))
    assert all(r.status_code == 200 for r in reviews)
    assert sum(not r.json()['duplicate'] for r in reviews) == 1
    assert detail(client, item, location) == before
    assert len(client.get('/api/response/plans/' + plan['id']).json()['events']) == 2
    movement(client, auth, body, kind='reserve', quantity='5', request_id=inputs['needs'][0]['request_id'])
    current = client.get('/api/response/plans/' + plan['id']).json()
    assert not current['is_current'] and current['effective_state'] == 'recheck_required'
    assert current['plan']['snapshot']['decision']['cargo_kg'] == '80'
    assert post(client, '/api/response/plans/' + plan['id'] + '/review', auth, json=review).status_code == 409
    assert post(client, '/api/response/plans', auth, json={**saved_input, 'submission_key': str(uuid4())}).status_code == 409


def test_source_keys_only_queue_immutable_unverified_signals_and_can_be_revoked(client):
    auth = signup(client)
    source = post(client, '/api/response/sources', auth, json={'name': 'Fictional warning connector'}).json()
    body = signal_body()
    def send(_): return client.post(source['ingest_path'], json=body, headers={'Authorization': 'Bearer ' + source['token']})
    with ThreadPoolExecutor(max_workers=8) as pool: results = list(pool.map(send, range(8)))
    assert all(r.status_code == 202 for r in results)
    assert len({r.json()['signal']['id'] for r in results}) == 1
    assert sum(not r.json()['duplicate'] for r in results) == 1
    signal = results[0].json()['signal']; assert signal['state'] == 'unreviewed'
    assert client.post(source['ingest_path'], json={**body, 'title': 'Changed evidence'}, headers={'Authorization': 'Bearer ' + source['token']}).status_code == 409
    assert client.post(source['ingest_path'], json={**body, 'state': 'verified'}, headers={'Authorization': 'Bearer ' + source['token']}).status_code == 422
    assert client.post('/api/response/signals', json=body, headers={'Authorization': 'Bearer ' + source['token'], 'X-CSRF-Token': ''}).status_code == 403
    changed = client.patch('/api/response/sources/' + source['id'], json={'expected_version': 1, 'enabled': False, 'reason': 'Synthetic revocation.'}, headers={'X-CSRF-Token': auth['csrf_token']})
    assert changed.status_code == 200
    assert send(0).status_code == 401
    with client.test_sessions() as session:
        assert session.scalar(select(func.count()).select_from(ResponseSignal)) == 1
        assert session.scalar(select(func.count()).select_from(StockRecord)) == 0


def test_foreign_organisations_viewers_and_demo_cannot_mutate_or_leak_response_evidence(client):
    auth, inputs, _, _, _, aircraft_id = setup_plan(client)
    preview = post(client, '/api/response/evaluate', auth, json=inputs).json()
    plan = post(client, '/api/response/plans', auth, json={**inputs, 'submission_key': str(uuid4()), 'evaluation_hash': preview['evaluation_hash']}).json()['plan']
    outsider = signup(client, 'outsider')
    assert client.get('/api/response/plans/' + plan['id']).status_code == 404
    assert client.get('/api/response/signals/' + inputs['signal_id']).status_code == 404
    assert post(client, '/api/response/evaluate', outsider, json=inputs).status_code == 404
    assert client.get('/api/response/aircraft/' + aircraft_id + '/history').json()['events'] == []
    assert client.get('/api/response/signals').json()['total'] == 0
    with client.test_sessions.begin() as session:
        membership = session.get(Membership, (outsider['user']['id'], outsider['workspace']['id'])); membership.role = 'viewer'
    assert post(client, '/api/response/signals', outsider, json=signal_body()).status_code == 403
    assert post(client, '/api/demo/response/signals', outsider, json=signal_body()).status_code == 403
    assert client.get('/api/demo/response/signals').status_code == 200


@pytest.mark.parametrize('changes', [{'observed_at':'2026-11-22T08:00:00'}, {'state':'verified'}, {'workspace_id':'foreign'},
    {'source_url':'javascript:alert(1)'}, {'source_url':'https://user:secret@example.org'}, {'certainty':'certain'}, {'title':' '},
    {'expires_at':'2020-01-01T00:00:00Z'}])
def test_warning_contract_rejects_ambiguous_or_server_owned_fields(client, changes):
    auth = signup(client)
    assert post(client, '/api/response/signals', auth, json=signal_body(**changes)).status_code == 422
    assert client.get('/api/response/signals').json()['total'] == 0


def test_warning_key_rotation_scope_and_current_issuer_membership(client):
    auth = signup(client)
    source = post(client, '/api/response/sources', auth, json={'name': 'Scoped warning source'}).json()
    rotate = {'expected_version': 1, 'reason': 'Rotate fictional key.'}
    changed = post(client, '/api/response/sources/' + source['id'] + '/rotate', auth, json=rotate)
    assert changed.status_code == 200
    new_source = changed.json()
    body = signal_body()
    for header in ['Bearer ' + source['token'], new_source['token']]:
        assert client.post(source['ingest_path'], json=body, headers={'Authorization': header}).status_code == 401
    assert client.post(source['ingest_path'], json=body, headers={'Authorization': 'Bearer ' + new_source['token']}).status_code == 202
    aircraft_source = post(client, '/api/sources', auth, json={'name': 'Aircraft-only source'}).json()
    assert client.post(source['ingest_path'], json=body, headers={'Authorization': 'Bearer ' + aircraft_source['token']}).status_code == 401
    assert post(client, '/api/response/sources/' + source['id'] + '/rotate', auth, json=rotate).status_code == 409
    with client.test_sessions.begin() as session:
        session.get(Membership, (auth['user']['id'], auth['workspace']['id'])).role = 'viewer'
    assert client.post(source['ingest_path'], json={**body, 'reference': 'WARN-2'}, headers={'Authorization': 'Bearer ' + new_source['token']}).status_code == 403


def test_support_versions_and_invalid_weights(client):
    auth = signup(client)
    assert save(client, auth, upload(client, auth, [row(aircraft_id='CIV-02', source_updated_at=utcnow().isoformat())])).status_code == 200
    route = '/api/response/aircraft/CIV-02'
    body = {'expected_version': 0, 'cargo_allowance_kg': '10', 'crew': 'unknown', 'maintenance': 'unknown', 'fuel': 'unknown',
        'observed_at': utcnow().isoformat(), 'source_name': 'Fictional report', 'reason': 'Fictional support entry.'}
    headers = {'X-CSRF-Token': auth['csrf_token']}
    for value in [True, '0', '-1', 'NaN', 'Infinity', '0.0001', '1000001']:
        assert client.put(route, json={**body, 'cargo_allowance_kg': value}, headers=headers).status_code == 422
    response = client.put(route, json=body, headers=headers)
    assert response.status_code == 200, response.text
    assert client.put(route, json=body, headers=headers).json()['duplicate']
    assert client.put(route, json={**body, 'crew': 'confirmed'}, headers=headers).status_code == 409
    assert client.put(route, json={**body, 'expected_version': 1, 'observed_at': (utcnow() - timedelta(hours=1)).isoformat()}, headers=headers).status_code == 409
    history = client.get(route + '/history')
    assert history.status_code == 200 and len(history.json()['events']) == 1
