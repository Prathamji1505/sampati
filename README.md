<h1 align="center">SAMPATI · सम्पाति</h1>
<p align="center"><strong>From scattered aircraft reports to a clear, shared picture.</strong></p>
<p align="center">Air Operations &amp; Resource Decision Support</p>

<p align="center">
  <a href="#the-problem">The problem</a> ·
  <a href="#meet-sampati">The product</a> ·
  <a href="docs/DEMO.md">Try the demo</a> ·
  <a href="#where-this-can-grow">Business direction</a> ·
  <a href="docs/SETUP.md">Run locally</a>
</p>

**Sampati is a workspace for people who need to understand changing aircraft reports.** It brings CSV and Excel files together, explains what has changed, highlights information that needs attention, and keeps a history of accepted updates. A person reviews changes before they enter the shared register.

The project explores a practical foundation for civilian fleet coordination: **make information understandable, current in context, and traceable before building more advanced decision support.**

![Sampati's actual welcome screen with its bilingual identity and original soaring-bird artwork](docs/images/welcome.png)

<p align="center">
  <a href="https://github.com/Prathamji1505/sampati/actions/workflows/ci.yml"><img src="https://github.com/Prathamji1505/sampati/actions/workflows/ci.yml/badge.svg" alt="Build and tests"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-d6a05a?style=flat-square" alt="MIT licence"></a>
  <img src="https://img.shields.io/badge/React_19-TypeScript-b72e48?style=flat-square" alt="React and TypeScript">
  <img src="https://img.shields.io/badge/FastAPI-PostgreSQL-b72e48?style=flat-square" alt="FastAPI and PostgreSQL">
</p>

| Project at a glance | |
| --- | --- |
| **Product** | Aircraft-report management, source-data checks and human-reviewed updates |
| **Intended users** | Civilian fleet-data coordinators, reporting teams and relief-logistics coordinators; audiences to validate through pilots |
| **Working today** | A complete local workflow from file intake through review, confirmation, register, exports and history |
| **Demonstration** | Fictional civilian records; no paid API or model download required |
| **Engineering evidence** | 59 backend tests in the recorded verification, successful hosted CI and desktop/mobile browser checks |
| **Stage** | Working prototype with public source; hosted application not yet configured |

## The problem

Imagine taking over a shift and receiving several aircraft-status spreadsheets. One file arrived recently but contains an older report. Another marks an aircraft's status as unknown. A third repeats information already imported. You need to know which values are accepted, which source supplied them, and what still needs attention.

The difficult part is keeping a coherent picture as information changes.

| What makes review difficult | How Sampati responds |
| --- | --- |
| Reports are spread across separate files. | Bring accepted records into one searchable organisation register. |
| Arrival time can be mistaken for observation time. | Show source timestamps and receipt times separately. |
| An older report can overwrite newer information. | Block older updates and contradictory values at the same source time. |
| Repeated uploads can create duplicate history. | Recognise equivalent datasets and return the original import. |
| Reviewers need to explain a change later. | Preserve import attribution and before/after values. |
| A connected source sends an unexpected update. | Hold incoming files in a review inbox until an authorised person confirms them. |

## Meet Sampati

Sampati gives a reviewer four connected views of the same information:

- **The register:** what the organisation has currently accepted.
- **The review:** what a new file proposes to change.
- **Report checks:** which source records need attention, why, and what to review next.
- **The history:** how the register reached its current state.

![Actual aircraft register with fictional records, reported status, sources, timestamps and freshness](docs/images/register.png)

*Actual product capture with fictional records, 7 November 2026. Freshness reflects capture time. [Screenshot provenance](docs/images/README.md).*

Three questions stay visible throughout the workflow: **What did the source report? When did it report it? Who accepted the change?** Reported availability and data freshness remain separate, so a fresh report with an unknown status is still shown honestly.

## How it works

![Receive, review, confirm and trace: Sampati's report-to-register workflow](docs/images/review-workflow.svg)

1. **Bring in a report.** Upload CSV or Excel, use a fictional sample, or receive a file through a scoped source connection.
2. **Understand the update.** Read validation errors and compare new, updated and unchanged records. Previewing a file does not change accepted aircraft data.
3. **Make an explicit decision.** An authorised reviewer confirms an eligible batch. Records and their change history save together.
4. **Work from the accepted picture.** Search, filter, inspect findings, export records and follow the history. Incoming files remain separate until accepted.

![Actual import review showing proposed fictional changes before confirmation](docs/images/import-preview.png)

### A small example that explains the value

Consider the fictional aircraft **DEMO-001 / Cedar** already in the register:

| What arrives next | What happens |
| --- | --- |
| A file whose source timestamp is earlier than Cedar's accepted report | The older update is blocked from replacing newer information. |
| A corrected file with a later source timestamp | The reviewer sees the proposed changes and can confirm them. |
| The exact accepted file arrives again | Sampati recognises the repeat and avoids a duplicate import. |
| A connected file disagrees at the same source timestamp | It stays pending; report checks explain the conflict for review. |

The core promise is simple: **a file arriving does not automatically make it the accepted truth.** One invalid row rejects the batch, and an aircraft missing from a file is not silently deleted.

## What is already built

| Product area | What a user can do |
| --- | --- |
| **Aircraft register** | Search aircraft and sources, filter status/freshness, inspect source details and export the current selection as Excel, CSV or JSON. |
| **Import review** | Use CSV/Excel templates, inspect actionable errors, preview changes and explicitly confirm a batch. |
| **Report checks** | Examine old/future timestamps, unknown status, missing names and pending-file disagreements. Expand evidence, inspect the source record, paginate results and export filtered findings with check time, rule version and register revision. |
| **Overview** | See counts, source coverage and attention rules computed from accepted records. |
| **Data connections** | Create limited ingestion keys, rotate or disable them, receive files into an inbox and review or reject datasets. A local watcher can submit changed files. |
| **Organisation teams** | Invite a specific account, assign owner/editor/viewer roles and switch between verified memberships. |
| **Accounts** | Sign in, change a password, revoke other sessions and recover access with saved one-time codes. |
| **History and continuity** | Inspect confirmed batches and before/after values, retain records across restarts, create backups and rehearse a restore in a disposable database. |

<details>
<summary><strong>Explore the history and mobile interface</strong></summary>

![Confirmed fictional imports in the history view](docs/images/history.png)

<img src="docs/images/mobile.png" width="300" alt="Sampati register in a 390-pixel touch-enabled browser context">

The mobile image is browser emulation. Tables scroll within their own region to preserve readable fields.

</details>

## Who this is designed to help

The initial product hypothesis centres on teams that receive structured civilian fleet reports and need a review process around them.

| Potential user | Task Sampati is designed to support |
| --- | --- |
| **Fleet-data coordinator** | Bring recurring reports into a coherent register and identify records needing follow-up. |
| **Reporting or review team** | Check proposed updates, resolve source disagreements and explain accepted changes. |
| **Relief-logistics coordinator** | Organise source-provided aircraft information with visible timestamps and uncertainty. |
| **Organisation administrator** | Give teammates appropriate access and limit what an external source can submit. |

These are intended audiences. Pilot interviews and observed workflow trials are the next step in validating the fit.

## Where this can grow

The broader vision is a source-aware civilian coordination workspace built on reliable report management. The current implementation supplies the review and traceability foundation.

| Direction | Next milestone | Evidence to collect |
| --- | --- | --- |
| **Validate the workflow** | Trial the review process with authorised civilian users and suitable sample reports. | Completion time, errors caught, reviewer comprehension and repeat use. |
| **Make it accessible to teams** | Package hosted deployment with HTTPS, managed secrets and off-device backups. | Reproducible deployment, access-boundary tests, restore checks and reliability measurements. |
| **Improve reporting fit** | Refine templates and connectors around real reporting formats. | Onboarding effort, recurring format problems and source-maintenance effort. |
| **Add useful context** | Introduce airport or weather context for a defined civilian user task. | Provenance, update age, failure behaviour and demonstrated user value. |
| **Evaluate advanced decision support** | Define a specific task and suitable authorised evidence before selecting rules or models. | Baselines, evaluation criteria and understandable uncertainty. |

**Commercial hypothesis:** an organisation-based subscription for shared workspaces, with onboarding and connector support as possible services. Pricing, willingness to pay, acquisition costs and retention need pilot evidence. Revenue and customer adoption have not been established.

## The engineering behind the workflow

| Layer | Technology | Responsibility |
| --- | --- | --- |
| **Interface** | React 19 · TypeScript · Vite | Register, review, checks, team tools and responsive navigation. |
| **Application service** | Python · FastAPI · Pydantic | Validate inputs, check access and handle review/confirmation. |
| **Persistence** | PostgreSQL · SQLAlchemy · Psycopg | Organisation-scoped records, sessions, imports and audit history. |
| **Schema evolution** | Alembic | Versioned database changes that retain existing data. |
| **Verification** | pytest · browser checks · GitHub Actions | Import rules, permissions, source scope, migrations and build integrity. |

The review uses a **signed preview bound to its content, importing account and workspace revision**. Confirmation checks it again and commits related changes atomically. This connects what a reviewer saw with what the database accepts.

Source keys can submit to their own connection; approval stays with a reviewer. Organisation endpoints check current membership and roles. The service enforces these boundaries alongside the interface controls.

[Architecture and source map](docs/ARCHITECTURE.md) · [Account model](docs/ACCOUNTS.md) · [Data dictionary](docs/DATA_DICTIONARY.md)

## Try it in three minutes

After starting the app:

1. Choose **Enter workspace** to open the fictional demo.
2. Open **Import dataset → Use sample**, review the preview, then choose **Confirm import**.
3. Search for `DEMO-001`, inspect its source and try the status/freshness filters.
4. Open **Report checks** to understand findings, then **Import history** to inspect the accepted update.
5. Reload to see the persisted register. Re-upload the same saved file to demonstrate repeat protection.

[Full demo script](docs/DEMO.md) · [Submission brief](docs/SUBMISSION.md)

### Run locally

The documented launcher targets Windows/PowerShell with Python 3.12, Node.js compatible with Vite 7, npm and installed PostgreSQL binaries.

```powershell
git clone https://github.com/Prathamji1505/sampati.git
cd sampati
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-lock.txt
npm --prefix frontend ci
.\.venv\Scripts\python.exe scripts\dev.py setup
.\.venv\Scripts\python.exe scripts\dev.py start
```

Open **[127.0.0.1:5173](http://127.0.0.1:5173)**. Setup generates local secrets and a project-owned PostgreSQL cluster on loopback port 55432. [Prerequisites and troubleshooting](docs/SETUP.md).

## Evidence and current scope

Recorded verification includes **59 passing backend tests**, frontend builds, migration checks, organisation-isolation tests, source-key/inbox checks, browser journeys and a backup/restore rehearsal. [Hosted CI](https://github.com/Prathamji1505/sampati/actions) and [verification notes](docs/VERIFICATION.md) identify the tested builds and limits.

This release uses fictional civilian data in a local application. Its checks describe **source-record quality**; reported status remains source information. Live tracking, trained predictions, operational dispatch, airworthiness certification and production hosting are outside the implemented release. Planned capabilities above remain separate from the working prototype.

[Requirements and acceptance map](docs/REQUIREMENTS.md) · [Security](SECURITY.md) · [Detailed local workflow](docs/LOCAL_WORKFLOW.md)

## The identity behind the product

**Sampati** draws on the far-reaching sight of Sampati in the Ramayana: a fitting idea for a product concerned with seeing information in context. The bilingual wordmark, soaring bird, crimson, charcoal, ivory and restrained saffron give that idea a distinct visual identity.

Built by **[Pratham Sengar](https://github.com/Prathamji1505)**. Source code is available under the [MIT licence](LICENSE). Third-party packages and fonts retain their own terms. Codex assisted implementation and documentation; ImageGen assisted the original artwork. [Attribution and asset provenance](THIRD_PARTY_NOTICES.md) · [Contributing](CONTRIBUTING.md).
