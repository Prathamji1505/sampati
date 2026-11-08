# Sampati presentation reference

Reviewed 8 November 2026. Scope: presentation only. Exact first-party references are Saishreek Singh's `Yoriichi-GOD` profile, `Yoriichi-GOD/REFLEX`, and `Yoriichi-GOD/SATquery-AI`. No similarly named repositories were used. Sampati comparison uses the local [README](../../README.md), inspected at commit `66e4b57` with a clean working tree before this note was added.

## What the exact references show

### REFLEX

The [current README](https://github.com/Yoriichi-GOD/REFLEX/blob/main/README.md) opens with a small emblem, short product promise, brief audience/problem description, and prominent links to a video, live AWS demo, reviewer tour, local setup and documentation. An explicit release-status paragraph comes before a large actual inspection screenshot. Its caption records capture date, image attribution and demonstration limits.

The remaining hierarchy is compact: problem and four-step workflow; a concrete example a reviewer can reproduce; measured results with denominators and sources; a short setup block; an intent-based documentation table; licensing and interpretation limits. Architecture is linked as deeper reading. Current README markup has no badge row. These are presentation observations; the linked live service and evaluations were not independently exercised here. [Source](https://raw.githubusercontent.com/Yoriichi-GOD/REFLEX/main/README.md).

### SATquery-AI

The [current README](https://github.com/Yoriichi-GOD/SATquery-AI/blob/main/README.md) uses a centred emblem, product name, short promise and four direct navigation links: walkthrough, measured evidence, setup and architecture. A short audience paragraph and explicit local-prototype status precede a wide, linked browser capture. Its caption states the capture date, source context and the limits of what visible markers establish.

Below the release/submission updates, a three-step workflow leads to a table mapping inputs to supported analysis and execution. Evidence has separate metrics and populations; a secondary screen is folded into a disclosure. Setup distinguishes software checks from provisioned inference. An intent-based documentation table routes readers to architecture, assets, reports and boundaries. Current README markup has no badge row. [Source](https://raw.githubusercontent.com/Yoriichi-GOD/SATquery-AI/main/README.md).

### Saishreek Singh's profile

The [profile README](https://github.com/Yoriichi-GOD/Yoriichi-GOD/blob/main/README.md) uses a custom SVG hero with separate mobile artwork. Six selected projects have numbered, wide visual panels, a short explanation, maturity/limits, and direct links to the complete UI, walkthrough, source or evidence. Selected-project imagery is the main visual hierarchy. Secondary projects receive text links further down.

Engineering disciplines, a working principle, dated project-reported evidence and contact links follow. The evidence section preserves evaluation scope rather than turning separate projects into a single score. The hero SVG itself specifies a charcoal background and outlined typography; the profile's responsive `<picture>` elements provide purpose-built mobile variants. This is an original personal visual system, not an asset collection to reuse. [README source](https://raw.githubusercontent.com/Yoriichi-GOD/Yoriichi-GOD/main/README.md) · [Hero source](https://github.com/Yoriichi-GOD/Yoriichi-GOD/blob/main/assets/hero.svg).

## Sampati's presentation gaps

These are recommendations inferred from the reference structures and Sampati's current documentation, not findings about product quality.

| Current Sampati presentation | Recommended change | Basis |
| --- | --- | --- |
| Several substantial scope paragraphs appear before the first screen. | Reduce the opening to one product paragraph and one clear prototype-status line; move detail to the relevant sections. | [Sampati opening](../../README.md); both reference openings above. |
| The first image is a welcome screen; subsequent prominent screens show the aircraft register and import review. The stated core product now covers incident review, relief needs, stock, shipments and follow-up. | Lead with an actual current relief-coordination screen, then show a short incident-to-delivery sequence. Keep the approved bird and welcome artwork as identity support. | [Sampati product and screenshots](../../README.md#meet-sampati). |
| The main “How it works” and “Try it” instructions still centre on aircraft imports. | Make the primary guided journey follow the disaster-response workflow. Retain the aircraft example as supporting report-review documentation. | [Current workflow](../../README.md#how-it-works), [demo instructions](../../README.md#try-it-in-three-minutes), [incident guide](../INCIDENTS.md), [delivery guide](../DELIVERIES.md). |
| Repeated feature, stage, audience, scope and commercial tables compete with the product story. | Keep one concise capabilities table and one release-status block. Link the roadmap, verification and commercial hypothesis instead of repeating them. | [Current README](../../README.md), [roadmap](../ROADMAP.md), [verification](../VERIFICATION.md). |
| Important reviewer material is linked throughout a long page. | Add a final “Explore the project” table with reader intents: see the workflow, run locally, understand architecture, inspect verification, inspect data sources, and follow planned work. | Reference navigation tables; [existing Sampati architecture](../ARCHITECTURE.md), [setup](../SETUP.md), [data-source strategy](../DATA_SOURCES.md). |

## Suggested README order

1. Approved emblem and bilingual name; one-line product promise.
2. Direct links to the reviewer walkthrough, local setup, architecture and verification.
3. One short audience/value paragraph; clear local-prototype status and hosting availability.
4. A large actual relief-workspace capture with date, fictional-data label and provenance link.
5. Problem and the implemented evidence → review → needs → stock → shipment → arrival/return → follow-up workflow.
6. A short reproducible fictional case, supported by two or three legible actual screens.
7. Current capabilities and boundaries, with deeper guides linked.
8. Short local setup, then architecture and recorded verification links.
9. Intent-based documentation navigation; roadmap; identity, author, licence and attribution.

Keep existing CI/licence/technology badges restrained if useful. The exact references do not support adding a decorative badge wall, invented performance figures, deployment links or adoption claims. A local demo link must identify itself as local. Existing verification supports only its recorded scope. [Sampati verification](../VERIFICATION.md).

## Asset and claim boundaries

Create Sampati-specific presentation assets from its approved emblem and its own actual UI. Reference composition, hierarchy and reviewer navigation; do not copy Saishreek's branding, SVG artwork, screenshots, project claims or metrics. Label fictional records and browser emulation, and retain capture provenance. Optional future assessment connectors remain planned unless the owning implementation and its verification establish otherwise. [Sampati image provenance](../images/README.md) · [Sampati third-party notices](../../THIRD_PARTY_NOTICES.md) · [Data-source strategy](../DATA_SOURCES.md).

For a later personal-profile showcase, use one strong Sampati panel with its actual UI, a concise product explanation, prototype status, repository link and reviewer/demo path. Preserve the user's established cat-avatar identity. Changing the personal-profile repository is a separate implementation decision; this note changes only research documentation.
