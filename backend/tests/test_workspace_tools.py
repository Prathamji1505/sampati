from datetime import datetime, timezone
import io

from openpyxl import Workbook, load_workbook

from backend.app.auth import COOKIE
from backend.app.models import Membership
from .test_accounts import FORM_HEADERS, PASSWORD, post, save, signup, upload
from .test_imports import confirm, content, preview, row


def xlsx(records, extra_sheet=False):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(list(records[0]))
    for item in records:
        sheet.append(list(item.values()))
    if extra_sheet:
        workbook.create_sheet('Extra')
    target = io.BytesIO()
    workbook.save(target)
    return target.getvalue()


def test_excel_import_uses_same_preview_and_confirmation(client):
    item = row('001')
    response = client.post('/api/demo/imports/preview', files={'file': ('fleet.xlsx', xlsx([item]))})
    result = response.json()
    assert result['valid'] and result['rows'][0]['aircraft_id'] == '001'
    assert confirm(client, result).status_code == 200


def test_excel_rejects_formulas_multiple_sheets_and_numeric_ids(client):
    for records, extra in [([row(note='=1+1')], False), ([row()], True), ([{**row(), 'aircraft_id': 1}], False)]:
        result = client.post('/api/demo/imports/preview', files={'file': ('fleet.xlsx', xlsx(records, extra))}).json()
        assert not result['valid'] and result['token'] is None


def test_excel_rejects_broken_zip_and_timezone_free_excel_dates(client):
    for file in [b'not a workbook', xlsx([{**row(), 'source_updated_at': datetime(2026, 11, 7, 10)}])]:
        response = client.post('/api/demo/imports/preview', files={'file': ('fleet.xlsx', file)})
        assert response.status_code == 200 and not response.json()['valid']


def test_excel_reordered_headers_preserve_id_type_checks_and_source_row_numbers(client):
    record = row('001')
    reordered = {key: record[key] for key in reversed(record)}
    result = client.post('/api/demo/imports/preview', files={'file': ('fleet.xlsx', xlsx([reordered]))}).json()
    assert result['valid'] and result['rows'][0]['aircraft_id'] == '001'
    reordered['aircraft_id'] = 1
    invalid = client.post('/api/demo/imports/preview', files={'file': ('fleet.xlsx', xlsx([reordered]))}).json()
    assert not invalid['valid'] and 'IDs as text' in invalid['errors'][0]['message']
    workbook = Workbook()
    workbook.active.append(list(record))
    workbook.active.append([])
    workbook.active.append(list({**record, 'reported_status': 'broken'}.values()))
    target = io.BytesIO()
    workbook.save(target)
    result = client.post('/api/demo/imports/preview', files={'file': ('fleet.xlsx', target.getvalue())}).json()
    assert not result['valid'] and result['errors'][0]['row'] == 3


def test_exports_are_scoped_and_excel_cells_are_literal(client):
    auth = signup(client)
    record = row(note='=1+1')
    assert save(client, auth, upload(client, auth, [record])).status_code == 200
    exported = client.get('/api/exports/register.xlsx')
    assert exported.status_code == 200
    workbook = load_workbook(io.BytesIO(exported.content), data_only=False)
    assert workbook.active['F2'].value == '=1+1' and workbook.active['F2'].data_type == 's'
    workbook.close()
    assert "'=1+1" in client.get('/api/exports/register.csv').text
    assert client.get('/api/exports/register.json').json()['records'][0]['note'] == '=1+1'
    assert client.get('/api/demo/exports/register.json').json()['records'] == []
    assert client.get('/api/exports/register.json', params={'q': 'does-not-exist'}).json()['records'] == []


def test_overview_reports_facts_without_predictive_claims(client):
    auth = signup(client)
    empty = client.get('/api/overview').json()
    assert empty['total'] == 0
    save(client, auth, upload(client, auth, [row()]))
    report = client.get('/api/overview').json()
    assert report['total'] == report['statuses']['available'] == 1
    assert 'No predictive model' in report['summary_method']
    assert client.get('/api/demo/overview').json()['total'] == 0


def two_accounts(client):
    first = signup(client, 'first-owner', 'First organisation')
    first_cookie = client.cookies.get(COOKIE)
    client.cookies.clear()
    second = signup(client, 'second-owner', 'Second organisation')
    second_cookie = client.cookies.get(COOKIE)
    return first, first_cookie, second, second_cookie


def use_cookie(client, value):
    client.cookies.clear()
    client.cookies.set(COOKIE, value, domain='testserver.local', path='/api')


def test_targeted_invitation_join_switch_and_role_enforcement(client):
    first, first_cookie, second, second_cookie = two_accounts(client)
    use_cookie(client, first_cookie)
    invitation = post(client, '/api/team/invitations', first, json={'username': 'second-owner', 'role': 'viewer'})
    assert invitation.status_code == 200
    token = invitation.json()['token']
    assert post(client, '/api/team/invitations/accept', first, json={'token': token}).status_code == 400
    use_cookie(client, second_cookie)
    accepted = post(client, '/api/team/invitations/accept', second, json={'token': token})
    assert accepted.status_code == 200, accepted.text
    current = accepted.json()
    assert current['workspace']['id'] == first['workspace']['id'] and current['workspace']['role'] == 'viewer'
    assert len(current['workspaces']) == 2
    assert post(client, '/api/imports/preview', current, files={'file': ('a.csv', content([row()]))}).status_code == 403
    assert post(client, '/api/team/invitations', current, json={'username': 'first-owner', 'role': 'editor'}).status_code == 403
    switched = post(client, '/api/auth/workspace', current, json={'workspace_id': second['workspace']['id']})
    assert switched.status_code == 200 and switched.json()['workspace']['role'] == 'owner'
    assert post(client, '/api/team/invitations/accept', switched.json(), json={'token': token}).status_code == 400


def test_owner_cannot_remove_or_demote_last_owner(client):
    auth = signup(client)
    user_id = auth['user']['id']
    assert client.patch('/api/team/members/' + user_id, headers={'X-CSRF-Token': auth['csrf_token']}, json={'role': 'viewer'}).status_code == 409
    assert client.delete('/api/team/members/' + user_id, headers={'X-CSRF-Token': auth['csrf_token']}).status_code == 409


def test_workspace_switch_rejects_nonmembers_and_revocation_removes_access(client):
    first, first_cookie, second, second_cookie = two_accounts(client)
    assert post(client, '/api/auth/workspace', second, json={'workspace_id': first['workspace']['id']}).status_code == 403
    use_cookie(client, first_cookie)
    invitation = post(client, '/api/team/invitations', first, json={'username': 'second-owner', 'role': 'editor'}).json()
    use_cookie(client, second_cookie)
    current = post(client, '/api/team/invitations/accept', second, json={'token': invitation['token']}).json()
    use_cookie(client, first_cookie)
    assert client.delete('/api/team/members/' + second['user']['id'], headers={'X-CSRF-Token': first['csrf_token']}).status_code == 200
    use_cookie(client, second_cookie)
    assert client.get('/api/workspace').status_code in {401, 403}


def test_recovery_codes_are_one_time_and_reset_password(client):
    auth = signup(client)
    generated = post(client, '/api/auth/recovery-codes', auth, json={'current_password': PASSWORD})
    assert generated.status_code == 200
    codes = generated.json()['codes']
    assert len(codes) == 5
    client.cookies.clear()
    reset_body = {'username': 'cedar-owner', 'recovery_code': codes[0], 'new_password': 'Replacement passphrase number 24!'}
    recovered = client.post('/api/auth/recover', headers=FORM_HEADERS, json=reset_body)
    assert recovered.status_code == 200, recovered.text
    assert client.post('/api/auth/recover', headers=FORM_HEADERS, json=reset_body).status_code == 401
    failed_login = client.post('/api/auth/login', headers=FORM_HEADERS, json={'username': 'cedar-owner', 'password': PASSWORD})
    assert failed_login.status_code == 401


def test_password_change_invalidates_old_recovery_codes_and_sessions(client):
    auth = signup(client)
    old_cookie = client.cookies.get(COOKIE)
    code = post(client, '/api/auth/recovery-codes', auth, json={'current_password': PASSWORD}).json()['codes'][0]
    changed = post(client, '/api/auth/password', auth, json={'current_password': PASSWORD, 'new_password': 'A changed password for this local test!'})
    assert changed.status_code == 200 and changed.json()['csrf_token'] != auth['csrf_token']
    assert client.get('/api/auth/security').json()['recovery_codes_remaining'] == 0
    use_cookie(client, old_cookie)
    assert client.get('/api/workspace').status_code == 401
    assert client.post('/api/auth/recover', headers=FORM_HEADERS, json={'username': 'cedar-owner', 'recovery_code': code, 'new_password': PASSWORD}).status_code == 401


def new_source(client, auth):
    response = post(client, '/api/sources', auth, json={'name': 'Fictional local source'})
    assert response.status_code == 201, response.text
    return response.json()


def ingest(client, source, records=None):
    return client.post('/api/ingest/' + source['id'], headers={'Authorization': 'Bearer ' + source['token']}, files={'file': ('source.csv', content(records or [row()]))})


def test_source_updates_wait_for_approval_and_are_idempotent(client):
    auth = signup(client)
    source = new_source(client, auth)
    records = [row()]
    received = ingest(client, source, records)
    assert received.status_code == 202
    assert client.get('/api/workspace').json()['aircraft'] == []
    again = ingest(client, source, records)
    assert again.json()['duplicate']
    incoming_id = received.json()['id']
    proposal = post(client, f'/api/sources/inbox/{incoming_id}/preview', auth, json={}).json()
    accepted = save(client, auth, proposal)
    assert accepted.status_code == 200, accepted.text
    inbox = client.get('/api/sources').json()['incoming']
    assert inbox[0]['state'] == 'accepted' and inbox[0]['import_id'] == accepted.json()['import']['id']
    assert save(client, auth, proposal).json()['duplicate']
    assert client.get('/api/sources').json()['incoming'][0]['reviewed_at'] == inbox[0]['reviewed_at']
    assert len(client.get('/api/workspace').json()['aircraft']) == 1


def test_source_revocation_and_rejected_inbox_block_further_changes(client):
    auth = signup(client)
    source = new_source(client, auth)
    incoming = ingest(client, source).json()
    proposal = post(client, f"/api/sources/inbox/{incoming['id']}/preview", auth, json={}).json()
    assert post(client, f"/api/sources/inbox/{incoming['id']}/reject", auth, json={}).status_code == 200
    assert save(client, auth, proposal).status_code == 409
    assert client.patch('/api/sources/' + source['id'], headers={'X-CSRF-Token': auth['csrf_token']}, json={'enabled': False}).status_code == 200
    assert ingest(client, source).status_code == 401


def test_sources_and_inbox_are_scoped_to_organisation(client):
    first = signup(client, 'first-owner')
    source = new_source(client, first)
    incoming = ingest(client, source).json()
    client.cookies.clear()
    second = signup(client, 'second-owner')
    assert client.get('/api/sources').json()['sources'] == []
    assert post(client, f"/api/sources/inbox/{incoming['id']}/preview", second, json={}).status_code == 404
    assert post(client, f"/api/sources/{source['id']}/rotate", second, json={}).status_code == 404
    assert client.post('/api/ingest/' + source['id'], files={'file': ('a.csv', content([row()]))}).status_code == 401


def test_rotating_source_key_revokes_previous_key(client):
    auth = signup(client)
    source = new_source(client, auth)
    rotated = post(client, '/api/sources/' + source['id'] + '/rotate', auth, json={})
    assert rotated.status_code == 200 and rotated.json()['token'] != source['token']
    assert ingest(client, source).status_code == 401
    assert ingest(client, rotated.json()).status_code == 202
