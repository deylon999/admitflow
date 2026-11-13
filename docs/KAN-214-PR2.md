# KAN-214 PR2: registration, login and persistent budgets

2026-11-13 S211. Base main494d270f5f44fefc2f295d442b4b9691d5f11610,
GitHub PR14 merged and user explicitly accepted continuation. Clean independent
branch feat/kan-214-register-login. Architecture: KAN-214-AUTH.md.

## Acceptance and boundaries before implementation

Implement POST /api/v1/auth/register, POST /login, GET /session and GET /csrf.
CSRF synchronizer prerequisite is brought forward from PR3: never expose login or
registration without CSRF. Preserve Origin/X-Requested-With/Host/body-budget guards.
Opaque access only in this PR; refresh credentials must NOT be issued until PR3
implements rotation/replay/logout. No account frontend or protected business routes.
Auth disabled by default via AUTH_ENABLED=false; enabled auth requires stable
AUTH_RATE_KEY (at least32 UTF8 bytes). Production remains PostgreSQL/HTTPS/Secure.
Do not enable incomplete lifecycle for production users before PR3-6 acceptance.

Registration uses an explicit verification-delivery port, default unavailable.
Unavailable transport ->503 for all addresses BEFORE account lookup/mutation, no
fake send or auto-verification. Tests inject an isolated recording/failing port;
no env-configurable test mailbox or public token retrieval. SMTP adapter, resend,
confirmation, recovery and real delivery verification are PR4. This PR can prove
registration persistence and actual port invocation, not real production delivery.
Unverified users cannot log in. Existing addresses receive uniform202; no password
change or account privilege change. Concurrent registration must create at most one
user/action/delivery; losing transaction returns same public response.

Persistent fixed-window rate counters committed separately before hashing/DB/mail;
HMAC key protects stored subjects. Always use request peer; ignore arbitrary XFF,
X-Real-IP. Peer behind current nginx is aggregate, not genuine end-user IP; trusted
proxy deployment contract remains external. Avoid account-only login lockouts.

Login verifies real/dummy Argon2id outside user lock, re-reads hash/status under lock
before issuing a fresh context; prevent password-change races. Rehash only verified
passwords with the current production profile. New independent access/session/CSRF;
never upgrade, delete or assign guest ownership. Response whitelist only stable
account ID/email/verified, access and absolute expiry. All protected reads validate
user, deadlines and revocation on server. Sensitive validation input never echoed.

Native PostgreSQL verification is mandatory; tests own random schemas in a disposable
admitflow_test* DB. Existing guest and applied migrations unchanged. Add tests to
existing CI collection, not a workflow rewrite. Review/merge remains owner action.

## Persistent budgets implemented (T281)

AccountRateBucket upsert increments atomically under each operation/subject/window
key, caps denied counters, commits independently of the user transaction, and returns
Retry-After from the server window. Multiple budgets ordered consistently. Soft
email-only delivery budget suppresses mail uniformly without a new account oracle.
Subjects stored only as HMAC digests. AUTH_ENABLED defaultsfalse and enabling requires
32..1024-byte stable AUTH_RATE_KEY; Settings repr omits that key. Existing production
HTTPS/PostgreSQL requirements unchanged. Native tests cover12 concurrent requests,
exact5 grants, new engine persistence, next window, soft-budget suppression,
no refund after later rollback and independent operation/subject scopes.

## Registration and CSRF (T282)

Implemented strict camelCase DTOs with SecretStr passwords; sanitized existing
validation responses. Synchronizer context stored separately; cookie HttpOnly/Lax,
/api/v1, Secure per config, no Domain. Same-origin/custom-header bootstrap and all
write protections retained; compare CSRF in constant time, reject absent/foreign/
expired contexts. Bootstrap does not create guests or promote their cookies.
Registration uses Argon2id on every valid request, including duplicates. Atomic
ON CONFLICT(email) DO NOTHING creates at most one user and one24h verification hash.
No email_verified_at/session/refresh assigned by registration. Commit before mail;
DB or transport failure never claims202 success. Missing transport503 before lookup.

Clarification to initial wording “one delivery”: racing duplicates may send a safe
existing-account notice, but only the winning insert gets a verification token.
The mail port is invoked for both cases to avoid an account-existence oracle on
provider failure. Email-only3/h soft budget caps all such deliveries uniformly;
existing password/action token is not changed. This supersedes only the stricter
initial delivery-count assumption, not the unique-user/action acceptance.
SMTP delivery and usable confirmation links remain PR4 and external verification.

Native registration tests: **20 passed**, exit0. Covers actual hash/action persistence,
duplicate response equality, two-transaction registration race, invalid/oversized/
non-string/escaped-surrogate input redaction, CSRF/Origin/cross-site/header failures,
mail unavailable/failure for both new/existing email and durable mail suppression.
Initial surrogate test failed in httpx encoding before reaching the API; corrected
by sending escaped JSON bytes, then the real server rejection passed.
Persistent-budget/config test command: **12 passed**, exit0.

## Login/session implemented (T283)

POST /login uses persistent peer30/15min + email/peer10/15min budgets BEFORE Argon2id.
Ignores X-Forwarded-For/X-Real-IP. Missing accounts verify a production dummy hash;
wrong password, absent, disabled and unverified users all return identical401.
Password hash/status rechecked under user lock AFTER expensive verification;
password-change race cannot create a session. Rehash happens only after successful
verification with the production profile. CSRF context locked/consumed after the
user lock; two concurrent logins using one browser context yield one session.
New access/session/context are committed before emitting cookies. No refresh is
minted. Session DTO whitelists account{id,email,emailVerified}, accessExpiresAt and
absoluteExpiresAt. Cookies HttpOnly/Secure in production, host-only/Lax,/api/v1.

GET /session and reusable current_account(db,request,now) join the user each time,
checking verification/status, revocation and access/idle/absolute deadlines. Unknown,
expired or revoked access returns terminal not_authenticated in PR2 (no refresh yet).
Session-bound CSRF cannot be borrowed by another account. Reload uses server state.
Bootstrap after expired access permits a new anonymous login context, never grants
account privileges. Repeated login is a fresh session; full logout/switch/revocation
policy and refresh are PR3, so production rollout remains disabled.

Native login/HTTP tests: **25 passed**, exit0. Includes actual hash/login/reload,
production cookie properties, all uniform credential denials, expiry/revocation/
deletion/status checks, cross-account CSRF, concurrent login, password-change race,
production-strength rehash, durable brute-force limits despite spoofed forwarding,
secret-free logs/responses, commit failure without cookies, disabled defaults and
preserved guest history/owner isolation. Verified users are explicitly seeded only
inside isolated test DBs; no application bypass for email confirmation exists.

## Implemented contracts (all /api/v1/auth)

| Endpoint | Request -> response | Access and errors |
|---|---|---|
| GET /csrf | none ->200 {csrfToken} | enabled, same-origin/custom header; peer120/15min;403/429/503 |
| POST /register | {email,password} ->202 {message} | enabled, valid CSRF+Origin/header, peer10/h, email delivery3/h;422/403/429/503 |
| POST /login | {email,password} ->200 session DTO, cookies | enabled, valid CSRF+Origin/header, peer30/15min+email-peer10/15min;401/403/422/429/503 |
| GET /session | none ->200 session DTO | enabled, access cookie, peer600/15min;401/429/503 |

Email ASCII identity rules and password15..128 codepoints/512-byte bound remain PR1.
Login bounds1..128, allowing future password-policy upgrades without truncation.
Errors: not_authenticated401, csrf_invalid403, invalid_input422, rate_limited429
with Retry-After, auth_unavailable503. Existing safe validation and Origin rejection
formats retained. No tokens in URLs or auth secrets in JSON; csrfToken is the
non-auth synchronizer value, intended only for JS memory. No frontend/storage code
changed. Missing real mail is explicitly503 even when AUTH_ENABLED=true.

## Regression, evidence and remaining review (T284)

Full local backend `TEST_DATABASE_URL=<isolated PG> backend/.venv/bin/python -m
pytest -q --require-postgres --ignore=backend/tests/test_admission_history.py
--ignore=backend/tests/test_accreditation_registry.py
--ignore=backend/tests/test_exam_requirements.py backend/tests`: **811 passed,
zero skipped**, exit0,223.67s. Nine further test cases were added after collection
(two failure cases + seven extra login CSRF/Origin cases); focused current rerun:
**16 passed**, exit0. Hosted CI must execute all820 cases on the final source.
Do not represent811 as a full run containing those nine added cases.

Existing frontend `npm run lint`, `npm run typecheck`, `npm run build`, `npm test`:
exit0, **147 passed** (all29 routes), unchanged JS/CSS asset hashes. No frontend,
CSS or visual baseline edits; no new pixel-comparator acceptance claimed. ETL:
**55 passed, one explicit missing-dataset skip**, exit0. `pip check` clean.
Repository tools17 tests, one local missing-PDF-dependency skip; hosted installs
those dependencies. Clean native PostgreSQL migration verifier: head0012 matches,
no new upgrade operations, exit0. No new or changed applied migration.

Tests used owned PostgreSQL17 container admitflow-kan214-pr2-db, loopback55439,
admitflow_test_kan214_pr2 and admitflow_test_kan214_pr2_migrations, random schemas
via pg_support. All schemas cleaned; owned container/anonymous volume removed.
User DBs/volumes, other containers, deployment/CI workflows and production secrets
untouched. Final SHA, PR URL, hosted run and exact job results are maintained in
PR description (avoids an evidence-only commit invalidating its own checked SHA).

T275 and T284 remain review until owner acceptance; implementation stepsT280-T283
done. Hosted results not inferred from local checks. No autonomous merge.
After review/merge: T276 PR3 refresh rotation/replay, logout and full revocation,
then PR4 real SMTP/confirmation/recovery, PR5 React and PR6 final acceptance.
KAN-214 is NOT done. AUTH_ENABLED defaultsfalse; real provider absent means503.
Peer counters behind current proxy are aggregate, not real per-client IP. Production
HTTPS/proxy/SMTP-egress and actual delivery remain explicit external release gates.
