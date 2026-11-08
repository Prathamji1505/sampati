# Product
<!-- impeccable:product-schema 1 -->

## Platform
web

## Stack
User-approved direction: React, TypeScript, Vite, Python, FastAPI, PostgreSQL, SQLAlchemy, Psycopg and Alembic. Local Windows development, with public GitHub source preparation authorised for hackathon and startup-event review. Application hosting remains unconfigured.

## Users
A beginner building their first application, civilian disaster-relief coordinators, aid-inventory custodians and delivery-record reviewers. These intended users remain to be validated with civilian organisations.

## Product Purpose
Support civilian welfare through reviewed flood assessments, relief requests, aid-inventory records and delivery tracking. The user selected civilian welfare as the project's direction on 8 November 2026, refined to flood-response coordination. H01 implements organisation-scoped relief requests, exact quantities/units, local-time deadlines, draft/submitted/reviewed/cancelled states, version-protected corrections and audit history. Incident intake/review connects a dated flood assessment to a relief draft; its quantities are entered by a person. H02 implements fixed catalogs, exact protected stock balances, separate source counts and request-linked movements/history. H03 connects inventory issues to reviewed tracking drafts, dispatch evidence, partial/full arrival confirmations, atomic undelivered returns, evidence corrections and request follow-up. See docs/INVENTORY.md and docs/DELIVERIES.md. The fictional civilian aircraft-report foundation remains available. The current charter and build order are in docs/CIVILIAN_WELFARE_SCOPE.md.

## Operating Context
A local web application with a fictional shared demo and account-separated organisation workspaces. No live aviation feeds or real organisational data. Accounts, sign-in/sign-out and server-side membership checks are implemented; targeted team invitations, roles, account recovery and verified organisation switching are implemented. Hosting remains unconfigured.

The root opens a welcome page in the existing Sampati visual identity. Enter workspace opens the register. Read workspace guide opens a standalone reading page at `#welcome/guide`, with Back to welcome and an explicit Enter workspace action. It does not mount the workspace, require sign-in or load aircraft data. The existing sidebar guide remains inside the entered workspace. The brand returns to Welcome, and native browser history and bookmarked workspace locations are supported.

## Capabilities and Constraints
Search and status filtering; row-specific errors; atomic imports; source and receipt timestamps; freshness separate from reported status; idempotent uploads; protection against late and conflicting reports. No combat allocation, weapons, military retasking, live tracking or airworthiness certification. Overview computes factual counts and attention rules; it does not use a trained model or external AI service.

Accounts use usernames and passwords, create a new empty organisation per account, and keep private records and import history separate from the demo. Sign-out revokes the session; importing records requires an owner/editor role. Session cookies and server-side membership select the workspace. No organisation can be joined merely by entering its name. Owners invite a specific existing account; invitations do not grant access until that account accepts. Recovery uses privately saved, one-time codes rather than email. Connected files wait in an incoming review queue; exports and reports use accepted records only.

## Evidence on Hand
RESOURCE_GUIDE.md, docs/research/datasets.md, docs/research/stack.md, and the user's approved implementation prompt. Example records must be clearly labelled fictional.

## Product Principles
- Preserve source truth and explain transformations.
- Preview before changing accepted records.
- Make errors actionable for a beginner.
- Show incomplete and old information honestly.

## Accessibility & Inclusion
Readable text, labelled controls, keyboard access, status text as well as colour, and responsive desktop/mobile use.

## Brand Commitments
The user selected SAMPATI · सम्पाति, inspired by Sampati's distant vision in the Ramayana. The current project descriptor is "Disaster Response & Relief Coordination", reflecting the user-approved civilian-welfare purpose. The implemented foundation remains the fictional aircraft-report workflow described above. Use a bilingual wordmark and the approved Sampati bird emblem. The approved palette is black and charcoal with crimson actions, warm ivory text, and a little saffron in the identity details.

The user subsequently requested a traditional folk drawing style, clarified that their supplied painting was a style reference, and selected the generated crimson-and-ivory soaring-bird composition. The current identity uses a matching illustrated bird emblem and a quiet header background. Public display lettering uses self-hosted, OFL-licensed Yatra One for the Latin wordmark and page headings; tables, controls and reading text retain DM Sans. The previously supplied personal-use font is retained privately and excluded from public source and build assets.

The user approved the current hand-painted bird emblem on 8 November 2026. Preserve its layered crimson/ivory feathers, fine brown ink contours, pigment texture and small gold details. The simplified modern logo was rejected; future refinements must retain the old folk-art style. The canonical asset is `frontend/public/artwork/sampati-emblem.png`, with its exact prompt and approval in `logo-provenance.json` beside it.

## Source Report Review

Report checks explain old/future source timestamps, unknown status, missing names and pending-file disagreements, with findings, evidence and next review steps. Filtering, source inspection, 20-row pagination and versioned filtered JSON export support review. A complete report does not establish aircraft condition, operational availability or flight clearance. Checking never rewrites source-reported status or confirms a pending import. The requirements and acceptance map is in docs/REQUIREMENTS.md.

## Open Decisions

No external AI provider or hosting target is selected.

## Independent, multi-source product

Sampati operates independently with its own records, contracts, access controls and review workflow. External analysis tools can complement it through optional adapters. The broader intake direction covers authorised databases, news/public reports, APIs, documents and forms, alongside implemented local CSV/Excel/JSON intake and human-entered requests. New connectors remain planned and must preserve provenance, dates, uncertainty and human review. See docs/DATA_SOURCES.md.

## Disaster-response direction

On 8 November 2026 the user defined Sampati as a **disaster-response and relief-coordination project**, starting with flood response. This is the governing direction for future development.

The proposed connection is: **Dated impact assessment → reviewed incident alert → confirmed local needs → current aircraft reports and operator checks → human-approved relief mission → mission updates and delivery confirmation.**

Assessment sources can supply dated spatial evidence, affected-area observations and uncertainty through a source-independent contract. Sampati would coordinate reviewed requests, resources and response records. Aircraft operators retain dispatch authority; reported availability and data freshness do not establish mission readiness. Post-event impact alerts and pre-event forecasting remain distinct capabilities.

The current application includes aircraft-report review, relief requests, flood-assessment intake/review, aid inventory, delivery tracking, structured relief intake automation and a relief handover overview. The shared incident contract connects reviewed evidence to human-entered needs, stock issues and source-backed arrival records. Source rules may create new drafts but never approve needs, move inventory or confirm an arrival. See docs/INCIDENTS.md, docs/INVENTORY.md, docs/DELIVERIES.md and docs/AUTOMATION.md. Live source adapters, transport/mission planning, authorised live aircraft positions, verified external context, civilian-user evaluation and hosted production remain development work.

Success should be evaluated through review accuracy, time to an approved response plan, delivery confirmation and follow-up of unmet needs. Social benefits and operational performance require civilian-user validation.
