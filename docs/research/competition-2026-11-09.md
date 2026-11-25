# SAMPATI: competitors, alternatives and defensible positioning

Research date and retrieval date for all external sources: **9 November 2026**. Scope: seven relevant first-party product or provider ecosystems, assessed against SAMPATI's current local civilian flood-relief workflow. Official documentation and provider websites only support the capability claims below. This is a documentation review, not a hands-on procurement evaluation, security audit, feature-completeness test or evidence of customer preference.

## Decision

SAMPATI enters an established category. Sahana already describes disaster assessments, requests and relief logistics; ShaRe explicitly mentions delivery/return monitoring. Open mSupply documents reservations, requested/issued quantities and delivery verification. Logistics Cluster's RITA documents actual stock and cargo operations. Human review, audit trails, maps, offline forms and connecting requests with stock are therefore **not defensible exclusive inventions**. See S01–S03, M01–M04 and L02–L04.

A narrower positioning is defensible as a description of this implementation:

> **SAMPATI is a local flood-relief coordination prototype that connects reviewed evidence and exact-unit needs to recorded stock, shipment evidence and follow-up based on confirmed arrivals.**

Its proposed audience is a small India-focused civilian relief team exploring an accountable handover workflow. That audience fit, ease of adoption and any advantage over a configured incumbent are **hypotheses to validate**, not demonstrated findings. India focus describes intended context; this research does not establish exclusive Indian requirements, existing Indian customers, local-language readiness or regulatory certification.

## SAMPATI baseline and comparison rules

**B01 — Current project scope.** [Release](../RELEASE.md), [relief requests](../RELIEF_REQUESTS.md) and [inventory](../INVENTORY.md) describe a local application using fictional examples: dated assessment evidence and human review; requests with exact quantities, units and deadlines; protected stock balances with separate count reports; shipment review, dispatch, partial/full arrival, undelivered returns and corrections; organisation-scoped access and histories. The release distinguishes CSV/JSON relief intake from supporting CSV/Excel report intake. Do not imply arbitrary Excel relief intake or a ready-made connector to every comparison product.

**B02 — Boundaries.** The same release explicitly leaves public hosting, live external adapters, AI inference, transport optimisation and field evaluation outside the current release. Inventory docs exclude lot/batch/expiry/temperature management and purchase orders. No validated customers, operational impact, offline field synchronisation, beneficiary CRM or finance capability is established by this scope. Local operation on one computer is not equivalent to disconnected multi-device field synchronisation.

**B03 — Meaning of review.** Owners/editors may review their own relief requests. Use **human-reviewed**, not independently approved or separation of duties. Recorded arrival evidence is supplied by people/sources; it is not independent proof of physical delivery. These are project documentation claims, not a fresh code audit performed for this report.

**Classification.** A *direct workflow alternative* substantially overlaps relief requests, stock or dispatch. An *adjacent alternative* solves assessment, information sharing or incident coordination and may participate in a composed solution. A configurable platform can support workflows beyond its documented templates. **Not established** means this review did not verify the exact behavior; it never means the product cannot implement it. No capability is marked absent solely because a marketing page omits it.

## Slide-ready comparison

Keep the IDs in speaker notes; each resolves to exact supporting URLs below. “Stronger” identifies documented breadth SAMPATI currently does not implement, not measured product superiority.

| Alternative | Relationship | Established overlap | Broader documented capability | Fair SAMPATI positioning |
| --- | --- | --- | --- | --- |
| **Sahana EDEN / ShaRe** | Direct; version-sensitive | Assessments, requests, warehouses/shipments in legacy Eden; ShaRe requests, commitments and delivery/return (S01–S03) | Current EDEN beneficiary case management, multi-tenancy, distributed roles | Focused local flood-relief demonstration; do not claim an original end-to-end category |
| **KoboToolbox** | Adjacent: assessment collection/review | Offline forms; approved/on-hold/not-approved review; granular project sharing (K01–K03) | Field collection and configurable surveys | A defined stock-to-arrival workflow; exact equivalent in Kobo is not established |
| **ODK** | Adjacent, configurable workflow alternative | Offline forms, review states/history, approval-linked Entities and follow-up (O01–O04) | Offline longitudinal workflows; managed cloud and India storage option | A prescribed relief workflow; do not reduce ODK to one-off surveys |
| **Open mSupply** | Direct for inventory/distribution | Requests, stock allocation, shipments, delivered/verified states and returns (M01–M04) | Batch/expiry handling, medical supply chains and offline-first operations | Flood evidence and remaining-needs review; no claim to deeper inventory |
| **Logistics Cluster: LogIE + RITA** | LogIE adjacent; RITA direct cargo overlap | LogIE validated logistics information; RITA stock, dispatch, receipt and release evidence (L01–L04) | Shared logistics picture and operational cargo/journey workflows | Local team workflow; these two tools are distinct and are not a SAMPATI integration |
| **ArcGIS emergency solutions** | Adjacent platform and composed alternative | Damage reporting, assessment management, incident dashboards and public information (A01–A03) | GIS analysis, public maps and offline field surveys | A narrow relief ledger/handover demonstration; exact stock-arrival equivalent not assessed |
| **D4H** | Adjacent incident coordination; configurable overlap | Forms, tasks, status boards, approvals and source/time/version histories (D01–D03) | Incident collaboration, cloud service, intermittent offline work | Relief-specific quantity and arrival semantics; equivalent configuration not established |

## Evidence and interpretation by alternative

### 1. Sahana: EDEN, legacy Eden and ShaRe

**S01 — Current EDEN is not interchangeable with old Eden documentation.** The Foundation says Eden ASP was forked in 2021 and became EDEN's main branch in May 2025; the previous codebase is archived as EDEN Legacy. Current EDEN concentrates on assistance to individual beneficiaries/case management, with multi-tenancy and distributed, multi-role processes. It is a foundation for professional implementers building specific applications, rather than intended for self-deployment by user organisations. The public code uses MIT licensing. Short source quotation: **“not intended for self-deployment by user organizations”**. [Sahana: current Eden](https://sahanafoundation.org/eden/)

**S02 — Legacy Eden has genuine relief-logistics overlap.** The Foundation's explicitly labelled legacy page describes assessments, organisations, resources, inventory and sending/receiving shipments. Its official legacy logistics documentation identifies Supply, Inventory, Requests and Asset modules, including item catalogues/packs, warehouses, shipments and requests/commitments. Short source quotation: **“manage requests and commitments of items”**. [Foundation legacy product description](https://sahanafoundation.org/products/eden/), [legacy logistics developer documentation](https://eden-legacy.sahanafoundation.org/wiki/DeveloperGuidelines/Logistics)

**S03 — ShaRe specifically overlaps the proposed relief loop.** The Foundation's ShaRe page describes relief requests, suppliers/donors, dispatch of goods/services, logistics, authorised commitments, delivery/return monitoring, situation reports and geographic aggregation. Short source quotation: **“monitor the delivery/return”**. [Sahana Relief and Rehabilitation Hub](https://sahanafoundation.org/share/)

**Interpretation.** Treat Sahana as a serious direct design alternative and a build-versus-configure investigation. Current EDEN's documented case-management depth exceeds SAMPATI's present remit. Do not combine all legacy and current modules into a claim that a single turnkey current EDEN installation provides every listed feature. ShaRe's detailed current deployment path, support terms, exact unit/return arithmetic, independent approvals and net-confirmed-arrival need calculation are **not established** by these pages. Its high-level overlap is enough to invalidate a claim that SAMPATI uniquely connects requests and delivery/returns.

### 2. KoboToolbox

**K01 — Field collection supports disconnection.** Kobo documents browser web forms and the Android KoboCollect app, both supporting offline collection. Forms must be prepared/downloaded while connected; browser responses upload on reconnection and KoboCollect can send later. Short source quotation: **“Both methods support offline data collection.”** [Data collection methods](https://support.kobotoolbox.org/data-collection-tools.html)

**K02 — Human review is explicit.** The data table supports Approved, Not approved and On hold states for individual or bulk submissions. Validate submissions can be granted separately from Edit submissions. Short source quotation: **“Additional verification or follow-up is needed”**. [Viewing and validating data](https://support.kobotoolbox.org/viewing_validating_data.html)

**K03 — Access is more granular than a shared survey link.** Official documentation covers project-level user access, separate view/add/edit/validate capabilities and row-level sharing. [Sharing projects with user-level permissions](https://support.kobotoolbox.org/managing_permissions.html)

**K04 — Hosting and plan limits matter.** The account guide, updated 6 November 2026, documents public servers, a free Community Plan and upgrades; for-profit pricing requires contact. Current usage documentation, updated 6 October 2026, describes submission/storage quotas and blocking new submissions when those quotas are exceeded. Locally collected offline submissions remain on devices until uploads can resume. [Creating an account](https://support.kobotoolbox.org/creating_account.html), [account usage limits](https://support.kobotoolbox.org/account_usage_limits.html)

**Interpretation.** Kobo is a credible assessment-intake/review alternative and potential future source, especially where disconnected enumerators matter. This review did **not** establish a preconfigured transactional relief stock ledger, shipment/return accounting or arrival-adjusted outstanding-needs workflow; do not claim those are impossible through configuration or integration. SAMPATI's CSV/JSON intake is not a live Kobo connector. Kobo's field-collection capability is documented; faster SAMPATI adoption is not.

### 3. ODK

**O01 — ODK supplies offline collection plus managed or self-managed deployment.** Its official site documents advanced forms with GPS/media/logic, disconnected collection and later synchronisation, download/analysis integrations and an open-source self-hosting route. ODK Cloud is a managed offering; the provider lists India among available data-storage regions. Short source quotation: **“Works online and offline”**. [ODK product, pricing and FAQ](https://getodk.org/)

**O02 — Central already has review and provenance.** Central supports submission review states, reviewer notes, activity history and edit differences. Review states do not inherently enforce downstream actions: rejected records remain in exports unless filtered. Short source quotation: **“they don't cause anything to happen automatically”**. [Managing submissions](https://docs.getodk.org/central-submissions/)

**O03 — Entities provide persistent follow-up workflows.** The official Entities guide documents registration automatically or after manager approval, multiple follow-up forms, offline creation/updates in supported Collect versions, bulk CSV creation and Entity history/conflict information. This is substantially more than independent one-time survey rows. Short source quotation: **“Use or update Entities in one or more follow-up Forms”**. [Managing Entities](https://docs.getodk.org/central-entities/)

**O04 — Permissions are scoped.** Central documents system administrators, project managers/viewers/data collectors and form-specific App User access. Project roles and API capabilities should not be conflated with SAMPATI's exact organisation-membership model. [Managing users](https://docs.getodk.org/central-users/)

**Interpretation.** ODK is a strong collection and configurable follow-up alternative. The stock constraints, movement invariants and exact net-arrival-to-request calculation required here were **not established as a packaged ODK relief workflow**. They may be implemented by form design and external software; that would require an implementation comparison. Offline longitudinal data capture and supported cloud operations are concrete areas where ODK's documented scope exceeds SAMPATI's.

### 4. Open mSupply

**M01 — Requisitions already track incomplete supply.** Open mSupply's documentation distinguishes requested, supply, issued and remaining quantities, explicitly calculating remaining as supply minus issued. Linked outbound shipments can be created repeatedly for remaining quantities. Units/packs and customer stock context are documented. Short source quotation: **“Supply - Issued”**. [Requisitions](https://docs.msupply.foundation/docs/distribution/requisitions/)

**M02 — Shipment state is different from delivery verification.** Its outbound guide documents New, Allocated, Picked, Shipped, Delivered and Verified states. Allocation reserves stock; picking removes it from inventory; delivery adds it to the recipient inventory; verification records the customer's quantity check. Batch allocation, expiry-based selection, pack sizes, placeholders and shipment history are documented. Short source quotation: **“Your customer has verified the quantity of the shipment.”** [Outbound shipments](https://docs.msupply.foundation/docs/distribution/outbound-shipments/outbound-shipments/)

**M03 — Returns and receipt are separate workflows.** The official customer-return guide documents creating returns, relating them to shipments and entering returned quantities. The inbound guide documents receiving quantities, batches, expiry dates and pricing fields. This establishes substantial movement-accounting overlap; it does not establish that every return has SAMPATI's particular meaning of undelivered stock linked to an original issue. [Customer returns](https://docs.msupply.foundation/docs/distribution/customer-returns/), [inbound shipments](https://docs.msupply.foundation/docs/replenishment/inbound-shipments/inbound-shipments/)

**M04 — It is offline-first.** Remote sites can operate without continuous internet and periodically synchronise with a central server. Short source quotation: **“Occasional internet connectivity is required to sync data”**. [Open mSupply FAQ](https://docs.msupply.foundation/docs/introduction/faq/)

**M05 — Licence fees differ from implementation cost.** The provider's product-selection documentation says Open mSupply is free of licence fees, while separately discussing configuration, hardware and maintenance/support costs. Do not transfer prices for legacy 4D-based mSupply products onto Open mSupply. [Official product/cost explanation](https://docs.msupply.org.nz/about:which_one_for_you), [legacy pricing page and exclusion](https://msupply.org.nz/pricing/)

**Interpretation.** This is one of the strongest direct comparisons for the logistics portion. SAMPATI is not a substitute for documented medical supply-chain features such as batches and expiry-aware allocation. A link from dated flood assessment to reviewed locality needs and arrival-based follow-up is a reasonable SAMPATI demonstration focus; the same full sequence in a configured mSupply deployment remains **not established**, rather than absent. Requested-minus-issued in M01 is not automatically equivalent to requested-minus-net-confirmed-arrival.

### 5. Logistics Cluster: distinguish LogIE from RITA

**L01 — LogIE is an information-sharing and mapping system.** Its official page documents logistics and geographic layers, existing and crowdsourced field data, validation with possible edits and follow-up enquiries, and website/API consumption. Short source quotation: **“All information submitted to the LogIE system goes through a validation process.”** [LogIE overview and data governance](https://logcluster.org/en/logie/about)

**L02 — RITA is the operational cargo system.** Its guide documents consignments, service-request upload, stock, journeys, dispatch quantities, waybills, receipt, release requests and inventory counts. Its context is Logistics Cluster/WFP shared storage and transportation services. [RITA operator quick start](https://rita-manual.logcluster.org/en/rita-operators-quick-start-guide), [RITA background](https://rita-manual.logcluster.org/en/introduction-background-rita)

**L03 — Receipt and release evidence have explicit quantities.** Receipt distinguishes good, damaged and lost-in-transit quantities; release orders can be accepted/rejected. The pallet guide documents release date, receiver, quantity and waybill/proof-of-delivery attachments. Short source quotation from the pallet guide: **“Proof of Delivery”**. [RITA receipt/release workflow](https://rita-manual.logcluster.org/en/rita-operators-quick-start-guide), [pallet view and release attachments](https://rita-manual.logcluster.org/en/pallet-view)

**L04 — Access and connectivity are material.** RITA's access guide says external users request access from RITA administrators. The quick start explicitly states its offline function is currently unavailable. This is a documented current limitation in the reviewed guide, not a limitation inferred from silence. Short source quotation from quick start: **“all operations are conducted directly over the internet”**. [Accessing RITA](https://rita-manual.logcluster.org/en/accessing-and-navigating-rita), [operator quick start](https://rita-manual.logcluster.org/en/rita-operators-quick-start-guide)

**Interpretation.** LogIE could complement a local relief ledger by supplying a logistics picture; RITA has direct cargo-workflow overlap and broader journey/warehouse operations. They must not be collapsed into a single product whose map also supposedly performs every transaction. Access for an arbitrary Indian local team, commercial service terms, a SAMPATI integration, and exact arrival-adjusted community-need arithmetic are **not established**. RITA is not a universal self-service SaaS substitute simply because its documentation is public.

### 6. ArcGIS emergency workflows

**A01 — Damage Assessment is a deployed solution family.** The current solution documentation lists public damage reports, damage-photo viewing, an assessment operations app and a public/internal Hub site. Requirements include ArcGIS Online, Survey123, Survey123 Connect and QuickCapture; assessment operations require a Creator user type. Short source quotation: **“manage, monitor and administer damage assessments”**. [Introduction to Damage Assessment](https://doc.arcgis.com/en/arcgis-solutions/latest/reference/introduction-to-damage-assessment.htm)

**A02 — Emergency Management Operations supports a common picture and public communication.** Current ArcGIS Online documentation lists Survey123 editors, an Experience Builder incident app, dashboards and a Hub information site, with different minimum user types. It addresses incident impact, disrupted services and response progress. [Current Emergency Management Operations](https://doc.arcgis.com/en/arcgis-solutions/latest/reference/introduction-to-emergency-management-operations.htm)

**A03 — Offline field collection is documented.** Survey123 can capture surveys while disconnected; questions depending on hosted services do not work offline. Device preparation and app selection matter. Short source quotation: **“Surveys continue to work in Survey123 Mobile and the Survey123 field app while disconnected.”** [Survey123 general FAQ](https://doc.arcgis.com/en/survey123/get-started/faqgeneral.htm)

**A04 — Licensing is a platform decision.** ArcGIS Online uses annual user-type licences and credits; storage and some services consume credits. The pricing/licensing page documents included applications and nonprofit/education programmes. [Official licensing options](https://www.esri.com/en-us/arcgis/products/arcgis-online/buy), [ArcGIS Online subscription FAQ](https://doc.arcgis.com/en/arcgis-online/reference/faq.htm)

**Interpretation.** ArcGIS is strongest here as a broader GIS/assessment/communication platform, especially for an agency already operating an ArcGIS organisation. These reviewed templates do not establish a SAMPATI-equivalent relief reservation/return ledger, but ArcGIS can be extended and integrated; omission from a template is not proof of inability. Esri's damage-assessment marketing is explicitly aligned with US FEMA programmes, so do not present that exact template as already adapted to India's institutional requirements. [Esri damage-assessment solution overview](https://www.esri.com/en-us/industries/emergency-management/solutions/damage-assessment)

### 7. D4H

**D01 — Coordination is broader than a dashboard.** D4H's official mobile overview documents situation updates, roles, forms, logs with media, task/status boards, personnel and a document library. Live updates require connectivity. [Incident Management app overview](https://help.d4h.com/article/508-incident-management-app-overview)

**D02 — Provenance is a named product feature.** D4H's audit-trail page documents source attribution from user logins, timestamps, version histories, attachments and chronological exports. Treat its stronger claims about tamper-proofing/security as provider claims rather than an independent assessment. Short source quotation: **“source, timestamp, and version history”**. [Incident audit trail](https://www.d4h.com/features/incident-audit-trail)

**D03 — Approval and intermittent offline operation exist.** E-signature fields can lock a form or section and retain signature history. D4H also documents previously synchronised channel data remaining usable offline, updates syncing on reconnection and limitations around conflicts/template changes; initial channel access requires connectivity and it recommends intermittent offline use. Short source quotations: **“preventing any further edits”** (signature page); **“offline mode is used for intermittent internet connections”** (help page). [E-signature approvals](https://www.d4h.com/features/e-signature-approvals), [offline capability](https://help.d4h.com/article/437-offline-capability)

**Interpretation.** D4H has documented incident collaboration, audit and approvals beyond SAMPATI's small relief prototype remit. Configurable status boards and forms may model parts of relief operations. This review did not establish its exact transactional stock invariants, partial-arrival/return arithmetic or community-need calculation. Do not claim D4H lacks inventory because its incident-management module is separate: its pricing page also advertises an Equipment Management module with consumables and stockpile-oriented tiers. [D4H modules and pricing](https://www.d4h.com/pricing/rest-of-world)

## Public pricing: factual observations, not a total-cost comparison

All observations below were retrieved on **9 November 2026**. No exchange-rate conversion, Indian tax assumption or negotiated quote is included. Licence price, hosting and configuration effort are different costs. SAMPATI has no validated production hosting/support cost model, so no “cheaper than” conclusion follows.

| Alternative | Public observation and exact source | Limit on interpretation |
| --- | --- | --- |
| **PR01 — Sahana** | Current EDEN page lists MIT open-source code. [Source](https://sahanafoundation.org/eden/) | No verified public implementation/support price for this exact relief configuration in reviewed pages. Open source does not mean free deployment/support. |
| **PR02 — KoboToolbox** | Account guide confirms a free Community Plan and upgrade options; for-profit users are directed to contact Kobo. [Source](https://support.kobotoolbox.org/creating_account.html) | Main [pricing page](https://www.kobotoolbox.org/pricing/) returned HTTP 403 in this research. Current paid amounts and numeric quotas were not verified. Older 2023/2024 forum quotas were deliberately not promoted to current prices. |
| **PR03 — ODK** | Official page displayed **Standard US$199/mo** (one active project, 10,000 monthly submissions) and **Professional US$499/mo** (one active project, 25,000 monthly submissions, Entities/API); Enterprise custom. Self-hosted software can be free; managed Cloud is paid. [Source](https://getodk.org/) | Page has yearly/monthly selection; displayed rates are recorded, but exact checkout billing cadence and India taxes were not independently confirmed. Entities/API availability in Cloud is plan-dependent. |
| **PR04 — Open mSupply** | Official product guide says Open mSupply has no licence fees and separately discusses installation/support costs. [Source](https://docs.msupply.org.nz/about:which_one_for_you) | No fixed quote established for this relief use case; legacy mSupply licence prices do not apply automatically. |
| **PR05 — LogIE / RITA** | Reviewed first-party pages explain tools/access, not a verified public per-seat price. [LogIE](https://logcluster.org/en/logie/about), [RITA access](https://rita-manual.logcluster.org/en/accessing-and-navigating-rita) | Price and eligibility for an arbitrary local team are **not established**; neither is characterised here as a free general-purpose subscription. |
| **PR06 — ArcGIS** | Annual user-type licences plus credits; pricing/licensing details and special nonprofit terms are published. [Licensing](https://www.esri.com/en-us/arcgis/products/arcgis-online/buy), [FAQ](https://doc.arcgis.com/en/arcgis-online/reference/faq.htm) | No reliable India-specific numerical quote retrieved for the combined assessment/field/operations configuration. Required user types and usage influence cost. |
| **PR07 — D4H** | Rest-of-World page lists Incident Management Basic **€4,800/year**, up to 25 users and two concurrent incidents, and states a **25% annual cloud plan is required**. Modular products and volunteer grants are described. [Source](https://www.d4h.com/pricing/rest-of-world) | Provider labels pricing indicative and tailored; confirm cloud-tier minimums, configuration and applicable India quote. €4,800 alone is not the all-in price. Do not substitute US-region prices. |

## Narrow differentiation to test

**P01 — One explicit relief handover sequence.** Show dated source evidence → human-reviewed need → compatible-unit reservation/issue → reviewed shipment → sourced dispatch → partial/full arrival or undelivered return → outstanding need based on net recorded arrival. The differentiation is this implementation's focus and visibility, not exclusive ownership of these concepts. S03, M01–M03 and L02–L03 establish close precedents.

**P02 — Explain separate quantities clearly.** In a demonstration, distinguish source-reported count, ledger on hand, available/reserved stock, issued stock, dispatched quantity and confirmed arrival. Demonstrate that dispatch alone does not satisfy a need and that a return does not silently erase history. Exact units and evidence dates support this explanation. Other products already distinguish important states, especially M02 and L03; any superiority in preventing confusion remains untested.

**P03 — State the file boundary.** Position the current product as accepting defined files and human records, with provenance and human decisions. Kobo, ODK, LogIE and ArcGIS already have collection/integration capabilities. A future adapter could complement them; none is implemented merely because CSV/JSON intake exists.

**P04 — Pilot a bounded task before claiming benefit.** Compare a small team completing the same fictional or authorised relief exercise in SAMPATI and an incumbent configuration. Observe whether they can distinguish sent from arrived, explain a shortfall after a partial arrival/return, identify outdated evidence, resolve a correction and hand over the remaining need with consistent units. Record task completion, errors and setup/support burden before asserting usability, speed or lower cost.

Suggested one-slide wording:

> **Established tools are strong in field capture, GIS, incident command and supply chains. SAMPATI explores a focused local workflow for reviewing flood evidence, coordinating relief quantities and following up on what is recorded as having arrived. Field fit and operational benefit remain to be validated.**

## Claims to avoid and open questions

| Avoid | Supported replacement or validation required |
| --- | --- |
| “No competitor connects needs, stock and delivery.” | Sahana/ShaRe, mSupply and RITA have material overlap (S02–S03, M01–M03, L02–L03). Describe the exact SAMPATI workflow. |
| “Kobo/ODK only collect surveys.” | Both have offline collection and review; ODK has persistent follow-up Entities (K01–K03, O02–O04). |
| “Unique human approval, audit or provenance.” | Competitors document those concepts. SAMPATI review is not necessarily independent (B03, K02, O02, D02–D03). |
| “Offline-ready for flood responders.” | Current local use does not establish field-device sync. Competitors have explicit offline capabilities (K01, O01/O03, M04, A03, D03). |
| “AI automatically predicts needs or optimises transport.” | Current automation is deterministic and source intake does not establish inference, forecasting or live transport planning (B02). |
| “Cheaper/easier/faster/better than enterprise tools.” | Pricing is non-equivalent, several alternatives are open source/free-plan, and no comparative task study exists. |
| “Proves delivery, prevents all fraud, saves lives or reduces relief time.” | It records attributable evidence and software constraints; physical truth and operational outcomes need independent validation. |
| “India's first” or “built for every Indian responder.” | This review establishes neither firstness nor nationwide adoption, language, offline or institutional fit. |

**Unresolved procurement questions:** exact deployed Sahana template/version; field sync and conflict behavior under each candidate's current app/version; granular role and approval configuration; immutable-versus-editable historical records; exact partial-arrival/return formulas; beneficiary/privacy needs; Indian hosting/support/contract requirements; localisation; existing NGO/government tooling; training burden; and whether a configured incumbent already meets the team's task. No absence or exclusivity conclusion should be drawn until these are tested with the owning product or provider.

## Source-quality notes

- All linked capability sources are first-party provider/Foundation documentation, official guides or official product pages. Search-engine summaries and third-party review sites did not supply report claims.
- Current and archived material are explicitly separated for Sahana. Current ArcGIS Online solution docs were used rather than retired Enterprise solution help. No historical deployment is presented as current active adoption.
- Provider descriptions establish advertised/documented behavior, not independent reliability, security, usability or impact. The strongest detailed workflow evidence here is in the ODK, Open mSupply and RITA user guides; ShaRe is a higher-level product description.
- Quotations are short and cumulative direct quotations remain below 25 words per external page. Other material is paraphrased. Prices and versions may change after the retrieval date; unresolved pricing is marked rather than filled from secondary sites.
