# Sampati progress · 25 November 2026

Current local release: **0.5**. Sampati remains a standalone civilian disaster-response and relief-coordination application. This snapshot describes implemented software and the next evidence gates; it does not claim operational deployment or measured humanitarian impact.

## What has advanced

| Area | Current progress |
| --- | --- |
| **Response preparation · R01** | Warning/news JSON intake and human verification, narrow source credentials and a local warning-file watcher; dated aircraft-support evidence; deterministic checks and explained preparation snapshots. |
| **Review and revision** | Saved preparations are checked against current source evidence. A new draft can reuse original inputs without refreshing their observation dates or rewriting the earlier record. Coordinator review does not reserve stock or authorise flight. |
| **Relief workflow · H01–H03** | Reviewed requests, exact inventory movements, source-backed dispatch/partial arrivals/returns, remaining needs and attributable history are implemented locally. |
| **Intake automation · A01** | CSV/JSON intake, repeat/conflict checks and an explicit owner rule for new drafts; accepted needs still require human submission/review. |
| **Navigation and loading** | Seven relief destinations remain visible; aircraft/data and settings are grouped. Phone navigation closes after selection and supports Escape/outside close. Workspace modules load on demand with a recovery action. |
| **Repository presentation** | Refreshed desktop/mobile screens, new warning/preparation examples, updated capture provenance, a current progress page and indexed research notes. |

The underlying 0.5 and navigation code was already published in `c2a1345` and `9bc320c`. This refresh documents that progress, replaces older imagery and fixes native warning-reference validation discovered while capturing the new form.

## What the current demo proves

- The shared fictional example retains **40 shelter kits requested, 10 recorded arrivals and 30 still needed**. A planned shipment or stock issue does not silently count as arrival.
- The separate disposable preparation example proposes **40 water packs × 2 kg = 80 kg** from a 100-pack stock position. Coordinator review leaves that stock unchanged.
- The captured workflow explains missing aircraft support before a preparation becomes reviewable. Source observations and review decisions remain distinct.

These are authored software scenarios. The screenshots do not establish a live warning feed, aircraft readiness, physical stock accuracy, real delivery or a field-tested response plan. [Capture provenance](images/README.md).

## Verification

On 25 November the full **242-test** backend suite, production build, migration consistency and dependency checks passed. The two capture runs produced **21 screenshots** with their stated read-only/disposable-fixture checks. See [VERIFICATION.md](VERIFICATION.md) and [GitHub Actions](https://github.com/Prathamji1505/sampati/actions) for build-specific evidence. The screenshot runs are not a repeat of every historical browser test.

## Next evidence gates

1. **Authorised live context · H04:** choose an actual coordinator task and source; verify access/terms, dates, updates/cancellations, outages and review mapping before calling an adapter supported.
2. **Civilian-user evaluation · H05:** observe realistic review, reconciliation and handover tasks; measure errors, task time and unmet-needs follow-up against stated baselines.
3. **Deployment · H06:** select the environment and budget, configure HTTPS/origins/cookies/secrets, rehearse off-device recovery and verify organisation boundaries in that environment.

General public-news polling, external database adapters, forecasting, flight routing/scheduling, AI models and independent physical verification remain separate work. [Full roadmap](ROADMAP.md) · [Release scope](RELEASE.md) · [Source strategy](DATA_SOURCES.md).
