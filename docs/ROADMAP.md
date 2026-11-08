# Sampati: disaster-response roadmap

Direction reviewed 8 November 2026. Governing scope: [civilian-welfare charter](CIVILIAN_WELFARE_SCOPE.md).

## The goal

Help civilian coordinators turn dated flood-impact evidence into reviewed needs, accountable resource records and confirmed relief deliveries. Sampati coordinates the review and response records; aircraft operators retain dispatch authority.

Sampati is independent of any particular assessment product. Local file intake is already supported; future integrations are optional adapters around Sampati's own contract. Choose sources to fit the coordinator's task rather than building the roadmap around a reference project.

The multi-source direction includes authorised databases, news/public reports, APIs, assessment tools, documents and forms. These adapters are planned; they must preserve provenance and route extracted information through review. [Supported inputs and adapter rules](DATA_SOURCES.md).

The intended end-to-end path is:

**Impact evidence → incident review → confirmed local needs → inventory and resource checks → human-approved response → delivery confirmation → unmet-needs follow-up.**

## What is implemented

| Foundation | Current capability | Evidence |
| --- | --- | --- |
| Source reports | Reviewed CSV/Excel imports, aircraft register, source quality checks, scoped connections, history and exports. | [Verification](VERIFICATION.md), import/account/quality tests. |
| Relief requests · H01 | Organisation-scoped drafts, exact quantities/units, deadlines, corrections, review/cancellation and attributed audit history. | [Request contract](RELIEF_REQUESTS.md), relief tests and browser journey. |
| Flood incidents | Versioned JSON preview/intake, immutable accepted evidence, dated uncertainty, reasoned review and links to human-entered relief drafts. | [Incident contract](INCIDENTS.md), incident tests and browser journey. |
| Aid inventory · H02 | Fixed item/unit and storage catalogs, exact protected balances, separate counts, request-linked reservations/issues/releases/returns and history. | [Inventory rules](INVENTORY.md), 33 inventory checks and real-browser journey. |
| Delivery tracking · H03 | Issue-linked reviewed tracking drafts, dispatch evidence, partial/full arrivals, atomic undelivered returns, corrections and request follow-up. | [Delivery rules](DELIVERIES.md), delivery tests and real-browser journey. |
| Relief intake · A01 | Scoped CSV/JSON sources, manual review or owner-controlled automatic new drafts, conflict/invalid-file pauses, immutable evidence and request provenance. | [Automation rules](AUTOMATION.md), backend, real watcher and browser journeys. |
| Handover overview | Review queues, earliest unmet reviewed needs, per-request units and dated export. | Arrival-derived remainder and isolation checks; real-browser export/navigation. |
| Shared controls | Accounts, membership roles, version guards, migrations, local backup and restore rehearsal. | [Architecture](ARCHITECTURE.md), [verification](VERIFICATION.md). |

Incident intake is a working local integration boundary. Connecting any live assessment producer is a separate, optional integration task. An impact assessment does not automatically determine supply quantities or approve a mission.

## Build order

| Priority | Milestone | Completion gate |
| --- | --- | --- |
| **Completed locally: H02** | Aid inventory API, migration and interface: items, units, stores, receipts, reservations, issues, releases, returns and separate count reports. | 142-test full suite and inventory browser journey passed, including concurrent issues, shared request limits and safe retries. |
| **Completed locally: H03** | Delivery tracking links reviewed requests and inventory issues to source-backed arrival/return evidence. | 173-test full suite and real-browser workflow passed, including partial fulfilment, atomic return retries, corrections and remaining needs. |
| **Completed locally: A01** | Changing relief-file intake and trusted-source draft automation; relief handover overview; compiled local launcher. | See current release evidence in VERIFICATION.md. |
| **Parallel integration** | Optional adapters for assessment sources using `sampati.incident.v1`. | Agree producer/consumer responsibilities, access, provenance, uncertainty, replay behavior and failure handling; verify with an actual producer fixture. |
| **Next: H04** | Civilian context for a defined coordinator task. | Verify source terms, timestamps, stale-data behavior and the value of each feed. |
| **H05** | Civilian-user evaluation. | Measure review accuracy, task completion, stock discrepancies and fulfilment-record accuracy against stated baselines. |
| **H06** | Hosted deployment. | Selected target, HTTPS, protected secrets, organisation isolation, capacity and rehearsed off-device recovery. |

Mission coordination depends on verified needs, resources and accountable approval. Live aircraft positions need an authorised source and a defined purpose. Neither is established by a source report saying an aircraft is available.

## What to demonstrate now

1. Preview and record a fictional flood assessment; inspect its dates, source and uncertainty.
2. Review the incident with a reason.
3. Open a linked relief draft and enter the locally confirmed quantity and unit.
4. Submit/review the request and inspect its history.
5. Open Aid inventory, add a fictional item/store, record a receipt, then reserve the reviewed request and record a partial issue/return. Contrast a count report with ledger stock.
6. Create/approve a shipment draft from an issue, record actual dispatch evidence, confirm partial arrivals and record undelivered returns. Inspect exact remaining needs in Request follow-up.
7. Show aircraft reports as supporting source information. Explain verified context, user evaluation and deployment as the next milestones; an issue alone does not prove arrival.

## Validation and business direction

Intended users are civilian relief coordinators, inventory custodians and delivery-record reviewers. Pilot interviews should establish whether these workflows match their actual responsibilities and reporting formats.

Evaluate review accuracy, time to an approved response plan, delivery confirmation and follow-up of unmet needs. Operational and welfare outcomes require field validation. An organisation subscription and onboarding/connector support remain commercial hypotheses; pricing, demand and adoption are unvalidated.

## Publication boundaries

Publish fictional examples, contracts, source code and executed verification. Keep credentials, local databases, private uploads and scratch outputs out of Git. Describe planned integrations and social outcomes separately from implemented software. Historical milestones remain preserved in [PROJECT_PLAN.md](../PROJECT_PLAN.md).


Inventory and delivery limits: [INVENTORY.md](INVENTORY.md), [DELIVERIES.md](DELIVERIES.md). Local tests verify software behavior; source/physical accuracy and field outcomes require civilian-user validation.
