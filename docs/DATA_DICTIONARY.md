# Dataset contract

UTF-8 CSV (an initial BOM is accepted), comma separated, at most 1 MiB and 2,000 records. All six header names are required; their order may differ. Duplicate or additional headers and inconsistent column counts are rejected. The whole batch must pass validation before confirmation is possible.

| Field | Rules |
|---|---|
| aircraft_id | Required, 1–64 ASCII letters/digits/dot/underscore/hyphen; first character alphanumeric. Preserved as text and case-sensitive; unique inside this workspace and each file. |
| display_name | Optional value, maximum 120 characters. |
| reported_status | Required: available, unavailable or unknown. Whitespace is trimmed; case is normalized to lowercase. |
| source_updated_at | Required ISO-8601 timestamp with explicit UTC offset or Z. Normalized to UTC; original timestamp text retained in audit snapshots. |
| source_name | Required nonempty source label, maximum 120 characters. |
| note | Optional value, maximum 1,000 characters. Plain text. |

Server-owned fields include the local workspace, importing actor, receipt time, import ID and workspace revision. Uploaded values cannot select another workspace or grant permission.

Imports are merge updates, not destructive replacement snapshots: absent rows do not delete aircraft. Older reports and same-time contradictory reports reject the entire batch. Equivalent reports at the same timestamp are unchanged. Exact normalized repeat datasets are no-ops, including when uploaded in a different row order. A preview expires after 30 minutes and is bound to its content and workspace revision. Confirmation rechecks both inside a database transaction.

Reported status and freshness are independent. A report is marked needing review after 24 hours, a configurable demo convention rather than an aviation rule. A future source timestamp is shown as needing review as well. Available means reported available, not independently certified airworthiness or flight clearance.

## Excel

`.xlsx` files use the same six headers and validation as CSV. Use exactly one visible worksheet and store IDs and timezone-bearing timestamps as text. Reordered columns are accepted. Formulas, numeric aircraft IDs, Excel datetime cells without explicit timezone text, extra populated columns, macros and external workbook links are rejected. The parser limits the compressed file to 1 MiB, expanded ZIP entries to 12 MiB, archive entries to 200 and worksheet rows to 2,001 including the header. The converted CSV also passes the existing 1 MiB validation. Unsupported `.xls` and `.xlsm` files must be converted first.

## Exports and incoming files

Excel exports force literal string cells, including values beginning with `=`. JSON keeps source text values. CSV exports quote fields and prefix formula-like values with an apostrophe; spreadsheet applications interpret CSV differently, so use Excel for spreadsheet viewing and Excel/JSON when preserving literal text matters. Export filters mirror register search, status and freshness filters.

A connected file is stored as validated rows in an organisation-scoped incoming queue. It can be previewed and confirmed, or rejected. Rejection invalidates an already-issued inbox preview. Accepted reports still obey timestamp/conflict and workspace-version checks. Queue submission alone never changes accepted aircraft, revision or import history. Missing rows continue to mean no change, rather than removal. An enabled source key may submit a newer correction after a rejection. Up to 100 files may wait pending at once; the UI shows the latest 100 submissions.
