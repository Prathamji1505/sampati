"""Exercise the real local file-watcher connection with a temporary fictional QA account."""
import http.cookiejar
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.cleanup_browser_accounts import main as cleanup


def main():
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(jar))
    csrf = ''
    user_id = None
    def request(path, body=None):
        headers = {'Content-Type': 'application/json', 'X-Sampati-Request': '1'}
        if csrf:
            headers['X-CSRF-Token'] = csrf
        req = urllib.request.Request('http://127.0.0.1:8000/api' + path,
            data=json.dumps(body).encode() if body is not None else None, headers=headers)
        with opener.open(req, timeout=20) as response:
            return json.load(response)
    try:
        account = request('/auth/signup', {'username': 'qa-browser-' + secrets.token_hex(7),
            'display_name': 'Browser QA watcher', 'organisation_name': 'Browser QA organisation watcher ' + secrets.token_hex(4),
            'password': secrets.token_urlsafe(32)})
        user_id, csrf = account['user']['id'], account['csrf_token']
        source = request('/sources', {'name': 'Fictional watcher check'})
        with tempfile.TemporaryDirectory(prefix='sampati-watcher-') as temp:
            path = Path(temp) / 'fictional.csv'
            path.write_text('aircraft_id,display_name,reported_status,source_updated_at,source_name,note\nWATCH-001,Cedar,unknown,2026-11-07T10:00:00Z,Fictional watcher,Test only\n', encoding='utf-8')
            command = [sys.executable, str(ROOT / 'scripts/watch_dataset.py'), '--source-id', source['id'], '--file', str(path), '--once']
            env = {**os.environ, 'SAMPATI_SOURCE_TOKEN': source['token']}
            for _ in range(2):
                subprocess.run(command, env=env, cwd=ROOT, check=True, capture_output=True)
            inbox = request('/sources')['incoming']
            assert len(inbox) == 1 and inbox[0]['state'] == 'pending', 'Watcher/dedup failed'
            assert request('/workspace')['aircraft'] == [], 'Watcher bypassed human review'
            preview = request('/sources/inbox/' + inbox[0]['id'] + '/preview', {})
            assert preview['valid'], 'Watcher file did not pass preview'
            request('/imports/confirm', {'token': preview['token'], 'rows': preview['rows']})
            assert len(request('/workspace')['aircraft']) == 1, 'Confirmation failed'
        print('Watcher passed: actual HTTP upload, repeat deduplication, pending inbox, human preview/confirmation.')
    finally:
        if user_id:
            previous = sys.argv
            try:
                sys.argv = ['cleanup_browser_accounts.py', user_id]
                cleanup()
            finally:
                sys.argv = previous


if __name__ == '__main__':
    main()
