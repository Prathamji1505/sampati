# Flood assessment intake and incident review

This is the first implemented connection in the disaster-response direction: **dated assessment → human review → linked relief-request draft**. It accepts fictional flood impact observations. No SATQueryAI endpoint, satellite processing, forecast model, automatic dispatch or live aircraft feed is configured.

Open **Incident review** in the sidebar, `#incidents` for your organisation, or `#demo/incidents` for fictional read-only examples.

## Try the workflow

1. Sign in as an organisation owner/editor and choose **Record assessment**.
2. Choose a JSON file, paste one assessment, or use **Use fictional example**. The example fills the editor without saving.
3. Choose **Preview assessment**, inspect the dates, source, summary and limitations, then **Record as Needs review**. Preview does not write records; the server validates the complete contract on recording.
4. Inspect the original accepted evidence and record a review decision with a reason. **Reviewed** means the source and limitations were checked. It does not confirm local needs, current flood conditions or mission readiness. Owners/editors can review their own records in this prototype; independent approval is not enforced.
5. From a reviewed assessment, choose **Create linked relief request**. Locality and source context are copied. Supply description, quantity, unit and requesting organisation must be entered by a person. Confirm the request's local source; imagery/population estimates never produce quantities automatically.
6. Follow linked references and attributed review history. Use **Open relief requests** to inspect the request register. Its separate draft/submitted/reviewed/cancelled workflow is described in [RELIEF_REQUESTS.md](RELIEF_REQUESTS.md).

## Shared contract v1

The application-owned contract is proposed for a future SATQueryAI adapter; it is not a claim about SATQueryAI's existing API. Coordinate the actual producer's fields, authentication, licensing and uncertainty semantics before implementing a live connector.

`GET /api/demo/incidents/contract` returns the machine-readable JSON Schema. **Download JSON contract** provides the same schema from the interface. A full example is in [examples/flood-assessment.json](../examples/flood-assessment.json). Each import contains one assessment, with no extra fields.

| Field | Meaning and validation |
| --- | --- |
| schema_version | Exactly `sampati.incident.v1`. |
| external_reference | Immutable 1–64 character reference: ASCII letter/digit first, then letters/digits/dot/underscore/slash/hyphen. Case-insensitive uniqueness within the organisation. Use producer prefixes to avoid collisions. |
| title / locality | 2–160 characters each. Describe an area rather than individual beneficiaries. |
| hazard / assessment_kind | Exactly `flood` / `impact_observation`. Pre-event forecasting needs a separate contract. |
| observed_at / generated_at | ISO timestamps with explicit timezone. Generation cannot precede observation. Intake rejects times more than five minutes ahead of the server clock; the tolerance is for clock skew. Observation, generation and server-owned receipt time stay separate. |
| source_name | 2–120 characters identifying the source. A supplied name does not authenticate that producer. |
| source_url | Optional HTTPS URL, without embedded credentials. No server fetch occurs. A user explicitly opens it in a separate tab. |
| summary | 10–2,000 characters of source evidence. |
| uncertainty | Required 2–1,000 character limitations statement. No fabricated numerical confidence score. |
| extent | `west`, `south`, `east`, `north` as finite JSON numbers. Longitude −180…180, latitude −90…90, west < east, south < north. A bounding rectangle, not a flood polygon. Antimeridian-crossing areas need separate assessments. |
| reported_affected_people | Optional/null or strict integer 0…1,000,000,000. Displayed as an unverified source estimate; never a confirmed beneficiary count. |

Text fields are trimmed, URLs are parsed/normalised, and accepted dates retain their supplied timezone text. Exact raw file bytes are not archived. The UI limits chosen/pasted files to 256 KB; field lengths and strict structure also bound the API's accepted content. No beneficiary/patient records are required.

Observations older than 24 hours display a factual age flag, independent of review status. This is a review aid, not a freshness guarantee or determination that an assessment remains accurate. Receipt does not refresh its observation time.

## Review states and evidence preservation

| Current state | Allowed decisions |
| --- | --- |
| Needs review (`pending`) | Reviewed, Dismissed |
| Reviewed | Needs review, Dismissed |
| Dismissed | Needs review |

Accepted assessment fields cannot be edited or deleted through the API. A revised assessment uses a new reference. Reopening/dismissing retains the evidence, reasons, authors and existing linked requests; it blocks **new** links until reviewed again. Existing requests retain their original incident reference and must be reassessed by people as new information arrives. No cascading cancellation or dispatch occurs.

## Reliability and access

- Session membership determines organisation scope. Owner/editor writes, viewer reads, demo read-only, existing CSRF/origin checks. All IDs are scoped; a foreign ID returns 404.
- Same reference + equivalent accepted content returns the existing assessment with HTTP 200 and `duplicate: true`. References and equivalent timezone instants are normalised for comparison. Different content under the same reference returns 409; it cannot overwrite evidence. This also makes retry after a lost response safe.
- Every actual review requires the expected version and a nonblank reason. Workspace then incident locks serialize competing updates; one stale writer gets 409. Same-state/current-version is a no-op. Reasons and actor labels are recorded atomically with each change.
- Reads use shared workspace locks for coherent lists/details. Lists use literal-text search, status filters and 20-row pagination. Audit history uses a version cursor with 50 events per page.
- New relief links require a currently reviewed incident in the same organisation, checked under the same workspace lock as request creation. A composite database foreign key also enforces that boundary. Existing requests remain unlinked after migration; no data is guessed.
- Incident changes do not increment the aircraft import revision or rewrite source reports. Setup adds two stable fictional demo assessments once; rerunning never refreshes/overwrites them.

## Code to learn from

| File | What to study |
| --- | --- |
| `backend/app/incidents.py` | Pydantic contract, canonical duplicate checks, scoped queries, review transaction and JSON Schema. |
| `backend/app/models.py` | Incident/evidence history tables and organisation-aware relief linkage. |
| `backend/migrations/versions/005_incidents.py` | Additive migration preserving existing requests. |
| `frontend/src/Incidents.tsx` | Explicit preview/save, status form, role-aware controls, audit pages and linked-draft handoff. |
| `backend/tests/test_incidents.py` | Invalid inputs, permissions, duplicate retries, linkage, race protection and pagination. |
| `scripts/browser-incidents.js` | Real Edge journey with temporary fictional accounts. |

Aid inventory, mission approval, delivery confirmations and a live SATQueryAI connector remain separate work. Executed checks belong in [VERIFICATION.md](VERIFICATION.md).
