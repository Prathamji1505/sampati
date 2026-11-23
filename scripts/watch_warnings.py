"""Send authorised local warning JSON exports to a warning-only connector.

Use SAMPATI_WARNING_KEY for the private key. This adapter neither scrapes news
nor verifies its truth. Replays are deduplicated by the receiving application.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.response import SignalInput  # noqa: E402


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def send_file(path, url, token, opener):
    if path.stat().st_size > 65536:
        raise ValueError('Warning JSON must be no larger than 64 KiB.')
    content = path.read_bytes()
    if len(content) > 65536:
        raise ValueError('Warning JSON grew beyond 64 KiB; export it again.')
    payload = SignalInput.model_validate_json(content).model_dump(mode='json')
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), method='POST',
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token})
    with opener.open(request, timeout=20) as response:
        if response.status != 202:
            raise ValueError('The warning endpoint did not accept this report.')
    return hashlib.sha256(content).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True, type=Path)
    parser.add_argument('--url', required=True, help='Local /api/response/ingest/UUID endpoint')
    parser.add_argument('--once', action='store_true', help='Check the directory once, then exit')
    parser.add_argument('--interval', type=float, default=5)
    args = parser.parse_args()
    url = urllib.parse.urlsplit(args.url)
    if url.scheme not in {'http', 'https'} or url.hostname not in {'127.0.0.1', 'localhost', '::1'} or url.username or url.password or url.query or url.fragment or not re.fullmatch(r'/api/response/ingest/[0-9a-fA-F-]{36}', url.path):
        parser.error('Use the exact loopback warning connector URL. Hosted endpoints need a separately configured adapter.')
    if args.interval < 1 or args.interval > 3600:
        parser.error('Choose an interval between 1 and 3,600 seconds.')
    token = os.environ.get('SAMPATI_WARNING_KEY', '').strip()
    if not token:
        parser.error('Set the private SAMPATI_WARNING_KEY environment variable first.')
    if not args.directory.is_dir():
        parser.error('The authorised warning export directory does not exist.')
    # Disable proxies and redirects: the scoped key stays on the chosen loopback endpoint.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    accepted = {}; failed = False
    while True:
        failed = False
        for path in sorted(args.directory.glob('*.json')):
            try:
                # Read at most 64 KiB when deciding whether an export changed.
                with path.open('rb') as handle:
                    data = handle.read(65537)
                if len(data) > 65536:
                    raise ValueError('Warning export exceeds 64 KiB.')
                digest = hashlib.sha256(data).hexdigest()
                if accepted.get(str(path)) == digest:
                    continue
                accepted[str(path)] = send_file(path, args.url, token, opener)
                print(f'Received for human review: {path.name}', flush=True)
            except Exception as error:
                failed = True
                # HTTP bodies and validation input values can contain private evidence.
                status = getattr(error, 'code', None)
                print(f'Not accepted: {path.name} ({"HTTP " + str(status) if status else type(error).__name__}). Check the export and connector policy.', file=sys.stderr, flush=True)
        if args.once:
            return 1 if failed else 0
        time.sleep(args.interval)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        pass
