# Accounts and organisation workspaces

The local account milestone extends the existing fictional-data workflow. It does not add military planning or operational aviation decisions.

## Boundary

- Guest data lives under `/api/demo/` in the original `local-demo` workspace.
- Private data lives under `/api/` and requires a valid session plus current membership.
- All aircraft, import, audit, comparison and fingerprint lookups include the resolved workspace ID.
- The server derives that ID from its stored session and membership. Client headers, query parameters, CSV fields and organisation names cannot select someone else's workspace.
- Signed preview tokens include workspace and actor identity. Tokens cannot be replayed across accounts or between demo and private mode.
- Switching the frontend workspace unmounts the prior register, pending preview and details. An expired private session shows the sign-in screen rather than silently substituting demo data.

## Accounts

Usernames are case-normalized and unique. Each sign-up atomically creates a user, a new organisation and owner membership; equal organisation names still create separate workspaces. The database stores Argon2id password hashes through pwdlib, following the password-hashing approach described by [FastAPI](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/).

Random session cookies are HttpOnly and SameSite=Strict, scoped to `/api`. The database stores session digests, expiry and a separate anti-forgery token. Private mutations require that token, while login/signup require a custom request header and are subject to origin checks. Logout deletes the stored session. Session rotation, cookie attributes and explicit anti-forgery checks are informed by [OWASP's session guidance](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html).

Account workspaces verify current role on each request. Owners and editors can import; viewers can read only. Per-address/account and per-address attempt windows are stored in PostgreSQL and locked during checks. They do not trust forwarded address headers in this local configuration. These are local controls, not a claim of production security certification. [OWASP multi-tenant guidance](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html)

## Verification and limits

The backend suite uses dedicated test-database schemas. Browser verification creates clearly marked, random fictional QA accounts in the local development database, checks the actual UI, then removes only the explicitly recorded fixture IDs through the guarded cleanup helper. It does not clear or replace demo records or user accounts.

Sign-up creates a new organisation owner per account. Targeted invitations, invitation acceptance, member roles/removal, verified organisation switching, password changes and one-time recovery are implemented. Recovery email, account deletion and hosted deployment remain unconfigured. HTTP cookies are deliberately not Secure for the loopback development URL; HTTPS deployment must enable `SESSION_COOKIE_SECURE`. No physical phone or production hosting was tested.

## Teams and recovery

Only owners issue/revoke invitations and manage membership. Invitations target an existing user ID, expire after three days, work once and require the issuer to remain an owner. Joining switches the current session to the new organisation and rotates its CSRF token; previous memberships remain selectable. Removing a membership cascades sessions currently using that membership. Role checks read current database membership on each request. A workspace-row lock and last-owner guard prevent removing every owner.

Changing a password requires the current password, revokes all old sessions and recovery codes, then issues a fresh session. Recovery-code generation requires the password and replaces the whole set. Only code hashes persist; raw codes appear once. Recovery consumes one code, changes the password and revokes existing sessions. Other unused codes in that set remain usable. A user-row lock serializes password changes, recovery and new-code generation. Losing the password and all saved codes has no built-in recovery path.

Source keys are random bearer credentials stored only as hashes, with once-shown raw values. They submit to one source's organisation-scoped inbox and cannot read or accept data. The connection creator must retain import permission. Disable/rotation revokes key use; rotating a key binds it to the current owner. Browser mutations still use session CSRF checks; machine ingestion uses the source key instead.
