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
