"""Serve fictional screenshot fixtures in an isolated schema of the test database.

Run with the project virtual environment. This does not seed development data.
Close with Ctrl+C; interrupted process kills may require removing the recorded
schema later. The exact generated schema names are retained in ignored .local.
"""
import os
from pathlib import Path
import secrets
import subprocess
import sys
import uuid

from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


def main():
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    sys.path.insert(0, str(root))
    url = make_url(dotenv_values(root / '.env')['TEST_DATABASE_URL'])
    if not (url.database or '').endswith('_test'):
        raise SystemExit('A dedicated database ending in _test is required.')
    schema = 'showcase_' + uuid.uuid4().hex
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text('CREATE SCHEMA ' + schema))
    record = root / '.local/showcase-schemas.txt'
    record.parent.mkdir(exist_ok=True)
    with record.open('a', encoding='utf-8') as output:
        output.write(schema + '\n')
    try:
        os.environ['DATABASE_URL'] = url.update_query_dict({'options': '-csearch_path=' + schema}).render_as_string(hide_password=False)
        os.environ['PREVIEW_SECRET'] = secrets.token_urlsafe(48)
        os.environ['SAMPATI_SERVE_FRONTEND'] = 'true'
        subprocess.run([sys.executable, '-m', 'alembic', '-c', 'backend/alembic.ini', 'upgrade', 'head'], check=True)
        from backend.app.main import app
        @app.get('/api/showcase-status')
        def showcase_status():
            return {'fictional': True, 'disposable_test_schema': True}
        # Put the fixture marker before the compiled frontend's catch-all mount.
        app.router.routes.insert(0, app.router.routes.pop())
        import uvicorn
        uvicorn.run(app, host='127.0.0.1', port=5173)
    finally:
        from backend.app.database import engine as application_engine
        application_engine.dispose()
        with engine.begin() as connection:
            connection.execute(text('DROP SCHEMA ' + schema + ' CASCADE'))
        engine.dispose()
        print('Removed disposable showcase schema; development data unchanged.')


if __name__ == '__main__':
    main()
