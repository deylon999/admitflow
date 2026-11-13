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
