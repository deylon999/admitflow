# KAN-214: real mail deployment

This PR wires the existing TLS-only adapter into an opt-in HTTPS deployment. It does not assert that live SMTP or inbox acceptance has happened. No provider credentials or domain were supplied in this session. Docker is unavailable locally; native PostgreSQL is used separately for automated auth tests.

## Owner inputs (required)

- HTTPS staging DOMAIN with DNS pointed to the host; ACME_EMAIL, access to that host and its private environment.
- SMTP host/port, STARTTLS (587) or implicit TLS (465); SMTP username/password stored on the host, never in Git or chat.
- SMTP_FROM verified by the chosen provider, including required DNS SPF/DKIM and DMARC policy; sandbox providers must also authorize the recipient.
- A controlled AUTH_TEST_EMAIL inbox and someone able to read messages and open links. SMTP DATA acceptance alone cannot prove delivery.
- Stable independent AUTH_RATE_KEY, existing PostgreSQL/SOURCE_IDENTITY_KEY secrets; outbound DNS and TCP to the provider allowed by hosting firewall/provider.

## Run on the existing staging host

Use the existing project name and private env file; **do not change POSTGRES_PASSWORD/SOURCE_IDENTITY_KEY or recreate/delete volumes**. Back up according to RUNBOOK. Never print `docker compose config` (it expands secrets); use `config --quiet`.

```sh
docker compose --env-file .env -f compose.prod.yaml -f compose.auth.yaml config --quiet
# Perform normal migrations if needed; this PR has no database migration.
docker compose --env-file .env -f compose.prod.yaml -f compose.auth.yaml up -d --no-deps backend
# Configuration-only validation (no outbound request)
docker compose --env-file .env -f compose.prod.yaml -f compose.auth.yaml exec backend python -m app.smtp_check
# Explicit single real notice; AUTH_TEST_EMAIL is injected only for this command.
docker compose --env-file .env -f compose.prod.yaml -f compose.auth.yaml exec -e AUTH_TEST_EMAIL backend python -m app.smtp_check --send
```

Export AUTH_TEST_EMAIL in the shell for `exec -e` (Compose .env is interpolation input, not automatically the exec environment). Rebuild backend with `build backend` before `up` when deploying changed source. Overlay attaches only backend to existing egress and supplies only backend the SMTP secrets. No ports or data-volume definitions change. Do not run `down -v`. Existing HTTPS Caddy/public-origin/secure-cookie configuration is retained. Review trusted-proxy policy separately; do not trust arbitrary forwarded IP headers.

Run the smoke from the backend container so it actually exercises its DNS/egress, TLS certificate verification, login and real provider DATA submission. Timeout is bounded, STARTTLS cannot downgrade. A success means provider acceptance, not inbox arrival. Confirm the actual generic notice in the controlled inbox and spam folder before recording delivery evidence.

## Required real lifecycle evidence (pending owner inputs)

Use the HTTPS UI and a fresh controlled mailbox/alias. Register, confirm an actual `/auth/verify#token=...` link, verify login is denied before confirmation and works after it. Request another verification message before confirmation and check receipt/new link, expiry and old-link rejection. Recover with a real `/auth/reset#token=...` message, change password, confirm new password works, old password fails and old sessions are revoked. In staging, exercise a provider-rejected credential/failure and check there is no sent notice. Exercise cooldown/limits without spamming mailboxes. Record date, environment, provider acceptance + observed receipt for each step; **never** save link tokens, credentials, inbox content or raw provider logs to Git. Automated recording/mock mailer tests prove logic only, never real delivery.

External proof remains pending until these steps are performed. No test user is created by the smoke command and no artificial token/success is generated.

## Local checks

2026-11-14: mail adapter + smoke-command unit tests:29 passed (exit0). Compose overlay `config --quiet` passed (exit0) using synthetic configuration-only variables; this does not test egress or delivery. Docker daemon unavailable, SMTP/HTTPS/inbox data absent; no real send attempted.
