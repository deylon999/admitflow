# KAN-214 PR4: SMTP, email verification and password recovery

2026-11-13 S213. Owner requested continuation; GitHub confirms PR16 merged.
Base d63a2087ed81a1bf435088d0927cf2176bc371eb, branch feat/kan-214-email-recovery.
Baseline PR16 source873f884/run43452948773 all4 jobs success: backend867/0skip,
frontend147,ETL55+1 dataset skip,migrations0012/head/check. Not PR4 evidence.

## Acceptance before implementation

Reuse the existing User/ActionToken/Session/Refresh/CSRF/Budget schema. No guest
ownership or frontend/design/CI/infrastructure changes. AUTH_ENABLED staysfalse.
Real SMTP credentials/from/domain and production egress/HTTPS remain external;
SMTP-field presence audit reveals no supplied provider. Never expose values.

Production adapter uses Python stdlib smtplib, authenticated STARTTLS or implicit
TLS, default certificate/hostname validation, finite socket timeout, at most two
concurrent sends/worker and one attempt/request (no automatic send retry). Link
origin is explicit HTTPS PUBLIC_ORIGIN, never request Host/callback; link secrets
use fragments /auth/verify#token=... and /auth/reset#token=..., not URL query/path.
No provider -> global503 BEFORE account lookup; no fake success. Provider rejection/
error -> generic503. SMTP acceptance is not proof of delivery to a real inbox.
Token/password/SMTP credentials must not appear in logs/errors. Tests inject a
recording port only inside isolated tests; no runtime mock transport switch.

Extend the registration port for verification/recovery. Accepted requests invoke
that same delivery path for existing/missing/disabled/already-verified/ineligible
addresses; tokenNone sends a safe generic notice, so provider errors do not expose
account existence. Soft shared email3/h and peer20/h budgets bound all email sends,
including registration; per-operation budgets and token-attempt budgets are durable
PostgreSQL/HMAC and committed before expensive operations. Soft suppression returns
only generic request acceptance, never claims an account was created or mail sent.

POST /auth/verification/request {email} ->202 generic; only active/unverified users
get a24h verification action. POST /verification/confirm {token} ->204, no auto-login.
Token domain/purpose separate; only hash persists. User row lock serializes resend
and confirm; new issuance invalidates older same-purpose actions. Only latest issued
link is valid; delivery order is not guaranteed by SMTP. SMTP failure after commit
leaves safe retry/resend, never restores an older token or confirmation status.

POST /auth/recovery/request {email} ->202 generic; only active/verified users get a
30min reset action. POST /recovery/confirm {token,password} ->204 after production
Argon2id validation/hash, one-use consumption and atomic revocation of ALL target
user sessions/refresh and outstanding action tokens. Never auto-login/verify email,
change another account/guest history or send the new password. Invalid/expired/used/
wrong-purpose/missing-user token ->same400. Invalid input422 is safely redacted.

All auth writes retain Origin/custom header and session/anonymous CSRF proof.
Consistent user->sessions->action lock order for reset vs refresh/logout/login.
Validate CSRF without mutating a foreign account's context during reset; revocation
is enforced by Session.revoked_at, not cookie deletion. Old CSRF cannot authorize
revoked sessions. Token/DB failure rolls back consumption/hash/revocation; no false204.
Native PostgreSQL race/security tests and full regression required. Frontend link
consumption, fragment clearing and UI forms remain PR5; no delivery/production gate
accepted by this PR's tests.

Sources checked2026-11-13:
[Python3.12 smtplib](https://docs.python.org/3.12/library/smtplib.html),
[OWASP recovery](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html).

## SMTP adapter (T291)

stdlib SMTP adapter selected from Settings when all SMTP fields are configured;
otherwise the unavailable port remains explicit. Both STARTTLS and implicit SSL
use create_default_context with CERT_REQUIRED/check_hostname. Authentication occurs
only after TLS; missing STARTTLS/refused recipients/provider errors fail closed.
One attempt/request, socket timeout1..10s (default5s per socket operation), two sends
per worker; no promise of a total5s transaction deadline. QUIT failure after DATA
acceptance does not trigger retry or falsely report send rejection. SMTP acceptance
is distinct from verified inbox delivery. Username/password/from are hidden in repr;
no debug logging or insecure TLS switch. Even development real SMTP requires fixed
HTTPS PUBLIC_ORIGIN; test recording ports remain isolated code injection only.

`pytest -q test_account_mail.py test_config.py test_config_strict.py`:
**33 passed**, exit0. Fake protocol clients inspect actual MIME/envelope, TLS context,
auth/send ordering, fragment-only links, generic notices, capacity, no retries,
connection/auth/send/refusal/QUIT errors and fail-closed configuration. This is NOT
a real provider/inbox delivery test. No dependency or infrastructure service added.

## Verification/resend implementation (T292)

Verification request/confirm APIs reuse existing CSRF/Origin guards and safe DTOs.
Shared mail-peer20/h and mail-email3/h now cover registration and both email action
requests, alongside existing operation budgets. Per-purpose hashed-token budget10
attempts/15min and confirmation peer30/15min commit independently. Missing provider
is503 before target lookup; every accepted eligible/ineligible address invokes the
same port, with tokenNone generic notices where no action is authorized.
Issuance locks/rechecks user ID AND normalized email (safe if a future email change
races the initial lookup), invalidates older same-purpose actions, persists a24h
purpose hash and commits before delivery. No raw action token outbox exists.
Confirmation consumes under the user/action lock and never creates an auth session.
Future email-change code must invalidate outstanding actions and sessions under
that same user lock; this PR does not implement profile/email changes.

Native test_account_email_verification.py + existing registration regression:
**43 passed**, exit0. Real register→confirm→login proves no auto-verification bypass;
tests cover resend invalidation/password preservation, unknown/verified/disabled
requests, forged/expired/used/wrong-purpose/deleted-user/disabled tokens, simultaneous
confirm/resend, missing/failing provider and confirmation during provider outage.
Mock/protocol acceptance is not real SMTP inbox delivery.

## Recovery and transactional revocation (T293)

Recovery request issues only for active/verified users and otherwise delivers a
safe generic notice through the same port. Confirm validates a purpose-separated
30min action, hashes the new server-validated password without holding the DB user
lock, then locks user -> ordered user sessions -> action, revalidates CSRF and
commits password/timestamps, every target session revocation, unspent refresh
consumption and all outstanding action-token retirement in one transaction.
No automatic login/verification or auth cookie issuance. Another logged-in account
and guest history remain untouched. CSRF rows are not bulk-mutated by reset:
foreign-context locking could deadlock cross-account resets, and revocation already
denies old access/refresh. Fresh CSRF bootstrap handles subsequent writes safely.

Native recovery suite: **18 passed**, exit0; current verification/recovery/security
suite: **83 passed**, exit0. Includes real register-confirm-login-reset-new-login,
all target device sessions revoked, other-account/guest preservation, eligible/
ineligible requests, invalid/expired/used/cross-purpose/deleted/disabled/unverified
tokens, resend/weak-password behavior, simultaneous reset and both deterministic
reset/refresh serializations, failed commit rollback and provider failure/outage.
An API-to-configured-SMTP test exercises MIME link consumption with a fake protocol
client; no runtime mock transport or production inbox delivery is claimed.

SMTP polish uses the explicit normalized sender domain for Message-ID (no local
hostname disclosure) and quoted-printable UTF8 text with ASCII wire representation
(no 8BITMIME dependency). Current mail/config suite **35 passed**, including explicit
connection and certificate failure cases; all TLS defaults remain strict.

## Final regression, API and external delivery gate (T294)

All new tests were present before full collection. Local command:
`TEST_DATABASE_URL=<isolated PG> backend/.venv/bin/python -m pytest -q
--require-postgres --ignore=backend/tests/test_admission_history.py
--ignore=backend/tests/test_accreditation_registry.py
--ignore=backend/tests/test_exam_requirements.py backend/tests`:
**976 passed, zero skipped**, exit0,299.11s. Current dedicated email/action/security
suite83 passed; mail/config35 passed. Framework/legacy migration warnings retained.
Frontend lint/typecheck/build/npm test exit0, **147 passed**, all29 routes. Frontend/
CSS/baseline untouched, generated assets unchanged; no new pixel comparison claim.
ETL55 passed +1 explicit missing-dataset skip. pip check clean. Repository tools17,
1 local missing-PDF-dependency skip; hosted installs those reporting dependencies.
Fresh real PostgreSQL verifier: head0012/schema alignment pass, no new migration.

Native tests owned PostgreSQL17 on loopback55439, only admitflow_test_kan214_pr4 and
admitflow_test_kan214_pr4_migrations and random pg_support schemas. Schema count0
before cleanup; owned container/anonymous volume removed. No user DB/volume,
production secret, applied migration, frontend, parser, CI or compose/network edit.
Final source SHA, PR URL, workflow URL and actually verified hosted job results are
recorded in the review PR description for branch feat/kan-214-email-recovery;
hosted checks are never inferred from local results. T277/T294 remain review until
owner acceptance, T290-T293 done. No autonomous merge or PR5 implementation here.

| Endpoint (/api/v1/auth) | Request -> success | Auth/CSRF/rate/errors |
|---|---|---|
| POST /verification/request |{email} ->202 generic acceptance |enabled, Origin/custom header+CSRF; operation peer20/h + shared mail-peer20/h/mail-email3/h;403/422/429/503 |
| POST /verification/confirm |{token} ->204 empty |enabled+CSRF/Origin/header; peer30/15min, token10/15min;400 invalid/expired/used/purpose/user,403/422/429/503 |
| POST /recovery/request |{email} ->202 same generic acceptance |same mail controls; only active/verified users get a reset action;403/422/429/503 |
| POST /recovery/confirm |{token,password} ->204 empty |enabled+CSRF/Origin/header; peer30/15min/token10/15min; production password policy;400/403/422/429/503; no auto-login/cookie issuance |

Token secret shape is bounded43 characters; invalid shape422 is redacted; valid
shape with invalid proof uses the same invalid_token400 message across states.
Authentication is not required for email actions; CSRF proof must match the current
anonymous or account context. Request operations never disclose account ID/status.
Quota suppression returns request acceptance only, not a claim that mail was sent.
Already-delivered valid actions can confirm while transport is unavailable.

## Configuration and real delivery acceptance procedure

- Required actual SMTP fields: SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM.
  SMTP_SECURITY=starttls (SMTP_PORT default587) or ssl (environment default465).
  SMTP_TIMEOUT_SECONDS1..10, default5 per socket operation, not a total SMTP deadline.
- Fixed HTTPS PUBLIC_ORIGIN and matching ALLOWED_HOSTS required for real SMTP,
  including development transport. Invalid/partial configuration fails closed.
  Do not commit secrets or enable SMTP debug logs. No runtime recording/console mode.
- Current compose does not forward SMTP fields and backend production network is
  internal-only. Deployment/egress/secret forwarding requires CI/CD-owner agreement;
  this PR deliberately changes none of that. Forward credentials only to backend.
- AUTH_ENABLED remainsfalse until complete lifecycle/UI acceptance. PR5 must add
  /auth/verify and /auth/reset UI, clear fragments immediately with replaceState and
  use explicit POST confirmation (no auto-consumption by GET/mail scanners).
- For actual delivery evidence, owner supplies provider/verified sender, agreed
  isolated test recipient and HTTPS staging after UI exists. Verify real inbox mail,
  fixed-origin link, verification/login and recovery/new-password flow; old sessions
  must fail. Record non-secret timestamp/status and owner acceptance, never raw token,
  password, SMTP credentials or a screenshot exposing the recovery link in Git.

**External gate: NOT ACCEPTED.** Runtime/project env audit supplied no SMTP fields;
no external recipient was contacted and no real inbox delivery verified. Fake
protocol-client and recording-port tests prove code integration only. Full KAN-214
requires real delivery or a separate explicit owner exception documented with this
limitation. Next after review/merge: T278 PR5 React forms/session/fragment integration,
then PR6 full browser/security/visual acceptance. No full auth production-readiness
claim; existing HTTPS/proxy/client-address gates remain open.
