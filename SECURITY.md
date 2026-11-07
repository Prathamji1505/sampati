# Security

Sampati currently targets a loopback-only local environment and fictional data. It is not configured for public hosting or real aviation operations.

## Reporting a vulnerability

Use the repository's **Security → Report a vulnerability** option if private reporting is available. Otherwise contact the maintainer through the contact method on [their GitHub profile](https://github.com/Prathamji1505). Do not put credentials, exploit details affecting private data, session cookies, recovery codes, source keys or personal records into a public issue. A public issue can request a private contact channel without including those details.

## Local development

- `.env`, `.local/`, databases, backups and installed dependencies are excluded from source control.
- Backend tests require a database name ending in `_test` and create a separate random schema per test.
- Demo routes intentionally permit local unauthenticated access. Organisation routes verify current membership and write roles.
- File preview does not save accepted aircraft. Confirmation checks a signed preview and commits the batch atomically.

## Before hosting

HTTPS and Secure cookies, origin configuration, persistent infrastructure, secret management, off-device backups, abuse controls and a deployment/security review remain work to do. The presence of tests or CI is not a production security certification.
