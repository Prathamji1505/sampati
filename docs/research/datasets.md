# Datasets for a civilian aviation logistics prototype

Checked: **2026-11-07**. Scope: an educational civil transport or disaster-relief simulation, using uploaded records and fictional scenarios. This note does not propose a source of live aircraft positions or operational aircraft availability.

## Recommendation

Build the first version from **a user-provided fleet-status CSV and a small, clearly labelled synthetic example**. Add OurAirports only for airport names, codes and location context. Add weather later if it helps the demonstration. Neither airport metadata nor weather establishes whether an aircraft is available; the prototype should describe availability as **reported by the uploaded data, as of a stated time**.

| Resource | Role | Decision |
| --- | --- | --- |
| Authorized user-provided fleet records | Aircraft attributes and reported status | Essential |
| Project-created synthetic records | Repeatable demonstrations and missing/stale-data cases | Essential |
| OurAirports | Airport reference metadata | Recommended optional enrichment |
| NOAA/NWS Aviation Weather Center METAR/TAF | Weather observations and terminal forecasts | Optional later feature |
| BTS flight performance / NASA C-MAPSS | Separate historical-data or machine-learning exercises | Omit from the first prototype |

These decisions and the proposed schema below are project recommendations, rather than claims that the public sources supply a complete logistics dataset.

## 1. Uploaded records and synthetic examples

There is no suitable public source in this shortlist for the complete, current availability of the user's chosen fleet. Treat an uploaded status as an assertion from its provider, not independently verified serviceability or permission to operate.

A deliberately small upload format could contain:

| Field | Suggested meaning |
| --- | --- |
| `aircraft_id` | Unique project identifier; fictional IDs such as `DEMO-001` work for demonstrations |
| `aircraft_type` | Civil aircraft category or user-supplied model label |
| `base_airport_ident` | Explicitly mapped airport reference identifier |
| `passenger_capacity`, `cargo_capacity_kg` | Optional user-provided attributes, with units fixed by the template |
| `reported_status` | Controlled values: `available`, `unavailable`, `unknown` |
| `source_updated_at` | Time the provider says the status applied, with an explicit timezone |
| `source_name` | Short provenance label, without personal contact details |
| `is_synthetic` | Keeps fictional examples distinct from uploaded records |

For a beginner build, use UTF-8 CSV first; an Excel importer can be added later. Require unique aircraft IDs, validate the status vocabulary, preserve blank values as unknown, and require timezone-aware timestamps. A missing row, expired status or missing timestamp must not become an available aircraft by default. Keep the original upload, import time and validation results so the user can inspect what produced a view.

Create a small fictional civil fleet with known available/unavailable/unknown cases, duplicate identifiers, missing airport mappings and old status timestamps. Fix a scenario clock and random seed if generation is used. A fixture is a software demonstration, not evidence about real aircraft. Use only uploaded records the provider is authorized to share; the public-source licences below do not grant rights to private uploads. Do not silently publish uploads or combine them with public demo fixtures.

## 2. OurAirports: airport reference context

**What is documented.** The provider's download page describes nightly CSV exports and releases the data to the public domain with no accuracy or fitness guarantee. This is a directory, not evidence of current operating access or aircraft availability. [OurAirports download page](https://ourairports.com/data/)

**Access and freshness.** The first-party repository supplies direct file links, including [airports.csv](https://davidmegginson.github.io/ourairports-data/airports.csv), [countries.csv](https://davidmegginson.github.io/ourairports-data/countries.csv) and [regions.csv](https://davidmegginson.github.io/ourairports-data/regions.csv). Its documented download workflow specifies no account or API key. Files are generated daily, but GitHub changes a file's date only when its contents change. A daily export does not mean every airport record was checked that day. [Official repository README](https://github.com/davidmegginson/ourairports-data/blob/main/README.md)

**Format and joins.** The dictionary specifies UTF-8 CSV. Airport rows include type, name, coordinates, elevation in feet, country/region and several code fields. `id` is a persistent internal identifier; `ident` may be an ICAO code, local code or generated identifier. Use the separate `icao_code` field when mapping to weather stations, and verify the mapping. `scheduled_service` describes scheduled airline service, not general airport availability. [Provider data dictionary](https://ourairports.com/help/data-dictionary.html)

**Licence evidence.** The data-specific public-domain statement above comes from the provider's indexed download page. The repository separately contains an Unlicense-style public-domain dedication worded for software; that file alone should not be substituted for the provider's data-specific terms. [Repository LICENSE](https://github.com/davidmegginson/ourairports-data/blob/main/LICENSE)

**Suggested use.** Start with a small civil-airport subset of `airports.csv`. Record source URL, retrieval time and repository commit or file checksum. Preserve original identifiers, require explicit code mappings and show unmapped records. Names, coordinates and directory flags are context for the simulation, not a clearance, current closure check or operational suitability assessment. No airport dataset was downloaded for this research, and no current row count or file-modification date is asserted.

## 3. Aviation Weather Center: optional weather context

**Access, formats and limits.** The public Data API documents worldwide METAR observations and TAF forecasts, up to 30 days of database history, and HTTPS GET examples without credentials. METAR supports text, JSON, GeoJSON, CSV, XML and IWXXM; TAF supports those except CSV. Limits are 100 requests/minute; most endpoints cap results at 400. CORS is not permitted. Use a custom user agent and bounded requests. Compressed full-cache files refresh every minute: METAR XML/CSV and TAF XML. Most METAR reports update hourly; the cache frequency is not the observation frequency. HTTP 204 means a valid request has no data. These are documented limits, not tested integration results. [AWC Data API](https://aviationweather.gov/data/api/)

**Meaning and timestamps.** METAR contains station weather observations; some reports omit elements. TAF is a forecast for a specified terminal area and time interval. Scheduled NWS TAFs are issued at least every six hours; amendments supersede earlier forecasts. Preserve the observation/issue time, forecast validity interval and retrieval time as separate values. [AWC product documentation](https://aviationweather.gov/help/data/)

**Coverage and delivery.** Worldwide product coverage does not imply every airport has a current report. AWC says it receives observations from outside station operators and directs users to its status page for missing data. [AWC FAQ](https://aviationweather.gov/help/#faq)

**Reuse terms.** NWS says information on its pages is public domain unless specifically noted otherwise. Its conditions prohibit implying endorsement, claiming the information as one's own, or presenting modified content as official. It provides no warranty or guaranteed timely Internet delivery. Preserve provenance and any product-specific notices; do not relabel the entire international payload as CC0 without checking for exceptions. [NWS disclaimer](https://www.weather.gov/disclaimer)

**Suggested implementation.** Keep weather optional, with a saved sample for offline demonstrations. Because the public API disallows cross-origin access, a browser app would need a server-side fetcher or a manual snapshot import; this is an architectural inference from that restriction. Request only explicitly mapped stations, cache results and back off on errors. Show missing/stale weather explicitly. Use it for display and explanation rather than automatic dispatch or availability decisions. Check authentication and response schema again before implementation: the documented no-key example was read, but no API request was tested.

## 4. Why BTS and NASA are deferred

**BTS:** its 2026 directive concerns reported scheduled domestic passenger-flight performance, including delays and cancellations, from defined reporting carriers and airports. That scope does not provide a complete fleet-status ledger. It could support a later civil historical-delay dashboard, but adds little to the first upload-and-status prototype. Do not infer aircraft availability from gaps between recorded flights. Dataset download, redistribution terms and integration were not evaluated for inclusion. [BTS 2026 technical reporting directive](https://www.bts.gov/explore-topics-and-geography/modes/aviation/number-40-technical-directive-reporting-time)

**NASA C-MAPSS:** NASA describes simulated engine degradation under combinations of operating conditions and fault modes, recording sensor channels. This is suitable for a separate prognostics learning exercise, not real-fleet availability ground truth. The repository requests acknowledgment of the repository and data donors and disclaims liability; a dataset-specific redistribution licence was not established from the reviewed landing page. No bundle or model was downloaded. [NASA PCoE repository, dataset 6](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/)

## Verification limits and next checks

- The OurAirports original download page and dictionary repeatedly failed direct retrieval here. Their first-party indexed content was available; the official GitHub README and licence were fetched successfully. Reopen the provider's terms when obtaining an actual snapshot. Do not describe the failed fetch as a provider outage.
- The AWC public API, product help and NWS disclaimer pages were readable. The linked OpenAPI YAML returned HTTP 403 through the research tools. This does not prove the public METAR/TAF endpoints require an account or that ordinary access is blocked. Schema and authentication details should be checked during integration.
- No dataset was downloaded, API quota was exercised, account was created, integration was run or package was installed. Source documentation was checked on the date above; it is not a guarantee of future access or unchanged terms.
- Before implementation, select the intended civil demonstration geography, a small airport list and a project policy for stale uploaded statuses. These are product decisions the public sources cannot supply.
