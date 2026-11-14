# KAN-214: receipt-driven resend UX

Stack: SMTP deployment PR21 -> backend dispatch/cooldown PR22 -> this frontend PR. PR20 was not merged at this branch point; its local red/error animation changes are included here. Review PR20 together with this stack to avoid merging overlapping implementations blindly.

## Acceptance and behavior

- Only an explicit validated `dispatch: accepted` opens the in-memory submitted registration stage for that email. Message-only old202, suppressed mail, malformed receipts, unexpected status200, HTTP/SMTP/network errors never open it. Login never derives mail eligibility from a401 or an arbitrary email.
- The centered resend control has a visible countdown, is disabled during cooldown/pending and retains the synchronous pending guard against duplicate requests. Backend enforces rolling cooldown/hourly budgets independently of browser state.
- An accepted submission whose mail never reaches the inbox can be retried after60s. Temporary resend errors preserve the known submitted stage and allow retry after the cooldown; suppression/legacy/error responses do not show a new successful dispatch. Changes to email, navigation and reload drop the stage. No receipts/addresses/passwords/tokens are persisted by the form.
- SMTP503 at registration can occur after account creation committed. The existing registration form remains retryable; a new allowed registration submission gives an account-neutral notice for an existing address, after which verification resend can issue a fresh link without changing its password. Backend hourly budgets remain authoritative.
- Copy distinguishes provider acceptance from inbox delivery. Suppressed/legacy requests have neutral notices; failures are red alerts. PR20's identical-error225ms animation/reduced motion behavior is preserved. CSS is local to auth layout; React v3 shared design/other pages are unchanged.
- Verification/recovery links remain `/auth/verify#token=...` and `/auth/reset#token=...`, explicit, one-time, expiring. Recovery still changes passwords and revokes old sessions. No production mock/fake send or success is introduced.

## Validation

2026-11-14: frontend lint/typecheck exit0; npm test exit0,201 passed,43.7s (runner also tsc -b + production Vite build). New cases cover explicit/suppressed/legacy/malformed receipts, unexpected200, 429/503/network errors, UI cooldown/pending, successful later retry, account/address-bound stage reset, red/neutral/success distinctions, animation and responsive centering. Screenshots attached in frontend/test-results/results.json; extracted auth-resend-390.png and auth-resend-1440.png visually inspected, no horizontal overflow.

Native PostgreSQL browser acceptance exercises actual endpoints/database and isolated recording mail transport; it is explicitly **not external SMTP delivery evidence**. An older native test initially looked for the unconditional login resend control; updated it to keep the submitted registration tab, deny unverified login in another tab and resend after cooldown, retaining token-purpose/expiry/login assertions. Final browser outcomes are appended below.

Backend auth/SMTP274 passed with --require-postgres (PR22). Full backend collection is blocked by Linux resource imports in13 unrelated Windows worker suites. No existing user database/volumes were touched. The dedicated test cluster and random test schemas own all mutations; stop only that owned cluster after tests.

## External work still required

No real SMTP provider/login/password/verified sender/HTTPS staging/inbox details are available in this session. The opt-in overlay and real-send command are prepared but not deployed or sent. Owner must supply the inputs in AUTH-SMTP-DEPLOYMENT.md via private environment, then execute its controlled-inbox checklist. Until actual register/resend/recovery messages are received, real delivery and the KAN-214 live-mail gate remain **unverified**, and PRs remain draft. SMTP DATA acknowledgement is insufficient to close that gate.

Final local native browser results: Chromium6/6 passed (12.6s after test update); Firefox6/6 passed (21.4s). Windows WebKit:4 passed,1 failed (existing cookie isolation assertion expects SameSite=Lax, browser context reports None),1 not run due serial failure. Cookie settings and assertion are NOT weakened. Backend cookie HTTP/security tests passed in the274-test run. Linux CI remains required for the full worker/WebKit evidence; no cross-platform full-pass claim is made. Reports live in ignored frontend/test-results/auth-{chromium,firefox,webkit}; combined first run and corrected Chromium log in ignored .qa-tools.

Three review tasks are recorded independently in the roadmap (T306/T307/T308); their PR stacking/merge order is documented here rather than marking prerequisite review tasks done to satisfy roadmap dependency rules. No release gate was accepted.
