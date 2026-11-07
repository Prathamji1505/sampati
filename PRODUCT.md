# Product
<!-- impeccable:product-schema 1 -->

## Platform
web

## Stack
User-approved direction: React, TypeScript, Vite, Python, FastAPI, PostgreSQL, SQLAlchemy, Psycopg and Alembic. Local Windows development, with public GitHub source preparation authorised for hackathon and startup-event review. Application hosting remains unconfigured.

## Users
A beginner building their first application, and a fictional civilian transport/disaster-relief coordinator reviewing uploaded aircraft reports.

## Product Purpose
Upload a fictional CSV or Excel file, validate it, preview changes, explicitly confirm, and see persistent source-reported aircraft records and import history. The user has approved proceeding with this workflow and refining the UI along the way.

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
The user selected SAMPATI · सम्पाति, inspired by Sampati's distant vision in the Ramayana. The project descriptor is "Air Operations & Resource Decision Support". This names the broader project; the implemented milestone remains the fictional aircraft-report workflow described above. Use a bilingual wordmark and the approved Sampati bird emblem. The approved palette is black and charcoal with crimson actions, warm ivory text, and a little saffron in the identity details.

The user subsequently requested a traditional folk drawing style, clarified that their supplied painting was a style reference, and selected the generated crimson-and-ivory soaring-bird composition. The current identity uses a matching illustrated bird emblem and a quiet header background. Public display lettering uses self-hosted, OFL-licensed Yatra One for the Latin wordmark and page headings; tables, controls and reading text retain DM Sans. The previously supplied personal-use font is retained privately and excluded from public source and build assets.

## Open Decisions
No external AI provider or hosting target is selected.
