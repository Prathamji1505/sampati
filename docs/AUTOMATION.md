# Relief intake automation

Open **Automation inbox**. Owners add named relief sources, privately save the once-shown key, and select a rule. Editors upload and decide files; viewers read evidence. New sources always start with **Review every file**.

## What happens to a file

UTF-8 CSV/JSON files use `sampati.relief-intake.v1`. Download **Format guide** for the schema, CSV headers and a fictional JSON example. Files contain a report reference, timezone-bearing observation time and up to 200 request rows, within 256 KiB. Request references are unique within the organisation. Decimal quantities, units, source names and deadlines use the existing request rules.

The original decoded text, validation errors, source, receipt time and policy version are retained. New references propose drafts; identical details are unchanged duplicates; changed existing references are conflicts. Invalid rows or any conflict pause the whole file. No subset is silently applied. Correct the source and upload again, or dismiss with a reason. Decisions and source-policy changes have attributed histories.

**Create new drafts automatically** is an explicit owner policy. Only wholly valid, fresh, conflict-free files qualify. Stale observations, disabled sources or a key issuer without current write access prevent automatic application. Stale/manual warnings require acknowledgement. Automation creates drafts only: a person must still submit and review needs. Stock, dispatch and arrival evidence have their own human workflows.

Existing requests are never overwritten by intake. Accepting a file stores new drafts and audit history together. Current accepted records and source rules are checked again before a decision; changed previews return a conflict and require refresh. Equivalent CSV/JSON uploads and repeated decisions reuse the original result, including dismissed files. Each created request links back to its intake evidence.

Inventory suggestions share category/unit only. They are leads to investigate, not item suitability checks or reservations. Current quantities, condition and location still need confirmation.

## Watch a changing file on your PC

Create a source and save its key privately. In a PowerShell terminal:

```powershell
$secureKey = Read-Host 'Paste source key' -AsSecureString
$env:SAMPATI_AUTOMATION_TOKEN = [System.Net.NetworkCredential]::new('', $secureKey).Password
.\.venv\Scripts\python.exe scripts\watch_relief.py --source-id SOURCE_UUID --file C:\relief\needs.json
```

The watcher checks every 15 seconds while running. `--once` submits once. Changed content is sent to that source only; the server deduplicates repeats. Closing the terminal stops watching. It supports local HTTP, rejects redirects and keeps keys out of arguments and logs. Keep the key outside datasets, source control and screenshots. Remove it from the terminal environment when finished: `Remove-Item Env:SAMPATI_AUTOMATION_TOKEN`.

Disabling a source stops new uploads. Replacing its key invalidates the old one and preserves its enabled state/rule. A removed or downgraded issuer stops connector access; an owner must replace the key. Changing a rule does not process existing pending files. Pending evidence remains available for a separate decision.

## Scope

This is deterministic structured-data automation. No language model, free-text extraction, live news feed or external database connector is configured. It does not infer beneficiary counts, aviation readiness or physical delivery. The three fictional demo files keep their original dates and use a paused source.
