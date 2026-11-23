# Sampati 0.5 - local civilian response preparation

Sampati is a standalone application for a civilian relief team to connect reviewed flood evidence, confirmed needs, aid stock and source-backed delivery records. It runs with fictional examples on a local computer. No particular external assessment product is required.

## Included

- Warning/news JSON intake, scoped warning-only connectors and a local changing-file adapter; human verification and immutable evidence/history.
- Dated aircraft support reports and an explained deterministic workflow planner using reviewed needs, exact unreserved stock, prior commitments, cargo weights and reported operator/context checks.
- Original preparation snapshots, current-evidence rechecks, coordinator review, repeat protection and JSON preparation exports. See [response preparation](RESPONSE_PLANNING.md).
- Incident assessment preview, immutable source evidence and reasoned review.
- Relief drafts, exact quantity/unit, deadline, corrections, submission, review and cancellation.
- Aid item/store catalogs, protected balances, separate count reports, reservations, issues, releases and returns.
- Issue-linked shipment review, sourced dispatch records, partial/full arrivals, undelivered returns, linked evidence corrections and remaining-needs follow-up.
- Structured CSV/JSON relief-file intake, raw evidence, conflict preview, manual decisions, repeat protection and an optional owner rule to create new drafts automatically.
- A relief handover overview with queue navigation, earliest remaining needs and a dated JSON export.
- Supporting aircraft source reports, CSV/Excel review, quality checks, history and exports.
- Organisation roles, sessions, CSRF checks, recovery codes, version guards and audit histories.
- Local migrations, setup, compiled single-server launcher and backup/restore helpers.

## Run and learn

Follow [SETUP.md](SETUP.md) for the prerequisites and first setup. The development launcher serves the app at `http://127.0.0.1:5173`; compiled local mode serves it at `http://127.0.0.1:8000`. Stop one before using the other. [DEMO.md](DEMO.md) describes the learning journey, and [LEARNING_GUIDE.md](LEARNING_GUIDE.md) explains the code.

See [VERIFICATION.md](VERIFICATION.md) for executed software checks and their limits.

## Honest release boundary

This is a local workflow release; deployment with responders remains unvalidated. Recorded evidence is supplied by users/sources. Automation and response preparation are deterministic; no AI model/provider is configured. Preparation review does not reserve stock, book aircraft or authorise dispatch. General news scraping, live public-provider/database/weather adapters, forecasting, route/schedule optimisation, real aircraft positions, public hosting and field evaluation remain separate work. They require authorised source access, a defined user task or an actual deployment environment. No cost saving, welfare outcome or operational adoption has been measured.

Public hosting needs a chosen environment, HTTPS, configurable trusted origins, secure cookies, abuse protection, secret management, off-device recovery and a deployment review. The packaged local launcher intentionally binds loopback and does not publish a server on the internet.
