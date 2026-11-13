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
