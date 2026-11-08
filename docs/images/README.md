# Product screenshot provenance

These images were refreshed from the running local Sampati application on **8 November 2026**, using Microsoft Edge through Playwright. They include the user-approved painted folk-art logo and current civilian-welfare descriptor. They show the shared fictional demo. They are real product captures, not generated interface mockups.

| File | Route / state | Viewport |
| --- | --- | --- |
| `welcome.png` | `/`, entry screen | 1440 × 900 |
| `register.png` | `/#demo/workspace`, accepted fictional records | 1440 × 1000 |
| `import-preview.png` | `/#demo/import`, a generated sample in preview, before confirmation | 1440 × 1000 |
| `history.png` | `/#demo/history`, existing confirmed demo batches | 1440 × 1000 |
| `mobile.png` | `/#demo/workspace`, touch-enabled mobile browser context | 390 × 844 |

The captures do not show a personal organisation, sign-in credentials, source keys or recovery codes. Capturing the sample preview does not confirm it or change accepted aircraft records. Freshness and relative times describe capture time; counts reflect the existing fictional demo state.

The bird artwork is ImageGen-assisted and reused from the app's [recorded assets](../../frontend/public/artwork/provenance.json); the approved emblem has its own [prompt and approval record](../../frontend/public/artwork/logo-provenance.json). The app uses OFL-licensed Yatra One display lettering. The mobile capture is browser emulation, rather than evidence from a physical phone.

The refresh completed with zero browser console errors and no welcome-page width overflow at 1440/1024/390/320px. Accepted demo records and import history remained unchanged at workspace revision 3.

## Relief-workflow showcase - 8 November 2026

`scripts/capture_showcase.js` captured the following from the compiled local release on port8000, using Edge via Playwright. They show the shared fictional demo. All desktop captures preserve the complete1440×1040viewport; the mobile image preserves390×844. Screens are not generated mockups. Clicking a README image opens its original file.

| Image | Actual route and state |
| --- | --- |
| [Remaining needs](remaining-needs.png) | `#demo/deliveries`, Request follow-up;40kits requested,10source-confirmed and30still needed. |
| [Relief overview](relief-overview.png) | `#demo/overview`, review queues and handover context. |
| [Incident review](incident-review.png) | `#demo/incidents`, dated assessments and review states. |
| [Aid inventory](aid-inventory.png) | `#demo/inventory`, distinct ledger on-hand, reserved and available stock. |
| [Delivery tracking](delivery-tracking.png) | `#demo/deliveries`, partial and full source-confirmed shipment records. |
| [Automation Inbox](automation-inbox.png) | `#demo/automation`, pending/invalid received files. |
| [Intake evidence](intake-evidence.png) | `#demo/automation`, `DEMO-INTAKE-001` source/policy context and new draft proposal. |
| [Phone layout](relief-mobile.png) | Touch-enabled emulation at`#demo/automation`. |

The capture completed with zero console errors, zero writes and unchanged accepted demo revision/import and module record counts. Fixed dates and freshness describe capture time. The images contain no private organisation, credentials, source keys or recovery codes. The visible quantities describe fictional software records, not independently verified physical supplies.

The responsive project panels `sampati-project.svg` and `sampati-project-mobile.svg` are authored vector layouts. They embed the complete corresponding desktop/mobile capture without cropping or altering its pixels, retaining the approved identity within the app. Yatra One title outlines preserve its OFL-licensed display lettering; the source font remains bundled with its licence. Panel text, layout and screenshots belong to Sampati. No reference-project assets are reused. These panels introduce the project on Pratham's GitHub profile; the actual application interface is unchanged.
