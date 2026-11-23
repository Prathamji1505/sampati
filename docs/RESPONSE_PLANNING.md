# Civilian response preparation

Sampati 0.5 adds a warning/news register, dated aircraft support reports and a deterministic workflow planner. It helps a civilian coordinator connect a verified report to reviewed supply needs and current resource evidence. Preparing or reviewing a workflow never changes stock, books an aircraft or authorises dispatch.

## What deterministic analysis means

These decisions come from explicit versioned rules, not learned model weights. The same evidence, evaluation time and policy produce the same result and explanation. The current rule version is `civilian-response.v1`.

The learning loop is: collect authorised examples → have civilian reviewers label the expected outcome and reasons → keep a separate held-out set → evaluate the rules → examine incorrect or incomplete decisions → change a documented rule → rerun the examples and regression checks. Do not tune rules against the held-out set or remove difficult examples to improve a score.

The [fictional evaluation template](../examples/response-rule-cases.json) contains a base evidence snapshot and labelled changes. Run it from the project root:

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_response.py --stress 5000
# Supply your independently labelled, private cases:
.\.venv\Scripts\python.exe scripts\evaluate_response.py --cases .local\my-response-cases.json
```

Results are saved under ignored `.local/evaluations/`. The tool reports label matches, required blocking reasons, false-reviewable outcomes and generated resource invariants. Generated trials exercise the rule function, not concurrent HTTP users. Toy examples do not measure field accuracy, preparedness or humanitarian outcomes. No ML training occurs.

## Coordinator workflow

1. Open **Response preparation → Warnings & news**. Record a dated report or import a warning JSON file. Preserve its reference, source, affected locality, certainty, severity and expiry.
2. Verify or dismiss the report with a reason. A connected source cannot verify its own report.
3. Review locally confirmed supply requests in **Relief requests**. An incident assessment or news article does not establish the supply quantity.
4. In **Aircraft support**, record the operator's reported cargo allowance, crew, maintenance and fuel checks, source and observation time. Import the aircraft into the organisation register first. Its reported availability and its support report remain separate records.
5. In **Workflow planner**, select a warning and map each reviewed request to an exact catalog item and store. Explicitly confirm the item match and supply the measured kilograms per declared unit and its source. No fuzzy item match or unit conversion is inferred.
6. Record dated weather and destination-access assessments from an appropriate source. Unknown values remain unknown.
7. Evaluate. Read every blocking reason, proposed quantity, aircraft exclusion and workflow step. A blocked preparation can be saved for follow-up, but cannot receive coordinator review.
8. Save the evidence snapshot. Record coordinator review only while all checks pass and the evidence still matches. Existing inventory and delivery screens handle subsequent human actions.

When a saved record needs rechecking, open it and choose **Use saved inputs for a new draft**. This restores its warning, requests, items, stores, weights and context into the builder, preserves the original observation dates, and creates a distinct draft after a new evaluation. The original record stays intact. Editing an existing aircraft support report also preserves its source observation time, including precision; update that time only when you have a new source observation.

The four sections preserve an unfinished preparation form while you inspect support reports. Leaving this workspace or reloading does not save an unfinished form; save a preparation draft when you need a durable record.

## Rules and limits

| Check | Behaviour |
| --- | --- |
| Warning | Must be human-verified, unexpired, within the source-age policy and have useful reported certainty. `unknown` and `unlikely` pause preparation. |
| Local needs | Requests must still be reviewed and match the warning locality after case/whitespace normalisation. Explicit area mapping is required when a broader warning names a different locality. |
| Item identity | Category and unit must agree; a person also confirms the exact catalog item. Similar names do not establish interchangeability. |
| Existing commitments | Request-linked reservations and issues remain committed. Releases and returns reduce commitments. Already committed quantities are not proposed again. |
| Stock | Only unreserved ledger stock is proposed. A source count is separate evidence and never becomes stock automatically. A dated non-count stock record must be current. |
| Multiple needs | Shared stock is used once within a proposal, in earliest-deadline/reference/ID order. A shortage remains explicit. This is a stated heuristic, not an optimal allocation claim. |
| Cargo | Exact decimal quantities are multiplied by source-supplied unit weights. Kilogram-denominated supplies must use one kilogram per unit. Volume, dimensions, hazardous-goods restrictions and aircraft-specific load envelopes require separate operator assessment. |
| Aircraft | A candidate needs a current `available` register report and current support evidence with crew, maintenance and fuel reported confirmed. The smallest reported cargo allowance that fits is chosen; aircraft ID breaks ties. All exclusions remain inspectable. |
| Time | `FRESHNESS_HOURS` is the existing source-age policy, default 24 hours, with a five-minute future-clock tolerance. These are software review thresholds, not aviation or emergency-response standards. |
| Review | Any changed dependency, changed rule/policy or crossed freshness/expiry threshold requires re-evaluation. Opening a saved plan shows whether the original snapshot still matches. |
| Concurrency | Workspace locking and version guards protect changes. Repeated save keys and review retries do not create additional drafts or review events. |

The bounded local planner accepts up to 50 selected requests and 500 registered aircraft per organisation. Exceeding the aircraft limit pauses evaluation instead of silently dropping candidates. Lists are paginated; search reviewed requests to locate older records.

Saved review is not a resource reservation. Multiple preparation records can discuss the same resources. Recheck the current stock and operator commitments when committing resources through the existing inventory workflow and the operator's own process. Flight routes, scheduling, range, weather forecasting, medical decisions and dispatch are outside this planner.

## Warning-only connections

An organisation owner can create, disable or rotate a connection under **Warning connections**. Its one-time key can submit evidence only. It cannot review warnings, approve requests, write stock, save plans or confirm arrivals. The issuer must retain a current owner/editor membership. Keys are hashed in storage and are absent from history and exports.

POST one JSON object to `/api/response/ingest/SOURCE_UUID` with `Authorization: Bearer PRIVATE_KEY`. Signed-in owners/editors can import the same object through the interface. No source URL is fetched by the application.

```json
{
  "reference": "DISTRICT-FLOOD-REV1",
  "kind": "warning",
  "title": "Example district flood warning",
  "locality": "Example River Ward",
  "severity": "severe",
  "certainty": "likely",
  "source_name": "Authorised district warning desk",
  "source_url": "https://example.org/warnings/REV1",
  "observed_at": "2026-11-22T10:00:00+05:30",
  "expires_at": "2026-11-22T16:00:00+05:30",
  "description": "Illustrative format only. Use actual authorised evidence and source timestamps."
}
```

`kind` is `warning` or `news`; severity is `extreme`, `severe`, `moderate`, `minor` or `unknown`; certainty is `observed`, `likely`, `possible`, `unlikely` or `unknown`. These metadata distinctions follow the vocabulary of the [OASIS Common Alerting Protocol](https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2-os.html). This JSON contract is not a CAP parser, signature verifier or public-warning delivery service.

References identify immutable evidence per connection, or per named manual source. Exact resubmissions return the existing record. Different evidence under the same reference returns 409; issue a new revision reference and review/dismiss superseded evidence explicitly. The current adapter does not automatically interpret provider updates or cancellations. Up to 1,000 unreviewed reports and 50 warning connectors are accepted per organisation.

For changing local JSON exports, set the one-time key in your shell environment and run:

```powershell
$env:SAMPATI_WARNING_KEY = 'YOUR_PRIVATE_SOURCE_KEY'
.\.venv\Scripts\python.exe scripts\watch_warnings.py `
  --directory .local\authorised-warnings `
  --url http://127.0.0.1:8000/api/response/ingest/SOURCE_UUID
```

The directory must already exist. Use `--once` for one pass. Files must be at most 64 KiB; partially written or invalid files are rejected and retried on a later pass. Export to a temporary filename, then rename the completed file to `.json`. The adapter restricts delivery to loopback, rejects redirects, does not use proxies, and does not print source keys or evidence bodies. In-memory file tracking resets on restart; server deduplication remains authoritative.

General news scraping, live weather and public-provider polling are not configured. An authorised adapter must normalise its source into this contract while preserving dates, area, uncertainty and update/cancellation semantics. The [GDACS official API quick start](https://www.gdacs.org/Documents/2025/GDACS_API_quickstart_v2.pdf) is a possible integration reference; no GDACS feed or endorsement is claimed.

## Implementation

The [rule module](../backend/app/response_rules.py) has no database, network or UI side effects. [Response routes](../backend/app/response.py) load organisation-scoped facts in bounded queries, apply the rules under a consistent workspace lock, and store original snapshots and journal entries. [Migration 009](../backend/migrations/versions/009_response_planning.py) adds the evidence tables and warning-source scope. Existing report, request, inventory and delivery records remain the owning sources.

Interface panels load on demand. A failed module download leaves a visible reload action and usable navigation. The app keeps the existing Sampati visual identity, native form controls, visible focus, contained wide tables and reduced-motion behaviour.
