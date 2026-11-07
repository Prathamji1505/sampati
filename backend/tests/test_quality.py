from datetime import timedelta
from types import SimpleNamespace

import pytest

from backend.app.auth import COOKIE
from backend.app.models import Membership, utcnow
from backend.app.quality import classify_incoming, inspect_report
from .test_accounts import signup, upload, save, post
from .test_imports import row
from .test_workspace_tools import new_source, ingest, use_cookie


def item(**changes):
    now = utcnow()
    return SimpleNamespace(**{
        'aircraft_id': 'CIV-001', 'display_name': 'Cedar', 'reported_status': 'available',
        'source_name': 'Fictional civilian register', 'note': '', 'source_updated_at': now,
        'source_timestamp_raw': now.isoformat(), 'last_import_id': 'example', **changes})


@pytest.mark.parametrize(('hours', 'freshness'), [(24, 'current'), (24.001, 'stale'), (-5/60, 'current'), (-5.01/60, 'future')])
def test_quality_time_boundaries_use_one_reference_time(hours, freshness):
    now = utcnow()
    result = inspect_report(item(source_updated_at=now - timedelta(hours=hours)), now, 24)
    assert result['freshness'] == freshness
    assert result['result'] == ('complete' if freshness == 'current' else 'review')
    assert result['reported_status'] == 'available'


def test_quality_explains_missing_facts_without_readiness_or_note_inference():
    now = utcnow()
    result = inspect_report(item(display_name='', reported_status='unknown'), now, 24)
    assert {finding['code'] for finding in result['findings']} == {'missing_name', 'unknown_status'}
    complete = inspect_report(item(note='Fictional maintenance words are not structured evidence.'), now, 24)
    assert complete['result'] == 'complete' and complete['reported_status'] == 'available'


def test_incoming_comparison_normalizes_time_without_overwriting_accepted_facts():
    accepted = item()
    report = {key: getattr(accepted, key) for key in ('aircraft_id', 'display_name', 'reported_status', 'source_name', 'note')}
    report['source_updated_at'] = accepted.source_updated_at.isoformat()
    assert classify_incoming(accepted, report) is None
    assert classify_incoming(accepted, {**report, 'reported_status': 'unavailable'}) == 'incoming_conflict'
    assert classify_incoming(accepted, {**report, 'source_updated_at': (accepted.source_updated_at + timedelta(seconds=1)).isoformat()}) == 'incoming_update'
    assert classify_incoming(accepted, {**report, 'source_updated_at': (accepted.source_updated_at - timedelta(seconds=1)).isoformat()}) == 'incoming_older'
    assert accepted.reported_status == 'available'


def test_quality_requires_membership_and_keeps_empty_demo_separate(client):
    assert client.get('/api/report-checks').status_code == 401
    auth = signup(client)
    assert save(client, auth, upload(client, auth, [row()])).status_code == 200
    private = client.get('/api/report-checks').json()
    assert private['summary']['records'] == 1
    assert client.get('/api/demo/report-checks').json()['summary']['records'] == 0
    client.cookies.clear()
    other = signup(client, 'other-owner')
    data = client.get('/api/report-checks', params={'workspace_id': auth['workspace']['id']}).json()
    assert data['workspace_id'] == other['workspace']['id'] and data['records'] == []


def test_pending_conflict_is_explained_read_only_and_disappears_when_rejected(client):
    auth = signup(client)
    record = row(source_updated_at=utcnow().isoformat())
    assert save(client, auth, upload(client, auth, [record])).status_code == 200
    source = new_source(client, auth)
    incoming = ingest(client, source, [{**record, 'reported_status': 'unavailable'}]).json()
    before = client.get('/api/workspace').json()
    checks = client.get('/api/report-checks').json()
    result = checks['records'][0]
    assert result['reported_status'] == 'available' and result['result'] == 'review'
    finding = result['findings'][0]
    assert finding['code'] == 'incoming_conflict' and finding['examples'][0]['incoming_id'] == incoming['id']
    after = client.get('/api/workspace').json()
    assert {key: after[key] for key in ('revision', 'aircraft', 'imports')} == {key: before[key] for key in ('revision', 'aircraft', 'imports')}
    assert post(client, '/api/sources/inbox/' + incoming['id'] + '/reject', auth, json={}).status_code == 200
    assert client.get('/api/report-checks').json()['records'][0]['result'] == 'complete'


def test_pending_evidence_is_scoped_and_exact_equivalents_are_ignored(client):
    auth = signup(client)
    record = row(source_updated_at=utcnow().isoformat())
    save(client, auth, upload(client, auth, [record]))
    source = new_source(client, auth)
    ingest(client, source, [record])
    own_cookie = client.cookies.get(COOKIE)
    client.cookies.clear()
    other = signup(client, 'other-owner')
    other_source = new_source(client, other)
    ingest(client, other_source, [{**record, 'reported_status': 'unavailable'}])
    use_cookie(client, own_cookie)
    result = client.get('/api/report-checks').json()
    assert result['summary']['pending_files'] == 1 and result['records'][0]['findings'] == []


def test_viewer_can_read_checks_and_reported_unavailable_is_not_a_quality_failure(client):
    auth = signup(client)
    save(client, auth, upload(client, auth, [row(reported_status='unavailable', source_updated_at=utcnow().isoformat())]))
    with client.test_sessions.begin() as session:
        session.get(Membership, (auth['user']['id'], auth['workspace']['id'])).role = 'viewer'
    response = client.get('/api/report-checks')
    assert response.status_code == 200
    assert response.json()['records'][0]['result'] == 'complete'
    assert response.json()['records'][0]['reported_status'] == 'unavailable'


def test_incoming_groups_count_all_files_but_bound_examples_and_exclude_new_ids(client):
    auth = signup(client)
    record = row(source_updated_at=utcnow().isoformat())
    save(client, auth, upload(client, auth, [record]))
    source = new_source(client, auth)
    for index in range(5):
        assert ingest(client, source, [{**record, 'note': f'Conflicting example {index}'}]).status_code == 202
    assert ingest(client, source, [row('CIV-NEW', source_updated_at=utcnow().isoformat())]).status_code == 202
    report = client.get('/api/report-checks').json()
    assert report['summary'] == {'records': 1, 'needs_review': 1, 'complete': 0, 'pending_files': 6, 'pending_new_ids': 1}
    assert report['counts_by_code'] == {'incoming_conflict': 1}
    finding = report['records'][0]['findings'][0]
    assert finding['count'] == 5 and len(finding['examples']) == 3
    assert [item['aircraft_id'] for item in report['records']] == [record['aircraft_id']]


def test_checks_clear_when_newer_incoming_report_is_accepted(client):
    auth = signup(client)
    time = utcnow()
    record = row(source_updated_at=(time - timedelta(hours=30)).isoformat(), reported_status='unknown')
    save(client, auth, upload(client, auth, [record]))
    source = new_source(client, auth)
    incoming = ingest(client, source, [{**record, 'source_updated_at': time.isoformat(), 'reported_status': 'available'}]).json()
    before = client.get('/api/report-checks').json()
    assert {finding['code'] for finding in before['records'][0]['findings']} == {'stale_report', 'unknown_status', 'incoming_update'}
    proposal = post(client, '/api/sources/inbox/' + incoming['id'] + '/preview', auth, json={}).json()
    assert save(client, auth, proposal).status_code == 200
    after = client.get('/api/report-checks').json()
    assert after['records'][0]['result'] == 'complete' and after['summary']['pending_files'] == 0
    assert after['workspace_revision'] == before['workspace_revision'] + 1
