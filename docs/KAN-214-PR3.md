# KAN-214 PR3: refresh, logout and revocation

2026-11-13 S212. User requested continuation; GitHub confirms PR15 merged.
Base main5cddc5401a05153917bbc02ad56166ea505d958c. Clean branch
feat/kan-214-session-lifecycle. PR15 final efbd0e6/run43414762564 all4 jobs success:
backend820/0skip,frontend147,ETL55+1 dataset skip,migrations0012/head/check.
This is baseline evidence, not verification of PR3 code.

## Acceptance and target contract before implementation

Preserve guest BrowserSession/owner_hash and existing Origin/custom-header guards.
No schema change expected: PR1 includes session/refresh/CSRF tables. Auth stays
AUTH_ENABLED=false pending PR4-6 email/frontend/acceptance. No SMTP/React work here.

Login issues access15min and independent refresh <=idle7d/absolute30d. Refresh cookie
admitflow_refresh HttpOnly/Lax/Secure in production, Path=/api/v1/auth, no Domain.
Session CSRF context/cookie bound to idle deadline and renewed with refresh; access
cookie remains /api/v1. No auth credentials in JSON/URL/browser storage.

POST /api/v1/auth/refresh {} ->200 existing session DTO/new cookies. Persistent
peer120/15min. Discover IDs, then lock user -> session -> refresh -> CSRF context,
re-read under locks. Validate bound CSRF BEFORE treating a spent refresh as replay
(prevents unauthorized revocation by a request without CSRF proof). One transaction
consumes old refresh, replaces access, inserts new refresh, extends idle within
absolute deadline and renews the SAME CSRF context (no secret rotation race).
Second use of spent refresh commits session-family revocation BEFORE terminal401.
At most one concurrent rotation; strict replay may invalidate that winner. Lost
refresh responses require re-login, no grace period or repeated credential issuance.
Spent hashes remain until absolute session expiry, as established in PR1 cleanup.

GET /auth/session ->401 access_expired ONLY for an active, verified, nonrevoked family
with a usable refresh; expired idle/absolute/refresh, forged or revoked credentials
are terminal not_authenticated. No silent guest creation or refresh on GET.
GET /auth/csrf can restore a bound context using a current refresh after access
expiry; spent refresh alone cannot obtain a bound context. A bound CSRF value is
not an account credential. Missing/foreign/wrong/expired context is403, valid
same-origin writes retain existing X-Requested-With/Origin rules.

POST /api/v1/auth/logout {} ->204 after server revocation commit, then delete access,
refresh and CSRF cookies at exact paths/flags. Resolve current family via refresh
when access expires, preserve every guest cookie/row. Other families remain active.
Keep a short (<=30min) CSRF tombstone for safe repetition with original valid proof;
it cannot authorize revoked account access or refresh. Fresh anonymous CSRF can
clear unknown/expired credentials; never revoke an unrelated active family.
After browser cookies are removed, a repeated write must bootstrap anonymous CSRF
rather than bypass CSRF. DB failure503 must not delete cookies/claim logout success.

All refresh/logout sensitive operations serialized on the same user/session rows;
commit failure rolls back consumption/issuance/revocation. Test real PostgreSQL
parallel refresh and refresh/logout, replay after restart, cookie mixtures, missing
CSRF/Origin, boundaries, production cookie deletion, rate limits and secret logs.
Frontend single-flight/Web Locks, request cancellation and account epoch are PR5;
strict backend rotation is ready to support that policy but does not claim browser
multi-tab acceptance. No frontend design, parser, CI or production networking changes.
