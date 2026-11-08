"""Submit a changing fictional dataset to Sampati's Automation inbox using a source key."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

MAX_BYTES = 256 * 1024


def submit(server: str, source_id: str, path: Path, content: bytes, token: str):
    boundary = 'sampati-' + uuid.uuid4().hex
    # Use a fixed filename rather than interpolating a user-controlled MIME header.
    filename = 'watched-relief' + path.suffix.lower()
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            'Content-Type: application/octet-stream\r\n\r\n').encode() + content + f'\r\n--{boundary}--\r\n'.encode()
    request = urllib.request.Request(f'{server}/api/automation/ingest/{source_id}', data=body,
        headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'multipart/form-data; boundary=' + boundary}, method='POST')
    # Do not follow redirects with a source credential.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=20) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-id', required=True)
    parser.add_argument('--file', type=Path, required=True)
    parser.add_argument('--server', default='http://127.0.0.1:8000')
    parser.add_argument('--interval', type=float, default=15)
    parser.add_argument('--once', action='store_true', help='Submit once and exit; useful for checking a connection.')
    args = parser.parse_args()
    server = urllib.parse.urlsplit(args.server)
    if (server.scheme != 'http' or server.hostname not in {'127.0.0.1', 'localhost'}
        or server.username or server.password or server.path not in {'', '/'} or server.query or server.fragment):
        parser.error('--server must be a local HTTP address such as http://127.0.0.1:8000')
    try:
        source_id = str(uuid.UUID(args.source_id))
    except ValueError:
        parser.error('--source-id must be the connection UUID shown in Sampati')
    if not math.isfinite(args.interval) or args.interval < 2:
        parser.error('--interval must be at least two seconds')
    if args.file.suffix.lower() not in {'.csv', '.json'}:
        parser.error('--file must be a CSV or JSON file')
    token = os.environ.get('SAMPATI_AUTOMATION_TOKEN', '').strip()
    if not token:
        parser.error('Set SAMPATI_AUTOMATION_TOKEN in this terminal first. Do not pass the key as an argument.')
    last_digest = None
    print('Watching for changes. Source rules may create new drafts; conflicts wait for human review. Press Ctrl+C to stop.', flush=True)
    try:
        while True:
            try:
                with args.file.open('rb') as handle:
                    content = handle.read(MAX_BYTES + 1)
                if len(content) > MAX_BYTES:
                    raise ValueError('The file exceeds the 256 KiB limit.')
                digest = hashlib.sha256(content).digest()
                if digest != last_digest:
                    result = submit(args.server.rstrip('/'), source_id, args.file, content, token)
                    last_digest = digest
                    print('Already received; original decision retained.' if result['duplicate'] else ('Drafts created by the trusted-source rule.' if result.get('automatic') else 'File recorded (' + result['state'] + '). Open Automation inbox in Sampati.'), flush=True)
                if args.once:
                    return 0
            except urllib.error.HTTPError as error:
                # Report only the status, never request headers or credential-bearing objects.
                print(f'Submission refused ({error.code}). Check the file, connection key and inbox in Sampati.', file=sys.stderr, flush=True)
                if args.once or error.code in {401, 403}:
                    return 1
            except (OSError, ValueError, urllib.error.URLError) as error:
                message = str(error) if isinstance(error, ValueError) else 'The file or local server is unavailable.'
                print(message, file=sys.stderr, flush=True)
                if args.once:
                    return 1
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print('Watcher stopped.')
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
