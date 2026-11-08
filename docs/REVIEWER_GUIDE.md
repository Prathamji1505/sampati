# A short tour of Sampati

Start the local app using [SETUP.md](SETUP.md). Use the shared **Demo workspace** to inspect fixed fictional records. Create your own organisation for a complete write walkthrough. No paid API or model download is required.

## See the result first

1. Open **Delivery tracking → Request follow-up**.
2. Inspect the fictional shelter request `DEMO-REL-003`: **40 kits requested, 10 source-confirmed arrivals, 30 still needed**.
3. Open **Delivery tracking** and compare `DEMO-SHIP-001` (partly delivered) with `DEMO-SHIP-002` (delivered). Planned, issued and arrived quantities remain distinct.
4. Open **Aid inventory** to inspect separate on-hand, reserved and available quantities. A count report is separate evidence; it does not silently replace the ledger.
5. Open **Overview** for pending queues and earliest outstanding needs. Export the dated relief snapshot for a handover.

These are demonstration records. Their original source dates are retained, so freshness changes with time.

## Inspect the incoming evidence

In **Automation Inbox**, inspect `DEMO-INTAKE-001` for a new draft proposal, `DEMO-INTAKE-002` for a conflicting reference and `DEMO-INTAKE-003` for an invalid quantity. Open the source context, original text and history. The fictional source is paused; demo decisions are read-only.

In **Incident review**, inspect the dated assessment, source, uncertainty and reasoned review. Population estimates do not become supply quantities automatically.

## Run the complete workflow in your own organisation

1. Sign up and open **Incident review → Record assessment → Use fictional example**. Preview it, record it and review it with a reason.
2. Start a linked relief draft. Enter the fictional requesting organisation, locality, supply, quantity/unit and deadline. Submit and review the request.
3. In **Aid inventory**, add the matching item/unit and a store, record a receipt, reserve the reviewed request and record an issue.
4. In **Delivery tracking**, create a draft from that issue. Review it, record dispatch evidence and a partial arrival, then inspect the remainder. Record undelivered goods received back at the original store with the return action.
5. In **Automation Inbox → Connected sources**, add a source and save its private key. Try a fictional example, inspect the preview and accept new drafts with a reason. Follow **View request → View intake evidence**.
6. An owner may explicitly enable automatic new drafts for a trusted source. Fresh, valid, conflict-free files can create drafts; people still submit and review the needs. [CSV/JSON watcher instructions](AUTOMATION.md).

Use fictional organisation-level information. Keep keys, passwords and recovery codes out of public demonstrations.

## Go deeper

[Incidents](INCIDENTS.md) · [Requests](RELIEF_REQUESTS.md) · [Inventory](INVENTORY.md) · [Deliveries](DELIVERIES.md) · [Automation](AUTOMATION.md) · [Verification](VERIFICATION.md)
