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
