# Итог организации backend AdmitFlow

## База и итоговая структура

Исторический baseline снят с `29c5902`. Рабочая база — `1e7693e` после merge PR #34 и cleanup #32, #33, #35. Старый auth-этап включён в main через `5ca1cca`. Четыре его реализации и aliases сохранены. [PR #34](https://github.com/deylon999/admitflow/pull/34), [master plan и инвентаризация](BACKEND_ORGANIZATION_MASTER_PLAN.md).

```text
backend/app/
├── main.py                 FastAPI, middleware, lifespan и порядок установки маршрутов
├── core/                   config, database, HTTP, Pydantic, UTC
├── auth/                   account API, ORM, security, SMTP, DTO, токены и лимиты
├── catalog/                университеты, программы, DTO, поиск, справочники и импорт
├── competitions/           публичные списки, ручной расчёт и условные сценарии
├── watchlist/              гостевые сессии, подписки, архив, история и идемпотентность
├── operations/             backup, restore, диагностика, миграции, мониторинг и worker
├── sources/                адаптеры, захват, хранение и публикация, журнал управления
├── admissions.py           связанная реляционная модель
├── catalog_search.py       ключи полнотекстовой нормализации для ORM callbacks
├── schemas.py              общая поверхность унаследованных DTO
└── data/                   версионированные справочники
```

`admissions.py` сохраняет регистрацию совместных FK и mapper callbacks. `catalog_search.py` позволяет этой модели загружаться без HTTP-каталога. `schemas.py` сохраняет совместный интерфейс DTO. Числа в расчётах, импорт, авторизация, SMTP и границы транзакций подтверждены существующими тестами. Варианты движков и новые paths покрыты отдельными проверками идентичности.

## Маршруты, модели и старые пути


- **FastAPI.** 53 маршрута с прежним порядком и методами и 45 путей OpenAPI. Хеши auth-on и auth-off OpenAPI совпадают с обеими базами. В графе зависимостей изменились квалифицированные Python-имена вынесенных обработчиков каталога, watchlist, readiness и owner/write_owner. Пути, имена маршрутов, методы, status, порядок и дерево `Depends` совпадают.
- **DTO.** 78 снимков моделей под 78 именами в режимах validation/serialization, плюс отдельный auth DTO snapshot. 15 контрольных HTTP-запросов каталогов, кампаний, гостевого доступа и cookie совпадают. Для cookie удаления проверяется реальный текущий срок. Сравнение заменяет только конкретный timestamp.
- **ORM и PostgreSQL.** 34 таблицы и 34 mapper identity в приложении и standalone Alembic. DDL, колонки, индексы, default и ORM mappings совпадают. Старые ссылки на классы разрешаются в ту же registry, в том числе для legacy pickle references. Schema-only дампы PostgreSQL 17.11 совпадают. Alembic head `0014`, все 14 revisions и их SHA-256 совпадают.
- **Python imports.** Legacy modules предоставляют тот же module object, поэтому строковые импорты и patches попадают в реальные globals. Проверены оба порядка импорта в новом процессе. `app.catalog` сохранил идентификатор после перехода в пакет. `app.operations` как пакет сохраняет три исторические функции идемпотентности из одного места реализации.
- **Пакеты.** History получил общий mapper кандидата без импорта роутера. Scenarios читают архив через read projection. Source controls и status зависят от ORM-модели очереди, а не от исполнителя jobs. Общая функция UTC реализует то же преобразование naive и aware значений. Два bounded-fetch транспорта сохраняют разные IPC limits и ошибки, необходимые разным источникам. Граф eager imports до и после ацикличен. В полном графе с deferred imports число простых циклов сократилось с 27 до 8. Остались отложенные callbacks публикации и подключение адаптеров. [Граф до и после](evidence/backend-organization-dependencies.json).

## Проверки

Linux Python 3.12.16, PostgreSQL 17.11, браузерный контейнер Playwright 1.64.1. Backend из `backend/` с отдельным `TEST_DATABASE_URL` на каждую стадию: `python -m pytest -q -ra --require-postgres --junitxml=<path>`. Frontend из `frontend/`: `npm ci`, `npm run lint`, `npm run typecheck`, `npm run build`, `node --test scripts/stop-child.test.mjs`, `npm test`, `npm run test:auth`. Общий пропуск во всех полных backend-прогонах — внешний MICCEDU-датасет. Выборки по подсистемам и хеши приведены в проверяемом JSON. [Результаты прогонов](evidence/backend-organization-validation.json).

| Этап | Backend passed / failed / skipped | Адресные проверки | Frontend · native auth |
| --- | --- | --- | --- |
| Baseline main | 1223 / 0 / 1 | — | 387 · 6 / 6 / 6 |
| Core | 1227 / 0 / 1 | 16 | 387 · 6 / 6 / 6 |
| Catalog | 1246 / 0 / 1 | 107 | 387 · 6 / 6 / 6 |
| Competitions | Идёт | 68 | 387 · 6 / 6 / 6 |
| Watchlist | Идёт | 88 | 387 · 6 / 6 / 6 |
| Operations | Идёт | 120 | 387 · 6 / 6 / 6 |

`backend/tests/snapshot_backend_contract.py` сохраняет routes, OpenAPI, зависимости и metadata. `backend/tests/snapshot_backend_organization.py` сохраняет весь DTO inventory и контрольные HTTP-запросы. Снимки выполняются в checked-out `backend/` через `PYTHONPATH=. python tests/<скрипт>.py <каталог>`. Первый скрипт использует `DATABASE_URL` postgres для offline Alembic DDL. Независимая проверка `MIGRATION_DATABASE_URL=<empty-test-URL> PYTHONPATH=. python tests/check_migrations.py` проверяет upgrade и drift. Дамп снимается `pg_dump --schema-only --no-owner --no-privileges --restrict-key=admitflowBackendOrganizationContract`.

Проверены legacy `python -m app.*` для backup, catalog_import, diagnostics, maintenance, national_catalog, national_coverage, observability, program_catalog_import, program_catalog_batch, smtp_check, university_name_report, worker и существующий `app.sources.cli`. Проверка cleanup выполнялась на временной БД. SMTP диагностика проверила fixture-конфигурацию. `python -m app.worker once` на пустой очереди вернул `idle`. FastAPI/Uvicorn отдал live 200, health 200 и OpenAPI 200. Compose с `--profile automation` поднял PostgreSQL, backend, frontend и worker, затем завершил тестовый проект. Тестовые данные расположены в tmpfs. Конфигурация production + auth overlay прошла `config --quiet` с фиктивными параметрами. `roadmap.py --render --check` и `check_doc_links.py` прошли.

## Pull Requests и порядок ревью

| Этап | PR | Ветка базы | Проверенный SHA ветки | GitHub Actions |
| --- | --- | --- | --- | --- |
| Core | [#38](https://github.com/deylon999/admitflow/pull/38) | `main` | `a579518de239` | Ожидается |
| Catalog | `refactor/backend-catalog` | `refactor/backend-core` | `c8d869ee7370` | До публикации |
| Competitions | `refactor/backend-competitions` | `refactor/backend-catalog` | `6840f96035f6` | До публикации |
| Watchlist | `refactor/backend-watchlist` | `refactor/backend-competitions` | `ee8d246198a6` | До публикации |
| Operations | `refactor/backend-operations` | `refactor/backend-watchlist` | `ee8d246198a6` | До публикации |

## Перемещённые модули

Пути относительно `backend/app/`. Исторический путь доступен как совместимый alias, CLI wrapper или пакет с прежним названием.

| Старый путь | Новый путь реализации | PR |
| --- | --- | --- |
| `account_api.py` | `auth/account_api.py` | [#34](https://github.com/deylon999/admitflow/pull/34) |
| `account_mail.py` | `auth/account_mail.py` | [#34](https://github.com/deylon999/admitflow/pull/34) |
| `account_security.py` | `auth/account_security.py` | [#34](https://github.com/deylon999/admitflow/pull/34) |
| `accounts.py` | `auth/accounts.py` | [#34](https://github.com/deylon999/admitflow/pull/34) |
| `config.py` | `core/config.py` | [#38](https://github.com/deylon999/admitflow/pull/38) |
| `http.py` | `core/http.py` | [#38](https://github.com/deylon999/admitflow/pull/38) |
| `schema_base.py` | `core/schema_base.py` | [#38](https://github.com/deylon999/admitflow/pull/38) |
| `database.py (Base, make_engine)` | `core/database.py` | [#38](https://github.com/deylon999/admitflow/pull/38) |
| `accreditation_registry.py` | `catalog/accreditation_registry.py` | `refactor/backend-catalog` |
| `catalog_identity.py` | `catalog/catalog_identity.py` | `refactor/backend-catalog` |
| `catalog_import.py` | `catalog/catalog_import.py` | `refactor/backend-catalog` |
| `catalog_lock.py` | `catalog/catalog_lock.py` | `refactor/backend-catalog` |
| `coverage.py` | `catalog/coverage.py` | `refactor/backend-catalog` |
| `exam_requirements.py` | `catalog/exam_requirements.py` | `refactor/backend-catalog` |
| `national_catalog.py` | `catalog/national_catalog.py` | `refactor/backend-catalog` |
| `national_coverage.py` | `catalog/national_coverage.py` | `refactor/backend-catalog` |
| `product_catalog.py` | `catalog/product_catalog.py` | `refactor/backend-catalog` |
| `product_catalog_schemas.py` | `catalog/product_catalog_schemas.py` | `refactor/backend-catalog` |
| `program_catalog_batch.py` | `catalog/program_catalog_batch.py` | `refactor/backend-catalog` |
| `program_catalog_batch_fetch.py` | `catalog/program_catalog_batch_fetch.py` | `refactor/backend-catalog` |
| `program_catalog_import.py` | `catalog/program_catalog_import.py` | `refactor/backend-catalog` |
| `program_catalog_models.py` | `catalog/program_catalog_models.py` | `refactor/backend-catalog` |
| `program_catalog_review.py` | `catalog/program_catalog_review.py` | `refactor/backend-catalog` |
| `program_catalog_sources.py` | `catalog/program_catalog_sources.py` | `refactor/backend-catalog` |
| `source_catalog.py` | `catalog/source_catalog.py` | `refactor/backend-catalog` |
| `university_name_report.py` | `catalog/university_name_report.py` | `refactor/backend-catalog` |
| `university_names.py` | `catalog/university_names.py` | `refactor/backend-catalog` |
| `catalog.py` | `catalog/__init__.py` | `refactor/backend-catalog` |
| `calculation.py` | `competitions/calculation.py` | `refactor/backend-competitions` |
| `competition_api.py` | `competitions/competition_api.py` | `refactor/backend-competitions` |
| `scenario_api.py` | `competitions/scenario_api.py` | `refactor/backend-competitions` |
| `scenario_explanations.py` | `competitions/scenario_explanations.py` | `refactor/backend-competitions` |
| `scenario_storage.py` | `competitions/scenario_storage.py` | `refactor/backend-competitions` |
| `scenarios.py` | `competitions/scenarios.py` | `refactor/backend-competitions` |
| `changes.py` | `watchlist/changes.py` | `refactor/backend-watchlist` |
| `direction_budget.py` | `watchlist/direction_budget.py` | `refactor/backend-watchlist` |
| `importing.py` | `watchlist/importing.py` | `refactor/backend-watchlist` |
| `source_api.py` | `watchlist/source_api.py` | `refactor/backend-watchlist` |
| `source_history.py` | `watchlist/source_history.py` | `refactor/backend-watchlist` |
| `source_tokens.py` | `watchlist/source_tokens.py` | `refactor/backend-watchlist` |
| `database.py (гостевые модели)` | `watchlist/models.py` | `refactor/backend-watchlist` |
| `operations.py (идемпотентность)` | `watchlist/idempotency.py` | `refactor/backend-watchlist` |
| `main.py (гостевые маршруты)` | `watchlist/api.py` | `refactor/backend-watchlist` |
| `backup.py` | `operations/backup.py` | `refactor/backend-operations` |
| `diagnostics.py` | `operations/diagnostics.py` | `refactor/backend-operations` |
| `jobs.py` | `operations/jobs.py` | `refactor/backend-operations` |
| `maintenance.py` | `operations/maintenance.py` | `refactor/backend-operations` |
| `migration_checks.py` | `operations/migration_checks.py` | `refactor/backend-operations` |
| `migrations.py` | `operations/migrations.py` | `refactor/backend-operations` |
| `observability.py` | `operations/observability.py` | `refactor/backend-operations` |
| `smtp_check.py` | `operations/smtp_check.py` | `refactor/backend-operations` |
| `worker.py` | `operations/worker.py` | `refactor/backend-operations` |
| `jobs.py (SourceJob, SourceCheck)` | `operations/source_job_models.py` | `refactor/backend-operations` |
| `source_operations.py` | `sources/source_operations.py` | `refactor/backend-operations` |
| `account_actions.py` | `auth/account_actions.py` | `refactor/backend-operations` |
| `account_dto.py` | `auth/account_dto.py` | `refactor/backend-operations` |
| `account_limits.py` | `auth/account_limits.py` | `refactor/backend-operations` |

## Поддержка границ и оставшиеся условия

Новый код внутри приложения импортирует реализации из функциональных пакетов. Старые импорты и `python -m` используются внешними консюмерами и проверками совместимости. При добавлении ORM-модели обновляется явная регистрация standalone Alembic и проверяется schema drift. Новые роутеры регистрируются в `main.py` в порядке, который проверяет snapshot. Публикационный callback остаётся в транзакции pipeline.

Проверка фактической доставки письма требует согласованного SMTP-провайдера и стенда. MICCEDU остаётся внешним условием для одного унаследованного теста. Статус PR и обязательных workflow относится к проверенному SHA выше. Сначала ревью core, затем catalog → competitions → watchlist → operations.
