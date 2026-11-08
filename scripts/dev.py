"""Small Windows-friendly launcher; owns only this project's local PostgreSQL cluster."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / '.local'
PGDATA = LOCAL / 'postgres'
PORT = '55432'
VENV = ROOT / '.venv' / ('Scripts' if os.name == 'nt' else 'bin')
PYTHON = VENV / ('python.exe' if os.name == 'nt' else 'python')


def pg_binary(name: str) -> str:
    executable = name + ('.exe' if os.name == 'nt' else '')
    configured = os.environ.get('POSTGRES_BIN')
    if configured and (Path(configured) / executable).exists():
        return str(Path(configured) / executable)
    located = shutil.which(executable)
    if located:
        return located
    candidates = sorted(Path('C:/Program Files/PostgreSQL').glob(f'*/bin/{executable}'), reverse=True)
    if candidates:
        return str(candidates[0])
    raise RuntimeError('PostgreSQL binaries were not found. Set POSTGRES_BIN to their folder.')


def run(command: list[str], **kwargs):
    return subprocess.run(command, cwd=ROOT, check=True, **kwargs)


def load_config() -> dict[str, str]:
    from dotenv import dotenv_values
    return {key: value for key, value in dotenv_values(ROOT / '.env').items() if value is not None}


def setup():
    LOCAL.mkdir(exist_ok=True)
    config_file = ROOT / '.env'
    if not config_file.exists():
        app_password, admin_password = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        config_file.write_text(
            f'DATABASE_URL=postgresql+psycopg://airframe_app:{app_password}@127.0.0.1:{PORT}/airframe\n'
            f'TEST_DATABASE_URL=postgresql+psycopg://airframe_app:{app_password}@127.0.0.1:{PORT}/airframe_test\n'
            f'PREVIEW_SECRET={secrets.token_urlsafe(48)}\nFRESHNESS_HOURS=24\n', encoding='utf-8')
        (LOCAL / 'database-secrets.json').write_text(json.dumps({'admin': admin_password, 'app': app_password}), encoding='utf-8')
    if not (LOCAL / 'database-secrets.json').exists():
        raise RuntimeError('Existing .env found without project database secrets. Configure DATABASE_URL manually or retain the local setup files together.')
    credentials = json.loads((LOCAL / 'database-secrets.json').read_text(encoding='utf-8'))
    if not (PGDATA / 'PG_VERSION').exists():
        password_file = LOCAL / 'init-password.tmp'
        try:
            password_file.write_text(credentials['admin'] + '\n', encoding='utf-8')
            run([pg_binary('initdb'), '-D', str(PGDATA), '-U', 'airframe_admin', '-A', 'scram-sha-256', '--encoding=UTF8', '--locale=C', '--pwfile', str(password_file)])
        finally:
            password_file.unlink(missing_ok=True)
    start_database()
    import psycopg
    from psycopg import sql
    with psycopg.connect(host='127.0.0.1', port=PORT, user='airframe_admin', password=credentials['admin'], dbname='postgres', autocommit=True) as connection:
        if not connection.execute("SELECT 1 FROM pg_roles WHERE rolname = 'airframe_app'").fetchone():
            connection.execute(sql.SQL('CREATE ROLE airframe_app LOGIN PASSWORD {}').format(sql.Literal(credentials['app'])))
        for database in ('airframe', 'airframe_test'):
            if not connection.execute('SELECT 1 FROM pg_database WHERE datname = %s', (database,)).fetchone():
                connection.execute(sql.SQL('CREATE DATABASE {} OWNER airframe_app').format(sql.Identifier(database)))
    run([str(PYTHON), '-m', 'alembic', '-c', 'backend/alembic.ini', 'upgrade', 'head'])
    run([str(PYTHON), '-m', 'scripts.seed_relief_demo'])
    run([str(PYTHON), '-m', 'scripts.seed_incident_demo'])
    print('Local database and migrations are ready. Existing PostgreSQL services were not modified.')


def start_database():
    if not (PGDATA / 'PG_VERSION').exists():
        raise RuntimeError('Run setup first.')
    status = subprocess.run([pg_binary('pg_ctl'), '-D', str(PGDATA), 'status'], capture_output=True)
    if status.returncode != 0:
        run([pg_binary('pg_ctl'), '-D', str(PGDATA), '-l', str(LOCAL / 'postgres.log'), '-o', f'-p {PORT} -h 127.0.0.1', '-w', 'start'])


def start():
    start_database()
    frontend = ROOT / 'frontend'
    node = shutil.which('node')
    if os.name == 'nt' and Path('C:/Program Files/nodejs/node.exe').exists():
        node = 'C:/Program Files/nodejs/node.exe'
    if not node:
        raise RuntimeError('Node.js was not found.')
    processes = [subprocess.Popen([str(PYTHON), '-m', 'uvicorn', 'backend.app.main:app', '--host', '127.0.0.1', '--port', '8000'], cwd=ROOT)]
    try:
        print('Starting the backend. The first start can take a moment...', flush=True)
        ready = False
        for _ in range(120):
            if processes[0].poll() is not None:
                raise RuntimeError('The backend stopped before becoming ready. Check the message above.')
            try:
                with urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=1) as response:
                    ready = response.status == 200
            except (urllib.error.URLError, TimeoutError):
                pass
            if ready:
                break
            time.sleep(0.5)
        if not ready:
            raise RuntimeError('The backend did not become ready. Check that the database is running.')
        processes.append(subprocess.Popen([node, str(frontend / 'node_modules/vite/bin/vite.js'), '--host', '127.0.0.1', '--port', '5173', '--strictPort'], cwd=frontend))
        print('Sampati: http://127.0.0.1:5173  |  API docs: http://127.0.0.1:8000/docs', flush=True)
        while all(process.poll() is None for process in processes):
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for process in processes:
            if process.poll() is None:
                if os.name == 'nt':
                    # The Windows venv launcher can have a Python child process.
                    subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['setup', 'start', 'db-start', 'db-stop'])
    args = parser.parse_args()
    if args.command == 'setup':
        setup()
    elif args.command == 'start':
        start()
    elif args.command == 'db-start':
        start_database()
    elif PGDATA.exists():
        run([pg_binary('pg_ctl'), '-D', str(PGDATA), '-m', 'fast', '-w', 'stop'])


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(f'Setup could not finish: {error}', file=sys.stderr)
        raise SystemExit(1)
