"""Run the compiled Sampati app on loopback, without a separate frontend server."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    os.chdir(ROOT)
    if not (ROOT / 'frontend/dist/index.html').is_file():
        raise SystemExit('Build the interface first: npm --prefix frontend run build')
    subprocess.run([sys.executable, '-m', 'alembic', '-c', 'backend/alembic.ini', 'upgrade', 'head'], check=True)
    environment = {**os.environ, 'SAMPATI_SERVE_FRONTEND': 'true'}
    print('Sampati: http://127.0.0.1:8000 | Close this terminal to stop the app.', flush=True)
    subprocess.run([sys.executable, '-m', 'uvicorn', 'backend.app.main:app', '--host', '127.0.0.1', '--port', '8000'], env=environment, check=True)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
