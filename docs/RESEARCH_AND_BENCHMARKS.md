# Research and proposed benchmarks

Research date: **8 November 2026**. This is a repository research note, separate from the project PDF. It records primary-source findings and a proposed evaluation plan; it does not report a competitive trial or humanitarian impact study.

## Scope and conclusion

Sampati's current scope is the accountable coordination chain from dated incident evidence through human review, confirmed needs, inventory transactions and delivery confirmation. Structured intake automation produces reviewable drafts. Field evaluation, AI interpretation, live operational integrations and hosted deployment are outside the completed scope. See [roadmap](ROADMAP.md), [data-source rules](DATA_SOURCES.md) and [automation contract](AUTOMATION.md).

The most useful references address different parts of that chain: **Sahana Eden** for needs and disaster-management records; **IFRC GO** for disaster reporting and source visibility; **KoboToolbox** for structured field collection and form permissions; **OpenBoxes** for warehouse and shipment workflows. These are learning and integration candidates, not evidence that Sampati outperforms them. The inspected sources do not establish a shared end-to-end leaderboard for this task.

The recommendations and proposed targets below are Sampati design judgments. They are distinguished from the capabilities explicitly described in the linked projects.

## Verified alternatives and complements

Repository identities, default branches and license files were inspected directly. Features below describe documented or inspected capabilities, not independently tested usability, reliability or performance.

| Project and official repository | Verified capability relevant to Sampati | Most useful comparison or integration question | Limits of this comparison | Repository license |
| --- | --- | --- | --- | --- |
| [Sahana Eden](https://github.com/sahana/eden) | Needs/request, inventory and event/incident models exist in the current source. Its foundation describes configurable disaster and humanitarian management. | Study how needs, requests, warehouses and shipment records connect; compare a narrowly configured relief workflow with Sampati's reviewed chain. | Eden is a configurable platform with deployment-specific behavior. An installed template and version must be selected before any task comparison. Its older product overview is explicitly a legacy archive. | [MIT](https://github.com/sahana/eden/blob/44bfc3cf033b163b438f48378680c70cf997046d/LICENSE). |
| [IFRC GO API](https://github.com/IFRCGo/go-api) | Event and field-report models, explicit information sources and visibility classes; official API guidance covers disaster information access and analysis. | Preserve publisher/source distinctions and access rules in any future context adapter; keep reported impact separate from confirmed local requests. | GO has Movement-specific concepts and visibility rules. A public repository is not authorization to read restricted operational records. The reviewed source is the API component, not a warehouse comparison. | [MIT](https://github.com/IFRCGo/go-api/blob/8787cb0cc86820a2400ba7621d2171e3606902e0/LICENSE). |
| [KoboToolbox KPI](https://github.com/kobotoolbox/kpi) | Form/data management API, versioned assets and object permissions. Official documentation supports offline collection through web forms and KoboCollect. | Evaluate an authorized form-export/API adapter for structured needs intake; retain form version, submission reference and review status. | The KPI server is only part of the collection ecosystem. Offline collection support does not prove offline Sampati synchronization, inventory control or delivery confirmation. | [GNU AGPL v3](https://github.com/kobotoolbox/kpi/blob/fd19d1e7cd7c504f5b4c3a3c5cb43e5d6912231b/LICENSE). |
| [OpenBoxes](https://github.com/openboxes/openboxes) | Warehouse inventory, stock movements, requisitions, shipments and transaction history; source services implement these domains. | Study stock availability, request-to-shipment transitions, counts and transaction history before expanding Sampati's inventory model. | This is a broader warehouse system, with healthcare roots. Its presence in a supply chain does not establish household receipt or incident-evidence review. No equivalence to Sampati's accounting semantics was tested. | [EPL 1.0](https://github.com/openboxes/openboxes/blob/c44432c3d0ddb46d94fa393b76194f163044e9fe/LICENSE.md). |

Supporting primary descriptions: [current Eden page](https://sahanafoundation.org/eden/), [Eden legacy overview](https://sahanafoundation.org/products/eden/), [GO API overview](https://go-wiki.ifrc.org/en/go-api/api-overview), [KPI README](https://github.com/kobotoolbox/kpi/blob/fd19d1e7cd7c504f5b4c3a3c5cb43e5d6912231b/README.md), [Kobo collection documentation](https://support.kobotoolbox.org/data-collection-tools.html), [OpenBoxes features](https://docs.openboxes.com/en/stable/about/features/) and [OpenBoxes README](https://github.com/openboxes/openboxes/blob/c44432c3d0ddb46d94fa393b76194f163044e9fe/README.md).

### Source modules worth reading first

These paths were verified in the owning repositories. The links pin the inspected commit, so a later branch change does not silently change the reference.

| Priority | Source files/modules | What to learn; proposed Sampati application |
| --- | --- | --- |
| 1 | Eden [`modules/s3db/req.py`](https://github.com/sahana/eden/blob/44bfc3cf033b163b438f48378680c70cf997046d/modules/s3db/req.py), [`inv.py`](https://github.com/sahana/eden/blob/44bfc3cf033b163b438f48378680c70cf997046d/modules/s3db/inv.py), [`event.py`](https://github.com/sahana/eden/blob/44bfc3cf033b163b438f48378680c70cf997046d/modules/s3db/event.py) | Needs versus requests, fulfillment status, warehouse/shipment tracking, event/incident associations. Compare domain boundaries before adding entities; do not import a whole platform's complexity. |
| 2 | OpenBoxes [`StockMovementService.groovy`](https://github.com/openboxes/openboxes/blob/c44432c3d0ddb46d94fa393b76194f163044e9fe/grails-app/services/org/pih/warehouse/inventory/StockMovementService.groovy), [`InventoryService.groovy`](https://github.com/openboxes/openboxes/blob/c44432c3d0ddb46d94fa393b76194f163044e9fe/grails-app/services/org/pih/warehouse/inventory/InventoryService.groovy), [`ShipmentService.groovy`](https://github.com/openboxes/openboxes/blob/c44432c3d0ddb46d94fa393b76194f163044e9fe/grails-app/services/org/pih/warehouse/shipping/ShipmentService.groovy) | Availability checks, requisition/shipment transitions and stock transaction boundaries. Inspect the associated tests before adopting an algorithm or state transition. |
| 3 | GO [`api/models.py`](https://github.com/IFRCGo/go-api/blob/8787cb0cc86820a2400ba7621d2171e3606902e0/api/models.py), [`api/visibility_class.py`](https://github.com/IFRCGo/go-api/blob/8787cb0cc86820a2400ba7621d2171e3606902e0/api/visibility_class.py) | Event, FieldReport, Source and visibility representations. Design future adapters to retain conflicting source claims and obey visibility instead of flattening everything into one figure. |
| 4 | KPI [`kpi/models/asset.py`](https://github.com/kobotoolbox/kpi/blob/fd19d1e7cd7c504f5b4c3a3c5cb43e5d6912231b/kpi/models/asset.py), [`kpi/permissions.py`](https://github.com/kobotoolbox/kpi/blob/fd19d1e7cd7c504f5b4c3a3c5cb43e5d6912231b/kpi/permissions.py) | Form versions, deployment status and object-level access. Bind an intake mapping to the exact source form/version and permissions. |

Inspected branch snapshots: Eden `master @ 44bfc3cf033b163b438f48378680c70cf997046d`; GO API `develop @ 8787cb0cc86820a2400ba7621d2171e3606902e0`; KPI `main @ fd19d1e7cd7c504f5b4c3a3c5cb43e5d6912231b`; OpenBoxes `develop @ c44432c3d0ddb46d94fa393b76194f163044e9fe`. These are research snapshots, not deployment recommendations. KPI explicitly recommends a release branch for production in its [README](https://github.com/kobotoolbox/kpi/blob/fd19d1e7cd7c504f5b4c3a3c5cb43e5d6912231b/README.md).

### License and reuse boundary

Use these projects first as references and, where authorized, as separate integration endpoints. Before copying or modifying source, review the pinned license and file-specific notices. MIT projects require preservation of the stated notice; KPI's AGPL includes requirements concerning modified software offered over a network; OpenBoxes has EPL distribution/source obligations. An API adapter and code incorporation need separate license analysis. This note records licenses; it does not grant compatibility clearance for a particular combined product. The actual texts are linked in the table.

Software licenses also do not establish rights to operational data, uploaded documents, names, maps or logos. Check each data resource's terms and access rules separately.

## Humanitarian standards as evaluation anchors

The [2024 Core Humanitarian Standard](https://handbook.corehumanitarianstandard.org/en/chs/2024) supports evaluating timeliness and needs (commitment 2), coordination (6), learning from feedback (7) and responsible resource management (9). This motivates measurements of review, unmet-needs follow-up and stock accountability. The metrics below are **proposed software measures**, not official CHS indicators or proof of CHS conformity. Complaints, community participation and field outcomes extend beyond the present software.

The [Sphere Handbook](https://spherestandards.org/handbook/) provides technical standards, indicators and contextual guidance for humanitarian response. Resource quantities require competent local assessment and the appropriate sector standard. A count of affected people must not automatically become a relief quantity or delivery claim. Do not label a ledger test as Sphere compliance.

The [OCHA Data Responsibility Guidelines, January 2025](https://centre.humdata.org/data-responsibility-guidelines-2025/) address responsible management of personal and non-personal operational data, including sensitive contextual data. They justify reviewing access, purpose and disclosure risk in an evaluation. They are OCHA guidance, not a certification awarded to Sampati.

## Proposed benchmark tasks and metrics

**Status: design only; no runs or target achievements are claimed here.** Thresholds below are proposed local acceptance gates for a fixed test set. They are not universal humanitarian service levels.

| Task | Measure and denominator | Proposed gate or reporting rule |
| --- | --- | --- |
| Preserve evidence during intake | Complete records / eligible accepted records: source ID/reference, observed/published date, retrieved date when applicable, uncertainty and reviewer attribution. | 100% on the labeled fixture set; missing source fields must remain explicit or block acceptance according to the contract. |
| Distinguish evidence from confirmed need | Correct review decisions / independently labeled cases; also false acceptance count and quantity/unit transcription errors. | Report counts and error types. Proposed gate: zero unauthorized confirmations or invented quantities in the designed adversarial cases. |
| Handle replay and revision | Unexpected new accepted records or transactions after identical retry; overwritten accepted evidence after a revision. | Zero in the defined replay/revision suite. Report number and kind of attempts, including interrupted retries. |
| Keep automation within draft authority | Automated transitions into approval, stock issue, dispatch or arrival / attempted prohibited transitions. | Zero successes; verify each boundary separately. A draft's creation is not a reviewed need or an approved response. |
| Maintain exact stock accounting | Per item/store/unit: expected balance from the scripted transaction ledger minus reported balance; count negative balances and over-reservations. | Exact equality and zero forbidden outcomes in scripted sequential and concurrent cases. Compare physical counts separately. |
| Reconcile partial delivery and returns | Exact agreement with an independently prepared scenario oracle for issued, arrived, returned and outstanding quantities. | All scripted cases agree; partial arrival cannot mark the whole request fulfilled, and an undelivered return cannot count as arrival. |
| Make unmet needs visible | Eligible unmet requests correctly identified / all unmet requests in the oracle; false completed count. | 100% identification and zero false completions on the defined fixture set. Record overdue status against a fixed evaluation clock. |
| Protect organization and role boundaries | Successful unauthorized read/write/export attempts / attempted cases in a role-by-operation matrix. | Zero; record all attempted cases. A passing sample is limited evidence, not a comprehensive security assessment. |
| Complete coordinator work accurately | Correct completed tasks / assigned tasks; median and range of completion time, reviewer corrections and assistance needed. | First establish the spreadsheet/manual baseline. Compare the same scenarios and training; do not declare a speed improvement before measurement. |
| Explain audit history | Correct reconstruction of who changed what, why and when / assigned reconstruction tasks. | Report correctness, missing evidence and time; proposed fixture gate: complete links for every recorded acceptance, stock change and delivery correction. |

The domain oracles must follow [inventory rules](INVENTORY.md) and [delivery rules](DELIVERIES.md), including their distinctions between counts and ledger stock, issue and arrival, and corrections and deletion. Do not sum unlike items or units into a single fulfillment percentage.

Existing local checks can seed cases: [incident tests](../backend/tests/test_incidents.py), [relief tests](../backend/tests/test_relief.py), [inventory tests](../backend/tests/test_inventory.py), [delivery tests](../backend/tests/test_deliveries.py) and [automation tests](../backend/tests/test_automation.py). A green test suite demonstrates exercised software behavior; it does not measure civilian usability, physical stock or welfare outcomes.

### Reproducible evaluation protocol

1. Freeze the Sampati commit, database schema, fixture versions, permissions, time zone, evaluation clock and hardware/browser. Keep raw timings and task-level outcomes.
2. Prepare an independent answer key for evidence decisions, exact quantities and permitted transitions. For human review tasks, have two reviewers label cases and adjudicate disagreements before scoring.
3. Use the same fictional cases for the existing manual/spreadsheet workflow and Sampati. Give comparable training and alternate task order to reduce learning effects. Record sample size, prior experience and assisted tasks.
4. Include stale/unknown dates, contradictory updates, duplicate submissions, mixed units, insufficient stock, concurrent reservations, partial arrivals, returns and correction retries.
5. Publish denominators and failures with median/range timings. A small convenience sample supports formative feedback, not population-wide conclusions.
6. Run another product only if a specific deployment/version can perform the same task under comparable configuration. Record setup effort separately and mark inapplicable tasks as such. Do not turn documentation gaps into scored feature failures.

## Small public inputs for future fixtures

No external dataset was imported into Sampati during this research. The following are bounded **candidate inputs** and exercises, not existing supported connectors or operational ground truth.

| Public source | Small exercise | Rights, evidence and limitations |
| --- | --- | --- |
| HXL project's [`input-valid.csv`](https://github.com/HXLStandard/libhxl-python/blob/dev/tests/files/test_io/input-valid.csv), [`input-multiple-headers.csv`](https://github.com/HXLStandard/libhxl-python/blob/dev/tests/files/test_io/input-multiple-headers.csv), [`input-multiline.csv`](https://github.com/HXLStandard/libhxl-python/blob/dev/tests/files/test_io/input-multiline.csv) | These inspected tiny fixtures contain four example activity rows, two rows after extra headers, and one multiline description respectively. Build a future mapping/preview exercise for semantic headers, missing values, accented text and quoted newlines. Preserve raw headers and explicit mappings. | The repository's [license](https://github.com/HXLStandard/libhxl-python/blob/dev/LICENSE.md) is the Unlicense. These are parser fixtures, not verified aid activity. The examples themselves illustrate why labels must be reviewed; never infer confirmed need from a targeted-population column. Pin a commit before vendoring. |
| UN Bangladesh [Eastern Flash Flood Situation Report No. 01](https://bangladesh.un.org/en/277301-bangladesh-eastern-flash-flood-situation-report-no-01), published 26 August 2024 | A human reviewer identifies publisher, reporting period (21–25 August), publication date, affected area and attributed claims, then records what still needs local verification. Use the page as a reference and a separately written answer key. | A dated situation report is evidence about that time, not a current needs register or delivery receipt. Rights for the attached publication were not established here; link to it rather than bundling it by default. Avoid copying contact details into fixtures. |
| [geoBoundaries India ADM1 metadata](https://www.geoboundaries.org/api/current/gbOpen/IND/ADM1/) and [API documentation](https://www.geoboundaries.org/api.html) | Optional geography exercise: select a few names/IDs from the linked simplified geometry and test explicit location matching, unmatched names and boundary vintage display. Keep geometry separate from incident quantities. | The inspected response reports 36 units, represented year 2011, and original license CC BY 2.5 India; retain source attribution and exact vintage. Do not describe it as current official boundaries or live flood extent. Only metadata was inspected; geometry was not evaluated or imported. |
| [ReliefWeb reports API documentation](https://apidoc.reliefweb.int/read/resources/reports/) | Future metadata adapter exercise using a small, fixed set of report IDs: retain title, source, original/publication date, URL and retrieval time; replay twice and handle updates without silently replacing accepted evidence. | Current [access guidance](https://apidoc.reliefweb.int/) requires an approved `appname`. None was requested or used here. Original publishers can retain content rights. This is an API candidate, not a downloaded benchmark dataset. |
| Existing [fictional flood assessment](../examples/flood-assessment.json) and local transaction tests | Start the end-to-end benchmark with reproducible fictional evidence, requests, receipts, reservations, issues, partial arrivals and returns, plus an independently calculated answer key. | These are local synthetic exercises, not public disaster observations. Keep this provenance explicit. They are the appropriate basis for exact transaction assertions where public reports do not provide a full ledger. |

HXL is an interoperability option: its [official reference postcard](https://hxlstandard.org/wp-content/themes/hxl-wordpress-theme/assets/images/hxl-1_1final-postcard-en.pdf) describes semantic hashtags added to tabular data. It does not replace Sampati's purpose-specific contracts or human review.

HDX is useful for dataset discovery, but resource-level licensing, update dates and disclosure risks still need inspection. The attempted HDX India-boundary page returned HTTP 403 in this research, so this note does not certify that resource's content or terms. A first-party geoBoundaries metadata endpoint was inspectable instead.

## Measured results versus future claims

| Evidence class | What can be said now |
| --- | --- |
| Repository/source research | The linked repositories, selected source paths and license texts were inspected on the research date. |
| Sampati software verification | Consult [VERIFICATION.md](VERIFICATION.md) for executed checks and their scope. This research did not rerun those checks or add a benchmark result. |
| External product comparison | No installed head-to-head task, latency, load, usability or reliability comparison was run. |
| Proposed gates | Every target in the benchmark table is unmeasured in this note; an execution record must supply commit, fixtures, method and results. |
| Humanitarian effectiveness | No field trial, delivery impact, lives-saved estimate, adoption claim, CHS verification or Sphere compliance is established by this research. |

The next practical step is a small, fictional, independently scored coordinator exercise, followed by civilian-user feedback with an appropriate data and consent plan. Choose one optional structured intake adapter only after confirming the user's task, authorized source access and mapping responsibilities.

