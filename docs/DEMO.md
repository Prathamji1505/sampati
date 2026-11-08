# Sampati demonstration guide

## Current flood-response workflow

Use a private organisation with an owner/editor account for writes; the shared incident, request, stock and delivery examples are read-only.

1. Open **Incident review → Record assessment → Use fictional example**.
2. Preview the assessment, inspect dates/evidence/uncertainty, then record it as needing review.
3. Review it with a reason. A review records an evidence decision; confirm actual local needs separately.
4. Choose **Create linked relief request** and enter the requesting organisation, supply description, quantity and unit from a fictional local report.
5. Submit/review the request and inspect its attributed history.
6. Add a supply item/store in Aid inventory, record a receipt, reserve the reviewed request and record a partial issue or return. Compare the separate source count and ledger balance.
7. Create/approve an issue-linked shipment draft, record actual dispatch evidence, then confirm a partial arrival or undelivered return. Inspect Shipment history and Request follow-up.
8. Explain the next dependencies: verified context, optional source adapters, user evaluation and production hosting. Aircraft reports support review; operators retain dispatch authority.

[Incident instructions](INCIDENTS.md) · [Request instructions](RELIEF_REQUESTS.md) · [Roadmap](ROADMAP.md).

## Supporting aircraft-report demonstration

For the current flood-response path, open `/#demo/incidents` and inspect a fictional assessment's observation/generation/receipt times, uncertainty and review history. Then inspect `/#demo/relief` for separately recorded needs. These examples are read-only.

To demonstrate the connected write workflow, create a temporary fictional organisation, open **Incident review → Record assessment → Use fictional example → Preview assessment → Record as Needs review**. Record a reasoned review, then choose **Create linked relief request**, enter the locally confirmed quantity/unit and save a draft. Inspect both histories. [Detailed incident walkthrough and contract](INCIDENTS.md). This requires no external service credentials and does not demonstrate a live connector, stock allocation, dispatch or delivery.

## Aid-inventory walkthrough

Open `/#demo/inventory` to compare the water item's recorded balance of 120 packs with its separate source count of 113 packs. Open the shelter position to follow its reviewed-request reservation, partial issue and return. These are stable, read-only fictional examples, not real stock.

In an empty fictional organisation, use **Items and locations** to create an item with a fixed unit and a store. **Record stock** opens their position. Record a receipt, then a source count and show that only the receipt changes ledger balances. Create/review a matching relief request; record its reservation, partial issue, release or return. Inspect source dates, actors, original references and after-event balances in Stock history. An issue does not prove delivery. [Inventory contract and limits](INVENTORY.md).

## Delivery walkthrough

Open `/#demo/deliveries`. DEMO-SHIP-001 has 5 of 8 shelter kits source-confirmed; DEMO-SHIP-002 has 5 of 5 confirmed. **Request follow-up** shows 10 confirmed out of the reviewed 40-kit request and 30 still awaiting confirmation. All evidence is fictional.

For writes, create a shipment draft from an unassigned inventory issue, approve its tracking details, record actual dispatch evidence and enter receiving-source references/quantities for arrivals. Record undelivered returns through the shipment so stock and tracking change together. Try a correction to an overstated arrival; its original evidence remains and inventory does not move. [Full delivery instructions and limits](DELIVERIES.md).

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

## Relief automation and handover

Open **Automation inbox** in the demo to inspect the three fixed fictional files: a new draft proposal, a conflicting reference and an invalid quantity. They are read-only and retain their original dates. In your own organisation, open **Connected sources**, add a source, save its private key and choose **Try fictional example**. Inspect its evidence, accept the new draft with a reason, then follow **View request → View intake evidence**.

An owner may change **Incoming files** to **Create new drafts automatically**, with a reason. A new valid, fresh example then creates drafts directly; conflicting or stale reports remain for review. Submit and review a request separately before reserving supplies. The watcher instructions are in [AUTOMATION.md](AUTOMATION.md).

Open **Overview** for pending review queues and earliest outstanding reviewed needs. Export the dated relief overview for a handover. Quantities remain per request and unit. Actual source-backed arrivals reduce the remainder; issues and drafts do not.

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
