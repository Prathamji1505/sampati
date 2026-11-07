from datetime import timedelta

from backend.app.auth import COOKIE, token_digest
from backend.app.models import Membership, User, UserSession, utcnow
from .test_imports import content, row

FORM_HEADERS = {'X-Sampati-Request': '1'}
PASSWORD = 'Test passphrase number 42!'


def signup(client, username='cedar-owner', organisation='Cedar Civil Transport'):
    response = client.post('/api/auth/signup', headers=FORM_HEADERS, json={
        'username': username, 'password': PASSWORD, 'display_name': username.title(), 'organisation_name': organisation,
    })
    assert response.status_code == 201, response.text
    return response.json()


def post(client, path, auth, **kwargs):
    return client.post(path, headers={**FORM_HEADERS, 'X-CSRF-Token': auth['csrf_token']}, **kwargs)


def upload(client, auth, records=None):
    response = post(client, '/api/imports/preview', auth, files={'file': ('civil.csv', content(records or [row()]), 'text/csv')})
    assert response.status_code == 200, response.text
    return response.json()


def save(client, auth, proposal):
    return post(client, '/api/imports/confirm', auth, json={'token': proposal['token'], 'rows': proposal['rows']})


def test_private_routes_require_login_while_demo_stays_available(client):
    assert client.get('/api/workspace').status_code == 401
    assert client.post('/api/imports/preview', files={'file': ('a.csv', content([row()]))}).status_code == 401
    assert client.get('/api/demo/workspace').status_code == 200


def test_signup_hashes_password_sets_cookie_and_creates_empty_private_workspace(client):
    response = client.post('/api/auth/signup', headers=FORM_HEADERS, json={
        'username': 'Cedar-Owner', 'password': PASSWORD, 'display_name': 'Cedar Owner', 'organisation_name': 'Civil Example',
    })
    assert response.status_code == 201
    assert 'httponly' in response.headers['set-cookie'].lower()
    assert 'samesite=strict' in response.headers['set-cookie'].lower()
    data = response.json()
    assert data['user']['username'] == 'cedar-owner'
    workspace = client.get('/api/workspace').json()
    assert workspace['aircraft'] == [] and not workspace['is_demo']
    assert workspace['id'] == data['workspace']['id']
    with client.test_sessions() as session:
        user = session.get(User, data['user']['id'])
        assert user.password_hash.startswith('$argon2id$')
        assert PASSWORD not in user.password_hash
        assert session.get(UserSession, token_digest(client.cookies.get(COOKIE))) is not None


def test_private_imports_require_csrf_and_record_actual_actor(client):
    auth = signup(client)
    rejected = client.post('/api/imports/preview', files={'file': ('a.csv', content([row()]))})
    assert rejected.status_code == 403
    proposal = upload(client, auth)
    assert client.get('/api/workspace').json()['aircraft'] == []
    saved = save(client, auth, proposal)
    assert saved.status_code == 200, saved.text
    assert '@cedar-owner' in saved.json()['import']['actor']
    assert len(client.get('/api/workspace').json()['aircraft']) == 1
    assert client.get('/api/demo/workspace').json()['aircraft'] == []


def test_two_organisations_cannot_read_imports_or_replay_each_others_previews(client):
    first = signup(client, 'first-owner')
    proposal = upload(client, first)
    saved = save(client, first, proposal)
    assert saved.status_code == 200
    first_cookie = client.cookies.get(COOKIE)
    client.cookies.clear()
    second = signup(client, 'second-owner')
    assert first['workspace']['id'] != second['workspace']['id']
    assert client.get('/api/workspace').json()['aircraft'] == []
    assert client.get('/api/imports/' + saved.json()['import']['id']).status_code == 404
    assert save(client, second, proposal).status_code == 400
    # A client-supplied tenant selector is not treated as permission.
    result = client.get('/api/workspace', headers={'X-Workspace-ID': first['workspace']['id']}, params={'workspace_id': first['workspace']['id']}).json()
    assert result['id'] == second['workspace']['id'] and result['aircraft'] == []
    own = upload(client, second, proposal['rows'])
    assert not own['already_imported']
    assert save(client, second, own).status_code == 200
    assert len(client.get('/api/workspace').json()['aircraft']) == 1
    client.cookies.clear()
    client.cookies.set(COOKIE, first_cookie, domain='testserver.local', path='/api')
    assert client.get('/api/workspace').json()['id'] == first['workspace']['id']


def test_demo_token_cannot_be_confirmed_in_private_workspace(client):
    proposal = client.post('/api/demo/imports/preview', files={'file': ('a.csv', content([row()]))}).json()
    auth = signup(client)
    assert save(client, auth, proposal).status_code == 400
    assert client.get('/api/workspace').json()['aircraft'] == []


def test_logout_revokes_cookie_and_saved_session(client):
    auth = signup(client)
    old_cookie = client.cookies.get(COOKIE)
    assert post(client, '/api/auth/logout', auth, json={}).status_code == 200
    assert client.get('/api/workspace').status_code == 401
    client.cookies.set(COOKIE, old_cookie, domain='testserver.local', path='/api')
    assert client.get('/api/workspace').status_code == 401


def test_login_uses_generic_errors_and_rotates_existing_session(client):
    auth = signup(client)
    old_cookie = client.cookies.get(COOKIE)
    failed = client.post('/api/auth/login', headers=FORM_HEADERS, json={'username': 'cedar-owner', 'password': 'incorrect'})
    missing = client.post('/api/auth/login', headers=FORM_HEADERS, json={'username': 'missing-owner', 'password': 'incorrect'})
    assert failed.status_code == missing.status_code == 401
    assert failed.json()['detail'] == missing.json()['detail']
    signed_in = client.post('/api/auth/login', headers=FORM_HEADERS, json={'username': 'cedar-owner', 'password': PASSWORD})
    assert signed_in.status_code == 200
    assert client.cookies.get(COOKIE) != old_cookie
    assert signed_in.json()['csrf_token'] != auth['csrf_token']
    with client.test_sessions() as session:
        assert session.get(UserSession, token_digest(old_cookie)) is None


def test_expired_session_and_revoked_membership_cannot_access_records(client):
    auth = signup(client)
    digest = token_digest(client.cookies.get(COOKIE))
    with client.test_sessions.begin() as session:
        saved = session.get(UserSession, digest)
        saved.expires_at = utcnow() - timedelta(seconds=1)
    assert client.get('/api/workspace').status_code == 401
    signed_in = client.post('/api/auth/login', headers=FORM_HEADERS, json={'username': 'cedar-owner', 'password': PASSWORD})
    assert signed_in.status_code == 200
    with client.test_sessions.begin() as session:
        session.delete(session.get(Membership, (auth['user']['id'], auth['workspace']['id'])))
    assert client.get('/api/workspace').status_code in {401, 403}


def test_viewer_role_can_read_but_cannot_import(client):
    auth = signup(client)
    with client.test_sessions.begin() as session:
        session.get(Membership, (auth['user']['id'], auth['workspace']['id'])).role = 'viewer'
    assert client.get('/api/workspace').status_code == 200
    assert post(client, '/api/imports/preview', auth, files={'file': ('a.csv', content([row()]))}).status_code == 403


def test_signup_rejects_short_password_and_does_not_join_by_organisation_name(client):
    bad = client.post('/api/auth/signup', headers=FORM_HEADERS, json={'username': 'short-owner', 'password': 'short', 'display_name': 'Owner', 'organisation_name': 'Same Name'})
    assert bad.status_code == 422
    first = signup(client, 'one-owner', 'Same Name')
    second = signup(client, 'two-owner', 'Same Name')
    assert first['workspace']['id'] != second['workspace']['id']


def test_auth_posts_need_custom_header_and_cross_origin_is_denied(client):
    body = {'username': 'any-owner', 'password': PASSWORD}
    assert client.post('/api/auth/login', json=body).status_code == 403
    assert client.post('/api/auth/login', headers={**FORM_HEADERS, 'Origin': 'https://unrelated.example'}, json=body).status_code == 403


def test_repeated_login_attempts_are_limited(client):
    for _ in range(10):
        assert client.post('/api/auth/login', headers=FORM_HEADERS, json={'username': 'missing-owner', 'password': 'wrong'}).status_code == 401
    response = client.post('/api/auth/login', headers=FORM_HEADERS, json={'username': 'missing-owner', 'password': 'wrong'})
    assert response.status_code == 429 and int(response.headers['retry-after']) > 0
