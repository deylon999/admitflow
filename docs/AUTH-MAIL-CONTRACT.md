# KAN-214: account mail dispatch contract

POST `/api/v1/auth/register`, `/verification/request`, `/recovery/request` retain their 202 and existing message. Additional fields:

- `dispatch: "accepted"`, `retryAfterSeconds: 60`: a real account message was accepted by the configured transport. With the production SmtpAccountMailer, TLS/auth/DATA completed without refusal. This is not proof of inbox receipt or that a verification/reset token was applicable.
- `dispatch: "suppressed"`, `retryAfterSeconds: 3600`: no mail attempted because of a soft hourly delivery budget. Keep neutral acceptance text; do not show a sent notice or use it as initial resend proof. Conservative retry time, not a reservation/guarantee.
- Provider/availability failures stay 503 `auth_unavailable`, with no dispatch claim; CSRF/validation/rate limits keep their codes. Verification resend has a rolling60-second email cooldown, persisted atomically in HMAC-keyed AccountRateBucket. Denials are429 with bounded Retry-After and do not mint/invalidate tokens. Existing peer/email shared hourly limits are preserved.

## Why this does not enumerate accounts

A public boolean for *verification-token issuance* would leak eligibility and is prohibited. This contract acknowledges only the real SMTP submission of an account notice. The existing transport already submits a real generic notice for **every** ineligible/missing/verified/disabled address and registration duplicate. It does not skip SMTP when a token is None. All account states follow the same public acceptance/failure path; cooldown and mail budgets depend on the supplied address/peer, never existence. Neither token kind nor user/eligibility is exposed. Mailbox owners may read their own notice; arbitrary callers cannot inspect its type through the API.

This resolves PR20's limitation by explicitly changing the backend contract, rather than treating an arbitrary 202 as delivery. Do not replace generic submissions with no-ops: that would break this invariant. Frontend must support old message-only 202 conservatively (no proof), show resend only in the submitted registration stage with explicit accepted dispatch, bind it to that address, and clear it on address changes/route exit. After an accepted submission with no inbox arrival, resend becomes available after the cooldown. Recovery uses the same truthful dispatch distinction but no verification resend.

## Token and data safety

No migration or existing user/data edits. Tokens remain hashed, purpose-bound, single-use and expiring (verify24h/reset30m); existing per-user locks serialize confirmation/reset. Resend replaces old verification links only after allowance, and reset still revokes old sessions/passwords. SMTP failure after token creation does not claim success; a later allowed resend generates a new link. Existing error text/codes, CSRF, cookies, refresh and logout are unchanged. SMTP acceptance can still precede bounce/spam filtering; only observed controlled inbox receipt can close the live delivery gate.

## Automated evidence

Native PostgreSQL in a new isolated local test cluster (not any existing user DB/volume). Added11 tests for explicit acceptance/suppression, four account states across verification/recovery, provider failure, rolling boundary and persistent cooldown, and valid-link preservation on denial. Existing concurrency test now expects one accepted resend and one429. Updated exact DTO assertions and shared-budget test to distinguish suppression from cooldown. Recording mailer and adapter unit tests are **not real-delivery evidence**. Full regression results recorded after completion.

Final native auth regression:274 passed (147.52s, exit0), all test_account_*.py plus test_smtp_check.py with --require-postgres; no skips. JUnit/log in ignored .qa-tools/auth-backend.{xml,txt}. Full backend collection was also attempted, but13 unrelated worker suites fail on Windows because resource (Linux module) is unavailable; no production workaround was introduced. The first targeted run needed6 exact-response expectations updated for the additive contract; the complete corrected auth regression passed.
