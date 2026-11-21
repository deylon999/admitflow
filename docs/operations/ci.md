# Проверки и диагностика CI

Действующий [workflow Checks](../../.github/workflows/ci.yml) запускается на
push и pull request. Ubuntu 24.04, Python 3.12, Node.js 24 и PostgreSQL 17 заданы
в workflow. Результат привязывается к SHA проверенного коммита.

| Job | Что проверяет | Артефакт |
| --- | --- | --- |
| frontend | npm ci, lint, typecheck, build, тест остановки runner, Chromium и Playwright с временным FastAPI | `frontend-tests` |
| backend | pytest с обязательными PostgreSQL-сценариями, учётные записи в Chromium, Firefox и WebKit, проверка контролей и утилит | `backend-tests` |
| migrations | Upgrade пустой PostgreSQL, совпадение ревизий и `alembic check` | `migration-tests` |
| etl | История приёма, реестр аккредитации и требования ЕГЭ. Отсутствие полной выгрузки MICCEDU отражается явным skip | `etl-tests` |

Установка в Actions — штатный `npx playwright install --with-deps chromium`
для frontend и `npx playwright install --with-deps chromium firefox webkit`
для набора авторизации. Изолированный runner сам управляет API и preview.
Старые команды `install_playwright_ci.sh` и `E2E_API` относятся к
[архиву](../archive/runbook-before-documentation-cleanup.md).

Локально из `frontend/` после установки Node- и Python-зависимостей:

```bash
npm ci
npm run lint
npm run typecheck
npm run build
npx playwright install chromium
npm test
```

Из корня, в окружении с зависимостями backend и работающим Docker:

```bash
python scripts/test_postgres.py
python scripts/test_postgres.py tests/test_product_catalog.py tests/test_program_publication_api.py
python scripts/roadmap.py --check
python scripts/check_doc_links.py
python -m pytest -q scripts/tests/test_roadmap.py scripts/tests/test_check_doc_links.py
```

`test_postgres.py` создаёт временный контейнер и запускает выбранные тесты с
`--require-postgres`. Полный backend workflow рассчитан на Linux: тесты worker
используют POSIX `resource`. Временная SQLite подходит для локального frontend
runner, а подтверждение PostgreSQL берётся из соответствующих тестов.

При сбое откройте job и упавший шаг, затем скачайте артефакт прогона: там
JUnit, логи, тестовые отчёты и, для браузерного сбоя, trace или screenshot.
Результаты фиксируются с SHA, причиной и областью проверки. Зелёный CI
не подтверждает внешнюю доставку SMTP, HTTPS staging или полноту каталога.
