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

## How relief intake becomes drafts

[Automation inbox](AUTOMATION.md) uses ordinary rules rather than a trained AI model. `automation_files.py` reads a strict CSV/JSON contract; `automation.py` compares each reference with current requests. New rows propose drafts, matching rows stay unchanged, and conflicts or invalid rows pause the file. Owners can explicitly trust a source to create new drafts automatically when every check passes. Human review still confirms needs and logistics.

PostgreSQL workspace locks serialize accepted changes. Canonical fingerprints make equivalent files repeat safely. A preview hash detects changes between reading and accepting. The intake and new drafts commit together, with a provenance link and actor history. Study `test_automation.py` for malformed files, revoked keys, current-record conflicts and concurrent retries.

The relief section in Overview computes queue counts and unmet needs from accepted records. Each request keeps its own unit; stock issues are never counted as arrivals. Its export is a dated snapshot for a shift handover.

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

## Learn the disaster-relief workflow

Start with [Relief requests](RELIEF_REQUESTS.md): a request records a quantity and unit reported by a human source. `backend/app/relief.py` validates exact decimal quantities and protects each edit with a version; its audit stores before/after values. Reviewing a request does not mean supplies were delivered.

Then follow [Incident review](INCIDENTS.md): `backend/app/incidents.py` defines the JSON contract with Pydantic. **Preview** displays a proposed assessment without writing; **Record** stores it as Needs review. A reviewer checks source dates and limitations and provides a reason. Only a reviewed incident can start a linked relief draft, and quantity stays blank until a person enters it. The assessment's source population estimate is not a supply calculation.

Study `backend/tests/test_incidents.py` for validation, organisation isolation, duplicate-safe retries and concurrent review conflicts. `scripts/browser-incidents.js` drives the same workflow through real controls. Inventory and delivery modules will extend the chain later.

## Learn the stock ledger

[Aid inventory](INVENTORY.md) introduces an important distinction: a source count is a report, while a receipt, issue, return or adjustment changes the recorded ledger. Available stock is on hand minus reserved. The server uses Python `Decimal` and PostgreSQL numeric columns so fractional quantities remain exact.

`backend/app/inventory.py` locks the organisation and stock position while checking the version, available stock, original reservation/issue and the reviewed request's remaining quantity. A request limit is shared across stores. An issue consumes an existing reservation rather than allocating the same supplies again. A return frees issued stock without recreating the old reservation. Read the concurrency tests in `backend/tests/test_inventory.py` to see two competing writers and the one accepted result.

Duplicate-safe saves use a stable client submission key plus a unique source reference. If the server commits a receipt but the response is lost, retrying retrieves that event instead of adding the stock again. Corrections append a reasoned adjustment; the original event remains visible. H03 will add delivery evidence separately, because an issue from a store is not proof of arrival.

## Learn delivery confirmation

[Delivery tracking](DELIVERIES.md) adds a second distinction: issuing goods from a store is not proof of arrival. `backend/app/deliveries.py` tracks drafts, human approval and actual dispatch evidence, then derives partial/full delivery from source-confirmed quantities. Request follow-up subtracts only net confirmed arrivals from a reviewed need.

An undelivered return changes both shipment history and stock. Both writes share one database transaction: either both commit or neither does. A stable submission key makes retry safe even when that transaction succeeded but the response was lost. A correction to an overstated arrival is a new linked event; it retains the original evidence and does not change stock.

The server also prevents reusing an already assigned issue, returning delivered stock through the generic inventory form, or editing a request so its active shipments no longer fit. See `backend/tests/test_deliveries.py` for concurrent confirmations, atomic rollback and exact fractional examples. These checks validate recorded software behavior, not real-world deliveries.

## Try the report checks

Open **Report checks** after accepting a dataset. A source-reported available aircraft can have an old report; the status stays available and a separate finding requests a newer report. A fresh unavailable report with a name can pass the data checks, because the check result describes the report rather than the aircraft.

`backend/app/quality.py` compares pending files with the accepted record by ID, source time and field values. A newer report is an incoming update; an older one is an older incoming report; different values at the same timestamp are a conflict. Equivalent pending rows add no finding. Incoming IDs that are not yet accepted are counted separately, rather than added to the register. Each finding group keeps an exact file count and shows up to three example filenames/times. Another organisation's source keys and file contents never appear in these results.

The backend holds a shared workspace lock while reading accepted records and pending evidence, so an import cannot replace the records halfway through a check. It uses one clock reading for the whole response. `frontend/src/ReportChecks.tsx` provides filters, source inspection, pagination and JSON downloads. The download records check time, rule version, threshold, revision, selected filters and all matching records. It is a review artifact, not a full archive of every pending file; use the import/inbox records for the original evidence.

Expanding a finding, exporting it or refreshing never confirms an import or changes status. Free-text notes are compared as source text; their meaning is not interpreted to infer maintenance condition. These are rules and comparisons, not a trained AI model. See docs/REQUIREMENTS.md for the remaining project gaps.
