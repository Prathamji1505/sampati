"""Exercise the real local watcher and handover with disposable fictional QA data."""
import csv
import io
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
from uuid import uuid4

import httpx

from backend.app.automation_files import HEADERS, example_payload

ROOT = Path(__file__).resolve().parents[1]


def main():
    suffix = uuid4().hex[:14]
    local = ROOT / '.local'
    local.mkdir(exist_ok=True)
    ids_file = local / 'release-qa-ids.json'
    with httpx.Client(base_url='http://127.0.0.1:8000', timeout=30) as client:
        response = client.post('/api/auth/signup', headers={'X-Sampati-Request': '1'}, json={
            'username': 'qa-browser-' + suffix, 'password': secrets.token_urlsafe(24),
            'display_name': 'Browser QA release watcher', 'organisation_name': 'Browser QA organisation watcher ' + suffix})
        response.raise_for_status()
        auth = response.json()
        existing = json.loads(ids_file.read_text()) if ids_file.exists() else []
        ids_file.write_text(json.dumps([*existing, auth['user']['id']]))
        headers = {'X-CSRF-Token': auth['csrf_token']}
        response = client.post('/api/automation/sources', headers=headers, json={'name': 'Fictional release watcher'})
        response.raise_for_status(); source = response.json()
        environment = {**os.environ, 'SAMPATI_AUTOMATION_TOKEN': source['token']}
        with tempfile.TemporaryDirectory(prefix='release-watcher-', dir=local) as temporary:
            folder = Path(temporary).resolve()
            assert folder.is_relative_to(local.resolve()) and folder.name.startswith('release-watcher-')
            path = folder / 'needs.json'
            path.write_text(json.dumps(example_payload(reference='QA-WATCHER-001')), encoding='utf-8')
            def watch(file):
                result = subprocess.run([sys.executable, str(ROOT / 'scripts/watch_relief.py'), '--source-id', source['id'], '--file', str(file), '--once'],
                    cwd=ROOT, env=environment, capture_output=True, text=True, timeout=40)
                assert result.returncode == 0, 'Watcher did not finish successfully.'
                assert source['token'] not in result.stdout + result.stderr
                return result.stdout
            assert 'File recorded (pending)' in watch(path)
            assert 'Already received' in watch(path)
            inbox = client.get('/api/automation/inbox').json()
            assert inbox['total'] == 1
            item = client.get('/api/automation/inbox/' + inbox['items'][0]['id']).json()['receipt']
            response = client.post('/api/automation/inbox/' + item['id'] + '/apply', headers=headers, json={
                'expected_version': item['version'], 'plan_hash': item['plan']['plan_hash'], 'reason': 'Fictional watcher source checked.'})
            response.raise_for_status()
            assert client.get('/api/overview/relief').json()['attention']['requests'] == 1
            response = client.patch('/api/automation/sources/' + source['id'], headers=headers, json={
                'expected_version': 1, 'enabled': True, 'automation_mode': 'new_drafts', 'reason': 'Trust fictional watcher for draft creation.'})
            response.raise_for_status()
            payload = example_payload(reference='QA-WATCHER-002')
            csv_path = folder / 'needs.csv'
            output = io.StringIO(newline=''); writer = csv.DictWriter(output, HEADERS); writer.writeheader()
            writer.writerow({**{key: payload[key] for key in ('schema_version', 'report_reference', 'observed_at')}, **payload['requests'][0]})
            csv_path.write_text(output.getvalue(), encoding='utf-8')
            assert 'Drafts created' in watch(csv_path)
            requests = client.get('/api/relief-requests').json()
            assert requests['total'] == 2 and all(item['status'] == 'draft' for item in requests['items'])
            assert client.get('/api/overview/relief').json()['needs_total'] == 0
    print('Passed: real JSON/CSV watcher, repeat protection, manual acceptance, automatic drafts, handover counts and credential-free logs.')
    print('Generated QA user: ' + auth['user']['id'])


if __name__ == '__main__':
    main()
