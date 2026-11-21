# Организация backend AdmitFlow

## База и границы

База работы — `1e7693ebc4ae1761aaba8dcbf659ff5793235813`. PR #34 вошёл в main коммитом `5ca1cca`. Cleanup #32, #33 и #35 и frontend #36–37 тоже включены. Историческая база до auth — `29c5902`. На обоих SHA зафиксированы девять идентичных JSON-снимков и идентичный schema-only дамп PostgreSQL 17.11. [PR #34](https://github.com/deylon999/admitflow/pull/34), [проверки auth-этапа](BACKEND_ARCHITECTURE_PR3.md).

`main.py` сохраняет ASGI entrypoint, старые точки подмены часов и порядок маршрутов. Core предоставляет настройки, общую декларативную базу SQLAlchemy, engine, Pydantic и HTTP middleware. Конфигурация лениво вызывает auth-проверку SMTP при наличии SMTP-настроек. Auth сохраняет свою ORM-модель и контракты. Catalogue и competitions проектируют данные из общей реляционной модели и зарегистрированных источников. Watchlist владеет запросами гостя, ручной историей, подписками и их доступом. Operations владеет эксплуатационными командами и runtime worker. Пакет sources сохраняет адаптеры, сетевые политики, регистрацию и транзакционную публикацию.

## Граф и ресурсы

[Машиночитаемый аудит](evidence/backend-organization-dependencies.json) содержит для каждого из 88 исходных Python-модулей исходящие eager и deferred imports, обратные зависимости, внешние библиотеки, entrypoints, статические внешние ссылки, строковые ссылки, точки подмены и присваивания на уровне модуля. Ссылки в JSON относятся к строкам исходного SHA.

- Alembic регистрирует отдельно auth, общие admissions, catalogue publications, jobs и worker heartbeats. Старый импорт `app.database` регистрирует гостевые модели. При переносе регистрация остаётся явной.
- Docker копирует `backend/app` и ресурсы; Compose запускает `app.main:app` и `python -m app.worker`. Linux runtime использует `resource`. CLI и QA runners находятся также в `scripts/`, `backend/tests/` и `frontend/scripts/`.
- `app/data/` хранит пять датасетов и каталогов проверок. `sources/profiles/` содержит указатель и shards. Перемещение кода сохраняет пути к этим ресурсам.
- На исходном SHA у графа нет циклов eager imports. Полный граф с отложенными импортами содержит циклы в публикации, status/jobs, сценариях и watchlist. Часть связей обслуживает транзакционные callbacks и требует сохранения порядка выполнения.
- Крупные модули `main`, `product_catalog`, `program_catalog_batch` и `program_catalog_import` проверены как упаковка разных операций. `main` перегружен HTTP-логикой гостя. Разделение CLI импорта и пакетного управления сохраняет действующие границы попытки, ревью и транзакций.

## Этапы

| Задача | Изменение | Проверка |
| --- | --- | --- |
| T336 | Аудит и базовая инфраструктура | Сравнение с main и pre-auth, старая идентичность импортов, чистый Alembic |
| T337 | Catalog | Поиск, публикация программ, работа CLI и загрузка ресурсов |
| T338 | Competitions | Контракты конкурсов, расчёт сценариев, порядок маршрутов |
| T339 | Watchlist | Сессия, история, владение, идемпотентность, явные callbacks |
| T340 | Operations и итоговая сверка | Backup/restore, диагностика, worker, миграции, CI и финальный отчёт |

## Циклы и дублирование

| Problem | Before | After | Proof of equivalence |
| --- | --- | --- | --- |
| Обратная зависимость истории от HTTP | История импортирует `candidate_fact` из router во время записи | Общий DTO и mapper находятся в `watchlist/candidate.py`, отдельно от HTTP и каталога | DTO и тесты публикации и истории совпадают |
| Эксплуатационный журнал и расписание | Jobs импортируют `record`, а контроль источника лениво загружает jobs | Планировщик, status и source controls используют одну `operations/source_job_models.py` | Metadata, lease, worker и операции проверены |
| Два bounded-fetch runtime | Worker загружает конкурсные списки, batch fetch загружает документы приёма | Оба остаются со своими лимитами, IPC-контрактами и обработкой ошибок | Доказанной эквивалентности нет |
| Идемпотентность ручных и автоматических записей | Разные fingerprint, replay и retirement правила | Общие функции используются только в исходных местах | Native PostgreSQL проверяет обе семантики |

| Преобразование UTC | Две одинаковые реализации в `main.py` и `sources/publishing.py` | Один `core/time.py`, исторические импорты сохранены | Тест покрывает naive и смещённый aware datetime |

## Реализация

В финальном графе 148 модулей с учётом новых пакетов и совместимых импортов. Граф eager imports остаётся ацикличным. При учёте deferred imports число простых циклов сократилось с 27 до 8. Остались связи между публикацией и сценариями, а также ленивое подключение адаптеров и профилей. Это сохраняет их исходные транзакционные и загрузочные границы.

`main.py` устанавливает функциональные роутеры на прежних позициях. `app.catalog` остаётся действующим публичным модулем после перехода в пакет. Исторический `app.operations` предоставляет функции гостевой идемпотентности, реализация находится в `watchlist/idempotency.py`. Runtime worker остаётся владельцем IPC bounded fetch, поскольку репозиторные patch-тесты проверяют его через старый модуль. В `sources` перенесён операционный журнал источника, связанные импорты обновлены.

В узлах графа baseline перечислены исходные пути. В секции `after.modules` перечислены актуальные зависимости. Точные SHA, хеши контрактов, команды, PR и результаты приведены в [итоговом отчёте](BACKEND_ORGANIZATION_FINAL_REPORT.md).

## Инвентаризация исходных модулей

| Current path | Responsibility | Dependencies | Target package | Action | Reason |
| --- | --- | --- | --- | --- | --- |
| `backend/app/__init__.py` | Package marker | — | `app` | KEEP | Existing package owns this responsibility. |
| `backend/app/account_actions.py` | One-time activation and recovery tokens | `auth.account_security`, `auth.accounts` | `auth` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/account_api.py` | Alias for account router | `auth.account_api` | `auth` | COMPATIBILITY SHIM | Keep PR #34 alias and canonical module identity. |
| `backend/app/account_dto.py` | Account request and response schemas | `auth.account_security`, `schema_base` | `auth` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/account_limits.py` | Account throttling and concurrency limits | `auth.accounts` | `auth` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/account_mail.py` | Alias for SMTP transport | `auth.account_mail` | `auth` | COMPATIBILITY SHIM | Keep PR #34 alias and canonical module identity. |
| `backend/app/account_security.py` | Alias for credential helpers | `auth.account_security` | `auth` | COMPATIBILITY SHIM | Keep PR #34 alias and canonical module identity. |
| `backend/app/accounts.py` | Alias for account ORM and registry | `auth.accounts` | `auth` | COMPATIBILITY SHIM | Keep PR #34 alias and canonical module identity. |
| `backend/app/accreditation_registry.py` | Accreditation dataset, schema and provenance | `national_catalog` | `catalog` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/admissions.py` | Shared relational models for catalogue, sources, contests and subscriptions | `catalog_search`, `database` | `app` | KEEP | Cross-domain FKs and mapper events use one shared registry. |
| `backend/app/auth/__init__.py` | Package marker | — | `app` | KEEP | Existing package owns this responsibility. |
| `backend/app/auth/account_api.py` | Account routes and session lifecycle | `account_actions`, `account_dto`, `account_limits`, `auth.account_mail`, `auth.account_security`, `auth.accounts`, `http` | `auth` | KEEP | Existing package owns this responsibility. |
| `backend/app/auth/account_mail.py` | Bounded SMTP transport | `auth.account_security` | `auth` | KEEP | Existing package owns this responsibility. |
| `backend/app/auth/account_security.py` | Password and credential primitives | — | `auth` | KEEP | Existing package owns this responsibility. |
| `backend/app/auth/accounts.py` | Account persistence mapping | `database` | `auth` | KEEP | Existing package owns this responsibility. |
| `backend/app/backup.py` | Backup manifests, validation, backup and restore CLI | `config`, `database`, `schema_base`, `sources.storage` | `operations` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/calculation.py` | Versioned manual calculation | `schema_base` | `competitions` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/catalog.py` | University seeding and university search | `admissions`, `catalog_lock`, `national_catalog`, `schemas` | `catalog` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/catalog_identity.py` | Stable campaign and programme identifiers | — | `catalog` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/catalog_import.py` | Reviewed catalogue and group registration CLI | `admissions`, `catalog_lock`, `config`, `database`, `sources.table_profiles` | `catalog` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/catalog_lock.py` | Transactional catalogue write lock | — | `catalog` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/catalog_search.py` | Pure search keys consumed by shared ORM listeners | — | `app` | KEEP | Shared mapper callbacks use pure search keys without loading the catalogue package. |
| `backend/app/changes.py` | Subscription event feed and read markers | `admissions`, `scenario_api`, `schema_base`, `sources.publishing` | `watchlist` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/competition_api.py` | Public competition projections and archive API | `admissions`, `schema_base`, `sources.publishing`, `sources.registry`, `sources.status` | `competitions` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/config.py` | Environment and deployment settings | —; deferred: `auth.account_security` | `core` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/coverage.py` | Source and competition coverage counts | `accreditation_registry`, `admissions`, `catalog`, `national_catalog`, `sources.contracts`, `sources.publishing`, `sources.registry`, `sources.status` | `catalog` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/database.py` | SQLAlchemy base, engine and guest persistence registry | — | `core` | REFACTOR | Separate Base and engine from guest persistence and retain the legacy registry import. |
| `backend/app/diagnostics.py` | Read-only database diagnostics and CLI | `database` | `operations` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/direction_budget.py` | Shared manual and automatic direction quota | `admissions`, `database`, `schema_base` | `watchlist` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/exam_requirements.py` | Reviewed EGE data and lookup | `national_catalog` | `catalog` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/http.py` | HTTP request budgets, origin and diagnostic middleware | — | `core` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/importing.py` | Manual history bundle validation and import | `calculation`, `database`, `schemas`; deferred: `direction_budget` | `watchlist` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/jobs.py` | Source job leases, scheduling and persistence | `admissions`, `database`, `source_operations`, `sources.publishing`; deferred: `sources.contracts`, `sources.publishing` | `operations` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/main.py` | FastAPI startup, middleware, dependency and router assembly | `calculation`, `catalog`, `config`, `coverage`, `database`, `http`, `importing`, `maintenance`, `migrations`, `national_coverage`, `observability`, `operations`, `schemas`, `sources.status`; deferred: `auth.account_api`, `changes`, `competition_api`, `direction_budget`, `product_catalog`, `scenario_api`, `source_api`, `source_catalog`, `sources.registry` | `app` | REFACTOR | Retain ASGI and route order; extract functional installers. |
| `backend/app/maintenance.py` | Expired guest and account data maintenance CLI | `auth.accounts`, `config`, `database` | `operations` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/migration_checks.py` | Schema inspection and guarded migration expectations | — | `operations` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/migrations.py` | Alembic runtime integration and restore sentinel | `accounts`, `program_catalog_models` | `operations` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/national_catalog.py` | National university dataset and CLI | — | `catalog` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/national_coverage.py` | National programme coverage and audit CLI | `accreditation_registry`, `admissions`, `national_catalog`, `observability`, `product_catalog`, `sources.publishing`, `sources.registry`, `sources.status`; deferred: `config`, `database` | `catalog` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/observability.py` | Worker heartbeat, status and event logging CLI | `admissions`, `database`, `jobs`, `sources.publishing`, `sources.status`; deferred: `config`, `database` | `operations` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/operations.py` | Legacy watch-write idempotency and retirement | `database` | `watchlist` | REFACTOR | Put guest writes with watchlist and retain the old import surface in the operations package. |
| `backend/app/product_catalog.py` | Public universities, programmes and EGE routers/projections | `accreditation_registry`, `admissions`, `catalog_import`, `exam_requirements`, `national_catalog`, `product_catalog_schemas`, `program_catalog_models`, `university_names` | `catalog` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/product_catalog_schemas.py` | Public catalogue DTOs | `schema_base` | `catalog` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/program_catalog_batch.py` | Durable reviewed programme capture/publish CLI | `program_catalog_batch_fetch`, `program_catalog_import`, `program_catalog_sources`, `sources.fetcher`, `sources.storage`; deferred: `config`, `database` | `catalog` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/program_catalog_batch_fetch.py` | Bounded subprocess for programme retrieval | `sources.fetcher` | `catalog` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/program_catalog_import.py` | Reviewed programme ingestion and publication CLI | `admissions`, `catalog_identity`, `catalog_import`, `catalog_lock`, `national_catalog`, `program_catalog_models`, `program_catalog_review`, `sources.storage`, `sources.table_profiles`; deferred: `config`, `database`, `migrations`, `sources.storage` | `catalog` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/program_catalog_models.py` | Programme evidence and publication ORM | `admissions`, `database` | `catalog` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/program_catalog_review.py` | Review declarations and bounded programme parsers | — | `catalog` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/program_catalog_sources.py` | Reviewed programme source selection | `national_catalog`, `program_catalog_review`, `sources.fetcher` | `catalog` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/scenario_api.py` | Scenario and archived subscription projections | `admissions`, `scenario_explanations`, `scenarios`, `schema_base`, `sources.publishing`; deferred: `source_api` | `competitions` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/scenario_explanations.py` | Scenario explanation contract and mapping | `scenarios`, `schema_base` | `competitions` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/scenario_storage.py` | Scenario persistence and publication callbacks | `admissions`, `scenarios`; deferred: `admissions`, `scenario_explanations`, `source_history`, `source_operations`, `sources.contracts`, `sources.publishing`, `sources.table_profiles` | `competitions` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/scenarios.py` | Versioned scenario calculation | `schema_base` | `competitions` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/schema_base.py` | Shared camel-case Pydantic model base | — | `core` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/schemas.py` | Shared legacy FastAPI DTO import surface | `calculation`, `schema_base` | `app` | KEEP | Shared DTO and response-schema surface; its distinct model names are public contracts. |
| `backend/app/smtp_check.py` | SMTP configuration and opt-in test delivery CLI | `auth.account_mail`, `auth.account_security`, `config` | `operations` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/source_api.py` | Guest source lookup and subscription API | `admissions`, `database`, `direction_budget`, `operations`, `schema_base`, `source_catalog`, `source_tokens`, `sources.contracts`, `sources.publishing`; deferred: `jobs`, `scenario_storage`, `source_history` | `watchlist` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/source_catalog.py` | Search and projection for source-backed contest groups | `admissions`, `schema_base`, `sources.registry`, `sources.status`; deferred: `admissions`, `sources.table_profiles` | `catalog` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/source_history.py` | Subscription snapshot and candidate event history | `admissions`; deferred: `source_api` | `watchlist` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/source_operations.py` | Source operation history and state controls | `admissions`, `sources.contracts`, `sources.publishing`; deferred: `jobs` | `sources` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/source_tokens.py` | Signed lookup confirmation tokens | — | `watchlist` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/sources/__init__.py` | Package marker | — | `app` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/adapters/__init__.py` | Package marker | — | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/adapters/sgu2026.py` | Reviewed SGU 2026 parser | `sources.contracts`, `sources.html_inspection`, `sources.registry` | `sources.adapters` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/audit.py` | Read-only source and database audit | `admissions`, `config`, `diagnostics`, `sources.contracts`, `sources.fetcher`, `sources.publishing`, `sources.registry`, `sources.storage`, `sources.validation` | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/batch.py` | Source batch operator workflows | `config`, `database`, `sources.contracts`, `sources.profile_registration`, `sources.registry` | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/capture.py` | Source capture and bounded fetch orchestration | `sources.contracts`, `sources.fetcher`, `worker` | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/cli.py` | Source operator CLI and dispatch | `admissions`, `config`, `database`, `jobs`, `sources.contracts`, `sources.publishing`, `sources.registry`, `sources.status`; deferred: `jobs`, `scenario_storage`, `source_operations`, `sources.pilots`, `sources.profile_registration`, `sources.table_profiles` | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/contracts.py` | Adapter contracts and scoped identifiers | — | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/fetcher.py` | Network fetch safety, policy and limits | — | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/html_inspection.py` | HTML structure and attestation inspection | `sources.contracts` | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/navigation.py` | Source page navigation and candidate discovery | — | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/page_cache.py` | Conditional source fetch cache | `sources.fetcher` | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/pilots.py` | Reviewed pilot source registration | `admissions`, `catalog`, `catalog_lock`, `sources.adapters.sgu2026`, `sources.contracts`, `sources.publishing`, `sources.registry`; deferred: `source_operations` | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/profile_catalog.py` | Profile resource catalogue I/O and atomic publication | —; deferred: `sources.table_profiles` | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/profile_registration.py` | Register reviewed source profiles | `admissions`, `catalog_lock`, `sources.contracts`, `sources.registry`; deferred: `source_operations`, `sources.table_profiles` | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/publishing.py` | Transactional publication and snapshot replay | `admissions`, `sources.contracts`, `sources.fetcher`, `sources.registry`, `sources.storage`, `sources.validation`; deferred: `scenario_storage`, `source_history` | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/registry.py` | Adapters, runtime registry and attestation checks | `sources.contracts`, `sources.fetcher`; deferred: `sources.adapters.sgu2026`, `sources.structured_family`, `sources.table_family`, `sources.table_profiles` | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/retention.py` | Raw source retention and reconciliation | `admissions`, `config`, `database`, `program_catalog_models`, `sources.storage` | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/status.py` | Freshness and source publication status | `admissions`, `jobs`, `sources.contracts`, `sources.publishing`, `sources.registry` | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/storage.py` | Raw source storage backends | — | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/structured_family.py` | Structured candidate list adapters | `sources.contracts`, `sources.registry` | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/table_family.py` | Review-bound table list adapters | `sources.contracts`, `sources.html_inspection`, `sources.registry`; deferred: `sources.fetcher` | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/table_profiles.py` | Load and validate reviewed table profiles | `sources.profile_catalog`, `sources.registry`, `sources.table_family` | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/sources/validation.py` | Publication checks and quarantine | `sources.contracts` | `sources` | KEEP | Existing package owns this responsibility. |
| `backend/app/university_name_report.py` | Coverage and diagnostics CLI for names | `accreditation_registry`, `catalog_import`, `database`, `national_catalog`, `product_catalog` | `catalog` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/university_names.py` | Reviewed university display names | `national_catalog`; deferred: `accreditation_registry` | `catalog` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
| `backend/app/worker.py` | Bounded source fetch and background scheduling CLI | `admissions`, `config`, `database`, `jobs`, `observability`, `sources.contracts`, `sources.fetcher`, `sources.publishing`, `sources.registry`, `sources.storage`, `sources.validation`; deferred: `sources.page_cache` | `operations` | MOVE | Place implementation with its owner; retain the legacy import and CLI as applicable. |
