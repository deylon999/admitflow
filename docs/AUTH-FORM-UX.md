# Auth form feedback ? 2026-11-14

Acceptance for this small PR: hide anonymous resend unless delivery is proven safely; never treat 202 as delivery; style auth-form errors locally; restart identical error notifications; preserve alert semantics, reduced motion and React v3 layout; run lint/typecheck/frontend tests and inspect 390/1440 screenshots. If the contract cannot prove delivery safely, document the limitation instead of inventing success.

## Changes

- Removed the unconditional resend control on Live login/register. No sent flag, fake mail or account-dependent visibility was introduced. The existing neutral acceptance message remains unchanged.
- Error notices use a local red foreground, pale red background and soft border. Invalid email/reset links share the same style; successful/accepted notices retain the existing lime style. CSS additions are scoped to `.af-auth-layout .af-auth-notice--error`; existing global rules and other pages are unchanged.
- Each submitted/validation error gets a monotonically increasing ID used as the React key. Identical errors remount; ordinary field edits preserve the node. Opacity/translateY animation lasts 225 ms and is disabled for reduced motion. New validation errors also remove stale success notices.

## API limitation and minimal safe solution

`backend/app/account_api.py` register/request_action return the same 202 when a soft email budget suppresses mail. Registration duplicates receive an existing-account notice instead of a new verification token. `frontend/src/shared/authDto.ts:accepted` only validates a message and returns null. Login neither sends mail nor proves mail dispatch. Existing backend evidence: `test_email_mail_budget_is_uniform_and_persistent` and `test_email_budget_is_shared_by_register_verify_and_recovery` explicitly assert suppressed mail still returns 202.

Therefore this frontend cannot safely implement delivery-gated resend. Checks for showing/centering the button after confirmed delivery and resend busy/success/failure are **not implemented or claimed as passing**. Hiding it for every anonymous address is the smallest safe current behavior. Registration acceptance is not renamed to ?mail sent?.

For a future backend change, expose delivery acknowledgement/resend only in an ownership-proven, narrowly scoped verification flow (e.g. a short-lived capability from an inbox link), bound to the address and purpose. Keep arbitrary-email endpoints indistinguishable, including duplicates and soft-budget suppression; do not add a public `sent`/`exists` flag. Only a successful real provider handoff may acknowledge dispatch (not inbox delivery). Suppression/errors must not acknowledge it. Center the resulting control within the form, use the existing pending ref/disabled pattern, and test retries, address changes and expiry. This requires a separately reviewed backend/security contract; it is not part of this frontend PR.

## Validation

From `frontend/`: `npm run lint` exit 0; `npm run typecheck` exit 0; `npm test` exit 0, **186 passed**, Chromium, 37.9 seconds, including 11 new cases. The runner also performs `tsc -b` and a production Vite build. Tests cover initial hidden resend; anonymous 202/503/403/network outcomes on login/register; no false success; acceptance followed by failure; two identical backend errors with two animationstart events; repeated client validation errors; stable DOM on edits; distinct computed colors; reduced motion; overflow at 390/1440. Existing tests cover pending duplicate prevention, CSRF transport, refresh, logout and cross-tab state.

Screenshots of error and acceptance at both widths are attached to Playwright JSON (`frontend/test-results/results.json`). Extracted local copies: `frontend/test-results/auth-{error,accepted}-{390,1440}.png`; visually inspected all four. Test outputs are ignored generated artifacts.

The first test launch stopped before tests because the local Python runtime lacked uvicorn. Installed `backend/requirements.txt` into ignored `backend/.venv` and reran successfully; frontend dependencies installed with `npm ci` (lockfile unchanged).

No backend, API error code/text, CSRF, cookie, refresh, logout or rate-limit code changed. This is a scoped source/contract review plus frontend regression, not a fresh native-PostgreSQL security audit or proof of real SMTP/inbox delivery.
