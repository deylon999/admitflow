# KAN-214: account authentication

Status: implementation in progress, NOT production authentication acceptance.
2026-11-13, S210. User specification is the acceptance authority.

## Baseline (T270)

Clean checkout; branch `feat/kan-214-account-foundation` based on current
`origin/main` 3708d901642727cacf5590bc2f6183884880b286.
GitHub confirms PR13 (KAN-212) merged, source e9097a7; PR12 (CI) merged,
source 6fa789d. Their reports describe 147 frontend / 719 backend checks
and migrations0011; these are prior evidence, not tests of KAN-214.
Reviewed PR descriptions against local log. No published history rewritten.

## Review sequence

1. Foundation: audit, threat model, contracts, independent models, additive
   migration and password primitives. No public auth endpoints enabled.
2. Register/login: account creation and sessions, persistent rate budgets.
3. Refresh/logout/CSRF: revocation, rotation, races and negative tests.
4. Verification/recovery: SMTP transport, single-use actions, delivery errors.
5. React: reuse shared request, separate account epoch, forms, reload/logout.
6. Acceptance: native PG E2E, security/visual/browser regression and hosted CI.

Each PR requires review and merge before the next stage. Agent does not merge.
Full KAN-214 remains open until all six are accepted. Missing real SMTP delivery
or HTTPS environment blocks production acceptance; mock delivery proves tests only.

## Lifecycle audit (T271)

Inspected requested backend main/database/config/http/schemas/maintenance/operations,
admissions Subscription/Assessment/ChangeEvent ownership, Alembic env/revisions and
session/API/native migration tests. Inspected frontend App/AuthPages/shared API,
DTO/resource/ResourceState, navigation/RouteLink, SCREEN_INVENTORY, Playwright config
and route/API/unit scenarios. Reviewed compose development/production, Dockerfiles,
PostgreSQL configuration, nginx proxy/security headers, Caddy, env examples and CI.

- Guest: explicit POST /api/v1/session creates 256-bit random token, SHA256 in
  BrowserSession, HttpOnly `abiturient_session`, /api, Lax, 30 days. Existing valid
  cookie reused; expired cookie returns401, no implicit renewal. GET gives expiry
  and draft scope; DELETE removes BrowserSession and cascades owned Watch,
  Snapshot, Subscription, Assessment, ChangeEvent, LookupBudget, OperationRecord.
  Hourly cleanup also deletes expired guest ownership. Existing behavior preserved.
- Guest writes use owner row locking (PostgreSQL FOR UPDATE; SQLite BEGIN IMMEDIATE),
  operations use owner-scoped idempotency. Resource IDs alone never authorize.
  Do not call guest DELETE on login/logout, relabel owner_hash, or merge histories.
- Current HTTP protections: exact production PUBLIC_ORIGIN, trusted Host, custom
  write header, sec-fetch-site rejection, no CORS; missing Origin allowed for CLI.
  Byte/time/JSON-depth budgets and safe validation errors; diagnostics log route
  templates/status/requestId, not bodies/query/cookies. no-store on all responses.
- nginx has address limits and trusted Docker subnet for forwarded addresses;
  these are insufficient account/email budgets across workers/restarts. No
  application-wide persistent authentication rate limiting currently exists.
  nginx provides CSP, no-referrer, frame DENY; Caddy HTTPS/HSTS. Production Settings
  requires PostgreSQL, Secure cookies, HTTPS origin and explicit migrations.
- CI has frontend, required native PG backend, standalone migrations and ETL jobs.
  Extend collected tests; no workflow rewrite/infrastructure change in PR1.
- React auth forms are Unsupported/opt-in Demo. `/app` is not account-only:
  live subscriptions/history are guest-owned. Profile/settings are Unsupported.
  No existing implemented account-owned business endpoint to reassign in PR1.
- Reuse request(), DTO decoders, AbortController, bounded timeout, no-store backend,
  ResourceState, navigation. Preserve guest sessionEpoch/draft scope/events.
  PR5 adds explicit public/guest/auth/account classification and separate account
  epoch+abort boundary; generic auth401 MUST NOT create/expire a guest session.
  Private data cleared synchronously on account switch, auth loss and logout;
  reject stale results after headers AND JSON decode. Broadcast only change markers.
- Runtime discrepancy: no admitflow containers currently running in this session;
  old STATE healthy-stack claim is historical. Other projects' containers left alone.
- External dependencies: real SMTP credentials/from/domain, verified delivery,
  production HTTPS host and trusted proxy address contract not provided. Production
  backend currently internal-only network: SMTP egress needs CI/CD-owner agreement
  before deployment. No new service/secret/production networking added here.

Baseline verification: `backend/.venv/bin/python -m pytest -q
backend/tests/test_sessions.py backend/tests/test_api.py`: 19 passed, exit0.
This baseline uses isolated SQLite fixtures; native PostgreSQL evidence follows
in T273 and is required independently. Existing httpx deprecation warning retained.

## Architecture and threat model (T272; target contracts, not implemented APIs)

Threats: credential stuffing, enumeration, CSRF/login CSRF, fixation, stolen/replayed
refresh, race double consumption, cross-account stale UI, DB disclosure, mail abuse,
proxy spoofing and resource exhaustion. XSS can act as a user even with HttpOnly;
existing CSP and escaping remain mandatory. DB write/admin compromise and stolen
mailbox require operational response; hashes alone cannot prevent them.

Six independent tables; no FK from/to guest ownership:
`account_users` (UUID string identity, normalized unique email, hash, status,
verification/password-change timestamps), `account_sessions` (user FK, current access
hash/expiry, absolute/idle deadlines, revocation), `account_refresh_tokens` (hash PK,
session FK, issued/expiry/consumed timestamps; retain spent hashes for replay),
`account_action_tokens` (hash PK, user FK, verify_email/reset_password purpose,
expiry/used timestamp), `account_csrf_contexts` (hash of HttpOnly context cookie,
random synchronizer value, optional session FK, expiry), `account_rate_buckets`
(operation+HMAC(subject)+window PK, count/expiry; no raw IP/email).
Server UUIDs stable across future email changes. FK cascades affect accounts only.
Checks enforce enums, lifetimes and nonnegative budgets; transactions enforce
cross-table lifecycle invariants. PostgreSQL uniqueness is the final race arbiter.

### Credentials, CSRF and concurrency

- Generate independent 32-byte secrets with secrets.token_urlsafe(32). DB stores
  domain-separated SHA256 digests of high-entropy credentials, never password SHA.
  Opaque access cookie `admitflow_access`, Path=/api/v1; refresh
  `admitflow_refresh`, Path=/api/v1/auth. HttpOnly, SameSite=Lax, Secure in production,
  no Domain; no bearer credentials in JSON/browser storage. Delete exact paths.
- Access 15min. Session absolute 30d, idle 7d; refresh credential expires no later
  than both. Every protected request checks user active+verified, session revocation
  and deadlines. Refresh extends idle only, never absolute; no new session/user/guest.
- Synchronizer CSRF: GET /auth/csrf creates expiring (30min anonymous, session-bound
  deadline after login) context. Cookie `admitflow_csrf_context`, HttpOnly /api/v1,
  Secure/Lax/no Domain. Return synchronizer value in JSON, keep in JS memory only.
  Store synchronizer value server-side (not an auth credential); context cookie hash
  alone cannot authorize account data. Require constant-time X-CSRF-Token comparison
  AND matching context cookie/session for every auth/account mutation, including
  register/login/recovery/refresh/logout. Retain current Origin/custom-header checks.
  Login destroys anonymous context and issues new session-bound context; sessions
  cannot borrow each other's CSRF. GET is never token-confirmation or logout.
- Atomic lock order user -> session -> credential/action, consistent in reset,
  login, refresh, logout and confirm. Discover user ID then acquire/re-read under
  locks. Refresh consumes old record, replaces access, inserts new refresh in one
  transaction; spent refresh revokes family, commits revocation before error401.
  Concurrent same refresh: at most one rotation, other revokes family. Strict replay
  has availability cost on lost responses; no grace window issuing multiple secrets.
  Browser single flight + Web Locks across tabs; recheck session after lock. If lock
  support unavailable, no automatic cross-tab rotation, request explicit re-login.
  No infinite refresh; one retry for account-protected requests only.
- Logout can identify session via refresh when access expired; verify CSRF, revoke
  family, delete account cookies/contexts, idempotent204. Unknown session may only
  clear cookies after valid preauth CSRF, never revoke someone else's session.
- Verification/reset: purpose-separated hash, 24h/30min expiry, single-use under user
  lock; resend invalidates older same-purpose actions. Reset revokes ALL sessions
  and pending reset tokens atomically, updates password timestamp, no automatic login.
  Confirmation links use fixed PUBLIC_ORIGIN + /auth/verify or /auth/reset and URL
  fragment, immediately remove fragment via replaceState before requests. Tokens
  never go into request URL/referrer/logs; POST JSON only. No callback/open redirect.

### Input policy and password storage

ASCII dot-atom local email only, domain labels with valid hyphens; trim outer
whitespace, lowercase entire address. Length <=254 bytes, local <=64, no consecutive
or edge dots, no quoted local/IP domain/SMTPUTF8. Unicode domain input must be explicit
punycode. Do not strip plus tags/dots or apply provider rules. Case-insensitive local
part is an explicit product identity rule; confirmation proves mailbox control.
PostgreSQL unique normalized email plus CHECK lowercase/trim; concurrent duplicate
registration returns same public response after IntegrityError rollback.

Password: 15..128 Unicode code points, <=512 UTF8 bytes, valid UTF8, no NUL;
no trim, normalization, truncation or composition requirements. Reject compact local
common-password denylist; it is NOT a complete breached-password corpus. No remote
password disclosure service. Argon2id via argon2-cffi25.1.0 RFC9106_LOW_MEMORY:
64MiB, t=3, p=4, salt16, tag32. Fresh random salt per hash; check_needs_rehash
on verified login, replace hash transactionally. Dummy hash verification for absent
users, same generic401 for wrong/missing/disabled/unverified credentials. Bound
parallel hashing (two per process) plus persistent pre-hash rate budgets; production
memory/load tuning required, never weaker hashes in tests.
Sources checked 2026-11-13: [RFC9106](https://www.rfc-editor.org/rfc/rfc9106.html),
[argon2-cffi parameters](https://argon2-cffi.readthedocs.io/en/stable/parameters.html),
[OWASP authentication](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html).

### Target API (prefix /api/v1/auth)

DTOs use existing camelCase model policy, extra fields forbidden, bounded inputs;
validation errors omit input values. Account DTO: `{id,email,emailVerified:true}`;
session DTO: `{account,accessExpiresAt,absoluteExpiresAt}`. No password hash/secret.
CSRF bootstrap DTO `{csrfToken}` is the sole non-auth synchronizer token response.

| Method/path | Body -> success | Credential and CSRF | Failure/repetition |
|---|---|---|---|
| GET /csrf | none ->200 csrf DTO | optional context/account cookies, no CSRF | safe repeat; bounded context creation |
| POST /register | {email,password} ->202 {message} | preauth CSRF | generic accepted for existing email;422/429/503 |
| POST /login | {email,password} ->200 session DTO | preauth CSRF, sets fresh account cookies | generic401;422/429/503; no guest promotion |
| GET /session | none ->200 session DTO | access, no CSRF |401 code access_expired only if session can refresh; other401 terminal;503 network is not logout |
| POST /refresh | {} ->200 session DTO | refresh+bound CSRF, rotates both credentials |401 terminal/replay;403/429/503; never blind retry |
| POST /logout | {} ->204 | account or preauth context+CSRF | idempotent;403/429/503 |
| POST /verification/request | {email} ->202 {message} | preauth CSRF | uniform existing/missing/verified;422/429/503 |
| POST /verification/confirm | {token} ->204 | preauth CSRF |400 invalid/expired/used (one message);429/503 |
| POST /recovery/request | {email} ->202 {message} | preauth CSRF | uniform response;422/429/503 |
| POST /recovery/confirm | {token,password} ->204 | preauth CSRF |400 invalid/expired/used;422/429/503; no login |

All mutations retain X-Requested-With and Origin checks. No automatic retries for
credential mutations. Auth errors have stable safe codes (401 access_expired,
not_authenticated;403 csrf_invalid;429 rate_limited;503 auth_unavailable).
Future account-protected endpoints use separate account dependency and query by
user UUID, never owner_hash. KAN-215 profile fields, KAN-216 global route policy and
KAN-225/226 business logic excluded; expose dependency/current-user contract only.

### Persistent rate and email policy (PR2-4)

Atomic PostgreSQL upsert fixed-window counters, committed separately BEFORE expensive
hash/mail operation, persist failures and survive restart/workers. HMAC key configured
via environment (production mandatory), no raw email/IP in buckets. Request peer
address is default; never parse arbitrary X-Forwarded-For. Deploy per-IP limits only
after explicit trusted proxy chain contract with CI/CD owner; peer-only counting
behind nginx must be documented as aggregate, not genuine per-client protection.
Per-IP operation limits: register10/h, login30/15min, refresh120/15min,
mail20/h, confirm30/15min, csrf120/15min. Additional email+IP login10/15min,
registration/email3/h, mail/email3/h. Email-only delivery budget silently suppresses
mail with uniform202 to avoid enumeration; IP budget429 Retry-After. No permanent
account lockout. Mail retries limited; SQL expiry cleanup hourly, indexed expiry.
Rate capacity and boundaries tested against native PG concurrency/restart.

SMTP adapter via stdlib smtplib with STARTTLS verified certs (or implicit TLS),
timeouts, credentials from environment. No configured provider ->503 globally before
account lookup; no pretend successful send. Existing/missing requests use uniform
public response and bounded transport-error handling to avoid enumeration. Deliver
outside DB locks with explicit delivery result; failed new registration remains
unverified and recoverable by resend. Do not report actual account creation when
DB commit fails. Real transport failures get generic503 without credential/error text;
PR4 must ensure failure response does not create a reliable account oracle (e.g.
provider circuit state applies to all requests). No unencrypted token outbox; only
hashes persist. Crash after commit/before send requires explicit bounded resend.

### Verification and release gates

PR1: real PG migration0011->0012 keeps guest rows byte-for-byte; fresh upgrade,
standalone alembic check, rollback/re-upgrade on isolated DB only; unique email race,
FK/enums/lifetime checks and account-delete/guest-delete independence. Hash tests
use production parameters. Remaining PRs test listed CSRF/replay/reset concurrency,
real browser flow with isolated test mailbox, private stale-state, all29 routes and
390/1440 visual comparator. Full backend/native guard and hosted four jobs required.
Review and owner acceptance remain external; SMTP mock is never production evidence.

## PR1 implementation evidence (T273)

Added six account ORM tables in app/accounts.py and frozen additive Alembic0012
(no runtime model imports in revision). Registered metadata in standalone Alembic
and migration callers. Hourly cleanup and cleanup-accounts CLI delete only expired
actions/contexts/buckets/absolute-expired account sessions; spent refresh records
remain until session deletion so replay can still be detected. Users never purged
by this command; guest cleanup semantics unchanged. Actual API enforcement follows
in PR2-4, not inferred from table availability.

Isolated PostgreSQL17 container `admitflow-kan214-test-db`, database
`admitflow_test_kan214`, loopback55439; no existing project volume/database touched.
Native tests allocate/drop their own random schemas through existing pg_support.
Command (TEST_DATABASE_URL points only to that disposable DB):
`backend/.venv/bin/python -m pytest -q backend/tests/test_account_foundation.py
backend/tests/test_migrations.py backend/tests/test_migration_metadata.py
backend/tests/test_database_diagnostics.py` -> **39 passed**, no skips, exit0.
Foundation cases include native two-transaction unique email race, six invalid
security-state constraints, expired-record cleanup retaining spent refresh,
account/guest deletion independence, all existing table rows identical across
0011->head and downgrade/re-upgrade, and standalone Alembic schema agreement.
Historical head assertions updated0011->0012 and table count20->26; no check removed.
Three existing framework/legacy migration deprecation warnings remain.

## Password primitives (T274)

Pinned argon2-cffi25.1.0 and resolved runtime dependencies in requirements/constraints;
no existing dependency upgraded. `app/account_security.py` implements documented
email/password policy, production-parameter hashing, bounded two-slot hashing,
dummy verification, rehash signalling, random tokens and purpose-separated digests.
This is a primitive library; login rate limiting/rehash transactions are PR2 work.
`pytest -q backend/tests/test_account_security.py backend/tests/test_sessions.py
backend/tests/test_api.py`: **52 passed**, exit0; `pip check`: no broken requirements.
Tests cover normalization boundaries, invalid input, actual Argon2id parameters,
unique salts, wrong/missing/malformed hashes, stronger historical rehash signalling,
128-codepoint Unicode passwords/whitespace preservation, capacity release and token
entropy/purpose separation. No weaker development/test hashing profile.

Regression adjustment: historical catalog migration test correctly exercises
0010/0011; its final schema check now upgrades to head first, so it can still compare
current metadata after0012. No catalog/source logic or applied revision changed.
Frontend source, CSS, dependencies, routes and visual baselines unchanged.

## Regression and handoff

- npm ci/lint/typecheck/build: exit0; existing npm test **147 passed** (all29
  route/history checks and browser/API/DTO scenarios). Browser runtime uses isolated
  SQLite fixtures; this is not substituted for native PG proof above.
- Frontend/CSS/baselines/workflows/compose diff against main: zero files changed.
  No new pixel-comparator run claimed; auth-form visual comparison remains PR5/6.
- ETL: **55 passed, 1 explicit missing-dataset skip**, exit0. No ETL source changed.
- Repository tools: 17 tests, 1 local missing-PDF-dependency skip; hosted CI installs
  its required reporting dependencies. roadmap render/check and git diff --check pass.
- Initial full native-guard run: 760 passed, two historical catalog head-check
  failures. Both corrected without removing assertions; focused current rerun
  foundation/password/catalog: **48 passed** incl absolute-expiry credential purge
  preserving the account, cascade cleanup and idempotence. Final full native-guard run: **763 passed, zero skipped**, exit0 (194.75s).
- Clean migration verifier requires its own fresh `admitflow_test*_migrations` DB;
  ran successfully against isolated `admitflow_test_kan214_migrations`, head0012,
  no schema drift. An initial invocation with the non-migrations test DB name was
  correctly rejected by its guard before migration; it did not modify that DB.

PR: https://github.com/deylon999/admitflow/pull/14 (PR1/6 only).
Initial source701e5ce workflow: https://github.com/deylon999/admitflow/actions/runs/43409888388.
Latest source SHA and hosted results are maintained in the PR description to avoid
an evidence-only commit invalidating its own final SHA. Owner review not received;
agent never merges. No registration/login/refresh/logout/email/recovery endpoint
exists yet, and no account auth acceptance or production delivery is claimed.
Next work after review/merge: T275 / PR2, register/login and persistent rate budgets
using the target contracts above. T276-279 remain open; no next-stage implementation
started before review. No production secrets, user DB, volumes or deployed stack changed.

Final local command: `TEST_DATABASE_URL=<isolated PG> backend/.venv/bin/python -m pytest -q --require-postgres --ignore=backend/tests/test_admission_history.py --ignore=backend/tests/test_accreditation_registry.py --ignore=backend/tests/test_exam_requirements.py backend/tests`. ETL runs separately above, as in CI. Final local PostgreSQL schemas cleaned; owned test container and its anonymous volume removed. User volumes untouched.

## S211 continuation after owner merged PR14

PR2 implementation and current endpoint/CSRF/disabled-rollout details are in
[KAN-214-PR2.md](KAN-214-PR2.md). Earlier “no endpoints” statements describe PR1's
historical state. PR2 issues access only, never refresh until PR3; it brings forward
synchronizer CSRF for safe login/registration. Actual mail unavailable until PR4.

## S212 lifecycle continuation after owner merged PR15

PR3 implementation, cookie/replay/logout contracts and evidence:
[KAN-214-PR3.md](KAN-214-PR3.md). Refresh now minted at login and rotated under
server locks; logout revokes the family before exact-path cookie deletion. A short
CSRF tombstone replaces immediate context deletion solely for idempotent logout;
revoked families cannot authorize account data or refresh. Browser coordination and
real SMTP/verification/recovery remain subsequent PRs; default auth stays disabled.

## S213 email actions after owner merged PR16

[PR4 contracts and evidence](KAN-214-PR4.md): TLS SMTP adapter, verification/resend,
one-use recovery and transactional password/session revocation implemented. Only
recording/protocol tests verified, no real provider/inbox delivery supplied. Default
auth remains disabled; frontend fragment/forms/session integration is PR5. Full
KAN-214 delivery acceptance remains external, independent of code/CI completion.

## S214 React integration after owner merged PR17

[PR5 implementation/contracts/evidence](KAN-214-PR5.md): real controlled auth forms,
server-confirmed state after login/reload, cross-tab locked refresh, account-only
profile summary/logout and fragment verification/reset screens. Shared client and
guest lifecycle preserved, Demo remains separate. Chromium default174 tests plus
2 native-PostgreSQL browser scenarios;108 retained Live/Demo comparisons identical.
PR5 awaits owner review/merge; KAN-214 full acceptance remains PR6 and the external
real SMTP/HTTPS gate. Earlier statements about missing frontend describe past PRs.
