# Delivery tracking: H03

H03 connects a reviewed relief request and its inventory issue to shipment tracking, source-confirmed arrivals and undelivered returns. It records human decisions and source evidence. It does not dispatch transport, grant flight clearance or independently verify that physical goods arrived.

Open **Delivery tracking** in the sidebar, `#deliveries` for your organisation or `#demo/deliveries` for read-only fictional examples. Use **Request follow-up** to inspect reviewed needs still awaiting confirmed delivery. No external service credentials are required.

## Record the chain

1. In Relief requests, create and review a fictional need with an explicit quantity and unit.
2. In Aid inventory, receive supplies, reserve the matching request and record an actual issue. An issue means goods left the recorded store; it is not an arrival.
3. Choose **New shipment**, search/select the issue, enter the portion assigned to this shipment and check the receiving organisation/destination. Save a draft. The assignment changes no inventory balance.
4. **Approve tracking record** with a source reference, source name/time and reason. Approval is by an owner/editor and may be by the same person who created it; independent approval is not enforced. Transport operators retain dispatch authority.
5. **Record dispatch evidence** only from an actual source report. This changes the tracking state to In transit; it does not command a vehicle or aircraft.
6. **Confirm arrival** from a receiving report. Enter its reference, source organisation/name, observation time, exact quantity and evidence note. Partial confirmations retain the unresolved remainder. Full source-confirmed quantity derives Delivered; there is no direct "set delivered" action.
7. Record undelivered goods returned to the original store using **Record undelivered return**. Shipment evidence and inventory restocking commit together. The shipment closes when confirmed arrivals plus returned quantities resolve its entire quantity.
8. Inspect **Shipment history** and **Request follow-up**. Planned assignments, dispatch, arrivals and returns remain different facts. No request review state is automatically rewritten as fulfilled.

References and source notes are recorded text, not uploaded proof or independently authenticated evidence. Use fictional organisation-level details in this prototype, without individual beneficiary or patient records.

## States and permitted actions

| State | Permitted actions |
| --- | --- |
| Draft | Approve tracking record; cancel unstarted shipment. |
| Approved | Record dispatch evidence; cancel unstarted shipment. |
| In transit | Confirm arrival; record undelivered return. |
| Partly delivered | Confirm arrival; record undelivered return; correct a prior arrival quantity. |
| Delivered | Correct a prior arrival quantity if its source overstated delivery. |
| Closed with returns | Correct a prior arrival quantity if one exists. A fully returned shipment has no arrival to correct. |
| Cancelled | None. The reference and history remain. |

The quantities determine the state after an arrival, return or correction:

- **Unresolved = shipment quantity − net confirmed delivered − returned.**
- Confirmed delivered equals the full shipment quantity → Delivered.
- Delivered plus returned equals the full shipment quantity → Closed with returns.
- Otherwise, positive delivered → Partly delivered; zero delivered → In transit.

Cancellation is available before recorded dispatch. It frees the tracking assignment without moving issued stock back to a store. After dispatch, resolve undelivered supplies through source-backed returns; do not cancel to erase transit evidence. Loss/damage resolution and physical returns after confirmed delivery require separate workflows and are not implemented here. Such unresolved quantities remain visible rather than being fabricated as returns.

## Arrival corrections

**Correct arrival quantity** subtracts an overstated amount from one original arrival confirmation. It requires the original event, a new evidence reference/time, source and reason. The amount cannot exceed that confirmation's remaining uncorrected quantity. The original event and its original after-state remain visible; the correction is another event.

A correction changes recorded confirmation totals and may reopen a resolved shipment. It does not move inventory. Do not use it to represent a physical return from a beneficiary. If previously overstated goods are actually undelivered and received back at the original store, record that physical return separately with its own source evidence.

History loads 50 events per page. Load older history to select an earlier confirmation for correction. Records, destinations, original links and quantities are immutable after draft creation; cancel an unstarted draft and create a new reference to correct its identity/details. There is no delete endpoint.

## Exact limits and return integrity

Every quantity has the inventory item's fixed unit, uses exact decimal storage and permits up to three decimal places. Quantities must be positive and no greater than 1,000,000,000. No automatic unit conversion or cross-unit total is provided.

An issue can have multiple shipment drafts, but cannot assign the same stock twice:

**Unassigned issue quantity = original issue − all inventory returns − active shipment claims.**

A noncancelled shipment's claim is its quantity minus its own recorded returns. It includes confirmed deliveries, so already delivered supplies cannot be returned through the generic inventory return form. An undelivered shipment return increases inventory returns and decreases that shipment's claim by the same amount, preserving the issue boundary. It links to the original stock issue and appears in both histories.

Use Delivery tracking for stock already assigned to a shipment. The normal inventory return form permits only unassigned issue quantity, or quantity freed by cancelling an unstarted shipment. A client cannot bypass this by supplying an internal shipment identifier.

Shipment allocations also cannot exceed the current request quantity across all issues/stores. New drafts, approval and dispatch require a currently reviewed request with matching category/unit. Request edits cannot reduce quantity below active/delivered shipment claims or change their units/category. Resolve unstarted assignments or undelivered returns first. Correcting an arrival alone does not free the shipment's assignment.

If a request is later cancelled/unreviewed, new drafts/approval/dispatch are blocked. Already dispatched shipments can still record actual arrivals, returns and corrections: changing a need's review state must not erase source facts. Request follow-up lists currently reviewed requests; other requests and their shipment histories remain available in their registers.

## Source times, retries and access

- Each approval, dispatch, arrival, return, cancellation or correction requires a unique evidence reference, source name, timezone-bearing source timestamp and nonblank reason. Text is trimmed. References are 1–64 ASCII characters: letter/digit first, then letters/digits/dot/underscore/slash/hyphen; uniqueness is case-insensitive within the organisation's evidence register.
- Source names allow 2–120 characters, reasons 1–500. Draft receiving organisations allow 2–120, destinations 2–160, notes up to 1,000. Extra/server-owned fields are rejected.
- Future source times beyond a five-minute clock-skew tolerance are rejected. Dispatch cannot precede the approval source time; arrivals/returns/corrections cannot precede dispatch. A correction cannot precede its original confirmation. Source time, server receipt time and actor are retained separately. Recording order is not presented as observation order.
- The server resolves the organisation from session membership. Owners/editors write; viewers read; the shared demo is read-only. Composite database foreign keys scope request, issue, shipment, parent confirmation and stock-return links. Foreign IDs return404.
- Mutations acquire the workspace lock, then the shipment/stock position as needed. Current shipment version is required; a return additionally requires the displayed stock version. A competing action returns409 and requires **Refresh shipment details**. Refresh resets the unsaved action form.
- Submission keys remain stable for retries. Same key or reference plus equivalent canonical content returns the existing record, without a second delivery/restock. Changed evidence conflicts. Duplicate lookup happens before stale-version checks, so a committed return whose response was lost is safe to retry. Quantities, reference case and equivalent timezone instants compare canonically.
- Shipment event and stock return are atomic. If stock version/limit checks fail, neither tracking nor stock changes. A stock identifier already used outside that shipment event cannot be adopted and counted as a fresh shipment return.

## Request follow-up

**Still needed = requested quantity − net source-confirmed arrivals**, per request and unit. Drafts, approvals, dispatch reports and stock issues do not reduce that number. Corrected arrivals increase it again. Returned undelivered supplies never count as delivered.

The table also shows assignment quantity, including delivered portions, to explain what is already committed to tracking records. This is not an extra delivered total. Use the **Only needs awaiting delivery** filter, literal-text search and 20-row pages. Cancelled/unreviewed requests are excluded from this follow-up view but their evidence is retained.

## Examples and code

Setup adds two read-only fictional shipments once against the pre-existing shelter issue: one partially delivered, one fully delivered, with eight evidence events. It does not alter the original six inventory events. The reviewed shelter request shows 10 kits source-confirmed out of 40, with 30 still needed. Rerunning the seed leaves source times and history unchanged.

| File | Learning purpose |
| --- | --- |
| `backend/app/deliveries.py` | State transitions, exact fulfilment, source rules, safe retries and atomic cross-ledger returns. |
| `backend/app/inventory.py` | Protecting shipment-assigned stock from direct generic returns. |
| `backend/app/relief.py` | Preventing request edits from invalidating active/delivered shipment quantities. |
| `backend/migrations/versions/007_deliveries.py` | Additive tables, composite organisation links and balance constraints. |
| `frontend/src/Deliveries.tsx` | Explicit draft/action forms, role-aware controls, partial states, follow-up and history paging. |
| `backend/tests/test_deliveries.py` | Validation, permissions, concurrency, chronology, correction and retry scenarios. |
| `scripts/browser-deliveries.js` | Real Edge walkthrough including partial arrivals and a lost-return-response retry. |

Executed evidence belongs in [VERIFICATION.md](VERIFICATION.md). Field validation, independent evidence verification, transport/mission planning, live providers and production hosting remain separate work.
