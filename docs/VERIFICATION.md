# First milestone verification

## Inventory backend publication check — 8 November 2026

- The expanded full backend suite passed **138 tests**, including inventory quantities, append-only records, request-linked reservations, roles/isolation, retries, balance limits and concurrent reservations. The existing upstream Starlette test-client deprecation warning remains.
- The frontend build passed before the subsequent inventory-interface work started. This backend publication does not mark that interface or its browser journey complete.
- All migrations through **006** applied successfully in a fresh disposable schema in the dedicated test database. Alembic model consistency passed there; the schema was removed afterwards. The live development database remained on 005.
- The staged-source publication scan checked local links and known local secrets without findings. New inventory source, tests and migration are included; in-progress inventory-interface changes are a separate increment.

See [inventory backend milestone](INVENTORY.md) for the API scope and remaining H02 work.

Checked locally on 7 November 2026.

## GitHub submission preparation

Rechecked on 7 November 2026 for the public source package. The earlier milestone records below remain historical evidence; public display lettering now uses Yatra One instead of the private personal-use prototype font.

- All **59 backend tests passed**, including the newly added source-report checks, against isolated schemas in the existing dedicated test database; the same upstream Starlette test-client deprecation warning remains.
- The frontend TypeScript/production build, Python dependency check and Alembic schema check passed.
- Five actual product screenshots were captured for the README using the fictional demo. Sample preview was never confirmed; accepted demo revision **3**, the aircraft records and import count were preserved.
- Welcome was contained at **1440, 1024, 390 and 320px**. The separate 390px touch context had no page overflow and retained 16px search-input text. The capture journey recorded **zero new console errors**.
- The self-hosted Yatra One display font loaded successfully. Its SIL OFL 1.1 notice is included. The original personal-use font was moved into ignored private assets and is absent from the public build.
- The mechanical detector returned no findings for the changed stylesheet and HTML. That source scan does not establish full accessibility compliance.
- The [first GitHub-hosted CI run](https://github.com/Prathamji1505/sampati/actions/runs/42374760025) **passed** the frontend production build, Python dependency check, all backend tests and migration/schema checks on Ubuntu with disposable PostgreSQL. This validates that source snapshot, rather than establishing application hosting or production readiness.
- A final read-only browser check of the Report checks readability update passed at **1440, 1024, 390 and 320px**: Data checks is the second table column, the sideways-scroll hint appears on small screens, the page remains contained and no browser errors were captured. The production build passed after that update.

Screenshots were visually inspected for the established artwork, typography, spacing and readable product content. [Capture details](images/README.md) record routes and viewport sizes. These checks do not establish production deployment readiness or aviation suitability.

## Environment actually exercised

- Windows, Python 3.12.4, Node.js 26.13.0 and npm 11.20.0.
- PostgreSQL 18.6 in this project's isolated loopback cluster on 55432.
- Resolved dependencies captured in backend/requirements-lock.txt and frontend/package-lock.json.

## Results

- `python -m pytest backend/tests -q`: **22 passed**. Each test uses a fresh schema in the dedicated test database.
- `npm --prefix frontend run build`: **passed**, including TypeScript checking and production asset compilation.
- `python -m pip check`: **passed**.
- `python -m alembic -c backend/alembic.ini check`: **no new upgrade operations detected**; models and migrated development schema agree.
- Real Edge browser journey: preview without saving, confirmed import, search, status filtering, freshness filtering, aircraft details, import audit, idempotent repeat upload, invalid batch blocked, reload persistence and mobile navigation all **passed**.
- A mobile overflow defect was found in a screen-reader-only table header and fixed by anchoring hidden text and containing the table. Follow-up page width was **390px for a 390px viewport**.
- Touch-enabled Chromium context: **16px input text**, coarse-pointer styling active and no page overflow.
- Backend and frontend processes were stopped and restarted. **The same 12 aircraft, identifiers and workspace revision 2 remained**.
- Final browser smoke check recorded **zero new console errors**.
- Development credentials, local database files, virtual environment and node_modules are ignored by Git.

Three fictional sample batches are intentionally present in the development workspace after the original and branding browser walkthroughs. Automated backend tests did not alter that workspace. Screenshots are local QA artifacts under .impeccable/review/ and are ignored by Git.

## Sampati identity and theme verification

Also checked on 7 November 2026 after the user selected SAMPATI · सम्पाति and a crimson/black palette with small saffron details.

- Production TypeScript/Vite build and all **22 backend tests passed** after the naming changes.
- The existing browser journey passed upload preview, confirmation, search, status/freshness filters, aircraft details, import audit, duplicate replay, invalid-file blocking, persistence and mobile navigation.
- Page width equals viewport width at **1440, 1024, 820, 640, 390 and 320px**; exactly one wordmark is visible at each width. The touch-enabled check retains 16px input text.
- The independent visual review approved the desktop/mobile identity and palette. Calculated primary-button text contrast is **5.72:1** at rest and **4.80:1** on hover; secondary text on raised surfaces is **7.25:1**.
- The mechanical design detector returned no findings. Final secondary-button hover and import-step-divider corrections were reviewed and approved separately.
- The app was restarted. The same **12 fictional aircraft** persisted; the running OpenAPI title and CSV download filename use Sampati. No new browser console errors were observed.
- Brand assets, browser title, frontend package metadata, API display text, launcher label and project documentation now use the selected name. Existing database identifiers are retained to preserve local data and configuration.

## Folk-art refinement verification

The subsequent folk-art refinement was also checked on 7 November 2026. Shivaraja loaded from the supplied local font and was confirmed on the wordmark and page headings; table text retained DM Sans. The new illustrated emblem and background have exact ImageGen prompts embedded in their PNG metadata and recorded in `frontend/public/artwork/provenance.json`. Production build, search, all four navigation views, the existing touch smoke check and viewport containment at 1440/1024/820/640/390/320px passed. The focused visual review approved the artwork/font integration, with no material issue introduced. No backend logic or accepted records changed in this refinement. The existing 320px filter row can clip the sort control's right inset; broader mobile-table cleanup remains outside this visual pass. Shivaraja's original personal-use licence files are retained with the font.

## Welcome entry verification

Checked on 7 November 2026. The root renders the welcome page, while `#workspace`, `#import`, `#history` and `#guide` identify the existing working views. Browser checks verified entry, logo-to-home navigation, guide access, Back/Forward, reload, keyboard entry and both skip links. Welcome made zero API calls, remained accessible with API requests blocked, and navigation left workspace revision 3 unchanged. At 1440/1024/820/768/640/390/320px there was no horizontal page overflow; the 50px entry button remained within the first viewport, including 320×640. The existing desktop and touch-enabled workspace smoke checks passed with 12 aircraft and zero console errors. The production build and focused visual review passed. The initial design detector returned no findings; final CSS corrections improved short-screen entry placement and tablet copy clearance.

This adds a surface within the existing design system. The shared DESIGN.md and sidecar are preserved; route-specific layout and behavior are recorded in `.impeccable/surfaces/welcome.md`. Existing generated artwork is reused with its embedded provenance.

## Account and organisation milestone verification

Checked on 7 November 2026. The suite now has **34 passing backend tests**, including the original import cases on explicit demo routes and 12 account/isolation cases. Checks cover password hashing, session rotation, HttpOnly/SameSite cookies, CSRF, expiry, revoked membership, viewer write denial, logout revocation, same-named independent organisations, request throttling, guessed workspace selectors, foreign import access and cross-workspace preview replay.

The additive 002 migration and Alembic schema check passed. Demo preservation was checked before and after migration and browser-QA cleanup: **12 aircraft, revision 3 and three existing imports** remained unchanged.

A real Edge browser and a second, separate touch-enabled browser context passed sign-up, empty private workspace, preview-before-save, confirmed private import with an attributable actor, session restoration on reload, demo/private switching, isolation between organisations, rejection of a foreign import, mobile navigation, sign-out and signing back in with saved records. A form-label association issue and a browser Unicode-pattern escape issue were found and corrected. The successful account journey recorded no new console errors. Four explicitly identified generated QA accounts from the verification runs were removed through the guarded fixture helper; no user account was seeded.

The frontend production build and dependency check passed. The prior branding and welcome assets were retained. These checks do not constitute a production security certification.

## Limits

No physical phone was connected; mobile behaviour was checked in a touch-enabled browser context and by code inspection. Accounts and organisation-scoped access are now implemented. Password recovery, invitations/team administration, deployment, live aviation integrations and AI prediction remain outside this milestone. The application is loopback-only and uses fictional records.

The installed Starlette test client emitted an upstream deprecation warning for HTTPX during the passing test run. It does not affect this verified local flow; the locked dependency set records what was tested.

## Civilian prototype expansion

Checked on 7 November 2026. These results supersede the earlier milestone's list of unimplemented recovery and team features.

- **49 backend tests passed** in isolated test-database schemas. Coverage includes the prior import/accounts suite, Excel validation and reordered headers, literal spreadsheet exports, scoped exports/reports, targeted invitations, role administration/last-owner protection, verified membership switching, password changes, one-time recovery, inbox approval/rejection, scoped keys and key rotation. The same upstream Starlette warning remains.
- Frontend production build, TypeScript checking and Python dependency consistency passed. Alembic upgraded the development database to **003**, and its schema check reports no missing operations.
- A real Edge journey with two separately authenticated browser contexts passed Excel template/upload, preview without saving, confirmation, Excel/CSV/JSON download events, overview counts, masked source-key display, simulated update submission, unchanged accepted revision while pending, inbox review/confirmation, targeted invitation acceptance, viewer import restrictions, switching between two verified organisations, editor-role changes, password change and recovery with a saved code. No new console or page errors were captured by the successful journey.
- Four new tool screens were captured and checked for page containment at **1440, 1024, 390 and 320px**. The separate touch-enabled register smoke check passed with **390px document width for a 390px viewport**, **16px input text**, coarse-pointer styling and zero new console errors. No physical phone was used.
- `scripts/check_watcher.py` passed actual local HTTP ingestion using the real watcher process, repeat deduplication, pending-inbox verification, no accepted records before confirmation, and successful human preview/confirmation. Its generated fixture was removed afterwards.
- Backup creation and archive-index verification passed. `restore_check.py` successfully restored schema **003** and aircraft records into a generated disposable database, read the restored contents and removed that temporary database. The live database was not replaced.
- The existing demo remains **12 aircraft, revision 3 and three imports** across migration, server restart and guarded cleanup. All generated QA accounts/workspaces from these checks were removed by their explicit IDs. Existing user accounts were not cleared or reseeded.
- The mechanical design detector scanned frontend source and found no regex findings. Its parsed-page contrast/tiny-text rules did not run; this source scan is limited evidence, not a full accessibility certification. Independent rendered review is recorded below after its verdict.

The current implementation is a loopback-only fictional civilian data-management prototype. Summary counts and attention rules are computed from accepted records. Model-based AI, operational dispatch, real aviation feeds, production hosting and military optimisation were not implemented or tested.

### Rendered finish review

A fresh independent review inspected all 16 tool captures across 1440/1024/390/320px, plus the current desktop/touch register. Its full review found the incumbent lettering, materials, palette, task hierarchy and responsive adaptation faithful, with one material control-size mismatch. A desktop account screenshot first required recapture because the browser's full-page capture displaced fixed elements at a nonzero scroll position; it was replaced after resetting scroll/focus, rather than treated as valid evidence.

The action-size correction removed both smaller `.tools-actions .button` minimum-height overrides. The production build and complete browser workflow passed again. Real computed-height checks verified 40px desktop actions and 44px source/export actions in a separate coarse-pointer browser context. All 16 tool captures were refreshed. The reviewer returned **ship**, scoring the one listed control-system fix **resolved**, with no fix-induced regression. This final verdict covers that fix list; it is not a production accessibility or security certification.

DESIGN.md, `.impeccable/design.json` and the approved artwork remain unchanged by this feature extension. The surface contract is in `.impeccable/surfaces/workspace-tools.md`. Repeated inbox confirmation was also checked to preserve its original review time/attribution rather than rewriting its audit on a no-op.

## Welcome guide separation fix

Checked on 7 November 2026. The user reported that reading the welcome-page guide entered the workspace. The real-browser reproduction confirmed `#demo/guide`, workspace navigation and two workspace reads before intentional entry. The cause was the welcome link targeting the existing in-workspace guide route.

The link now targets standalone `#welcome/guide`, rendered before the authentication/workspace branch. Public and in-workspace guides share one content component; the public page offers Back to welcome and Enter workspace, while the sidebar guide retains Start an import and the configured freshness threshold.

`scripts/browser-welcome-guide.js` passed: no workspace navigation or workspace-data requests during reading, reload or browser Back/Forward; guide renders with API requests blocked; direct navigation and heading focus work; page width stays contained at 1440/1024/390/320px; explicit entry loads the register; the in-workspace guide and import action still work; zero unexpected browser console errors. The frontend production build passed. No backend behavior or accepted records were changed by this fix. The source detector found no regex findings in the three guide source files; parsed-page contrast/tiny-text rules were not run.

A fresh independent finish review returned **ship** for this narrow preservation fix. It inspected all four required guide captures and routing/shared-content source, found no material fixes, and confirmed the inherited identity, standalone reading frame, distinct return/entry controls and contained responsive layouts. Runtime claims rely on the recorded browser regression; DESIGN.md and its sidecar were preserved.

The subsequent requested guide footer addition includes bilingual SAMPATI identity, the established source-first tagline and the fictional-data notice. Production build and browser checks at 1440/390/320px passed, with no page overflow or new console errors. A fresh footer-only review inspected all three captures and returned **ship** with no material fixes. The footer uses the incumbent divider, palette, typography and responsive wrapping; workspace entry behavior is unchanged.

## Explained source-report checks

Implemented and verified on 7–8 November 2026. The milestone adds the requirements/acceptance map in docs/REQUIREMENTS.md and read-only Report checks at `#checks` / `#demo/checks`. These assess source-record quality; they do not calculate operational availability or aircraft readiness.

- The full backend suite passed **61 tests**, including 12 new quality checks. Coverage includes exact freshness/future boundaries, preserving reported status, no maintenance inference from note text, scoped/private/demo access, viewer reads, pending report equivalence/conflict/newer/older comparisons, exact grouped file counts with bounded examples, rejection/acceptance clearing evidence, and accepted-record preservation. The existing upstream Starlette test-client warning remains.
- The actual Edge workflow passed an empty state, importing 23 fictional reports, named findings and next steps, result/finding/search filters, source-details inspection, 20-row pagination and JSON download content checks. The export contained all matching records with rule version and context, rather than only the displayed page.
- An incoming file introduced a same-time conflict, a newer report and a new aircraft ID. The accepted status/revision did not change during checks or export; inbox navigation and rejection removed the pending findings correctly. A separate touch context verified 44px action height and 16px search text. A synthetic 503 showed the correct unavailable state, and Refresh checks recovered after the failure was removed. The successful main journey captured no unexpected browser console or page errors.
- Report checks captures at **1440/1024/390/320px** passed page containment. Findings sit next to aircraft IDs; the mobile table scrolls internally with a visible instruction. A fresh independent full review returned **ship**, with no material fixes for this inherited workspace extension. Its runtime claims rely on the recorded journey; it independently inspected the four captures and relevant implementation.
- Production build, dependency consistency and schema check passed. No migration or new dependency was needed. Explicit generated QA account cleanup left **zero generated QA accounts**; the demo remains **12 aircraft, revision 3 and three imports**. Existing user accounts were not cleared or reseeded.
- The source detector found no regex findings in the two feature files; parsed-page contrast/tiny-text checks did not run. This is limited evidence, not an accessibility certification. The current design-system files, public Yatra One typography, guide/footer and existing artwork were preserved by this feature.

The final guide regression on 8 November found a separate 320px header overflow with the current display font: the logo, return button and gap exceeded the available width, producing a 323px document. A two-declaration public-guide-only fix allows wrapping and right-aligns the return button on its second row. The full guide regression now passes at 1440/1024/390/320px, including no workspace-data reads before entry, direct links, reload/history, focus, API-blocked reading, explicit entry and the in-workspace import action. A fresh guide-header review returned **ship** with no material fixes; the latest production build passed. No backend code changed during this resumed header repair.

## Civilian-welfare direction

On 8 November 2026 the user selected civilian welfare as the project's purpose. The current charter is docs/CIVILIAN_WELFARE_SCOPE.md. It sets a proposed disaster-relief build order of relief requests, aid inventory, delivery tracking, civilian context, evaluation and deployment. These new welfare modules are planned, not implemented by the scope update. The current source-report foundation remains available.

Welcome and the desktop sidebar now use “Civilian Relief & Logistics Coordination”. PRODUCT.md, the roadmap, requirements, README and submission brief reflect the new direction. DESIGN.md and its sidecar change only descriptor prose; existing tokens, fonts and artwork are preserved by this edit.

Production build passed. Actual Edge checks verified the exact descriptor, workspace entry, page containment and zero new console errors at 1440/390/320px. Visibility checks confirmed the descriptor appears on Welcome at all three widths and in the desktop sidebar; mobile navigation continues to omit it according to the incumbent design. No backend logic, data contract, database or dependencies changed in this scope update.

A fresh independent review inspected all six Welcome/workspace captures. It matched the inherited design and truthful scope, requesting one correction to the surface contract's mistaken mobile-sidebar visibility promise. The contract and verification wording were corrected to reflect the actual visibility. The reviewer scored that documentation fix resolved and returned **ship** at the fix-list scope. The review did not claim that the planned welfare modules had been built.

## H01: reviewed relief requests

Implemented and checked on 8 November 2026. Organisation-scoped relief requests support exact decimal quantities/units, local-time deadlines, drafts, corrections with reasons, submission/review/cancellation, optimistic version guards and attributed before/after history. Details and limits are in RELIEF_REQUESTS.md. Reviewed means request details checked; it does not confirm inventory, independent approval, dispatch or delivery.

- The full backend suite reached **82 passing tests**, including 21 new relief checks. Invalid and server-owned inputs, duplicate keys/references, timezone-equivalent no-op edits, status graph, terminal cancellation, CSRF/roles/demo/isolation, literal search, paging, history and concurrent updates were covered. The initial timezone no-op test exposed an offset-format mismatch; normalising snapshots to UTC fixed it before the full pass.
- The real Edge journey passed draft creation, exact fractional quantity, correction audit, submit/review/return/cancel, 20-row paging/search, stale-edit rejection without overwrite, cross-organisation 404/scoped references, viewer-only controls, organisation switching and a lost-response-after-commit retry producing one request/event.
- Forms, lists and details passed containment at **1440/1024/390/320px**. A touch context checked 44px save height and 16px quantity text. Expected stale409 and isolated network-abort cases were separated from unexpected browser errors; no unexpected main-page errors remained.
- Migration **004**, schema consistency, production build and dependency consistency passed. A backup restored into a disposable database with 24 aircraft and three relief requests. Explicit QA fixture removal preserved original accounts, workspace/aircraft/import counts and demo revision3.
- A fresh independent full finish review inspected all 12 captures and returned **ship**, with no material fixes. It found the inherited system and task sequence faithful; runtime confidence relies on the recorded checks. The source detector had no regex findings for the two feature files; parsed-page contrast/tiny-text checks were not run. Tokens and artwork were preserved by this increment.

## Flood-assessment intake and incident review

Implemented and checked on 8 November 2026 for the refined flood-response direction. This increment implements **assessment JSON → human-reviewed incident → linked relief-request draft**, using the application-owned `sampati.incident.v1` contract. It does not connect to a live SATQueryAI service, perform satellite analysis or forecasting, infer supply quantities, assign aircraft, approve missions or confirm deliveries. The exact contract, states and remaining work are in INCIDENTS.md.

- The expanded full backend suite passed **109 tests** (27 new incident tests/parameter cases), with the existing upstream Starlette test-client deprecation warning. Coverage includes immutable accepted evidence, canonical duplicate retries, reference conflicts, strict timezone/extent/URL/estimate validation, future-observation rejection, CSRF/role/demo/isolation, review graph/no-ops/version guards, concurrency, literal search/20-row paging, 50-event audit paging and same-organisation/reviewed-only relief linkage. Reopening retains existing links and prevents new ones until reviewed again.
- Migration **005** adds incident/evidence history and nullable request links. It applied successfully and Alembic reported no new upgrade operations. Existing requests remain unlinked; aircraft/import revision is independent. The production build and `pip check` passed; no new dependency was added.
- `scripts/browser-incidents.js` passed a real Edge journey: read-only demo, empty private state, malformed JSON/non-writing preview, file upload and schema download, Needs review intake, identical retry, reasoned review, linked relief form with initially blank quantity, exact human-entered quantity, stale-review rejection/reopen, paging/search, foreign-organisation 404, viewer controls, 44px touch action and 16px editor, and a lost-response-after-commit retry creating exactly one assessment/event. One intentional409 and an isolated retry abort are expected; zero unexpected main-page console/page errors were recorded.
- All **16 final captures** (intake/preview, details, filtered list, linked request form at **1440/1024/390/320px**) passed document containment. The first render inspection caught the incident register missing the inherited table/footer classes; those classes and a mobile sideways-scroll instruction were applied together. The complete browser journey passed again with all 16 captures refreshed. No further build-thread visual hunt follows the second inspection.
- The mechanical source detector ran once over four changed UI source files and reported no regex findings, before the final table-class/scroll-instruction correction. Parsed-page contrast/tiny-text rules were not run; this is not a full accessibility certification. The shared tokens, fonts and approved artwork were preserved.
- A fresh independent full finish review inspected all 16 final captures and relevant contracts/source. It returned **ship**, with no material fixes, finding the inherited typography/material/palette, evidence-before-decision hierarchy, mobile adaptation and truthful scope faithful. It did not rerun the parent's runtime checks.
- The complete H01 relief browser regression passed again after the optional link extension. The welcome-guide regression was expanded to observe incident, relief and report-check data requests as well as the original routes; it passed direct entry, API-blocked reading, reload/history/focus, all four widths, zero workspace data reads before explicit entry and zero new console errors.
- Explicit fixture cleanup removed all generated QA accounts. The preserved baseline is **one original account, two workspaces, 24 aircraft, four imports, demo revision3**. Demo relief records remain three requests/six events; the new stable incident examples are two assessments/three events. Rerunning the incident seed added zero records and retained original evidence timestamps.
- The final private archive `.local/backups/sampati-20261108T074415774423Z.dump` restored successfully into a newly generated disposable database: **schema005, 24 aircraft, three relief requests and two incident assessments**. The helper removed only that temporary database; the live database was unchanged.
