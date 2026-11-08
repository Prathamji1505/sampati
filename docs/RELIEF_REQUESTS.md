# Relief requests: H01

H01 records civilian supply needs and human review. It does not reserve inventory, approve dispatch or confirm delivery. Open **Relief requests** in the sidebar, or use `#relief` for your organisation and `#demo/relief` for read-only fictional examples.

Requests can now optionally link to a reviewed flood incident in the same organisation. Open **Create linked relief request** from Incident review; only locality/source context is copied, and a person supplies the needs and quantities. The link is fixed at creation and included in audit snapshots. Existing requests stay unlinked. Reopening/dismissing the incident preserves existing requests and blocks new links until reviewed again. See [INCIDENTS.md](INCIDENTS.md).

## Record and review a request

1. An owner or editor chooses **New request**. **Use fictional example** fills a form without saving it.
2. Enter a reference, requesting organisation, locality, supply category/description, quantity, unit, needed-by time and source name. Save a draft.
3. Correct draft details with a recorded reason, or submit the draft for review.
4. Mark submitted details reviewed, return them to Draft for correction or cancel with a reason.
5. Read the request history to inspect the actor, time, reason and before/after values. History loads in pages of 50 events.

Reviewed means someone checked the request details. This prototype lets owners/editors review requests, including their own; it does not claim independent approval or a completed delivery. [Inventory](INVENTORY.md) and [Delivery tracking](DELIVERIES.md) now link reviewed needs to separate stock and arrival records. Draft corrections cannot reduce quantities below active/delivered shipment claims or change their units/category until those assignments are resolved. Cancellation does not erase actual shipment evidence or automatically return inventory.

## States

| Current state | Allowed next states | Detail corrections |
| --- | --- | --- |
| Draft | Submitted, Cancelled | Allowed, with a reason |
| Submitted | Reviewed, Draft, Cancelled | Return to Draft first |
| Reviewed | Draft, Cancelled | Return to Draft first |
| Cancelled | None | Not allowed |

Cancellation is final, with no delete endpoint. A cancelled reference remains reserved within that organisation. An unchanged edit or same-state request is a no-op when its expected version is current. A stale expected version returns a conflict, including on repeat submissions; refresh details before another decision.

## Data contract

| Field | Rules |
| --- | --- |
| reference | 1–64 ASCII letters/digits/dot/underscore/slash/hyphen, starting with a letter or digit. Original case is displayed; uniqueness is case-insensitive within the organisation. Immutable after creation. |
| requesting_organisation | 2–120 characters; organisation-level description, not individual beneficiary data. |
| locality | 2–160 characters. |
| category | food, water, medicine, shelter or other. Medicine denotes a supply category, not clinical advice. |
| item_name | 2–160 characters describing the requested supplies. |
| quantity | Positive decimal, at most 1,000,000,000, with no more than three decimal places. Stored as an exact decimal; JSON responses use canonical decimal text. |
| unit | items, boxes, kits, litres, kilograms or packs. No automatic conversion or aggregation across units. |
| needed_by | ISO-8601 text with an explicit offset or Z. The UI accepts device-local time and sends a timezone-bearing value. The original timestamp is retained; comparisons use UTC. Past deadlines are valid historical needs and are labelled, not silently rejected. Cancelled requests do not display as past-deadline work. |
| source_name | 2–120 characters identifying the source/report. |
| note | Optional, at most 1,000 characters of plain text. |
| submission_key | Client-generated UUID kept for retries of the same create action. Not a credential or workspace selector. |

Strings are trimmed before validation. Status, version, organisation scope, authorship, timestamps and audit entries are server-owned. Clients cannot set them during creation. Only `expected_version` is supplied to guard a later edit/status change. Reasons are required and limited to 500 characters.

## Reliability and access

- The session and current membership resolve the organisation. A supplied workspace identifier cannot grant access. Owners/editors create, correct and review; viewers read and inspect history. Demo writes are denied server-side.
- Creation locks the workspace, rechecks membership and stores the draft plus its first audit event in one transaction. The same submission key/content returns the existing request without another event; changed content with that key conflicts. Another key with the same reference conflicts. Separate organisations can use the same reference.
- Corrections/status changes lock the workspace and request and require the version the person opened. Two competing updates cannot silently overwrite one another. Every actual change increments the request version and inserts its audit event atomically.
- Request/list reads use a shared workspace lock for coherent snapshots. Source timestamps are normalised for comparison so equivalent deadlines in different offsets do not generate a false correction. There are no audit-edit endpoints.
- Aircraft reports, import history and the aircraft workspace revision are separate. Recording a relief request does not invalidate an aircraft import preview or rewrite aircraft status.
- The list searches reference, organisation, locality, item and source, with literal substring matching, status/category filters and 20-row pages. Data remains scoped even when a user guesses another record ID.

## Demo and setup

Migration `004` adds `relief_requests` and `relief_request_events`. Back up before applying migrations:

```powershell
.\.venv\Scripts\python.exe scripts\backup.py
.\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
.\.venv\Scripts\python.exe -m scripts.seed_relief_demo
```

Normal `scripts/dev.py setup` now performs migration and demo seeding. The seed adds three fictional requests only to the designated demo workspace. It never overwrites existing examples or creates user accounts. Their deadlines are fixed at initial seeding, rather than refreshed each time the page is read. Your private organisation starts with an empty relief register.

## Code map

- `backend/app/relief.py`: request validation, normalisation, workflow, version checks, list/detail APIs and audit snapshots.
- `backend/app/models.py` and migration `004`: request/event storage, exact quantities, uniqueness and integrity constraints.
- `frontend/src/ReliefRequests.tsx` and `relief-requests.css`: list, creation/correction form, review and history views.
- `backend/tests/test_relief.py`: validation, retries, transitions, isolation, role checks, pagination and concurrent writes.
- `scripts/browser-relief.js`: real browser journey with explicitly generated fictional QA accounts.

Use fictional supply and organisation details for development. The first module does not require individual patient, beneficiary or medical-history fields. Actual organisation data requires a defined access and retention policy.
