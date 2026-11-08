# Sampati: disaster-response roadmap

Direction reviewed 8 November 2026. Governing scope: [civilian-welfare charter](CIVILIAN_WELFARE_SCOPE.md).

## The goal

Help civilian coordinators turn dated flood-impact evidence into reviewed needs, accountable resource records and confirmed relief deliveries. Sampati coordinates the review and response records; aircraft operators retain dispatch authority.

The intended end-to-end path is:

**Impact evidence → incident review → confirmed local needs → inventory and resource checks → human-approved response → delivery confirmation → unmet-needs follow-up.**

## What is implemented

| Foundation | Current capability | Evidence |
| --- | --- | --- |
| Source reports | Reviewed CSV/Excel imports, aircraft register, source quality checks, scoped connections, history and exports. | [Verification](VERIFICATION.md), import/account/quality tests. |
| Relief requests · H01 | Organisation-scoped drafts, exact quantities/units, deadlines, corrections, review/cancellation and attributed audit history. | [Request contract](RELIEF_REQUESTS.md), relief tests and browser journey. |
| Flood incidents | Versioned JSON preview/intake, immutable accepted evidence, dated uncertainty, reasoned review and links to human-entered relief drafts. | [Incident contract](INCIDENTS.md), incident tests and browser journey. |
| Shared controls | Accounts, membership roles, version guards, migrations, local backup and restore rehearsal. | [Architecture](ARCHITECTURE.md), [verification](VERIFICATION.md). |

Incident intake is a working local integration boundary. A live SATQueryAI producer is a separate next step. An impact assessment does not automatically determine supply quantities or approve a mission.

## Build order

| Priority | Milestone | Completion gate |
| --- | --- | --- |
| **In progress: H02** | Backend APIs and migration are implemented; interface/browser verification remain. Aid inventory: items, units, storage locations, receipts, reservations, issues and returns. | Attributable stock movements; explicit units; no negative balance or double issue under concurrent writes. |
| **Then: H03** | Delivery tracking linking reviewed requests and inventory issues. | Human-approved records, partial fulfilment, explicit cancellation/returns and source-backed delivery confirmation. |
| **Parallel integration** | Live SATQueryAI adapter using `sampati.incident.v1`. | Agree producer/consumer responsibilities, access, provenance, uncertainty, replay behavior and failure handling; verify with an actual producer fixture. |
| **H04** | Civilian context for a defined coordinator task. | Verify source terms, timestamps, stale-data behavior and the value of each feed. |
| **H05** | Civilian-user evaluation. | Measure review accuracy, task completion, stock discrepancies and fulfilment-record accuracy against stated baselines. |
| **H06** | Hosted deployment. | Selected target, HTTPS, protected secrets, organisation isolation, capacity and rehearsed off-device recovery. |

Mission coordination depends on verified needs, resources and accountable approval. Live aircraft positions need an authorised source and a defined purpose. Neither is established by a source report saying an aircraft is available.

## What to demonstrate now

1. Preview and record a fictional flood assessment; inspect its dates, source and uncertainty.
2. Review the incident with a reason.
3. Open a linked relief draft and enter the locally confirmed quantity and unit.
4. Submit/review the request and inspect its history.
5. Show aircraft reports as supporting source information. Explain inventory and delivery tracking as the next milestones.

## Validation and business direction

Intended users are civilian relief coordinators, inventory custodians and delivery-record reviewers. Pilot interviews should establish whether these workflows match their actual responsibilities and reporting formats.

Evaluate review accuracy, time to an approved response plan, delivery confirmation and follow-up of unmet needs. Operational and welfare outcomes require field validation. An organisation subscription and onboarding/connector support remain commercial hypotheses; pricing, demand and adoption are unvalidated.

## Publication boundaries

Publish fictional examples, contracts, source code and executed verification. Keep credentials, local databases, private uploads and scratch outputs out of Git. Describe planned integrations and social outcomes separately from implemented software. Historical milestones remain preserved in [PROJECT_PLAN.md](../PROJECT_PLAN.md).


Inventory backend details: [INVENTORY.md](INVENTORY.md). This increment does not mark the complete H02 user workflow finished.
