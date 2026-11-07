"""Create and verify a local PostgreSQL backup without changing the live database."""
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys

from dotenv import dotenv_values
from sqlalchemy.engine import make_url

from dev import ROOT, pg_binary


def main():
    config = dotenv_values(ROOT / '.env')
    url = make_url(config['DATABASE_URL'])
    if url.host not in {'127.0.0.1', 'localhost'} or url.database != 'airframe':
        raise RuntimeError('This helper only backs up the local Sampati database named airframe.')
    folder = ROOT / '.local' / 'backups'
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    target = folder / f'sampati-{stamp}.dump'
    env = {**os.environ, 'PGPASSWORD': url.password or '', 'PGHOST': url.host,
           'PGPORT': str(url.port or 5432), 'PGUSER': url.username or '', 'PGDATABASE': url.database}
    try:
        subprocess.run([pg_binary('pg_dump'), '--format=custom', '--no-owner', '--no-acl', '--file', str(target)],
            env=env, check=True, capture_output=True)
        subprocess.run([pg_binary('pg_restore'), '--list', str(target)], env=env, check=True, capture_output=True)
    except subprocess.CalledProcessError as error:
        target.unlink(missing_ok=True)
        raise RuntimeError('The local backup could not be completed. Check that the project database is running.') from error
    print(f'Backup created and archive index verified: {target}')
    print('Includes private records and account hashes. Keep this backup private. No live records were changed.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, KeyError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
