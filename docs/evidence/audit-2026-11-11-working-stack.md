# Working stack audit, 2026-11-11

Real app on PostgreSQL (migrations, national catalog, reviewed programmes, SGU archive published) behind the production frontend build.

## What was checked

- Browser crawl of 90 routes found by following every internal link from 27 seed routes at 1440 px: page errors, console errors, HTTP statuses, not-found pages, horizontal overflow.
- 3080 API requests in-process: every route of the OpenAPI schema with 14 odd values in path and query and 8 malformed bodies, as an anonymous visitor and as a guest.
- Full suites: backend 765 passed on PostgreSQL, frontend 94 browser tests, lint, typecheck, build.

## Found and fixed

| Problem | Fix |
| --- | --- |
| Register-only organisations whose short name in the accreditation register is «-» were shown with the name «-» in the catalog and on their page (2 records). | The full legal name is used when the short name is not a real name. Test over the whole catalog. |
| A first-time visitor of «Мои направления», «История» and «Уведомления» read «Гостевой доступ завершён», although no session ever existed. | The message covers both cases: not started or ended. |
| Script tests (roadmap, weekly report PDF) and the roadmap check were not run in CI. | Added to the backend job. |

## Checked, no defect

- No 5xx and no unhandled exception on any of the 3080 requests.
- No not-found page reachable by links, no horizontal overflow, no page errors. The only console messages are the expected 401 of guest-only data before a session starts.

## Not fixed, needs a product decision

- The landing buttons «Войти» and «Оценить шансы» lead to pages that honestly say «Функция пока не подключена» (accounts and forecast are not built). The main call to action therefore ends in a stub; the working flow is «Конкурсные списки → найти себя → сохранить».
- Docker Compose, nginx and the production profile were not started in this environment (no Docker); CI and the 2026-11-10 smoke by the team cover them.
