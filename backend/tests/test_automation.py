import csv
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import io
import json
from uuid import uuid4

import pytest

from backend.app.automation_files import HEADERS, example_payload
from backend.app.models import AutomationReceipt, AutomationReceiptEvent, DataSource, Membership, utcnow
from .test_accounts import FORM_HEADERS, post, signup
from .test_relief import create as create_request, payload as request_payload


def source(client, auth):
    response = post(client, '/api/automation/sources', auth, json={'name': 'Fictional local relief desk'})
    assert response.status_code == 201, response.text
    return response.json()


def upload(client, auth, connection, payload=None, raw=None, filename='relief.json'):
    return post(client, f"/api/automation/sources/{connection['id']}/upload", auth,
        files={'file': (filename, raw if raw is not None else json.dumps(payload or example_payload()).encode(), 'application/octet-stream')})


def get_receipt(client, item):
    return client.get('/api/automation/inbox/' + item['id']).json()


def apply(client, auth, item, **changes):
    return post(client, f"/api/automation/inbox/{item['id']}/apply", auth, json={
        'expected_version': item['version'], 'plan_hash': item['plan']['plan_hash'], 'reason': 'Checked source evidence and draft proposals.', **changes})


def policy(client, auth, connection, **changes):
    return client.patch('/api/automation/sources/' + connection['id'], headers={'X-CSRF-Token': auth['csrf_token']},
        json={'expected_version': connection['policy_version'], 'enabled': True, 'automation_mode': 'new_drafts',
            'reason': 'Trust this fictional source to create drafts only.', **changes})


def ingest(client, connection, payload=None, token=None):
    return client.post(connection['ingest_path'], headers={'Authorization': 'Bearer ' + (token or connection['token'])},
        files={'file': ('relief.json', json.dumps(payload or example_payload()).encode())})


def test_manual_preview_apply_provenance_and_retry_exactly_once(client):
    auth = signup(client); connection = source(client, auth); payload = example_payload()
    item = upload(client, auth, connection, payload).json()['receipt']
    assert item['state'] == 'pending' and item['plan']['counts']['new_draft'] == 1
    assert client.get('/api/relief-requests').json()['total'] == 0
    result = apply(client, auth, item)
    assert result.status_code == 200, result.text
    saved = result.json()['receipt']; request_id = saved['results'][0]['request_id']
    request = client.get('/api/relief-requests/' + request_id).json()
    assert request['request']['status'] == 'draft' and request['request']['intake_id'] == item['id']
    assert request['events'][0]['after']['intake_id'] == item['id'] and '@cedar-owner' in request['request']['created_actor']
    retry = apply(client, auth, item).json()
    assert retry['duplicate'] and retry['receipt']['reviewed_at'] == saved['reviewed_at']
    assert upload(client, auth, connection, payload).json()['duplicate']
    assert len(get_receipt(client, item)['events']) == 2 and client.get('/api/relief-requests').json()['total'] == 1
    assert client.get('/api/workspace').json()['revision'] == 0


def test_canonical_csv_json_deduplication_and_timezone_decimal_normalization(client):
    auth = signup(client); connection = source(client, auth); payload = example_payload()
    first = upload(client, auth, connection, payload).json()['receipt']
    output = io.StringIO(newline=''); writer = csv.DictWriter(output, HEADERS); writer.writeheader()
    row = {**{key: payload[key] for key in ('schema_version', 'report_reference', 'observed_at')}, **payload['requests'][0]}
    row['quantity'] = '12.1250'; row['reference'] = row['reference'].lower()
    row['needed_by'] = row['needed_by'].replace('+00:00', 'Z')
    writer.writerow(row)
    second = upload(client, auth, connection, raw=output.getvalue().encode('utf-8-sig'), filename='relief.csv')
    assert second.status_code == 202, second.text
    assert second.json()['duplicate'] and second.json()['receipt']['id'] == first['id']


@pytest.mark.parametrize('change', [
    {'quantity': True}, {'quantity': '0'}, {'quantity': 'NaN'}, {'quantity': '0.0001'}, {'quantity': '1000000001'},
    {'needed_by': '2026-11-08T12:00:00'}, {'status': 'reviewed'}, {'workspace_id': 'foreign'}, {'incident_id': str(uuid4())},
])
def test_invalid_row_blocks_whole_file_without_dropping_evidence(client, change):
    auth = signup(client); connection = source(client, auth); payload = example_payload()
    payload['requests'].append({**payload['requests'][0], 'reference': 'INVALID-ROW', **change})
    response = upload(client, auth, connection, payload)
    assert response.status_code == 202, response.text
    item = response.json()['receipt']
    assert item['state'] == 'blocked' and item['error_count'] and item['raw_text']
    assert apply(client, auth, item).status_code == 409
    assert client.get('/api/relief-requests').json()['total'] == 0


@pytest.mark.parametrize('raw,filename', [
    (b'{"schema_version":"x","schema_version":"y"}', 'a.json'), (b'{', 'a.json'),
    (b'{"quantity":NaN}', 'a.json'), (b'reference,reference\nA,B', 'a.csv'),
    (b'wrong,header\nx,y', 'a.csv'), (b'[]', 'a.json'), (b'', 'a.json'),
])
def test_malformed_text_is_auditable_blocked_receipt(client, raw, filename):
    auth = signup(client); connection = source(client, auth)
    item = upload(client, auth, connection, raw=raw, filename=filename).json()['receipt']
    assert item['state'] == 'blocked' and item['errors']
    assert upload(client, auth, connection, raw=raw, filename=filename).json()['duplicate']


def test_transport_limits_and_envelope_validation(client):
    auth = signup(client); connection = source(client, auth)
    for raw, filename, code in [(b'x' * (256 * 1024 + 1), 'a.json', 413), (b'x', 'a.xlsx', 422), (b'\xff', 'a.csv', 422)]:
        assert upload(client, auth, connection, raw=raw, filename=filename).status_code == code
    for changes in [{'schema_version': 'unknown'}, {'observed_at': '2026-11-08T12:00:00'},
        {'observed_at': (utcnow() + timedelta(days=1)).isoformat()}, {'requests': []}, {'extra': 1}]:
        payload = {**example_payload(), **changes}
        assert upload(client, auth, connection, payload).json()['receipt']['state'] == 'blocked'
    payload = example_payload(); payload['requests'] *= 2
    assert upload(client, auth, connection, payload).json()['receipt']['state'] == 'blocked'


def test_conflict_blocks_new_rows_and_duplicates_never_overwrite_accepted_request(client):
    auth = signup(client); connection = source(client, auth); payload = example_payload(reference='EXISTING')
    accepted = create_request(client, auth, {**payload['requests'][0], 'submission_key': str(uuid4())})
    item = upload(client, auth, connection, payload).json()['receipt']
    assert item['plan']['counts']['duplicate'] == 1
    result = apply(client, auth, item).json()['receipt']
    assert result['results'][0]['action'] == 'unchanged_duplicate'
    conflicting = example_payload(reference='EXISTING'); conflicting['requests'][0]['quantity'] = '15'
    conflicting['requests'].append({**payload['requests'][0], 'reference': 'NEW-ALONGSIDE-CONFLICT'})
    item = upload(client, auth, connection, conflicting).json()['receipt']
    assert item['plan']['counts'] == {'new_draft': 1, 'duplicate': 0, 'conflict': 1}
    assert item['plan']['proposals'][0]['differences'] and apply(client, auth, item).status_code == 409
    current = client.get('/api/relief-requests/' + accepted['id']).json()['request']
    assert current['version'] == 1 and current['quantity'] == '12.125'
    assert client.get('/api/relief-requests').json()['total'] == 1


def test_stale_preview_rechecks_current_request_and_source_policy(client):
    auth = signup(client); connection = source(client, auth); payload = example_payload()
    item = upload(client, auth, connection, payload).json()['receipt']
    create_request(client, auth, {**payload['requests'][0], 'submission_key': str(uuid4())})
    assert apply(client, auth, item).status_code == 409
    fresh = get_receipt(client, item)['receipt']
    changed = policy(client, auth, connection, enabled=False, automation_mode='review').json()
    assert changed['policy_version'] == 2
    assert apply(client, auth, fresh).status_code == 409
    fresh = get_receipt(client, item)['receipt']
    assert apply(client, auth, fresh).status_code == 409
    assert apply(client, auth, fresh, acknowledge_warnings=True).status_code == 200


def test_trusted_rule_creates_only_drafts_and_holds_stale_conflicting_invalid_files(client):
    auth = signup(client); connection = source(client, auth)
    assert policy(client, auth, connection).status_code == 200
    payload = example_payload(reference='AUTO-NEW'); result = ingest(client, connection, payload)
    assert result.status_code == 202, result.text
    saved = get_receipt(client, result.json())['receipt']
    assert saved['state'] == 'applied' and saved['automatic'] and saved['source_policy_version'] == 2
    request = client.get('/api/relief-requests/' + saved['results'][0]['request_id']).json()['request']
    assert request['status'] == 'draft' and request['created_actor'].startswith('Automation')
    assert ingest(client, connection, payload).json()['duplicate']
    stale = example_payload(now=utcnow() - timedelta(days=2))
    response = ingest(client, connection, stale).json()
    assert response['state'] == 'pending' and not response['automatic']
    item = get_receipt(client, response)['receipt']
    assert item['plan']['warnings'][0]['code'] == 'stale'
    assert apply(client, auth, item).status_code == 409
    assert apply(client, auth, item, acknowledge_warnings=True).status_code == 200
    conflict = {**payload, 'report_reference': 'UPDATED', 'requests': [{**payload['requests'][0], 'quantity': '20'}]}
    assert ingest(client, connection, conflict).json()['state'] == 'pending'
    invalid = {**example_payload(), 'requests': [{**payload['requests'][0], 'quantity': '0'}]}
    assert ingest(client, connection, invalid).json()['state'] == 'blocked'


def test_dismissal_is_terminal_audited_and_same_file_never_requeues(client):
    auth = signup(client); connection = source(client, auth); payload = example_payload()
    item = upload(client, auth, connection, payload).json()['receipt']
    decision = {'expected_version': item['version'], 'reason': 'Source withdrew this fictional report.'}
    path = '/api/automation/inbox/' + item['id'] + '/dismiss'
    result = post(client, path, auth, json=decision).json()['receipt']
    assert post(client, path, auth, json=decision).json()['duplicate']
    assert apply(client, auth, item).status_code == 409
    assert upload(client, auth, connection, payload).json()['receipt']['state'] == 'dismissed'
    events = get_receipt(client, item)['events']
    assert len(events) == 2 and events[0]['reason'] == decision['reason'] and events[0]['after']['reviewed_at'] == result['reviewed_at']


def test_keys_purpose_scope_rotation_disabled_and_revoked_issuer(client):
    auth = signup(client); connection = source(client, auth)
    assert ingest(client, connection, token='invalid').status_code == 401
    assert client.post('/api/ingest/' + connection['id'], headers={'Authorization': 'Bearer ' + connection['token']}, files={'file': ('a.csv', b'x')}).status_code == 401
    assert client.get('/api/sources').json()['sources'] == []
    assert post(client, '/api/sources/' + connection['id'] + '/rotate', auth).status_code == 404
    rotated = post(client, '/api/automation/sources/' + connection['id'] + '/rotate', auth,
        json={'expected_version': 1, 'reason': 'Replace test key.'}).json()
    assert ingest(client, connection).status_code == 401
    assert ingest(client, rotated).status_code == 202
    public = client.get('/api/automation/sources/' + connection['id']).json()
    assert connection['token'] not in json.dumps(public) and rotated['token'] not in json.dumps(public)
    assert public['events'][0]['action'] == 'key_rotated'
    disabled = policy(client, auth, rotated, enabled=False, automation_mode='review').json()
    assert ingest(client, rotated).status_code == 401
    assert upload(client, auth, connection).status_code == 409
    policy(client, auth, disabled, enabled=True, automation_mode='review')
    with client.test_sessions.begin() as session:
        session.get(Membership, (auth['user']['id'], auth['workspace']['id'])).role = 'viewer'
    assert ingest(client, rotated).status_code == 403
    assert upload(client, auth, connection).status_code == 403
    assert client.get('/api/automation/inbox').status_code == 200


def test_editor_owner_and_foreign_workspace_isolation(client):
    auth = signup(client); connection = source(client, auth); item = upload(client, auth, connection).json()['receipt']
    with client.test_sessions.begin() as session:
        session.get(Membership, (auth['user']['id'], auth['workspace']['id'])).role = 'editor'
    assert policy(client, auth, connection).status_code == 403
    assert post(client, '/api/automation/sources', auth, json={'name': 'Editor source'}).status_code == 403
    assert apply(client, auth, item).status_code == 200
    foreign = signup(client, username='other-owner')
    assert client.get('/api/automation/inbox/' + item['id']).status_code == 404
    assert client.get('/api/automation/sources/' + connection['id']).status_code == 404
    assert upload(client, foreign, connection).status_code == 404
    assert client.get('/api/automation/inbox').json()['total'] == 0
    assert post(client, '/api/demo/automation/sources', foreign, json={'name': 'Demo edit'}).status_code == 403


def test_concurrent_connector_retries_make_one_receipt_and_one_draft(client):
    auth = signup(client); connection = source(client, auth); policy(client, auth, connection)
    payload = example_payload()
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: ingest(client, connection, payload), range(2)))
    assert all(response.status_code == 202 for response in responses), [response.text for response in responses]
    assert len({response.json()['id'] for response in responses}) == 1
    assert sorted(response.json()['duplicate'] for response in responses) == [False, True]
    assert client.get('/api/relief-requests').json()['total'] == 1
    with client.test_sessions() as session:
        assert len(session.query(AutomationReceiptEvent).all()) == 2


def test_policy_version_noop_and_blank_reason_validation(client):
    auth = signup(client); connection = source(client, auth)
    assert policy(client, auth, connection, automation_mode='review').json()['unchanged']
    assert policy(client, auth, connection, reason=' ').status_code == 422
    assert policy(client, auth, connection, enabled='yes').status_code == 422
    assert policy(client, auth, connection).status_code == 200
    assert policy(client, auth, connection, enabled=False).status_code == 409
    assert len(client.get('/api/automation/sources/' + connection['id']).json()['events']) == 2
