# SAMPATI · सम्पाति

Air Operations & Resource Decision Support. The name draws on Sampati's far-reaching sight in the Ramayana. The approved visual identity pairs black and charcoal surfaces with crimson actions, warm ivory text, and small saffron details.

The identity includes an original folk-style bird emblem and panoramic background generated with ImageGen from a user-provided drawing-style reference. [Artwork prompts and provenance](../frontend/public/artwork/provenance.json) record both assets. The public repository self-hosts OFL-licensed Yatra One for the wordmark and page headings; operational text uses DM Sans. The original personal-use prototype font is retained privately under `.local/private-assets/` and is excluded from the repository and build.

A local learning project for fictional civilian aircraft reports. Upload a CSV or Excel file, inspect validation and proposed changes, explicitly confirm an import, then explore the persistent register and its history.

Reported availability is source information, not airworthiness certification. The local prototype now supports accounts and separate organisation workspaces, alongside the shared fictional demo. Use fictional records. No AI service or external aviation feed is required.

## Run on this Windows PC

Open PowerShell in the project folder. Dependencies are installed in `.venv` and `frontend/node_modules` during the initial build.

```powershell
.\.venv\Scripts\python.exe scripts\dev.py start
```

Open **http://127.0.0.1:5173**. API documentation is at **http://127.0.0.1:8000/docs**. Keep the terminal running; press Ctrl+C to stop the web servers. The project-owned database continues running; stop it separately when wanted:

```powershell
.\.venv\Scripts\python.exe scripts\dev.py db-stop
```

Starting the app starts its database again. The dedicated database uses loopback port **55432**, independently of the installed PostgreSQL service on 5432. Its data and generated credentials are local ignored files under `.local` and `.env`; retain them together and do not commit them.

The root URL opens the Sampati welcome page. **Enter workspace** opens your private register when signed in, otherwise the fictional demo. The logo returns to Welcome. The app checks account-session status on load; aircraft data is fetched after workspace entry. Browser Back/Forward and reload preserve the current location.

Private locations are `/#workspace`, `/#import`, `/#history` and `/#guide`. Demo locations use the `#demo/` prefix, for example `/#demo/workspace`. Sign-in and account creation are at `/#login` and `/#register`.

**Read workspace guide** on Welcome opens the standalone `/#welcome/guide` page. Reading it does not enter the workspace, show workspace navigation or fetch aircraft data. Choose **Back to welcome** to return, or **Enter workspace** when ready. The guide inside an entered workspace remains available from its sidebar.

## Create your own workspace

1. Open `http://127.0.0.1:5173/#register`, or choose **Sign in or create an account** in the demo sidebar.
2. Choose a username, display name, organisation name and password of at least 12 characters.
3. Your new organisation starts with an empty register. Try sample data or import a fictional CSV or Excel file and confirm it.
4. The workspace selector switches between your organisation and Demo workspace. Switching clears pending previews and view state; the server independently resolves membership.
5. Use **Sign out** beside your name. Signing back in restores access to your saved organisation records.

Creating an organisation with an existing organisation's name does not join it. Owners can invite a specific existing username from Organisation team. The recipient accepts the one-time code and can then switch between verified memberships. Save one-time recovery codes in Account settings before you need them. No account is pre-created for the user.

## First demonstration

1. On the welcome page, choose **Enter workspace**.
2. On Aircraft register, choose **Try sample data**.
3. Review the 12 fictional records. The preview has not changed the register.
4. Choose **Confirm import**.
5. Search or filter the table; open an aircraft to inspect its source and timestamps.
6. Open **Import history** to inspect the confirmed import and before/after values.
7. Restart the application and confirm the records remain.

For repeatable file demonstrations, use the files in `examples/`. Import `fictional-fleet.csv` first, then try `older-report.csv` (rejected), `newer-update.csv` (accepted after preview), or one of the invalid files. Re-uploading the exact original dataset is a no-op.

The built-in sample download uses fresh timestamps whenever requested; downloading it again later represents a different source report. Re-upload the same saved file to test exact repetition.

## Set up a fresh checkout

Prerequisites: Python 3.12+, a supported Node.js version with npm, and installed PostgreSQL binaries. Tested version details are in the lockfiles and verification notes.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-lock.txt
& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend ci
.\.venv\Scripts\python.exe scripts\dev.py setup
.\.venv\Scripts\python.exe -m scripts.create_examples
.\.venv\Scripts\python.exe scripts\dev.py start
```

If PostgreSQL binaries are installed elsewhere, set `POSTGRES_BIN` to their `bin` folder. `setup` creates a separate project-owned SCRAM-authenticated cluster, an unprivileged application login, development and test databases, and runs Alembic migrations. It does not change the existing PostgreSQL service. The browser never receives database credentials.

## Check the build

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
& 'C:\Program Files\nodejs\npm.cmd' --prefix frontend run build
```

Backend tests require the generated `TEST_DATABASE_URL`. They refuse a database name without `_test` and use a fresh random schema per test. They do not reset the development database. If the database was stopped, run `scripts\dev.py db-start` first.

The repository also includes `scripts/browser-check.js`, a Playwright CLI function for the fictional demo journey. It imports sample reports through the interface and leaves them available for inspection. Use it only with the local fictional workspace. `scripts/browser-smoke.js` checks the rendered register and a touch-enabled mobile browser context. These are browser checks, not proof of behaviour on a physical phone.

Frontend formatting is available with `npm --prefix frontend run format`.

See [verification results](VERIFICATION.md) for the actual tests, browser checks, restart check, tested versions and remaining limits.

## How the code fits together

- `frontend/src/App.tsx`: entry routing, workspace interface and browser interaction state.
- `frontend/src/Welcome.tsx` and `welcome.css`: the welcome screen in the existing visual identity.
- `frontend/src/Brand.tsx`: shared bilingual brand used on Welcome and in the workspace.
- `frontend/src/api.ts`: browser requests and useful network-error messages.
- `backend/app/main.py`: endpoints and confirmation transaction.
- `backend/app/auth.py`: password hashing, server-side sessions, membership checks, write permissions and sign-in throttling.
- `frontend/src/AuthScreen.tsx` and `accounts.css`: account creation and sign-in in the established visual identity.
- `backend/app/imports.py`: CSV parsing, comparisons, fingerprints and signed preview tokens.
- `backend/app/schemas.py`: agreed record validation.
- `backend/app/models.py`: database tables.
- `backend/migrations`: versioned database structure.
- `scripts/dev.py`: local setup and launcher.

The browser asks FastAPI to inspect a file. The backend validates every row, compares accepted records, and signs a short-lived preview bound to normalized content, the workspace revision and the importing account. It writes no aircraft or import data during preview. On confirmation it checks the signature and content, locks the workspace revision, rechecks the records, and saves the import, aircraft changes and audit entries together.

Passwords are stored as Argon2id hashes. Signing in issues a random HttpOnly, SameSite=Strict cookie; only its digest is stored in the session table. Sessions expire after 12 hours and are revoked on sign-out. The browser keeps its anti-forgery token in memory and restores it through the session endpoint after reload; no session credentials are kept in browser localStorage. Private reads and writes check current membership, and viewer roles cannot import. The account-creation UI currently creates owners only.

Private data endpoints live at `/api/workspace` and `/api/imports/...` and require a verified account session. Demo equivalents live under `/api/demo/...` and intentionally remain available without sign-in. Uploaded values and client-supplied organisation identifiers do not grant workspace access.

## Data rules

See [the data dictionary](DATA_DICTIONARY.md) for exact headers and limits. One invalid row rejects the whole batch. Missing rows do not delete aircraft. Older reports and same-time contradictory reports are blocked. Equivalent repeat datasets return the earlier import without creating another entry. Preview tokens expire after 30 minutes.

The demo freshness threshold is 24 hours, configured by `FRESHNESS_HOURS`. Reports more than five minutes in the future also need review. Freshness is separate from source-reported status and is recalculated on refresh, including every 30 seconds while the tab is visible. Display times follow the browser's local timezone; original source timestamp text is available in aircraft details.

## Current boundaries

This remains a loopback-only fictional-data learning app. Private endpoints require sign-in and current organisation membership; the demo intentionally remains public within the local app. Cookies are configured for local HTTP. Hosted use requires HTTPS/Secure-cookie configuration, deployment controls, off-device backup management and further security review. Recovery codes, invitations and team administration are implemented; email recovery, account verification and account deletion are not. Do not expose this local prototype to a network or add real organisational records yet.

Excel, source-key uploads and a persistent review inbox are implemented. Imports remain limited to 1 MiB and 2,000 records. No trained prediction model or external AI provider is configured. No operational dispatch, military planning, live tracking, or automatic airworthiness decisions are implemented. The provisional UI can be refined with the user.

## Complete local workflow

- **Import dataset:** CSV or .xlsx, downloadable templates, row errors, signed preview, confirmation and audit history.
- **Aircraft register:** search, status/freshness filters, details, and Excel/CSV/JSON export of the current filter. Prefer Excel for spreadsheet use; CSV prefixes formula-like text with an apostrophe, so Excel/JSON preserve raw values more faithfully.
- **Overview:** factual counts, source coverage, old/future reports and unknown status. Counts describe current accepted records; they are not predictions or a historical fleet time series.
- **Data connections:** owner-created, scoped, once-shown keys; disable/rotate keys; generate fictional updates; review or reject incoming datasets. Up to 100 pending files per organisation; the screen shows the latest 100 received files.
- **Organisation team:** account-targeted invitations lasting three days; owner/editor/viewer roles; member removal; last-owner protection; verified organisation switching.
- **Account settings:** password changes, revocation of other sessions and old codes, and five once-shown recovery codes. Use a saved code at `/#recover` if you forget your password.

A source key can submit only to its connection. It cannot read aircraft or approve an import. The source name inside the file remains source-provided data; the inbox separately records which connection submitted it. Keys stop working if disabled, rotated or their creating account loses import access.

## Connect a changing file

Create a connection in the private workspace's Data connections page. Copy its key into an environment variable in a PowerShell terminal. To avoid putting the key into command history:

```powershell
$sourceSecret = Read-Host 'Source key' -AsSecureString
$env:SAMPATI_SOURCE_TOKEN = [System.Net.NetworkCredential]::new('', $sourceSecret).Password
.\.venv\Scripts\python.exe scripts\watch_dataset.py --source-id YOUR_SOURCE_ID --file 'C:\path\fictional-fleet.xlsx'
```

Keep the terminal running. The watcher checks every 15 seconds, submits changed content, retries temporary failures and never approves data. An unchanged file is skipped; server-side deduplication also prevents repeat pending/accepted datasets. For a single connection check add `--once`. Stop with Ctrl+C, then clear the terminal environment variable with `Remove-Item Env:SAMPATI_SOURCE_TOKEN`.

## Back up and rehearse a restore

```powershell
.\.venv\Scripts\python.exe scripts\backup.py
.\.venv\Scripts\python.exe scripts\restore_check.py
```

Backups go to ignored `.local/backups`. The first command makes a PostgreSQL archive and verifies its index. The second restores the latest archive into a newly generated disposable local database, checks its schema and aircraft count, and removes only that temporary database. It does not replace the live database. Keep `.env`, `.local/database-secrets.json` and backups private and retain their relationship; session/preview configuration is outside the database archive. A disk-local backup is not protection against losing the PC.

For an actual loss, stop the app, retain any surviving data directory, prepare a separate empty database, restore the chosen archive there, point `DATABASE_URL` to it and run migrations before restarting. Never restore over a populated database. This prototype includes a restore rehearsal rather than an automatic destructive recovery command.

[Learning guide](LEARNING_GUIDE.md) explains the new modules. [Account model](ACCOUNTS.md) and [verification evidence](VERIFICATION.md) describe tested behaviour and remaining limits.
