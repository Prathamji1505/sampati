from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timedelta, timezone
import io

import pytest

from backend.app.schemas import HEADERS, MAX_BYTES


def row(aircraft_id='DEMO-001', **changes):
    return {
        'aircraft_id': aircraft_id, 'display_name': 'Cedar', 'reported_status': 'available',
        'source_updated_at': datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        'source_name': 'Fictional test source', 'note': 'Synthetic test record.', **changes,
    }


def content(rows):
    buffer = io.StringIO(newline='')
    writer = csv.DictWriter(buffer, fieldnames=HEADERS)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode()


def preview(client, rows):
    response = client.post('/api/demo/imports/preview', files={'file': ('fleet.csv', content(rows), 'text/csv')})
    assert response.status_code == 200, response.text
    return response.json()


def confirm(client, proposal):
    return client.post('/api/demo/imports/confirm', json={'token': proposal['token'], 'rows': proposal['rows']})


def workspace(client):
    return client.get('/api/demo/workspace').json()


def test_preview_writes_nothing_and_confirm_persists(client):
    proposal = preview(client, [row()])
    assert proposal['valid'] and proposal['counts']['new'] == 1
    assert workspace(client)['aircraft'] == []
    assert workspace(client)['imports'] == []
    response = confirm(client, proposal)
    assert response.status_code == 200, response.text
    saved = workspace(client)
    assert len(saved['aircraft']) == len(saved['imports']) == 1
    assert saved['revision'] == 1
    assert saved['aircraft'][0]['source_timestamp_raw'] == proposal['rows'][0]['source_updated_at']
    history = client.get('/api/demo/imports/' + response.json()['import']['id']).json()
    assert history['changes'][0]['before'] is None


@pytest.mark.parametrize('changes,field', [
    ({'reported_status': 'ready'}, 'reported_status'),
    ({'source_updated_at': '2026-11-07T12:00:00'}, 'source_updated_at'),
    ({'source_updated_at': 'tomorrow'}, 'source_updated_at'),
    ({'source_name': ''}, 'source_name'),
    ({'aircraft_id': ''}, 'aircraft_id'),
    ({'aircraft_id': 'bad/id'}, 'aircraft_id'),
])
def test_invalid_batches_reject_all_rows(client, changes, field):
    proposal = preview(client, [row('DEMO-002'), row(**changes)])
    assert not proposal['valid'] and proposal['token'] is None
    assert any(error['field'] == field for error in proposal['errors'])
    assert workspace(client)['aircraft'] == []


def test_duplicate_ids_reject_whole_file(client):
    item = row()
    proposal = preview(client, [item, item])
    assert not proposal['valid']
    assert proposal['errors'][0]['row'] == 3


def test_repeated_upload_is_idempotent(client):
    records = [row(), row('DEMO-002')]
    proposal = preview(client, records)
    first = confirm(client, proposal)
    assert first.status_code == 200
    again = preview(client, list(reversed(records)))
    assert again['already_imported']
    second = confirm(client, again)
    assert second.status_code == 200 and second.json()['duplicate']
    assert first.json()['import']['id'] == second.json()['import']['id']
    assert len(workspace(client)['aircraft']) == 2
    assert len(workspace(client)['imports']) == 1


def test_late_report_rejected_and_newer_report_audited(client):
    first_row = row()
    assert confirm(client, preview(client, [first_row])).status_code == 200
    old_time = (datetime.fromisoformat(first_row['source_updated_at']) - timedelta(hours=1)).isoformat()
    late = preview(client, [{**first_row, 'source_updated_at': old_time, 'reported_status': 'unavailable'}])
    assert not late['valid'] and late['counts']['blocked'] == 1
    assert workspace(client)['aircraft'][0]['reported_status'] == 'available'
    new_time = (datetime.fromisoformat(first_row['source_updated_at']) + timedelta(minutes=1)).isoformat()
    revised = preview(client, [{**first_row, 'source_updated_at': new_time, 'reported_status': 'unavailable'}])
    saved = confirm(client, revised)
    assert saved.status_code == 200, saved.text
    audit = client.get('/api/demo/imports/' + saved.json()['import']['id']).json()['changes'][0]
    assert audit['before']['reported_status'] == 'available'
    assert audit['after']['reported_status'] == 'unavailable'


def test_same_timestamp_conflict_rejected(client):
    original = row()
    confirm(client, preview(client, [original]))
    proposal = preview(client, [{**original, 'note': 'Contradictory details.'}])
    assert not proposal['valid']
    assert 'same timestamp' in proposal['errors'][0]['message']


def test_preview_revision_prevents_lost_updates(client):
    one = preview(client, [row('DEMO-001')])
    two = preview(client, [row('DEMO-002')])
    assert confirm(client, one).status_code == 200
    assert confirm(client, two).status_code == 409
    assert [item['aircraft_id'] for item in workspace(client)['aircraft']] == ['DEMO-001']


def test_concurrent_confirmations_serialize(client):
    one = preview(client, [row('DEMO-001')])
    two = preview(client, [row('DEMO-002')])
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda proposal: confirm(client, proposal).status_code, [one, two]))
    assert sorted(results) == [200, 409]
    assert len(workspace(client)['aircraft']) == 1


def test_preview_tampering_is_rejected(client):
    proposal = preview(client, [row()])
    proposal['rows'][0]['reported_status'] = 'unavailable'
    assert confirm(client, proposal).status_code == 400
    assert workspace(client)['aircraft'] == []


def test_invalid_token_rejected(client):
    proposal = preview(client, [row()])
    proposal['token'] += 'x'
    assert confirm(client, proposal).status_code == 400


def test_missing_rows_do_not_delete_and_ids_remain_text(client):
    first, second = row('001'), row('002')
    confirm(client, preview(client, [first, second]))
    newer = (datetime.fromisoformat(first['source_updated_at']) + timedelta(minutes=1)).isoformat()
    confirm(client, preview(client, [{**first, 'source_updated_at': newer}]))
    assert [item['aircraft_id'] for item in workspace(client)['aircraft']] == ['001', '002']


def test_freshness_does_not_change_reported_status(client):
    stale = row(source_updated_at=(datetime.now(timezone.utc) - timedelta(days=2)).isoformat())
    confirm(client, preview(client, [stale]))
    saved = workspace(client)['aircraft'][0]
    assert saved['freshness'] == 'stale'
    assert saved['reported_status'] == 'available'


def test_utf8_bom_and_quoted_note(client):
    item = row(display_name='Cèdre', note='Contains a comma, and a "quote".')
    response = client.post('/api/demo/imports/preview', files={'file': ('fleet.csv', b'\xef\xbb\xbf' + content([item]), 'text/csv')})
    assert response.json()['valid']
    assert response.json()['rows'][0]['note'] == item['note']


def test_header_and_column_errors(client):
    bad_header = client.post('/api/demo/imports/preview', files={'file': ('fleet.csv', b'aircraft_id,aircraft_id\nA,B', 'text/csv')}).json()
    assert not bad_header['valid'] and bad_header['errors'][0]['field'] == 'headers'
    malformed = (','.join(HEADERS) + '\nA,B,available\n').encode()
    result = client.post('/api/demo/imports/preview', files={'file': ('fleet.csv', malformed, 'text/csv')}).json()
    assert not result['valid'] and result['errors'][0]['field'] == 'columns'


def test_size_and_extension_limits(client):
    result = client.post('/api/demo/imports/preview', files={'file': ('fleet.csv', b'x' * (MAX_BYTES + 1), 'text/csv')})
    assert not result.json()['valid']
    result = client.post('/api/demo/imports/preview', files={'file': ('fleet.xlsx', content([row()]), 'text/csv')})
    assert not result.json()['valid']


def test_cross_origin_changes_rejected(client):
    response = client.post('/api/demo/imports/preview', headers={'Origin': 'https://unrelated.example'}, files={'file': ('fleet.csv', content([row()]), 'text/csv')})
    assert response.status_code == 403


def test_example_can_be_previewed(client):
    sample = client.get('/api/examples/sample.csv')
    assert sample.status_code == 200
    result = client.post('/api/demo/imports/preview', files={'file': ('sample.csv', sample.content, 'text/csv')}).json()
    assert result['valid'] and result['row_count'] == 12
