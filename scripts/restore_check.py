"""Restore a Sampati archive into a disposable local database, then remove only that database."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

from dotenv import dotenv_values
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url

from dev import ROOT, pg_binary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup', type=Path, help='Archive inside this project’s .local/backups; defaults to the latest.')
    args = parser.parse_args()
    folder = (ROOT / '.local/backups').resolve()
    candidates = sorted(folder.glob('sampati-*.dump'))
    target = (args.backup or (candidates[-1] if candidates else folder / 'missing')).resolve()
    if not target.is_relative_to(folder) or not target.is_file() or target.suffix != '.dump':
        parser.error('Choose a backup .dump file inside this project’s .local/backups folder.')
    url = make_url(dotenv_values(ROOT / '.env')['DATABASE_URL'])
    if url.host not in {'127.0.0.1', 'localhost'} or url.database != 'airframe':
        parser.error('This helper requires the local Sampati database configuration.')
    credentials = json.loads((ROOT / '.local/database-secrets.json').read_text())
    # The database name is generated here, never supplied by an argument or archive.
    check_name = 'sampati_restore_check_' + uuid.uuid4().hex
    assert check_name.startswith('sampati_restore_check_') and len(check_name) == 54
    env = {**os.environ, 'PGPASSWORD': url.password or '', 'PGHOST': url.host, 'PGPORT': str(url.port or 5432),
           'PGUSER': url.username or '', 'PGDATABASE': check_name}
    connection_args = dict(host=url.host, port=url.port or 5432, user=url.username, password=url.password, dbname=check_name)
    with psycopg.connect(host=url.host, port=url.port or 5432, user='airframe_admin', password=credentials['admin'], dbname='postgres', autocommit=True) as admin:
        admin.execute(sql.SQL('CREATE DATABASE {} OWNER {}').format(sql.Identifier(check_name), sql.Identifier(url.username)))
        try:
            subprocess.run([pg_binary('pg_restore'), '--exit-on-error', '--no-owner', '--no-acl', '--dbname', check_name, str(target)],
                env=env, check=True, capture_output=True)
            with psycopg.connect(**connection_args) as restored:
                revision = restored.execute('SELECT version_num FROM alembic_version').fetchone()[0]
                aircraft = restored.execute('SELECT count(*) FROM aircraft').fetchone()[0]
            print(f'Restore verified in a temporary database: schema {revision}; {aircraft} aircraft records.')
        finally:
            # Identifier is checked above, and only this newly-created database is removed.
            admin.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(check_name)))
    print('Temporary restore database removed. The live Sampati database was not changed.')


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError:
        print('The archive could not be restored. The live database was not changed.', file=sys.stderr)
        raise SystemExit(1)
