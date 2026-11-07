# Contributing

Sampati is a fictional civilian aircraft-report prototype. Start with the [setup guide](docs/SETUP.md), [architecture](docs/ARCHITECTURE.md) and [data contract](docs/DATA_DICTIONARY.md).

Before opening a change:

1. Describe the problem and the behavior the change should produce.
2. Keep examples fictional. Exclude uploaded files, credentials, databases, recovery codes and source keys.
3. Preserve preview-before-confirmation, organisation isolation, idempotency and source timestamps.
4. For backend behavior changes, exercise the relevant tests against a dedicated `_test` database. For interface changes, run the build and check the affected screen at desktop and mobile widths.

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
npm --prefix frontend run build
```

Use a small, focused pull request with the reason for the change and the checks actually run. Report defects through GitHub Issues with reproduction steps and fictional example data. See [SECURITY.md](SECURITY.md) for sensitive findings.

The repository's source licensing terms apply; dependency, font and artwork terms are separate. See [third-party notices](THIRD_PARTY_NOTICES.md).
