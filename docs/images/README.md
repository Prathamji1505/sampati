# Product screenshot provenance

The product screenshots were refreshed on **25 November 2026** from Sampati **0.5**, source baseline `9bc320c` plus the warning-reference validation correction in this refresh. Microsoft Edge and Playwright captured the actual compiled application. These are real interface captures, rather than generated UI mockups.

## Shared fictional demo

`scripts/capture_showcase.js` captured 15 screens from the compiled app at loopback port 8000. The desktop showcase uses **1440 × 1040**, except Welcome (**1440 × 900**) and the supporting aircraft/import/history views (**1440 × 1000**). Phone captures use **390 × 844**, touch-enabled browser emulation.

| Image | Route and state |
| --- | --- |
| [Welcome](welcome.png) | `/`, current product entry and approved bird identity. |
| [Remaining needs](remaining-needs.png) | `#demo/deliveries`, Request follow-up: 40 kits requested, 10 recorded arrivals, 30 still needed. |
| [Relief overview](relief-overview.png) | `#demo/overview`, review queues and handover context. |
| [Incident review](incident-review.png) | `#demo/incidents`, dated assessments and review states. |
| [Relief requests](relief-requests.png) | `#demo/relief`, fictional request register. |
| [Aid inventory](aid-inventory.png) | `#demo/inventory`, distinct on-hand, reserved and available ledger stock. |
| [Delivery tracking](delivery-tracking.png) | `#demo/deliveries`, partial/full recorded arrivals. |
| [Automation inbox](automation-inbox.png) | `#demo/automation`, pending/invalid incoming files. |
| [Intake evidence](intake-evidence.png) | `#demo/automation`, `DEMO-INTAKE-001` evidence and draft proposal. |
| [Aircraft register](register.png) | `#demo/workspace`, accepted fictional source reports. |
| [Import preview](import-preview.png) | `#demo/import`, generated fictional sample in preview only. It was not confirmed. |
| [Import history](history.png) | `#demo/history`, existing confirmed batches. |
| [Relief phone layout](relief-mobile.png) | `#demo/automation`, current phone interface. |
| [Phone navigation](navigation-mobile.png) | `#demo/automation`, menu open with primary relief tasks, grouped utilities, guide and sign-in. |
| [Aircraft phone layout](mobile.png) | `#demo/workspace`, current supporting register. |

The capture reported zero console/page errors and no page overflow. It made no accepted-data writes: the only non-read action was the non-persisting sample preview. Workspace revision/import count and the incident, relief, stock, delivery and inbox list totals were unchanged. Fixed original source dates were retained, so old data may correctly appear stale.

## Isolated response-preparation example

`scripts/capture_response_showcase.js` captured six additional screens at loopback port 5173. Its marker guard requires the disposable test service provided by `scripts/showcase_server.py`. The service uses a unique schema in the dedicated `_test` database; it does not create fixtures in the development database or a real organisation.

All desktop captures use **1440 × 1040**. The phone capture uses **390 × 844** with touch enabled. Blocker/result screens show a scrolled viewport focused on the actual evaluation; the application pixels and values are unchanged.

| Image | Actual state |
| --- | --- |
| [Warning review](warning-review.png) | `#response`, Warnings & news: source, observation/expiry, certainty and reasoned review of a fictional warning. |
| [Missing-support checks](response-blockers.png) | Workflow planner: explanation before aircraft support is supplied. |
| [Aircraft support](aircraft-support.png) | Aircraft support: recorded fictional operator evidence. |
| [Preparation builder](response-builder.png) | Workflow planner: entered need, catalog/store mapping and evidence inputs. |
| [Reviewed preparation](response-preparation.png) | Workflow planner: 40 packs at 2 kg each, 80 kg proposed cargo, QA-CIV-1 candidate and coordinator review. |
| [Preparation phone layout](response-mobile.png) | The same reviewed record reopened in a separate touch-enabled browser context. |

The complete capture checks the missing-support block, successful preparation/review, no change to the 100-pack stock position, phone containment and native reference validation. The final run reported zero browser exceptions or console errors. The fictional account and its records are disposable test fixtures. Passwords, cookies, source keys and recovery codes are absent from the images.

These examples do not show a live warning service or independently verified conditions. Preparation review does not reserve supplies, book an aircraft or authorise dispatch. A source-backed arrival is still a recorded report rather than independent physical verification.

## Assets and authored panels

The approved bird artwork is ImageGen-assisted; [artwork provenance](../../frontend/public/artwork/provenance.json) and [logo provenance](../../frontend/public/artwork/logo-provenance.json) retain its prompts and approval. Display lettering uses the bundled OFL-licensed Yatra One font.

`sampati-project.svg` and `sampati-project-mobile.svg` are authored presentation panels. They retain their existing vector layout and title outlines, with embedded screenshots replaced by the current complete desktop/mobile captures. These panels are not standalone product screenshots. `review-workflow.svg` is an authored diagram of the supporting report-review process, not a captured interface.

## Reproduce

1. Build the current frontend and run the compiled local application on port 8000 with its existing fictional shared demo.
2. In an Edge Playwright session, run `scripts/capture_showcase.js`. It checks accepted-data counts and rejects unexpected writes/errors.
3. In a separate terminal, run `.venv\Scripts\python.exe scripts\showcase_server.py` with the project configured for a dedicated test database. Keep port 5173 free.
4. Use a fresh Edge Playwright session and run `scripts/capture_response_showcase.js`. This creates only fictional fixtures in that temporary service.
5. Close the temporary server with Ctrl+C to remove its schema. Exact generated schema names are recorded under ignored `.local/` if a process kill interrupts normal cleanup.

No physical phone was used. A screenshot refresh verifies current rendering and the selected paths described above; it does not rerun every historical workflow or establish full accessibility, production readiness or field accuracy.
