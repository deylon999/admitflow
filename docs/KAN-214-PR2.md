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
