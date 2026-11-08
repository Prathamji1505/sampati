# First implementation milestone

## Current direction: civilian welfare

On 8 November 2026 the user explicitly changed the project objective to civilian welfare, then refined it to flood response and disaster-relief coordination. The current charter is docs/CIVILIAN_WELFARE_SCOPE.md. Prior milestones below remain implementation history. Relief requests and local flood-assessment intake/review are implemented. The next dependencies are aid inventory → delivery tracking → verified civilian context → evaluation → deployment, alongside an agreed live assessment-source adapter. The original military air-operations brief is no longer the completion target. Existing source-report features remain supporting infrastructure.

Project name: SAMPATI · सम्पाति. The first milestone is a local, fictional civilian aircraft-report workspace.

1. Record the data contract and create repeatable fictional examples.
2. Prepare isolated Python/frontend dependencies and a project-owned PostgreSQL cluster on loopback port 55432. Leave the existing service on 5432 unchanged.
3. Implement a transactional, version-checked CSV preview/confirm API with migrations.
4. Build the register, import review and history screens in React.
5. Verify input failures, replay/idempotency, old reports, concurrent previews, persistence and the real browser flow.

Completion means an accepted import appears only after confirmation, survives restart, and can be understood through source timestamps and history. Dependencies, tests, launch instructions and limitations are recorded in README.md. Account isolation, external context, Excel, AI and publication are later milestones.

## Completed first milestone

The blueprint, seven fictional fixture files, local dependency setup, isolated PostgreSQL cluster, migration, transactional preview/confirm API, React register/import/history/guide screens and starter validation coverage are implemented. Backend tests (22), production build, schema consistency and the real browser journey pass. Restart persistence was verified with 12 fictional aircraft. See docs/VERIFICATION.md for exact evidence and limits.

## Completed interface refinements

The user-selected Sampati identity, folk-style artwork, Shivaraja display lettering and crimson/charcoal theme are implemented. A welcome page now introduces the application before entry to the register. The guide, home navigation, browser history, direct workspace locations and responsive entry flow are verified. Shared accounts and organisation boundaries remain a separate milestone before any real or shared use.

## Account and organisation milestone

Implemented account creation, sign-in, sign-out, empty private organisations, membership-scoped reads/writes, account-bound previews and a demo/private workspace selector. The additive migration preserves all existing demo aircraft and imports. Password hashes, opaque cookie sessions, CSRF checks and persisted sign-in attempt limits support the local flow. The established Sampati identity and welcome artwork are preserved.

Account and isolation tests plus the prior import tests total 34 passing checks. Two separate browser contexts verified organisation separation, private imports, reload, sign-out and signing back in. Browser-QA fixtures are removed after verification. Recovery and team administration were subsequent work, now completed below; hosted deployment remains unconfigured.

## Civilian prototype completion

The user has authorised completing the remaining useful project tasks. Scope stays a local fictional civilian data-management prototype, without combat planning, weapons, threat-based retasking or automatic airworthiness decisions.

Build in dependency order:
1. Excel import and protected spreadsheet exports through the existing validation workflow.
2. Reporting based on accepted records, source freshness and data-quality findings.
3. Organisation invitations, role administration, password changes and one-time recovery codes.
4. Scoped source credentials and a persistent incoming-data review queue, plus a local file-watcher connector. New data does not automatically replace accepted records.
5. Responsive UI integration, scheduled view refresh, useful loading/error states and documented local backup/restore and deployment preparation.
6. Meaningful backend, permission and browser checks; preserve existing accounts, branding and accepted demo data.

No paid provider, external deployment, live flight feed or trained prediction model is assumed. Computed summaries must be labelled factual/rule-based rather than presented as AI predictions.

## Completed civilian prototype expansion

Implemented all six groups above within the local civilian scope: CSV/Excel templates and imports; filtered literal-text Excel, escaped CSV and raw JSON exports; factual overview and attention lists; targeted invitations and role management; password changes and one-time recovery; source-key inbox, simulator and changing-file watcher; 30-second visible-tab refresh; backup and isolated restore rehearsal; responsive integration and documentation. The original identity, existing accounts and accepted demo data are preserved.

No hosting, live aviation feed, paid provider, model training, weather-based dispatch or military operational optimisation is included. The broader problem statement is not claimed solved by this learning prototype. Current verification evidence is in docs/VERIFICATION.md.

## Next milestone: explainable source-report checks

Create a concrete civilian requirements/acceptance map in docs/REQUIREMENTS.md. Implement read-only per-record checks for source freshness, incomplete fields, unknown status and pending report disagreements, preserving the original reported status. Expose reasons, source evidence, next review steps, filtering, pagination and a versioned filtered export. Verify isolation, time boundaries, pending-file grouping, read-only behavior and the rendered workflow. Operational availability calculations remain a separate unimplemented requirement; these checks do not infer maintenance condition, crew suitability or dispatch readiness.

Completed: requirements checklist and Report checks are implemented. The full 61-test backend suite, browser workflow, filtered JSON content checks, touch/four-width layout checks and independent rendered review passed. Accepted data and existing users were preserved; generated QA accounts were removed. A final guide-header overflow at 320px was repaired and its full regression/review passed on resume. See docs/VERIFICATION.md for executed evidence and the remaining limits.

## Disaster-response direction

On 8 November 2026 the user defined Sampati as a **disaster-response and relief-coordination project**, starting with flood response. This is the governing direction for future development.

The proposed connection is: **Dated impact assessment → reviewed incident alert → confirmed local needs → current aircraft reports and operator checks → human-approved relief mission → mission updates and delivery confirmation.**

Assessment sources can supply dated spatial evidence, affected-area observations and uncertainty through a source-independent contract. Sampati would coordinate reviewed requests, resources and response records. Aircraft operators retain dispatch authority; reported availability and data freshness do not establish mission readiness. Post-event impact alerts and pre-event forecasting remain distinct capabilities.

The current foundation includes aircraft-report review, relief requests and local flood-assessment intake/review. The shared incident contract and reviewed-incident linkage to human-entered relief drafts are implemented; docs/INCIDENTS.md records the workflow. The live assessment-source connector, inventory, mission assignment, delivery tracking and authorised live aircraft positions remain development work. H02/H03 supply and delivery milestones remain the next dependencies.

Success should be evaluated through review accuracy, time to an approved response plan, delivery confirmation and follow-up of unmet needs. Social benefits and operational performance require civilian-user validation.

## Completed H01: relief requests

Organisation-scoped request drafts, exact quantities/units, local-time deadlines, draft corrections, submission/review/cancellation, version guards and attributed before/after history are implemented. The 82-test backend suite and full real-Edge request journey passed; a fresh full interface review returned ship. Inventory and deliveries are separate work. See docs/RELIEF_REQUESTS.md and docs/VERIFICATION.md.

## Implemented flood-assessment connection

The shared `sampati.incident.v1` contract, JSON preview/intake, immutable accepted flood evidence, source dates/uncertainty, reasoned review with race protection, and reviewed-incident linkage to relief drafts are implemented. The expanded backend suite passes 109 tests. No live producer connector or automatic needs/mission decision is implied. See docs/INCIDENTS.md and the dated verification evidence.
