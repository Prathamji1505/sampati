# Aid inventory: backend milestone

This increment starts H02 with organisation-scoped inventory APIs, persistence and regression tests. The inventory interface and complete user journey are still being developed. Delivery confirmation remains H03 work.

## Data model

- **Items:** stable code, descriptive name, supply category and explicit unit.
- **Storage locations:** stable code, name and locality within the organisation.
- **Stock positions:** exact on-hand, reserved and available balances per item/location, with a version guard.
- **Stock records:** append-only receipts, reservations, releases, issues, returns, count reports and reasoned adjustments.

Reported counts stay separate from ledger balances. A report never silently rewrites stock. Quantities use exact decimals with up to three decimal places, explicit units and a ceiling of one billion per supported quantity. There is no implicit unit conversion.

Reservations require a compatible reviewed relief request. Releases/issues reference an earlier reservation; returns reference an issue. Parent references, organisation scope, available quantities and request commitments are checked server-side. Version checks and locking prevent silent competing updates. Retry keys and references distinguish a repeat from conflicting content.

## API surface

Private endpoints are rooted at `/api/inventory`; demo equivalents use `/api/demo/inventory` with writes denied.

| Endpoint | Purpose |
| --- | --- |
| `GET /catalog` | Read the organisation's items and storage locations. |
| `POST /items`, `POST /locations` | Create scoped catalog entries. |
| `GET /inventory` (root) | Search and paginate stock positions. |
| `GET /position` | Inspect balances, reports and paginated ledger records for an item/location. |
| `GET /requests` | Find eligible reviewed requests for an item. |
| `POST /records` | Record a validated stock event with source time, reason and expected version. |

For the list endpoint, use `/api/inventory` itself, without a repeated `/inventory` segment. Authentication, current membership, roles and anti-forgery checks apply to private mutations.

## Migration and verification

Migration `006_inventory.py` follows incident migration 005. Apply migrations through the documented setup workflow after retaining a private backup. The new migration is tested in a disposable schema and by hosted CI; this publication does not automatically upgrade a running development database.

The regression suite covers exact quantities, immutable history, retry/conflict behavior, roles/demo/isolation, stock/request limits, search/paging and concurrent reservations. See [verification evidence](VERIFICATION.md) for executed results.

## Remaining H02 work

Complete and verify the inventory interface, demo/onboarding flow and real-browser journey before presenting H02 as an end-to-end feature. H03 will connect approved deliveries and confirmations to reviewed requests and inventory movements. An inventory issue alone is not proof of delivery.
