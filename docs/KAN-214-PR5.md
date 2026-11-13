# KAN-214 PR5: React account integration

2026-11-13 S214. Owner requested PR5; PR17 merged into
3035f5e0bd2ba1cbeb3c13c1a002e136d16661d2. Clean isolated branch
feat/kan-214-react-auth. PR17 source0451f7a/run43464449737: all4 hosted jobs success,
backend976/0skip,frontend147,migrations0012/head/check. Real SMTP delivery NOT accepted.

## Audit and acceptance before implementation (T295)

Inspected shared/api request/guest epoch, resource/ResourceState, DTOs, App/router,
navigation/RouteLink, Shell/AuthPages/Unsupported, inventory/tests/runner/runtime,
styles/UI primitives and backend DTO/lifecycle/email contracts. Preserve KAN-212
check after headers AND body/decoder, AbortController, safe errors, explicit guest
recovery and source/catalog paths. Do not replace owner_hash or guest subscriptions.

Add explicit public/guest/auth/account endpoint classification, separate account
epoch/abort boundary and lifecycle hook to existing shared/api.ts. No second fetch
client. Auth/session is a controlled private read; only classified account-protected
access_expired can request one refresh/retry. Never refresh login401, public/guest401,
403 or an unclassified auth error. Exact status/whitelist DTO validation mandatory.

Account state derived from GET auth/session after reload/login/refresh; network503
is unknown/error, not proof of anonymity. No private children before confirmation.
No auth credentials/password/CSRF/one-time links in localStorage/sessionStorage.
Only random transition markers may be stored/broadcast. Abort/reject old account
results on switch/logout/loss without changing guest epoch or deleting guest data.

Serialize account-cookie mutations and restoration with a named Web Lock, and
single-flight inside each tab. Recheck server session after acquiring the lock;
parallel tabs should not rotate the same refresh twice. Bounded lock/request waits;
no blind POST retry. When Web Locks unavailable, no automatic refresh; require
explicit re-login without revoking a still-valid server family. Backend replay
remains strict; no grace/bypass. Account transition markers immediately clear old
private state in peers; end reconciles under lock, expiry never echo-loops.

Live /auth/login/register/recovery reuse approved AuthPage frame/CSS. Controlled
fields, server policy15..128 codepoints for new passwords, confirmation, loading,
double-submit guard, abort, safe API/429/network errors and secret clearing. Never
claim account creation/sent email from a generic202 or failed503. Login confirmation
requires server GET session matching POST login identity. Explicit Demo keeps original
visual form and no real auth request. No full profile/route policy/KAN-215/216 scope.

Add /auth/verify and /auth/reset technical screens in existing auth layout. Capture
and erase #token before network/render, keep only in memory, clear on use/unmount.
StrictMode must not consume/lose the token twice. No query-token fallback/callback
URL; no automatic GET or mount confirmation. Reload after erasure requires reopening
the email link; this intentional tradeoff avoids secret persistence. Backend503 is
shown as unavailable; actual provider/inbox validation stays outside this code PR.

Minimal current-account/profile guard+logout, not a blanket /app guard (guest features
stay live). Default public/guest layout remains unchanged; only necessary auth/
profile state content may differ. Original29 inventory retained plus2 technical
routes; no visual baseline rewrite. Real native-PG browser flow uses an owned test
runtime and file mailbox outside web root/artifacts, never a product debug endpoint.
Existing CI contour unchanged; opt-in native PG browser evidence reported separately
from default mock/browser-contract tests if frontend CI has no PostgreSQL service.

T296 implementation: shared transport now classifies public/guest/auth/account paths;
account errors never trigger guest expiry, error codes are bounded/whitelisted and
Retry-After is retained. Account DTOs whitelist fields. Independent account epoch
checks both headers and body and aborts private reads. External account store uses
server session proof, one refresh mutation under Web Locks, same-tab single flight,
nonsecret cross-tab markers and explicit unavailable state. Guest epoch remains intact.
Validation: frontend typecheck/lint and 32 transport/DTO tests passed locally.

T297 implementation: Live forms use the existing v3 auth frame/styles; controlled
fields, matching long password validation, bounded input, safe errors/429 and abort
on route exit. Generic202 is shown as a conditional accepted request, not account
creation/delivery proof. Live login confirms the returned identity via GET session.
Resend/verification/reset are explicit actions; fragment credentials are erased
before rendering/API and never persisted. Demo stays inert with its original preview.
Initial full browser run: all9 new auth scenarios passed; three regressions exposed
an unnecessary account bootstrap on public catalog pages and changed public401
wording. Fixed by lazy bootstrap on auth/app routes and preserving the public error
contract. No existing guest assertion was relaxed.

T298: minimal current-account guard and server logout preserve guest identity. Peer
begin markers clear old account content before slow logout, end markers reconcile
under Web Locks; a bounded fallback handles a tab closing before its end marker.
Focus/pageshow revalidation also drops old private state first. A terminal session
read invalidates pending private reads; an account change during an API retry cannot
expire the new account. No refresh without Web Locks (HTTPS/localhost browser API).
Default browser suite extended with credential denial, failed POST/session mismatch,
slow logout/route cancellation, malformed links, expired refresh and no-lock fallback.
Native-PG browser runtime lives only in backend/tests: random disposable schema,
private ephemeral file mailbox/clock outside artifacts and web root, no debug HTTP
routes or runtime product flags. Credentials excluded from E2E trace/screenshots.

Validation T298: default Playwright172 passed; targeted transport/DTO35 passed after
additional stale-owner retry fix; two native PostgreSQL browser scenarios passed
(account lifecycle/refresh/logout/recovery and account switch/CSRF/wrong password).
Full unchanged backend regression:976 passed,0 skipped,4 existing Alembic warnings,
306.32s on Python3.14/PostgreSQL17. Backend product code/migrations are unchanged.

## Final implementation and contracts (T299)

The existing `shared/api.ts` remains the only browser HTTP transport. Existing guest
session events, epoch checks after headers/body/decoder, cancellation, resources,
public catalogs and explicit guest recovery are preserved. Auth adds a distinct
account epoch/abort boundary and a whitelist current-user DTO. `account.ts` owns
server reconciliation; `useAccount` reads its stable external snapshot. No account
proof is taken from storage. Cross-tab BroadcastChannel and storage carry only a
random ID/phase marker (deduplicated); channel also works when storage is blocked.
Public routes do not bootstrap accounts unnecessarily. Auth/app reload does, with
checking/anonymous/authenticated/error states; network failure is never anonymity.

A named Web Lock serializes account cookie mutations, CSRF bootstrap and authoritative
session reads. Same-tab restore is single-flight. After obtaining the lock the tab
checks the server again before issuing at most one refresh mutation. No refresh on
public/guest/login401; only account-protected access_expired is eligible for one
refresh and one request retry. A terminal401 clears private state. Epochs reject
old results during policy waits, headers, body and retry. Logout starts by hiding
private content and ends only on backend204; failed logout is an error, never a
claim of revocation. Cookies are managed exclusively by the existing backend.

Browser support is Chromium verified. Web Locks requires HTTPS (localhost is a
secure-context exception); without locks valid access still works, automatic
refresh is disabled with an explicit re-login state. Other browser engines and
production HTTPS/proxy deployment remain PR6 acceptance work. No unbounded polling,
refresh grace period or blind retry of a POST was added.

Backend password hashing, DB-backed rate budgets, CSRF binding, strict opaque
refresh rotation and server revocation remain the reviewed PR1–4 implementation.
No backend product code, schema, applied migration, dependency lock, Compose or
GitHub Actions workflow changed. Account users remain separate from BrowserSession;
no owner_hash replacement, guest/account data merge or guest deletion is performed.
The new profile screen only shows the server-confirmed email and logout. All guest
/app functions remain available; full profile and global redirects are KAN-215/216.

Frontend uses these existing contracts (all under `/api/v1/auth/`; errors are safe
whitelisted codes/status,429 includes Retry-After):

| Method/path | Request | Success | Browser policy |
|---|---|---|---|
| GET csrf | none |200 csrfToken |memory only, under account lock |
| GET session |none |200 account/id/email/emailVerified + accessExpiresAt/absoluteExpiresAt |server proof;401 renewable only with access_expired |
| POST register |email,password |202 generic message |CSRF; no auto-login; new password15..128 codepoints/512 UTF8 bytes |
| POST login |email,password |200 session DTO |CSRF; follow-up GET must confirm the same ID |
| POST refresh |{} |200 session DTO |CSRF; one rotation under Web Lock, no blind retry |
| POST logout |{} |204 |CSRF; server revocation; preserve guest cookie |
| POST verification/request |email |202 generic message |CSRF; no account enumeration or delivery claim |
| POST verification/confirm |token |204 |CSRF; explicit action, fragment held in memory only |
| POST recovery/request |email |202 generic message |CSRF; no enumeration or delivery claim |
| POST recovery/confirm |token,password |204 |CSRF; single use; then reconcile current browser account, never auto-login |

Account-only future reads must use the explicit account/* scope and backend account
ownership checks. This PR introduces no business account data endpoints. New
account mutations must define their CSRF/transaction/idempotency contract; the
frontend classifier alone is never resource authorization. KAN-216 can consume
useAccount/retryAccount and the guard states without restricting guest features;
KAN-215/225/226 can build on stable account ID and reviewed server sessions.

## Reproducible validation and evidence

Run npm commands from frontend. Use a disposable PostgreSQL17 database named
admitflow_test*; never set test URLs to a working application database.

```sh
npm run lint
npm run typecheck
npm run build
node --test scripts/stop-child.test.mjs
npm test
AUTH_BROWSER_E2E=1 TEST_DATABASE_URL='<disposable-postgresql-url>' npm test
node scripts/check-auth-visual.mjs
```

The opt-in native-PG runner owns one random schema and removes it on shutdown; its
mailbox/clock use a private temporary directory outside the web root/artifacts,
removed by the Node runner. Real browser flows have tracing/screenshots/video off
so email credentials/passwords cannot enter artifacts. Normal default CI still runs
all existing tests plus auth unit/browser-contract cases; it has no PG browser
service. Native-PG browser evidence is local, not a hosted full-stack delivery claim.

Backend validation from repository root:

```sh
TEST_DATABASE_URL='<disposable-postgresql-url>' backend/.venv/bin/python -m pytest -q --require-postgres --ignore=backend/tests/test_admission_history.py --ignore=backend/tests/test_accreditation_registry.py --ignore=backend/tests/test_exam_requirements.py backend/tests
backend/.venv/bin/python -m pytest -q -ra backend/tests/test_admission_history.py backend/tests/test_accreditation_registry.py backend/tests/test_exam_requirements.py
python -m unittest scripts.tests.test_roadmap scripts.tests.test_weekly_report
python scripts/roadmap.py --render --check
```

Clean-database migration gate (from backend, database name ends in _migrations):
`PYTHONPATH=. MIGRATION_DATABASE_URL='<empty-disposable-postgresql-url>' .venv/bin/python tests/check_migrations.py`.
It confirms emptiness before touching schema:0012/head, no new upgrade operations.
No application databases or volumes were used. Full backend976 passed/0skip,
4 pre-existing Alembic warnings,306.32s. ETL55 passed plus1 explicit unavailable
external dataset skip; repository tools17 with1 local optional PDF dependency skip
(hosted installs that dependency); pip check clean; server lifecycle3 passed.
Frontend175 tests, including7 new transport/DTO and21 browser-contract cases, plus
2 native-PG browser scenarios. The latter cover registration, real email-token
consumption via the test port, login/reload, exactly one parallel-tab refresh,
logout/stale-cookie rejection, recovery/one-use/reset/revocation, absolute expiry,
guest cookie preservation, two-account switching, CSRF and wrong-password denial.
Resetting account A while logged in to B preserves B's independent session.

Visual comparison against reviewed main3035f5e:108/108 exact screenshot byte matches
at390/1440 (25 retained Live routes + all29 Demo routes, both widths). The three
Live auth forms and minimal account profile intentionally change functionality and
have separate captures; both new technical routes captured too (12 screenshots).
Only the coverage.generatedAt fixture is fixed equally for the two builds, since
it otherwise differs on every API request. Comparison waits for rendered resources
and completed font/paint frames, not an idle network (canceled competition requests
can remain pending in the preview proxy). No threshold or historical baseline was
changed. Auth resend uses the existing outline button style; no CSS redesign.

[Machine evidence](evidence/kan-214-pr5.json),
[108 visual comparisons](evidence/kan-214-pr5/visual-comparison.json),
[desktop login](evidence/kan-214-pr5/login-desktop.png),
[mobile registration](evidence/kan-214-pr5/register-mobile.png),
[mobile account guard](evidence/kan-214-pr5/account-guard-mobile.png).
Exact final SHA, review PR, hosted run/job conclusions and review status are recorded
in the PR description so documentation does not create a second untested CI head.

## Acceptance boundaries and handoff

T295–T298 implementation steps complete; T278/T299 remain in review pending owner
acceptance. Do not merge automatically. KAN-214 full acceptance is still PR6, real
SMTP provider/inbox delivery or the owner's explicit documented exception, and
production HTTPS/proxy checks. AUTH_ENABLED remains false by default. No real email
was sent or inbox delivery verified. The isolated file mailer proves the backend
integration and browser workflow only. No production-ready claim or gate completion.

Final mobile follow-up: account email uses scoped overflow-wrap so a valid64-character
local part stays inside a390px screen. Added a browser assertion for this boundary;
full frontend175 passed (22.6s), lint/typecheck clean. This only affects the new live
account summary, not the108 retained comparison routes. No CSS file changed.

Final privacy boundary: the link capture canonicalizes the same trailing slash
accepted by App, so `/auth/verify/#token=...` is also erased before rendering/API.
Extended the fragment browser scenario with this accepted route variant. Full175
frontend tests passed again (22.5s), lint/typecheck clean; no extra auth mutation.
