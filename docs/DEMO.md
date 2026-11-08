# Sampati demonstration guide

## Current flood-response workflow

Use a private organisation with an owner/editor account for writes; the shared demo examples are read-only for incidents and requests.

1. Open **Incident review → Record assessment → Use fictional example**.
2. Preview the assessment, inspect dates/evidence/uncertainty, then record it as needing review.
3. Review it with a reason. A review records an evidence decision; confirm actual local needs separately.
4. Choose **Create linked relief request** and enter the requesting organisation, supply description, quantity and unit from a fictional local report.
5. Submit/review the request and inspect its attributed history.
6. Explain the next dependencies: aid inventory, delivery tracking and a verified live SATQueryAI adapter. Aircraft reports are supporting information; operators retain dispatch authority.

[Incident instructions](INCIDENTS.md) · [Request instructions](RELIEF_REQUESTS.md) · [Roadmap](ROADMAP.md).

## Supporting aircraft-report demonstration

For the current flood-response path, open `/#demo/incidents` and inspect a fictional assessment's observation/generation/receipt times, uncertainty and review history. Then inspect `/#demo/relief` for separately recorded needs. These examples are read-only.

To demonstrate the connected write workflow, create a temporary fictional organisation, open **Incident review → Record assessment → Use fictional example → Preview assessment → Record as Needs review**. Record a reasoned review, then choose **Create linked relief request**, enter the locally confirmed quantity/unit and save a draft. Inspect both histories. [Detailed incident walkthrough and contract](INCIDENTS.md). This does not require a SATQueryAI API key and does not demonstrate a live connector, stock allocation, dispatch or delivery.

## Aircraft-report foundation

Start the application using [setup](SETUP.md). This walkthrough uses fictional data and requires no account or paid service. It works with the shared local demo; do not use real organisational records.

| Time | Action | What the reviewer should notice |
| --- | --- | --- |
| 0:00–0:20 | Open Welcome, then choose **Enter workspace**. | Sampati introduces the product before opening the register. |
| 0:20–1:00 | Choose **Try sample data**, or open **Import dataset** and select the downloaded sample. | The file is validated and changes are previewed before anything is saved. |
| 1:00–1:20 | Review new/updated/unchanged counts, then choose **Confirm import**. | Confirmation is an explicit decision. A repeat of the exact saved file is a no-op. |
| 1:20–2:00 | Search for `DEMO-001`, change a status or freshness filter and open its details. | Reported status, source timestamp, receipt time and freshness answer different questions. |
| 2:00–2:30 | Open **Import history** and inspect a confirmed import. | Reviewers can follow before/after values and confirmation attribution. |
| 2:30–3:00 | Reload the page. Explain the organisation and source-connection paths. | Accepted records persist. Incoming connected files still need a human review. |

The built-in sample generates timestamps when requested. Save the downloaded file and reuse that exact file when demonstrating replay protection. Existing demo records can make the next sample an update rather than a first import; the preview explains which applies. Screenshot counts are an example state, not a required starting state.

## Optional deeper demonstration

1. Create an account at `/#register` with a password of at least 12 characters. Your new organisation starts empty.
2. Import a fictional CSV or Excel file and confirm it in that organisation.
3. Visit **Data connections**, create a source and privately copy its once-shown key. Submit a fictional update using the simulator or [file watcher](LOCAL_WORKFLOW.md#connect-a-changing-file).
4. Show that a pending file has not changed accepted records. Preview it from the inbox, then confirm it.
5. Use a second account to demonstrate a targeted invitation, verified membership switching and a viewer role that cannot import.

Do not record source keys, passwords or recovery codes in a public demo video. The public screenshots use the shared fictional workspace and contain none of these credentials.

## Useful failure cases

Use files in [`examples/`](../examples/) to demonstrate validation: missing fields, invalid timestamps, invalid statuses and duplicate aircraft IDs. `older-report.csv` demonstrates older-report rejection after its matching baseline; `newer-update.csv` demonstrates a permitted later update. The fixtures retain fixed timestamps, so their freshness depends on the current time.

## A concise explanation

> Sampati brings aircraft reports into one reviewable workspace. A reviewer sees every proposed change before it becomes accepted data, and every record keeps its source and history. This prototype demonstrates that workflow with fictional civilian reports; it does not connect to live aircraft or decide whether an aircraft can fly.
