# Right-side auth UI polish

Baseline: main8f29692 (PR23 merged). TaskT309.

Acceptance: preserve the hero DOM/CSS/responsive behavior and all non-auth pages; reuse shared primitives; responsive right column420-460px; consistent8/12/16/24/32 spacing; truthful success headings and primary login CTA after real backend acknowledgement only; preserve API/request/token/security behavior. Validate initial/pending/error/dispatch/cooldown/invalid/expired/success states at320/375/390/768/1024/1440/1920, keyboard focus/wrapping/reduced motion; run typecheck/lint/build/npm test and publish before/after evidence in a separate PR.

The referenced screenshot was not attached in the provided conversation. Work follows the written design requirements; no claim of matching an unseen reference. UI recording/mocked API fixtures are layout evidence only, never real SMTP/inbox delivery proof.

## Implementation

- Shared src/shared/AuthLayout.tsx reuses PageTitle/Surface/RouteLink. Live AccountPages and DemoAuthPage share presentation only; demo retains its existing explicit no-auth behavior.
- Only right-panel selectors (.af-auth-panel) style the448px responsive column, card, spacing, typography, controls, notices, footer and focus. Existing design tokens reused; no new dependency. No fixed panel height/clipping.
- Existing complete state drives reset/verify heading, check mark and full-width blue login link after backend204 only. The form already disappears when its token is cleared; that lifecycle is unchanged. Supporting status copy now explains the next step instead of repeating the title. Existing success assertions match the new explanatory copy; new UI tests assert heading/status/no-form/login CTA and reject success-shaped202.
- Form aria-busy derives from existing busy state. role=alert/status, animation IDs and reduced motion retained. No changes to request state hook, API/DTO/account helpers, routes, SMTP, token handling, password rules, CSRF, cookies, refresh/logout/rate limits or backend code.

## Verification (2026-11-15)

| Check | Result |
| --- | --- |
| npm run typecheck | exit0 |
| npm run lint | exit0 |
| npm run build | exit0, production Vite build |
| npm test | exit0,359 passed (1.2min), existing201 retained +158 UI cases |
| Responsive browser matrix |22 states x7 widths =154 screenshots/containment checks;320/375/390/768/1024/1440/1920 |
| Additional UI checks |keyboard focus +long email at320/1440, invalid202 completion proof for reset/verify |
| Native PG18/browser subset |3 scenarios each:Chromium7.1s,Firefox10.4s,WebKit10.0s;9 passed |
| Source preservation |hero JSX/hero CSS rules and useSubmission hook compared verbatim to main; all unchanged |
| Other-page visual guard |/app?mode=demo and /faq?mode=demo screenshots identical before/after |
| Git/roadmap |diff --check and roadmap --render --check pass |

All154 UI views have screenshots in frontend/test-results (CI uploads that directory). Dedicated ignored baseline/review captures contain70 before +70 after auth images,35 hero crops per version and2 other-page captures. Manually inspected all five auth routes, success/error/loading/validation/accepted/cooldown/invalid states across the required sizes (representative images at every width; automated containment for the full matrix). A temporary owned preview/capture harness and native test runner live only under ignored .qa-tools. Native checks use the existing runtime/real endpoints/random PostgreSQL test schemas with a recording mailbox, never external SMTP proof. Only the owned PG cluster was started/stopped; no existing user databases or Docker volumes changed.

## Before / after

Baseline is main8f29692; same Chromium/900px viewport height, fonts, locale and controlled UI API fixtures in each pair. Committed PNGs total about280KB.

| View | Before | After |
| --- | --- | --- |
| Login1440 | [Before](evidence/auth-ui-polish/login-1440-before.png) | [After](evidence/auth-ui-polish/login-1440-after.png) |
| Register320 | [Before](evidence/auth-ui-polish/register-320-before.png) | [After](evidence/auth-ui-polish/register-320-after.png) |
| Reset success1440 | [Before](evidence/auth-ui-polish/reset-success-1440-before.png) | [After](evidence/auth-ui-polish/reset-success-1440-after.png) |
| Verify success390 | [Before](evidence/auth-ui-polish/verify-success-390-before.png) | [After](evidence/auth-ui-polish/verify-success-390-after.png) |

## Known limits

- No reference screenshot was attached; cannot claim matching it. Written design requirements were used.
- Hero markup, colors, typography, decoration, grid and breakpoints are untouched.28/35 initial hero crop PNGs are byte-identical. Seven short mobile recovery/verify crops differ in height because the **unchanged** min-height:100vh grid distributes free space differently when right content height changes. That existing adaptive behavior was kept rather than adding fixed-height hacks or editing the hero. Login/register/reset initial hero crops match at all7 widths. No all-state pixel-identity claim is made.
- This is UI/source/automated native auth validation, not real SMTP or production HTTPS/inbox delivery. External gates remain open.
- Only3 native scenarios per engine ran locally; the full native suite and broader Linux CI are separate checks whose current outcomes are maintained in the PR description/checks. No tests were skipped/weakened to make the UI pass.
