# Independent operation and data sources

Sampati is a standalone disaster-response and relief-coordination platform. It owns its records, review rules, organisation permissions and audit history. Another analysis tool can complement it through an optional adapter; no particular external product is required to run it.

## Supported now and planned next

| Source | Current position | Integration direction |
| --- | --- | --- |
| Local files | CSV/Excel aircraft reports and versioned JSON flood assessments are implemented. | Preserve validation, preview and explicit human acceptance. |
| Human-entered information | Relief-request drafts and reasoned review decisions are implemented. | Keep locally confirmed quantities separate from assessment estimates. |
| Changing files | The scoped file watcher and incoming review inbox support the existing dataset contract. | Additional formats need their own validation and review mapping. |
| Databases | External database connectors are planned. Sampati's own PostgreSQL persistence is already implemented. | Read authorised views/exports with limited credentials, checkpoints and traceable source references. |
| News and public reports | Automated news intake is planned. | Retain publisher, article link, publication/update time, retrieval time and supporting excerpts where permitted. Treat reports as evidence for review, rather than confirmed needs or stock. |
| APIs and assessment tools | The local incident contract is implemented; live adapters are planned. | Map dated evidence, uncertainty and producer references into a versioned contract. |
| Other documents and forms | Additional document/form ingestion is planned. | Define supported fields, extraction review and source attribution before accepting records. |

No database/news connector, automatic document extraction or model-based source analysis is claimed as implemented by this document.

## Shared intake architecture

**Source → adapter or local upload → validated source record → review inbox → human decision → accepted coordination records and history.**

An adapter translates a source into Sampati's contracts. It cannot bypass organisation access, validation or review. The existing contracts remain purpose-specific: aircraft dataset, flood assessment and relief request. A new source or hazard may require an explicit contract extension.

## Rules for future adapters

- Preserve the source identity and reference, original URL where applicable, observation/publication time, retrieval time and uncertainty.
- Keep raw evidence separate from an extracted interpretation and from a human-confirmed request.
- Detect repeats and revisions; retain contradictions for review instead of silently replacing accepted information.
- Show stale, failed or unavailable sources explicitly. Cached records retain their original dates.
- Use authorised access and appropriate source terms; keep credentials out of browser code, exports and Git.
- Verify each adapter with representative fixtures, access-boundary tests, replay/error cases and a reviewed example before advertising it as supported.

The next core dependencies remain inventory and delivery tracking. Source adapters can be prioritised by a civilian user's actual workflow rather than by a reference project's technology. [Roadmap](ROADMAP.md) · [Incident contract](INCIDENTS.md).
