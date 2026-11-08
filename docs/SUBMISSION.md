# Sampati — submission brief

**Project:** SAMPATI · सम्पाति — Disaster Response & Relief Coordination<br>
**Creator:** [Pratham Sengar](https://github.com/Prathamji1505)<br>
**Stage:** working local prototype; fictional civilian data<br>
**Repository:** [Prathamji1505/sampati](https://github.com/Prathamji1505/sampati)

## The problem

Flood-response coordinators need to connect dated impact evidence, locally confirmed supply needs, resource reports and delivery records. Sampati's goal is to make that chain reviewable and traceable. The working prototype implements incident intake/review and relief-request recording, corrections, cancellation and history; inventory and delivery tracking are the next dependencies. See the [roadmap](ROADMAP.md) and [welfare charter](CIVILIAN_WELFARE_SCOPE.md) for acceptance gates.

Aircraft reports can arrive in separate files with inconsistent fields, duplicated batches and out-of-order timestamps. A list of statuses alone makes it difficult to see which source supplied a value, when it was reported and how the register changed.

This is the problem explored by the prototype. User demand, adoption and time savings have not yet been measured.

## The implemented solution

The disaster-relief workflow also accepts dated flood assessments through a versioned JSON contract, retains source evidence and uncertainty, records reasoned human review and opens linked relief-request drafts. Quantities are entered by a person. This local workflow prepares an integration boundary; it does not connect to a live SATQueryAI service. Inventory, approved missions and delivery confirmations remain future milestones.

Sampati validates CSV and Excel reports, shows proposed changes, and requires explicit confirmation before updating accepted records. Search and freshness filters help reviewers examine the current register; audit history preserves the change path. Organisation memberships and scoped file connections support separate workspaces and an incoming review queue.

## What makes the implementation interesting

- **Review is part of ingestion:** signed, account-bound and revision-bound previews connect the displayed changes to the confirmation transaction.
- **Source truth stays visible:** status, source timestamp, receipt time and freshness are separate fields and concepts.
- **Late and repeated data are handled explicitly:** older/conflicting reports are blocked; equivalent replays do not create duplicate imports.
- **Connected sources have limited authority:** an ingestion key can submit a file, while approval stays with an authorised human.
- **Identity has a purpose:** the Sampati name and folk-style bird artwork frame a source-first workspace in a bilingual Indian visual identity.

These describe implementation choices, rather than claims of market uniqueness or competitive superiority.

## Reviewer path

Follow the [three-minute demo](DEMO.md), inspect the [architecture](ARCHITECTURE.md) and read the actual [verification evidence](VERIFICATION.md). The README screenshots show the working local application with fictional records. There is no public hosted demo at this stage.

## Stack

React 19, TypeScript and Vite; Python 3.12, FastAPI, SQLAlchemy, Psycopg and Alembic; PostgreSQL. CSV/Excel parsing and the source watcher run locally. No AI API or aviation-feed subscription is required.

## Next validation and development

Interview authorised civilian coordinators and test the review workflow with suitable non-sensitive sample reports. Measure task completion, error detection and review time before claiming operational improvements. A hosted deployment, email recovery, off-device backups and further accessibility/security work are separate milestones.

## Event-specific details

This repository was prepared before any particular event was named in this submission brief. It does not claim that all implementation was created during a future hackathon window. Check the event's rules on prior work and record the actual event dates, team, baseline commit and event-specific contributions in your submission. Existing Git history should remain authentic.

## Attribution and limitations

Source code is MIT-licensed. [Third-party notices](../THIRD_PARTY_NOTICES.md) disclose package/font provenance, ImageGen artwork, Codex assistance and repository-presentation references. The application does not perform trained inference, live tracking, dispatch or airworthiness certification. Local software tests establish behavior within their recorded scope; they are not aviation or production certification.
