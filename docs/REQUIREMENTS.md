# Civilian prototype requirements and acceptance criteria

The user selected civilian welfare as the current project objective on 8 November 2026. [The welfare charter](CIVILIAN_WELFARE_SCOPE.md) defines H01–H06: relief requests, aid inventory, delivery tracking, civilian context, evaluation and deployment. H01 is implemented; its contract is in [Relief requests](RELIEF_REQUESTS.md). H02–H06 remain planned. C01–C09 below track the implemented source-report foundation. C10 is deferred and is not a requirement for the next welfare MVP; a report-quality check must not be presented as aircraft readiness.

This checklist tracks what the local, fictional civilian learning prototype actually implements. It does not claim to solve military air operations. “Complete report” means that a source record passes the named data checks; it does not establish aircraft readiness, mechanical condition, crew suitability or flight clearance.

| ID | Requirement | Acceptance criterion | Position |
| --- | --- | --- | --- |
| C01 | Bring aircraft source reports together | CSV and .xlsx use the same six-field contract; one invalid row blocks confirmation; source times retain their timezone text. | Implemented and covered by import tests. |
| C02 | Make changes reviewable | Preview writes no aircraft/imports; confirmation commits records and before/after history atomically; repeated datasets are no-ops. | Implemented and covered by transaction/replay tests. |
| C03 | Keep organisations separate | Session membership scopes every data endpoint; viewers can read; owners/editors review; foreign IDs and guessed selectors grant no access. | Implemented and covered by isolation/role tests. |
| C04 | Receive changing files | A source key can submit only to its connection; changed files wait in an inbox; rotation/disable stops old credentials; accepted records change only after confirmation. | Implemented; real watcher/browser checks recorded in VERIFICATION.md. |
| C05 | Explain report quality | Each accepted record has named findings, reasons and next review steps for old/future times, unknown status, missing names and pending updates/conflicts; reported status remains unchanged. | Implemented in the Report checks milestone. |
| C06 | Record check context | Response/export records rule version, check time, workspace revision and freshness threshold; all time checks use one reference time. | Implemented; covered by boundary, export and browser checks. |
| C07 | Show pending evidence honestly | Compare only pending files in this organisation; equivalent reports add no finding; grouped counts remain exact while examples are bounded; accepted/rejected files stop appearing as pending evidence. | Implemented; covered by comparison/inbox tests. |
| C08 | Help people inspect findings | Search and result/finding filters, expanded explanations, source details, inbox navigation, 20-row pagination and filtered JSON export work in the existing interface. | Implemented; verification evidence in VERIFICATION.md. |
| C09 | Preserve local access and data | Password/session/recovery/team controls work; backup can be restored into a disposable database; demo data remains unchanged by read-only checks. | Implemented; local checks only, not production certification. |
| C10 | Calculate civilian operational availability | Requires a separately defined and validated civilian domain model, authoritative structured evidence and agreed review rules. Source-record quality alone must never be labelled availability. | Not implemented. |
| C11 | Add live civilian context | Each external feed needs provenance, licensing, timestamps, failure handling and a defined user purpose before integration. | Not configured; no live weather/airspace/aviation feeds. |
| C12 | Add validated predictive analytics | Requires a suitable authorised dataset, an explicit prediction target, a baseline, evaluation criteria and an honest uncertainty presentation. | No trained model or external AI provider configured. |
| C13 | Prepare production hosting | Define deployment/access requirements and verify HTTPS, secret handling, capacity, restore procedures and independent security checks for that environment. | Local prototype only; hosting remains unconfigured. |

## Flood-response connection

The local incident workflow now implements a versioned flood impact-observation contract, explicit JSON preview/recording, immutable accepted evidence, source/observation/generation/receipt dates, uncertainty, scoped review with reasons/version checks, and links from reviewed incidents to relief-request drafts. See [INCIDENTS.md](INCIDENTS.md) for acceptance rules and remaining integration limits. A live external assessment connection, forecasting, mission approval, inventory and confirmed delivery are not implemented by this contract.

## Scope of the current checks

Checks are deterministic comparisons of source data. Free-text notes are not interpreted as maintenance evidence. The program does not select aircraft, assign crews, plan flights, recommend dispatch, optimise military resources or retask operations. No model learns from these checks, and no status is automatically rewritten.

Visible-tab refresh is every 30 seconds; the optional watcher polls a file every 15 seconds. These are configured polling intervals, not guarantees of real-time end-to-end delivery. Human acceptance remains a separate step.

Verification belongs to a specific build and tested scenario. Use docs/VERIFICATION.md for executed evidence rather than treating this table as proof of production readiness or full problem-statement completion.
