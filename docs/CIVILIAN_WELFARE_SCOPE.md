# Sampati: civilian relief and logistics coordination

Civilian-welfare direction selected by the user on 8 November 2026. The initial disaster-relief workflow below is the proposed implementation scope, to be validated with intended users.

## Purpose

Help civilian relief organisations keep requests, aid supplies and delivery records understandable, current and traceable. The first intended use case is disaster-relief logistics: a coordinator receives requests for food, water, medicines or shelter supplies and needs a reviewed record of what is requested, what stock is reported and what has actually been delivered.

The project descriptor is **Disaster Response & Relief Coordination**. The Sampati name, bilingual identity and visual system remain.

## Current product

The working application includes dated flood-assessment JSON intake, human incident review and links to relief-request drafts, described in INCIDENTS.md. Organisation-scoped relief requests support draft creation, review, correction, cancellation and an audit history. It also retains the fictional civilian aircraft source-report foundation: imports, human review, a register, report checks, source connections, accounts, team roles, exports and local backups. Aid inventory has a backend/API milestone; its interface remains in progress. Delivery management remains planned. See RELIEF_REQUESTS.md for the H01 contract and VERIFICATION.md for executed evidence.

The project is now evaluated against civilian welfare needs. Completing the original military air-operations problem statement is no longer the project objective. Historical research and verification remain records of what was considered and built; this charter sets the current scope.

## Intended users and workflows

- A civilian relief coordinator records an organisation's request and reviews its details.
- An inventory custodian records incoming, reserved, issued and returned aid supplies with a traceable stock balance.
- A delivery coordinator records approved shipments and delivery confirmations against relief requests.
- A reviewer checks conflicting or outdated source data and follows its audit history.

These are intended users to validate with interviews and fictional walkthroughs. No organisation, partnership, operational adoption or measured welfare outcome is claimed.

## Build order and acceptance criteria

| Milestone | What will be built | Acceptance criteria |
| --- | --- | --- |
| H01: Relief requests | Organisation-scoped requests with a requesting organisation, locality, supply category, quantity/unit, needed-by time, source reference and reviewed status. | Owners/editors create and review; viewers read; invalid quantities/timezones are rejected; status changes are audited; another organisation cannot read or change a request; duplicate external references are handled explicitly. |
| H02: Aid inventory | Supply items, storage locations and append-only stock movements, keeping reported balances separate from confirmed movements. | Quantities have explicit units; no silent unit conversion; movements are attributable; reservations and issues cannot produce a negative balance; concurrent updates cannot issue the same stock twice. |
| H03: Delivery tracking | Human-approved shipment records linking requests and inventory issues, with partial-delivery and confirmation history. | Delivered quantities cannot silently exceed a request's remaining quantity; partial fulfilment remains visible; cancellation/return handling is explicit; a delivery is recorded only with a source confirmation. |
| H04: Civilian context | Useful weather or public disaster information with source, observation time, receipt time and a clear failure state. | Select and verify a provider and its terms before integration; old/unavailable information is labelled; cached observations are not presented as current; context does not grant flight clearance. |
| H05: Evaluation | Reproducible fictional workflows and an authorised civilian-user pilot plan. | Measure duplicate detection, review task completion, stock discrepancies and fulfilment-record accuracy against stated baselines; report actual results and limits; do not infer lives saved from software tests. |
| H06: Deployment | A reviewable hosting plan, protected secrets, HTTPS/access controls, backups and restore checks for a selected environment. | Build and migration checks pass; organisation isolation is tested; recovery is rehearsed; target, access and cost decisions are recorded before publication. |

**H01 is implemented** as the reviewed request register described in RELIEF_REQUESTS.md. H02–H06 remain planned; the next module is **H02: Aid inventory**. Changing this charter alone does not implement those later capabilities.

## Data and review rules

Use fictional records for development. A first request model should describe supplies, organisations and delivery localities rather than individual patients or beneficiaries. It does not need patient histories, personal medical details or individual beneficiary identifiers. Real records require an authorised organisation and a defined access/retention policy.

Quantities, units, source timestamps, authorship and review state must remain explicit. Receiving a report does not automatically approve a shipment. An actor's role and organisation membership are checked on the server. Corrections should be traceable rather than silently rewriting history.

The existing report checks continue to describe data quality. They do not establish aircraft condition or operational availability. No military planning, combat-resource allocation or military retasking is part of this welfare product. The scope change does not add any prediction, optimisation, live feed or automatic dispatch capability by itself.

## Success for the next demo

A reviewer can create a fictional request for a clearly stated quantity of relief supplies, find it in the correct organisation, change its review status with an audit trail and show that another organisation has no access. Later milestones can connect that request to inventory and confirmed deliveries. Each demonstrated capability must have its own executed evidence in VERIFICATION.md.

## Disaster-response direction

On 8 November 2026 the user defined Sampati as a **disaster-response and relief-coordination project**, starting with flood response. This is the governing direction for future development.

The proposed connection is: **Dated impact assessment → reviewed incident alert → confirmed local needs → current aircraft reports and operator checks → human-approved relief mission → mission updates and delivery confirmation.**

Assessment sources can supply dated spatial evidence, affected-area observations and uncertainty through a source-independent contract. Sampati would coordinate reviewed requests, resources and response records. Aircraft operators retain dispatch authority; reported availability and data freshness do not establish mission readiness. Post-event impact alerts and pre-event forecasting remain distinct capabilities.

The current foundation includes aircraft-report review, relief requests and local flood-assessment intake/review. The shared `sampati.incident.v1` contract and reviewed-incident linkage to human-entered relief drafts are implemented; see [INCIDENTS.md](INCIDENTS.md). A live assessment-source connector, inventory, mission assignment, delivery tracking and authorised live aircraft positions remain development work. H02/H03 supply and delivery milestones remain next dependencies.

Success should be evaluated through review accuracy, time to an approved response plan, delivery confirmation and follow-up of unmet needs. Social benefits and operational performance require civilian-user validation.
