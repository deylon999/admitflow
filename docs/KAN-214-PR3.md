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

## Refresh implementation (T286)

Login now persists independent domain-hashed refresh and session-bound CSRF with
idle7d deadline. Refresh peer120/15min plus session60/15min durable HMAC budgets
bound both distributed single-session abuse and aggregate peer load. After ID-only
discovery, lock user/session/refresh/context in that order. Locked ORM reads use
populate_existing so values cached before waiting cannot bypass revocation/consumption.
CSRF bootstrap also locks and revalidates family/credentials before attaching a
new context, preventing resurrection through a race with refresh or logout.
Existing expired-access denial test now expects access_expired when refresh is usable;
other terminal cases remain not_authenticated. Cookie tests assert refresh presence
and its narrower /api/v1/auth path. No guest or applied migration changes.

Native PG command: test_account_refresh.py + test_account_login.py +
test_account_http_security.py -> **39 passed**, exit0 (22.81s after revalidation fix).
Coverage includes actual rotation/hashed records, expiry/reload bootstrap, no guest
creation, strict replay revocation committed before401, concurrent refresh at most
one rotation, every terminal session/user/refresh state and absolute deadline caps.

## Server logout implementation (T287)

Logout resolves current family by refresh (including spent/expired records) or
access fallback, takes the same user/session/credential/context locks and requires
matching bound CSRF for an active family. Unknown or already inactive credentials
may be cleared using fresh anonymous CSRF. All refresh records become unusable by
family revocation, and unspent records are marked consumed. Existing bound CSRF
contexts are capped to30min tombstones for idempotent replay of the original logout
proof; they never authorize access/refresh. Logout does not extend tombstones.
Revocation commits before exact-path Secure/HttpOnly/Lax cookie deletion. No guest
DELETE/session creation, no reassignment of owner_hash and no other family revoked.

Native test_account_logout.py: **8 passed**, exit0 after final bulk-update handling.
Covers current/expired-access/access-only logout, repeated original proof, fresh
anonymous repeat, unknown/expired credentials, other account/family isolation,
refresh/logout serialization, guest history and DB failure without cookie deletion.
A first test fixture used global unscoped httpx cookies; corrected to actual server
host/path scopes before validating browser deletion. Race snapshots preserve cookie
scopes so either legal ordering (refresh200 then logout, or logout then refresh401)
is reproducible without a test-only CookieConflict.

## Concurrency and security verification (T288)

Current native PG refresh/logout/lifecycle-security suite: **47 passed**, exit0,
30.30s. Includes14 negative CSRF/Origin/header cases on both endpoints, mixed valid
account cookies, spent-refresh rejection without CSRF-authorized revocation, spent
refresh unable to bootstrap bound CSRF, durable peer/session budgets despite spoofed
forwarded headers, failed rotation/replay commit rollback, fresh application/engine
revocation persistence, production issuance/deletion flags, two competing refreshes,
refresh/logout serialization and a deterministic bootstrap/logout race paused before
row locking. Re-reading after the lock produces anonymous CSRF for the revoked
family. Future-time test proves idle extension while absolute deadline stays fixed.
No test uses weaker hashing, SQLite substitution or a public test-token endpoint.
Existing disabled-default test now includes refresh/logout; full backend collection
contains all new cases before the final run. HTTP/DTO/guest behavior stays covered.

## Implemented contracts

| Endpoint | Success | Policy/failures |
|---|---|---|
| POST /api/v1/auth/login |200 existing session DTO + access/refresh/CSRF cookies |PR2 credentials/CSRF/limits retained; refresh now minted atomically |
| POST /api/v1/auth/refresh |200 same account/session/absolute deadline, rotated access+refresh |body{}; valid bound CSRF/Origin/custom header; peer120 + session60 per15min;401 terminal,403 CSRF/mixed credentials,422 invalid body,429 Retry-After,503 unavailable |
| POST /api/v1/auth/logout |204 empty, account cookie deletion after commit |body{}; valid bound CSRF or anonymous proof for unknown/inactive family; peer60 + session60 per15min;403/422/429/503; no guest deletion |
| GET /api/v1/auth/session |200 current account/session |access_expired401 only when renewal is possible; other auth401 terminal;503 DB fault does not mean logout |
| GET /api/v1/auth/csrf |200 {csrfToken} |current access or fresh refresh binds context under locks; otherwise anonymous; no silent rotation/revocation/guest creation |

Origin/custom-header errors retain existing safe format. Tokens never appear in JSON
except the non-auth synchronizer value. Family revocation changes server state and
marks unspent refresh records consumed; the DB is the authority across workers.
Fresh access remains <=15min, idle <=7d, absolute <=30d since initial login. Refresh
cannot extend absolute lifetime or create a new user/session/guest. Lost-response
strict replay has an explicit re-login availability tradeoff. Frontend PR5 must
serialize refresh across tabs and perform only a bounded retry on classified auth
errors; this backend PR does not claim that browser coordination is implemented.
