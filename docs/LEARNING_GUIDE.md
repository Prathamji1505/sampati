# How Sampati works

Think of three separate things: a source report, a proposed import, and the accepted register. A file can be valid without being accepted. Every accepted change has a source timestamp and an import trail.

## Follow one file

1. React displays the form and sends the selected CSV/Excel file to FastAPI.
2. `files.py` reads the file. openpyxl reads Excel; the CSV parser reads CSV. defusedxml hardens XML processing used by Excel. Both formats become the same six-field records.
3. Pydantic checks field values, IDs, lengths, statuses and timezone-bearing timestamps. A bad row blocks the batch.
4. `services.py` compares the rows with accepted records through SQLAlchemy. It returns new/updated/unchanged rows and errors. A signed preview binds the user, organisation, content and database revision. Previewing writes no accepted aircraft or imports.
5. Confirmation checks the signature again and locks the organisation revision in PostgreSQL. Aircraft, import metadata and before/after audit entries commit together. A failure rolls the transaction back.
6. React reloads the accepted register. The interface also refreshes every 30 seconds while visible.

Psycopg is the PostgreSQL connection driver. SQLAlchemy describes tables and queries. Alembic records database structure changes so features can be added without rebuilding the database.

## Changing datasets

The standard-library Python watcher computes a SHA-256 digest of the file every 15 seconds. Changed content goes to a single connection using its source key. The server validates it and stores an incoming dataset. A person reviews and confirms it through the same signed import path. This separates receiving data from accepting it. Key rotation stops the old key; a repeat normalized dataset does not create duplicate pending/accepted entries.

Try it without a second program: create a source, choose **Generate fictional update**, inspect the pending inbox, choose **Review**, then confirm. The update deliberately changes only a few fictional records so the workflow is easy to inspect.

## Accounts and teams

Passwords become Argon2 hashes through pwdlib. The browser receives an opaque HttpOnly session cookie; the database stores its digest, expiry and current organisation. A separate CSRF token accompanies browser changes. Membership, rather than a typed organisation name, grants access.

An owner can invite an existing username as an editor or viewer. The code is bound to that account and expires after three days. Owners manage members and source keys; editors import/review; viewers read and export. Every organisation must retain an owner. Recovery codes are random, hashed, shown once and usable once each; save them privately before forgetting a password.

## What the overview knows

The overview counts accepted source-reported statuses and checks rules such as report age, future timestamps and unknown status. It does not infer mechanical condition or predict failures. It has no trained model or language-model provider. The chart describes today's accepted register, rather than a historical fleet trend.

For example, a source can report `available` while its timestamp is older than 24 hours. Sampati keeps the source's status and independently marks the report as needing review. An absent aircraft row does not prove unavailability and does not delete an existing aircraft.

## Where to explore the code

| File | Purpose |
| --- | --- |
| `frontend/src/App.tsx` | Register, file preview, confirmation, history and route state |
| `frontend/src/WorkspaceTools.tsx` | Overview, connections, team and account screens |
| `frontend/src/AuthScreen.tsx` | Sign-up, login and recovery |
| `frontend/src/api.ts` | Scoped browser requests, CSRF and downloads |
| `backend/app/schemas.py` | The record contract |
| `backend/app/files.py` | Excel reading and exports |
| `backend/app/imports.py` | CSV reading, comparisons and signed previews |
| `backend/app/services.py` | Shared preview and inbox acceptance |
| `backend/app/main.py` | Register/import routes and confirmation transaction |
| `backend/app/accounts.py` | Team access, passwords and recovery |
| `backend/app/sources.py` | Connection keys and incoming files |
| `backend/app/reports.py` | Counts, attention rules and filtered exports |
| `scripts/watch_dataset.py` | Local changing-file connector |
| `scripts/backup.py` / `scripts/restore_check.py` | Backup and disposable restore rehearsal |

pytest checks behaviour and permissions in isolated test-database schemas. The Playwright scripts use real Edge browser flows with temporary fictional accounts. These checks support a local learning prototype; production hosting and live aviation integrations require separate work.
