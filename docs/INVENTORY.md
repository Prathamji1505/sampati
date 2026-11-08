# Aid inventory: H02

H02 records civilian supply items, storage locations and an attributable stock ledger. It connects reviewed relief needs to reservations and issues. An issue records supplies leaving a store; **delivery confirmation remains H03**.

[H03 Delivery tracking](DELIVERIES.md) is now implemented separately. Once an issue is assigned to a shipment, use its delivery workflow for source-backed undelivered returns. The generic inventory return form permits only unassigned quantity; shipment arrivals/corrections never silently change store balances.

Open **Aid inventory** in the sidebar, `#inventory` for your organisation or `#demo/inventory` for read-only fictional examples. Owners/editors record events; viewers inspect. Private organisations begin empty.

## First walkthrough

1. Open **Items and locations**, create a supply item with a fixed code/category/unit, then create a storage location. A catalog entry alone creates no stock.
2. Return to the stock register and choose **Record stock**. Select the item/store and open its position.
3. Choose **Receipt**, enter a positive quantity, unique event reference, source name/time and evidence note, then explicitly record the event.
4. To keep an external count, use **Source count report**. It appears separately and never changes ledger balances. A zero count is valid.
5. Create and review a relief request with the same category and unit. Choose **Reservation**, search the reviewed request and record the quantity being held. Suitability remains a human decision; matching a category/unit does not establish that two supplies are interchangeable.
6. **Issue reserved supplies** references the original reservation. **Release reservation** frees its unissued quantity. **Return issued supplies** references the original issue and cannot exceed its unreturned quantity.
7. Read **Stock history** for sources, source/receipt times, reasons, actor labels, original record references, request references and after-event balances. Load older history to find earlier reservations/issues.

Use fictional records for this local prototype. It does not need patient or individual beneficiary data.

## What each quantity means

| Quantity | Meaning |
| --- | --- |
| Recorded on hand | Exact ledger balance after recorded receipts, issues, returns and adjustments. It is not a physical-stock certification. |
| Reserved | Stock held by active, unissued/unreleased reservation quantities. |
| Available | Recorded on hand minus reserved. This is available ledger stock, not a dispatch approval. |
| Latest source-reported count | A separate report selected by observation time, with receipt order breaking equal-time ties. Receiving an older report cannot make it the latest count. |

All quantities stay in the item's fixed unit. There are no automatic conversions, cross-unit totals or inferred supply quantities. A count observed earlier can legitimately differ from today's ledger after later movements; inspect dates and evidence before a correction. Reports never reconcile the ledger automatically.

## Event rules

| Event | On hand | Reserved | Link / limit |
| --- | --- | --- | --- |
| Receipt | + quantity | Unchanged | Source receipt/evidence required. |
| Reservation | Unchanged | + quantity | Currently reviewed request with matching category/unit; limited by available stock and that request's remaining allocation. |
| Release reservation | Unchanged | − quantity | Original reservation, up to its unissued/unreleased quantity. Allowed after a request changes/cancels. |
| Issue reserved supplies | − quantity | − quantity | Original reservation; request must still be reviewed, compatible and within its current quantity. Does not confirm delivery. |
| Return issued supplies | + quantity | Unchanged | Original issue, up to its unreturned quantity. Allowed after cancellation. Does not recreate the old reservation. |
| Source count report | Unchanged | Unchanged | A dated report; quantity may be zero. |
| Adjustment in | + quantity | Unchanged | New reasoned correction with source evidence; original events retained. |
| Adjustment out | − quantity | Unchanged | New reasoned correction; cannot remove reserved stock or make on hand negative. |

Recorded on hand is always between zero and 1,000,000,000; reserved is between zero and on hand. Except reports, event quantities must be positive. Quantities use exact decimals with at most three decimal places, and API responses use decimal strings. The UI's numerical input does not determine the server's arithmetic.

## Request allocation rules

For one request, outstanding reservations plus net issued stock equals **reservations − releases − returns**. Issuing consumes a reservation rather than adding a second allocation. Returns free the issued commitment without reopening the old reservation.

This commitment is checked across all items and storage locations in the organisation, not separately per store. It cannot exceed the reviewed request quantity. If a draft correction changes a request's unit/category while old allocations remain, resolve incompatible reservations/issues with releases/returns before making new allocations. Old units are never added to the new unit. A cancelled/unreviewed request blocks new reservations and issues; release/return remain possible. The system does not automatically cancel ledger events or infer a delivery from request status.

## Identity and evidence

- Item code, name, category and unit stay fixed after creation. Location code, name and locality also stay fixed. Use a new code for a different identity. This preserves the meaning of older ledger entries.
- Codes and event references are 1–64 ASCII characters: letter/digit first, then letters/digits/dot/underscore/slash/hyphen. Uniqueness is case-insensitive within the organisation; original case is displayed. Each event reference is unique across that organisation's inventory.
- Text is trimmed and validated. Names require at least two characters. Evidence/reasons are nonblank, up to 500 characters; source names up to 120. Source timestamps require an explicit timezone and cannot be more than five minutes ahead of the server clock. The UI accepts device-local time and sends a timezone-bearing value. Source and server receipt time remain distinct.
- Events follow **recording order**. A receipt reported late changes the ledger when explicitly recorded; source time does not retroactively replay old balances. No update/delete endpoint exists for stock events. Corrections are additional events with reasons.
- The current local catalog limit is 500 items and 500 locations per organisation. Register pages contain 20 positions, and stock history loads 50 records per page. Reviewed-request search returns up to 20 matching results; search a specific reference for older requests. Parent choices come from loaded history, so load earlier pages when needed.
- Transfers, lot/batch/expiry/temperature tracking, expiry-aware medicine suitability, purchase orders and delivery management are not implemented by this ledger. No real-world inventory accuracy or medical suitability is asserted.

## Reliability and organisation boundaries

The server resolves organisation membership from the session and rechecks owner/editor permission under the workspace write lock. Demo writes are denied. Composite database foreign keys prevent linking another organisation's item, location, relief request or parent event. A parent must also belong to the same item/location position and have the expected event type.

Mutations lock the workspace and then the stock position. Every event supplies the version displayed when its form was opened. Competing writes cannot silently overwrite balances, consume the same reservation twice or bypass a request limit by using another store. A stale version returns 409 and requires **Refresh stock details**. Refresh resets the form, so retain any source note you still need before refreshing.

A client-generated submission key stays stable for retries. The same key or event reference with equivalent canonical content returns the existing record, without changing balances or history. Different details conflict. The duplicate check precedes the version check, so retrying after a committed response was lost is safe. Equivalent quantities, reference case and timezone instants compare canonically. The immutable response preserves that event's original after-balances; refresh details for the latest position.

Catalog saves are also retry-safe by code: equivalent details return the existing entry; different details under the same code conflict. No aircraft import revision, source report, incident review or relief status is changed by recording stock.

## Code to explore

| File | What it teaches |
| --- | --- |
| `backend/app/inventory.py` | Exact Decimal input, transactions, locks, stock/request limits, idempotency and scoped reads. |
| `backend/app/models.py` | Four inventory tables, composite tenant boundaries and nonnegative balance constraints. |
| `backend/migrations/versions/006_inventory.py` | Additive migration preserving existing data. |
| `frontend/src/Inventory.tsx` | Catalog/register/detail forms, explicit save, separate counts, role-aware UI and history paging. |
| `backend/tests/test_inventory.py` | Validation, lifecycle, cancelled/changed requests, concurrent issues and shared request budgets. |
| `scripts/browser-inventory.js` | Real Edge workflow with isolated fictional accounts. |
| `scripts/seed_inventory_demo.py` | Stable read-only examples, seeded once without refreshing original evidence. |

Setup seeds two items, one store, two positions and six fictional stock events, including a report that intentionally differs from the ledger. The shelter reservation references the existing reviewed fictional relief request. Running setup again leaves these examples unchanged.

Executed checks and their limits are recorded in [VERIFICATION.md](VERIFICATION.md). [Delivery tracking](DELIVERIES.md) now extends issues with human review, dispatch evidence and explicit arrivals/returns.
