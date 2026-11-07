# First milestone verification

Checked locally on 7 November 2026.

## GitHub submission preparation

Rechecked on 7 November 2026 for the public source package. The earlier milestone records below remain historical evidence; public display lettering now uses Yatra One instead of the private personal-use prototype font.

- All **59 backend tests passed**, including the newly added source-report checks, against isolated schemas in the existing dedicated test database; the same upstream Starlette test-client deprecation warning remains.
- The frontend TypeScript/production build, Python dependency check and Alembic schema check passed.
- Five actual product screenshots were captured for the README using the fictional demo. Sample preview was never confirmed; accepted demo revision **3**, the aircraft records and import count were preserved.
- Welcome was contained at **1440, 1024, 390 and 320px**. The separate 390px touch context had no page overflow and retained 16px search-input text. The capture journey recorded **zero new console errors**.
- The self-hosted Yatra One display font loaded successfully. Its SIL OFL 1.1 notice is included. The original personal-use font was moved into ignored private assets and is absent from the public build.
- The mechanical detector returned no findings for the changed stylesheet and HTML. That source scan does not establish full accessibility compliance.
- GitHub Actions is configured to build the frontend and exercise backend tests plus migrations against disposable PostgreSQL. A configured workflow is not evidence of a successful hosted run; run results appear on GitHub after publishing.

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
