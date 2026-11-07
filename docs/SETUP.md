# Run Sampati locally

Sampati is a local fictional-data prototype. The full launcher has been exercised on Windows/PowerShell. No hosted URL or pre-created account is supplied.

## Prerequisites

- Python 3.12 and `py` available in PowerShell.
- Node.js 22 or newer compatible with Vite 7, and npm on `PATH`.
- Installed PostgreSQL binaries, including `initdb`, `pg_ctl`, `pg_dump` and `pg_restore`. This project was exercised with PostgreSQL 18.
- Git for cloning the source.

If PostgreSQL is outside `PATH`, set its actual installation folder in the current terminal, for example:

```powershell
$env:POSTGRES_BIN = 'C:\Program Files\PostgreSQL\18\bin'
```

## First checkout

```powershell
git clone https://github.com/Prathamji1505/sampati.git
cd sampati
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-lock.txt
npm --prefix frontend ci
.\.venv\Scripts\python.exe scripts\dev.py setup
.\.venv\Scripts\python.exe scripts\dev.py start
```

`setup` generates `.env` and `.local/database-secrets.json`, creates a separate SCRAM-authenticated cluster on loopback port **55432**, creates development and test databases and applies migrations. Do not copy `.env.example` over the generated `.env`. The existing system PostgreSQL service is not reconfigured.

Keep the terminal running. Open [the app](http://127.0.0.1:5173) or [API documentation](http://127.0.0.1:8000/docs). Choose **Enter workspace** to explore the fictional demo; use **Try sample data** if the register is empty. For your own empty organisation, visit `/#register`; there are no default credentials. [Follow the demo](DEMO.md).

DM Sans is requested from Google Fonts; system sans-serif text remains usable offline. Display lettering and artwork are local assets. No aviation feed or AI API credentials are required.

## Stop and restart

Press **Ctrl+C** in the launcher terminal to stop the web servers. The project-owned database remains running:

```powershell
.\.venv\Scripts\python.exe scripts\dev.py db-stop
```

Run `scripts\dev.py start` with the virtual-environment Python to start again. Accepted records persist in `.local/postgres/`.

## Verify

```powershell
.\.venv\Scripts\python.exe scripts\dev.py db-start
.\.venv\Scripts\python.exe -m pytest backend\tests -q
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini check
npm --prefix frontend run build
```

Tests load the generated `TEST_DATABASE_URL`, reject a database without the `_test` suffix, and create/drop a separate random schema per test. They do not reset the development workspace. The production build performs TypeScript checking and writes ignored assets under `frontend/dist/`.

GitHub Actions uses a disposable PostgreSQL service for the same backend and migration checks, and Node.js 22 for the frontend build. That workflow does not exercise a complete non-Windows launcher or provision production hosting.

## Troubleshooting

| Symptom | Next step |
| --- | --- |
| PostgreSQL binaries not found | Set `POSTGRES_BIN` to the installed `bin` directory, then retry setup. |
| `npm` is not recognised | Reopen PowerShell after installing Node, or call `& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend ci`. |
| Port 5173 or 8000 is already in use | Check whether Sampati is already running. Stop its original launcher with Ctrl+C before starting a second instance. |
| Existing `.env` without database secrets | Retain `.env` and `.local/database-secrets.json` together. For an intentionally external database, configure it manually; do not delete local data to bypass the check. |
| The test database cannot be reached | Run `db-start`, confirm setup completed and retain `TEST_DATABASE_URL`. Never point tests at a development database. |
| An example is stale or rejected as older | Checked-in examples are fixed historical reports. Use **Try sample data** on a fresh workspace for timestamps generated at request time. |

## Detailed workflows

See [the local workflow reference](LOCAL_WORKFLOW.md) for accounts, source-key file watching, backup/restore rehearsal and complete data rules. Keep `.env`, source keys, recovery codes, local databases and backups out of Git.
