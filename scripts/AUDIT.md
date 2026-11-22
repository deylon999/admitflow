# Аудит служебных скриптов

Основа — дерево `main` на `5ca1cca` после PR #32 и #34. Проверены пути из [workflow](../.github/workflows/ci.yml),
[Compose разработки](../compose.yaml), [production Compose](../compose.prod.yaml),
[Dockerfile backend](../backend/Dockerfile) и [frontend](../frontend/Dockerfile),
а также импорты, Python/Node entrypoints, команды в runbook и исторических
отчётах. В таблицах приведены основные потребители и ссылки для воспроизведения.
Отсутствие отдельного теста указано знаком «—» в столбце тестов.

- **KEEP** — сохраняется существующая реализация по прежнему пути.
- **MOVE** — реализация переезжает в указанный раздел. Прежний файловый путь
  сохраняется через wrapper. Исторические команды в отчётах остаются пригодными.
- **REFACTOR** — изменяется только способ разрешить импорт у существующего
  публичного entrypoint.
- **DELETE** — кандидатов нет. Исследовательские скрипты нужны для повторных
  проверок, даже если их не запускает CI.

В колонке «Пути» `ROOT` означает корень репозитория, вычисляемый из файла,
`cwd` — текущую директорию вызывающего процесса. Явные относительные аргументы
по-прежнему разрешаются из `cwd`. В обычных контейнерах корневой `scripts/`
отсутствует, поскольку он исключён [.dockerignore](../.dockerignore).
Пометка «Docker host» означает вызов Docker из скрипта на машине оператора.
Тестовые файлы backend с именами `test_*.py` запускаются pytest из `backend/`.
«CI тест» означает импорт реализации тестом, «CI CLI» — прямой запуск команды.

## Корневой scripts

| Решение | Файл | Назначение и вход | Основные зависимости | Тесты, CI и Docker | Документы | Пути |
| --- | --- | --- | --- | --- | --- | --- |
| KEEP | `local_smoke.py` | `python scripts/local_smoke.py`, запуск стека и проверка сохранности | stdlib, Docker Compose, PostgreSQL, Alembic | `test_local_start`, CI тест, Docker host | README, catalog-runbook | ROOT, абсолютный Compose-файл |
| KEEP | `roadmap.py` | `--check`, `--render`, карточки и handoff | stdlib, реестры docs | `test_roadmap`, CI CLI | AGENTS, DEVELOPMENT | ROOT, `docs/` |
| REFACTOR | `test_postgres.py` | `python scripts/test_postgres.py` или `python -m scripts.test_postgres`, запуск pytest в отдельном PG | `ops.postgres_runtime`, Docker, pytest | проверка CLI, миграции в CI используют собственный PG, Docker host | README, RUNBOOK | ROOT, subprocess из `backend/` |
| KEEP | `check_auth_acceptance.py` | проверка отчётов JUnit и браузерных результатов | stdlib, JSON-матрица auth | `test_auth_acceptance`, CI CLI | KAN-214-PR6 | cwd, пути отчётов из аргументов |
| KEEP | `requirements-dev.txt` | `pip install -r`, зависимости unit-тестов | requirements-report, pypdf | CI установка | WEEKLY_REPORT, карта scripts | включение файла рядом |
| KEEP | `requirements-report.txt` | `pip install -r`, зависимости PDF | ReportLab, системный шрифт | `test_weekly_report` через requirements-dev | scripts/README | рядом с requirements-dev |

## MOVE в scripts/data

Точка входа каждого CLI — `python -m scripts.data.<имя>` или прежний
`python scripts/<имя>.py`. Отдельных вызовов этих CLI из Compose нет.

| Имя .py | Назначение | Основные зависимости | Тесты и CI | Документы | Пути |
| --- | --- | --- | --- | --- | --- |
| `admissions_inventory` | Кандидатные ссылки и структура списков | bs4, backend discovery, source_inventory | `test_admissions_inventory`, CI тест | b15-admissions-inventory | ROOT, инвентарь и кэш |
| `audit_sgu` | Независимая сверка строк SGU | stdlib parser, backend SGU adapter | — | sgu-4588, b11-progress | ROOT для backend, исходник и отчёт из аргументов |
| `audit_table_family` | Независимая сверка общих таблиц | stdlib parser, backend table profiles | — | b12-progress | ROOT для backend, аргументы cwd |
| `build_accreditation_registry` | Воспроизводимая сборка реестра из ZIP/XML | stdlib, открытая выгрузка | `test_accreditation_registry`, CI ETL | accreditation-registry, KAN-217 | ROOT для артефакта, вход cwd |
| `build_admission_history` | Сборка исторического набора и паспорта | bs4, gzip/CSV/JSON, snapshot каталога | `test_admission_history`, CI ETL | ML README, KAN-232 | ROOT для данных, вход cwd |
| `build_bgu_fixture` | Синтетическая тестовая страница из метаданных BGU | stdlib, scope JSON | fixture покрыт `test_filtered_table` и `test_bgu_attestation`, CI тест | b17-attestation | ROOT, fixture и scope |
| `build_exam_requirements` | Подготовка требований ЕГЭ из reviewed PDF | stdlib, `pdftotext` | `test_exam_requirements`, CI ETL | KAN-219 exam requirements | ROOT для артефакта, PDF cwd |
| `capture_admission_history` | Загрузка архивных страниц MICCEDU | bs4, urllib, build_admission_history | `test_admission_history`, CI ETL | ML README, KAN-232 | ROOT для импорта, JSONL из аргумента |
| `capture_catalog` | Захват публичных данных о вузах MICCEDU | bs4, urllib | `test_catalog_capture`, CI тест | national-catalog, b14-national-catalog | ROOT, кэш и итоговый файл |
| `capture_program_catalog` | Ограниченный захват зарегистрированных документов программ | backend fetcher, review registry | `test_program_catalog_capture`, CI тест | KAN-218-PR2 | ROOT, рабочий каталог оригиналов |
| `group_source_formats` | Связь наблюдений по структуре таблиц и seeds | bs4, admissions_inventory, source_inventory | `test_format_groups`, CI тест | b15-format-families | ROOT, исходные инвентари, кэш |
| `pack_profiles` | Запись проверенных shard-профилей | backend profile catalog | `test_profile_catalog` покрывает API хранения, CI тест | b15-profile-catalog | ROOT, каталог профилей |
| `prepare_bgu_scope` | Подготовка публичной области BGU для ручного review | bs4, source_inventory | scope покрыт `test_bgu_attestation`, CI тест | b17-bgu-scope | ROOT, входы инвентаря и выход scope |
| `research_stateful_formats` | Исследование страниц с состоянием, селекторами и пагинацией | bs4, source_inventory, admissions_inventory | `test_stateful_research`, CI тест | b16-stateful-research | ROOT, seeds, кэш и отчёт |
| `review_bgu_scope` | Независимый построчный аудит точного scope BGU | backend HTML, profile catalog, table decoder | `test_bgu_attestation`, CI тест | RUNBOOK, b17-attestation | ROOT, паспорта и отчёт |
| `review_section_family` | Сверка оригиналов с секциями и публикация reviewed профиля | bs4, backend table/profile catalog | секции покрыты `test_section_family`, CI тест | b15-section-family | ROOT, профили и отчёт |
| `review_sgu_scope` | Сверка приватного оригинала SGU4576 | backend profiles, stdlib parser | область покрыта backend-тестами parser и attestation | sgu-4576, b14-national-catalog | ROOT и файл из аргумента |
| `sanitize_pilot` | Производный обезличенный DOM SGU | bs4, backend HTML inspection | производный fixture в backend-тестах SGU | backend SGU fixture README, sgu-4588 | ROOT для backend, вход и выход cwd |
| `sanitize_table_source` | Производный обезличенный DOM GUAP | bs4 | производный fixture в тестах table family | guap-2026-math, b12-progress | вход и выход cwd |
| `source_inventory` | Ограниченный обход публичных сайтов вузов | bs4, backend Fetcher/catalog, robots | `test_source_inventory`, CI тест | national-inventory, b14-national-catalog | ROOT, кэш и отчёт |

## MOVE в scripts/qa

CLI запускаются модульно или по прежним файловым путям.
`load_server` — процесс стенда, `load_support` — импортируемый модуль.
CI запускает валидатор Markdown. Остальные команды раздела запускаются
явно. Backend-тесты миграций, воркера и каталога выполняются в CI отдельно.

| Имя .py | Назначение | Основные зависимости | Тесты и Docker | Документы | Пути |
| --- | --- | --- | --- | --- | --- |
| `check_doc_links` | Локальные Markdown-ссылки и якоря | stdlib, Git | `test_check_doc_links` и CLI включены в CI | AGENTS, operations/ci | ROOT и отслеживаемые пути Git |
| `audit_private_artifacts` | Проверка артефактов на приватные данные | Git, bs4, оригинал и приватный ключ | — | b11-progress, privacy scan | ROOT, Git и frontend/dist, аргументы cwd |
| `load_profile` | Синтетическая нагрузка на HTTP/PG | httpx, SQLAlchemy, backend, load_server | ручной нагрузочный прогон, выделенный PG | t044-load, QUALITY | ROOT, дочерний процесс, отчёт cwd |
| `load_server` | Uvicorn API только для стенда | Uvicorn, backend, load_support, LOAD_PORT | дочерний процесс load_profile | t044-load | ROOT, именованный импорт Uvicorn |
| `load_support` | Синтетический адаптер и строки | backend contracts/registry | используется нагрузочным стендом | t044-load | импорт из load_profile и load_server |
| `measure_archive` | Профиль ASGI/PG для архивного сценария | backend fixtures, httpx, SQLAlchemy | ручная проверка, Docker host | b11-progress, archive performance | ROOT, `backend/tests/`, отчёт cwd |
| `rehearse_catalog_migration` | Сверка сохранности столбцов после 0010→0011 | SQLAlchemy, backend Alembic, тестовый PG | `test_migrations` покрывает миграции отдельно | RUNBOOK, b16-integration | ROOT, тестовый URL и отчёт |
| `rehearse_compose` | Воспроизведение пересоздания контейнеров и сохранности истории | Compose, PostgreSQL, образы, httpx | отдельный проект и Docker host | RUNBOOK, b10-runtime | ROOT, временный Compose override |
| `rehearse_postgres_restore` | Сверка восстановления тестовой базы и raw | Docker, pg_dump/restore, backend fixtures | ручной restore, Docker host | RUNBOOK, b10-restore | ROOT, временные файлы и отчёт cwd |
| `rehearse_reviewed_worker` | Прогон проверенного профиля через реальный worker | backend, SQLAlchemy, Docker, профиль и официальный источник | worker покрыт `test_worker`, Docker host | b12-progress | ROOT, subprocess в backend |
| `rehearse_sgu_worker` | Сверка SGU live или offline replay | backend worker, PG, Docker, профиль SGU | worker покрыт `test_worker`, Docker host | RUNBOOK, b11-progress | ROOT, `backend/tests/`, отчёт cwd |
| `replay_archives` | Повторное проигрывание двух архивов | Docker PG, backend replay fixtures | отдельная репетиция, Docker host | b12-progress, b12-replay | ROOT, `backend/tests/` и отчёт |
| `verify_filtered_scope` | Проверка BGU worker/PG и независимого аудита | backend worker, PG, review_bgu_scope | `test_bgu_attestation` покрывает профиль | b17-worker-lookup | ROOT, тестовые модули и отчёт |
| `verify_program_catalog` | Репетиция импорта настоящих документов программ | Docker PG, FastAPI, SQLAlchemy, optional Playwright | импорт покрыт backend-тестами, Docker host | KAN-218-PR2 | ROOT, backend subprocess и private research |
| `verify_program_catalog_batch` | Replay и публикация batch в отдельном PG | Docker PG, backend CLI, FastAPI, сохранённые документы | `test_program_catalog_batch` покрывает CLI отдельно, Docker host | KAN-218-PR3 | ROOT, backend subprocess и private research |
| `verify_reviewed_scope` | Проверка SGU worker/PG и offline аудита | backend worker, PG, review_sgu_scope | worker и SGU parser покрыты отдельно | b14-national-catalog | ROOT, `backend/tests/` и отчёт |
| `verify_section_family` | Проверка секций, кэша и offline аудита | backend worker, PG, review_section_family | секции и worker покрыты отдельно | b15-section-family | ROOT, `backend/tests/` и отчёт |

## MOVE в scripts/ops и scripts/reports

| Назначение | Файл и вход | Основные зависимости | Тесты, CI и Docker | Документы | Пути |
| --- | --- | --- | --- | --- | --- |
| Бэкап и проверка восстановления | `ops/backup_production.sh`, прежний Bash-файл | Bash, Compose, pg_dump/restore, tar, find | операторская команда, Docker host | RUNBOOK и cron | cwd для Compose, wrapper находит реализацию относительно себя |
| Сигнал по диску, бэкапам и worker | `ops/ops_check.py` | stdlib, Compose exec и optional webhook | `test_ops_check`, CI тест, Docker host | RUNBOOK и cron | cwd для Compose, аргументы для путей |
| Управление отдельным PostgreSQL | `ops/postgres_runtime.py`, импорт | stdlib, Docker, postgres:17-alpine | test_postgres и QA, Docker host | RUNBOOK | Docker-имя и порт независимы от cwd |
| Еженедельный отчёт | `reports/weekly_report.py`, CLI или импорт | Git, TASKS.json, ReportLab для PDF | `test_weekly_report`, CI тест | scripts/README | ROOT для Git/TASKS, вывод пользовательский или временный |

## KEEP для scripts/tests

| Файл | Что проверяет и как запускается | Зависимости | Потребители и пути |
| --- | --- | --- | --- |
| `test_roadmap.py` | `python -m unittest scripts.tests.test_roadmap` | stdlib, roadmap | CI из корня, временные копии и fixtures |
| `test_weekly_report.py` | `python -m unittest scripts.tests.test_weekly_report` | weekly_report, ReportLab/pypdf для PDF | CI из корня, временные PDF и JSON |
| `test_auth_acceptance.py` | `python -m unittest scripts.tests.test_auth_acceptance` | stdlib, auth validator | CI из корня, временные JUnit/JSON |
| `test_check_doc_links.py` | `python -m pytest -q scripts/tests/test_check_doc_links.py` | pytest, check_doc_links | CI из корня, временное дерево |
| `test_cli_compatibility.py` | новый тест старых и канонических CLI | stdlib, subprocess | CI из корня, тест абсолютного пути из другой cwd |

## Frontend scripts

Все Node entrypoints из [frontend/package.json](../frontend/package.json)
и команды `node scripts/...` выполняются из `frontend/`. Стандартный
`npm test` и отдельный `npm run test:auth` вызываются в CI.
Все frontend-скрипты сохраняют прежние пути рядом с Vite/Playwright. Решение KEEP применяется к строкам без отдельной пометки.

| Файл | Точка запуска и назначение | Зависимости | Тесты, CI и Docker | Документы | Пути |
| --- | --- | --- | --- | --- | --- |
| `backend-python.mjs` | Новый общий импорт для выбора Python | Node fs/path, PYTHON, backend/.venv | CI через test.mjs | frontend README | абсолютный путь backend |
| `check-auth-visual.mjs` | node, строгий исторический pixel diff | Git/tar, Vite, Chromium, тестовый API | локальный visual, CI не вызывает | KAN-214-PR5/PR6 | frontend cwd, Git на уровень выше, временная папка |
| `compare-main.mjs` | node с SHA, visual replay | Git/tar, Vite, Chromium, локальный API | локальный visual | frontend README, KAN-212 | import.meta, assets и test-results |
| `dev.mjs` | npm run dev, Vite watch build и preview | Vite, proxy config | запуск разработчиком | frontend README | frontend cwd, выход в node_modules/.cache |
| `postgres-runtime.py` | Python, fixture API внутри контейнера | backend app, uvicorn, PG, fixture | Docker mount из verify-postgres, CI не вызывает | KAN-212 | контейнерные /app, /fixture.html |
| `run-visual-tests.mjs` | npm run test:visual, проверка оригинала и делегирование | test.mjs, соседний v3 | локальный visual | frontend README | frontend cwd, соседний checkout |
| `stop-child.mjs` | импорт, завершение дочерних процессов | Node signals, stdin | stop-child.test, CI тест | KAN-238-CI-REPORT | соседние модули |
| `stop-child.test.mjs` | node --test, проверка завершения | Node test, stop-child | CI CLI | KAN-238-CI-REPORT | импорт соседнего модуля |
| `summarize-visual.mjs` | node, сводка visual | Node fs, результаты Playwright | ручной запуск | frontend README, catalog-runbook | frontend cwd, QA_EVIDENCE_DIR |
| `test-api.mjs` | REFACTOR, node, отдельный тестовый FastAPI | backend-python.mjs, catalog_runtime.py | общая fixture-служба также используется test.mjs | catalog-runbook | frontend cwd, subprocess в backend |
| `test-auth-browsers.mjs` | npm run test:auth, три native-PG браузера | Node, Playwright, PG, test.mjs | CI CLI | KAN-214-PR6 | frontend cwd, отдельный results dir каждого браузера |
| `test.mjs` | REFACTOR, npm test / test:e2e, owned API и Vite preview | backend-python.mjs, Vite, TypeScript, Playwright | CI CLI | frontend README, KAN-238-CI-REPORT | frontend cwd, subprocess в backend |
| `verify-postgres.mjs` | node, E2E с отдельным PostgreSQL | Docker, Vite, Chromium, fixture API | ручной E2E, Docker host и bind mount | frontend README, KAN-212 | import.meta, путь frontend runtime |
| `verify-source.mjs` | npm run verify:source, сверка сохранности исходника | Node fs/crypto, manifest и соседний v3 | локальная сверка | frontend README, foundation-cleanup | frontend cwd, manifest в docs, соседний checkout |


## Параллельный аудит evidence

В [PR #33](https://github.com/deylon999/admitflow/pull/33) команда
`python scripts/audit_evidence.py [--ref REF]` читает дерево Git, ищет дубликаты
и проверяет SHA‑256 манифест. Зависимости — Python stdlib и Git. Корень
берётся из пути файла, отчёт выводится в stdout. Решение KEEP для публичной
команды и реализации этого PR. `check_doc_links` проверяет Markdown и якоря,
а аудит evidence проверяет хеши и автоматических потребителей. Обе команды
можно запускать независимо. В текущем `main` аудит evidence появится после
слияния #33, поэтому PR организации не добавляет собственную реализацию.

## Backend CLI и запускаемые тестовые стенды

Все строки этого раздела имеют решение KEEP. Модули `app.*` запускаются
`python -m <модуль>` из `backend/` либо в backend-образе из `/app`. Они используют
конфигурацию, доменные сервисы, модели и fixtures из своего пакета. Корневой
`scripts/` в backend-образ не копируется. Пути в явных аргументах привязаны к
рабочей директории, встроенные данные привязаны к модулю. Сохраняются и пути,
и публичные команды.

| Модуль | Аргументы | Назначение, зависимости и эффекты | Тесты, CI и Docker | Документы |
| --- | --- | --- | --- | --- |
| `app.backup` | `create [--output]`, `verify FOLDER`, `restore FOLDER --destination DIR` | SQLite, raw, файловая копия. Restore пишет в новое назначение | `test_backup`, CI тест | RUNBOOK |
| `app.catalog_import` | без аргументов | Идемпотентный импорт reviewed архивного каталога в настроенную БД. SQLAlchemy и встроенные профили | `test_product_catalog`, CI тест, Compose exec из local_smoke | catalog-runbook |
| `app.diagnostics` | `database` | Проверка БД и ревизии Alembic, структурированный результат | тесты диагностики, Compose exec в rehearsal | RUNBOOK и архив |
| `app.maintenance` | `cleanup-sessions` или `cleanup-accounts` | Уборка просроченных сессий либо данных аккаунтов. Настроенная БД | тесты session/account lifecycle, операторский CLI в backend-образе | RUNBOOK и AUTH документы |
| `app.national_catalog` | `validate` или `import`, `--input`, `--output` | Сверка артефакта MICCEDU и его импорт. JSON и SQLAlchemy | backend-тесты национального каталога, CI тест | national-catalog |
| `app.national_coverage` | `--output` | Отчёт покрытия по настроенной БД. JSON в stdout или файл | backend-тесты coverage, CI тест | NATIONAL_COVERAGE и KAN-221 |
| `app.observability` | `status`, `trace RUN_ID` | Сводка worker и источников или трасса импорта. SQLAlchemy | тесты observability, Compose exec из ops_check | RUNBOOK |
| `app.program_catalog_batch` | `capture --year --work-dir [--limit] [--source]`, `publish --year (--captured DIR или --reviewed-originals DIR) --raw-store DIR [--source]` | Ограниченный захват и транзакционная публикация. Локальные оригиналы, реестр источников, backend, PostgreSQL для публикации | `test_program_catalog_batch`, CI тест, subprocess из QA | KAN-218-PR3 |
| `app.program_catalog_import` | `--raw-directory DIR --raw-store DIR [--source]` | Импорт проверенных локальных оригиналов. PostgreSQL и raw store | backend-тесты programme import, CI тест | KAN-218-PR2 |
| `app.smtp_check` | `--send` | Проверка SMTP-конфигурации. Отправка только с флагом, использует AUTH_TEST_EMAIL | тесты SMTP, операторский Compose exec | operations/smtp |
| `app.sources.audit` | `SOURCE_ID [--limit]` | Сверка сохранённых raw, профилей и фактов, БД и raw store | backend-тесты source audit, CI тест | источники и RUNBOOK |
| `app.sources.batch` | `SOURCE_ID... [--enable] [--plan]` | Атомарная регистрация профилей, план без соединения с БД | backend-тесты profile batch, CI тест | RUNBOOK |
| `app.sources.capture` | `fetch TARGET [--output]`, `verify FOLDER` | Получение ограниченного официального снимка или offline проверка. Fetcher, manifest и файловый кэш | backend-тесты capture, CI тест | passports и RUNBOOK |
| `app.sources.cli` | `ACTION [SOURCE_ID] [--enable]` | Состояние и управление зарегистрированными источниками. SQLAlchemy, реестр и очередь | `test_worker` и `test_source_operations`, CI тест, операторский Compose exec | RUNBOOK и паспорта |
| `app.sources.retention` | `--days`, `--apply` | Аудит хранения raw. Удаление применяется флагом | backend-тесты retention, CI тест | RUNBOOK и DATA_RULES |
| `app.university_name_report` | `--output FILE` | Снимок имён и provenance. Справочные данные приложения и JSON | тесты имён вузов, CI тест | UNIVERSITY-DISPLAY-NAMES |
| `app.worker` | `once` или `loop`, `--poll-seconds` | Обработка jobs на настроенных PostgreSQL/raw. POSIX `resource` в части fetch | `test_worker`, оба Compose вызывают worker | RUNBOOK |
| `backend/tests/auth_runtime.py` | env `TEST_DATABASE_URL`, `AUTH_TEST_DIRECTORY` | Временная схема PostgreSQL, clock и mailbox. Запускается через `npm run test:auth` | CI backend, Firefox/Chromium/WebKit | KAN-214-PR6 |
| `backend/tests/catalog_runtime.py` | env `CATALOG_CONTROL_STDIN` | SQLite и fixture API на loopback. Дочерний процесс `npm test` и `test-api.mjs` | CI frontend | catalog-runbook |
| `backend/tests/check_migrations.py` | env `MIGRATION_DATABASE_URL` | Одноразовая PostgreSQL, сравнение ревизии и метаданных. Запуск из `backend/` | CI migrations, PostgreSQL service | operations/ci |
| `backend/tests/runtime_smoke.py` | `--base-url`, `--output` | HTTP-проверки на локальном стеке, пишет отчёт, удаляет свою тестовую сессию | операторский тест через Compose-стек | T103, архив прежнего runbook |
| `backend/tests/snapshot_backend_contract.py` | `OUTPUT` | Снимок API/CLI на временных данных | запуск для сравнения #34, зависит от backend dev | аудит backend #34 |

`app.sources.cli ACTION` принимает `list`, `status`, `enqueue`, `enqueue-all`,
`disable`, `register-sgu`, `register-reviewed`, `enable-scenarios`, `enable`,
`quarantine` и `resume`. `--enable` допустим только при регистрации.

## Аргументы host-утилит

Квадратные скобки обозначают необязательные аргументы. Для утилит без
парсера указан фактический способ настройки. Запускайте `--help` только
у команд, которые его обрабатывают до начала операции.

| Каноническое имя | CLI-аргументы или окружение |
| --- | --- |
| `roadmap.py` | `--check --render --next --self-test --context --task ID --log [ID] --entries N` |
| `local_smoke.py` | `--output DIR --no-build`. Порт из `WEB_PORT`, проект из кода скрипта |
| `test_postgres.py` | `[--python PYTHON] [TEST ...]` |
| `check_auth_acceptance.py` | `[--matrix JSON] --backend-junit XML --browser-results DIR --output JSON` |
| `qa/check_doc_links.py` | Дополнительных аргументов нет, поддерживается `--help` |
| `data/admissions_inventory.py` | `--input --output --cache --workers --per-institution` |
| `data/audit_sgu.py` | `INPUT --output` |
| `data/audit_table_family.py` | `INPUT --profile {sgu,guap} --output` |
| `data/build_accreditation_registry.py` | `ARCHIVE [--output]` |
| `data/build_admission_history.py` | `CAPTURE [--check]` |
| `data/build_bgu_fixture.py` | Без параметров, фиксированные вход и выход |
| `data/build_exam_requirements.py` | `--pdf` можно повторять, `--check` проверяет артефакт |
| `data/capture_admission_history.py` | `--output [--pause] [--editions ...]` |
| `data/capture_catalog.py` | `--cache --output --details` |
| `data/capture_program_catalog.py` | `SOURCE [--output]` |
| `data/group_source_formats.py` | `--input --seeds --cache --output` |
| `data/pack_profiles.py` | `--input --output-dir` |
| `data/prepare_bgu_scope.py` | Без параметров, использует подготовленные локальные метаданные и кэш |
| `data/research_stateful_formats.py` | `--seeds --inventory --cache --output` |
| `data/review_bgu_scope.py` | `[--publish]` |
| `data/review_section_family.py` | Без параметров, использует локальный кэш и фиксированный выход |
| `data/review_sgu_scope.py` | `INPUT` |
| `data/sanitize_pilot.py` | `INPUT --output NEW_DIR` |
| `data/sanitize_table_source.py` | `INPUT --output NEW_DIR` |
| `data/source_inventory.py` | `--limit --workers --cache --output` |
| `qa/audit_private_artifacts.py` | `--original --key-file --output [--guap-original]` |
| `qa/load_profile.py` | `--database-url --output [--sessions --directions --rows --seats --seconds --prepare-concurrency --port --pace --api-workers]` |
| `qa/load_server.py` | `LOAD_PORT LOAD_WORKERS` и окружение родительского нагрузочного стенда |
| `qa/load_support.py` | Импортируемый модуль |
| `qa/measure_archive.py` | `--output` |
| `qa/rehearse_catalog_migration.py` | `--output` и `TEST_DATABASE_URL` выделенной копии |
| `qa/rehearse_compose.py` | `--backend-image --frontend-image --output` |
| `qa/rehearse_postgres_restore.py` | `--output [--archive-sgu]` |
| `qa/rehearse_reviewed_worker.py` | `PROFILE --output [--capture-directory]` |
| `qa/rehearse_sgu_worker.py` | `--output [--replay-original]` |
| `qa/replay_archives.py` | `--output` |
| `qa/verify_filtered_scope.py` | `--output` и `TEST_DATABASE_URL` |
| `qa/verify_program_catalog.py` | `--raw-directory --output --browser` |
| `qa/verify_program_catalog_batch.py` | `[--originals --captured] --output` |
| `qa/verify_reviewed_scope.py` | `--output` и `TEST_DATABASE_URL` |
| `qa/verify_section_family.py` | `--output --all-profiles --page-cache` и `TEST_DATABASE_URL` |
| `ops/backup_production.sh` | `OUTPUT_DIR`, окружение `COMPOSE RAW_SERVICE KEEP_DAYS` |
| `ops/ops_check.py` | `--compose --backups --disk`, `ALERT_WEBHOOK_URL` включает уведомления |
| `ops/postgres_runtime.py` | Импортируемый модуль |
| `reports/weekly_report.py` | `--week [--main --extra --format --output --font]` |

## Аргументы frontend-инструментов

| Точка запуска | Аргументы и параметры |
| --- | --- |
| `npm run dev` | `--host --port --strictPort` |
| `npm test`, `npm run test:e2e` | После `-- --` аргументы Playwright. `PYTHON` и `QA_API_TARGET` задают окружение runner |
| `npm run test:auth` | `TEST_DATABASE_URL` и необязательный `AUTH_BROWSER_RESULTS_ROOT` |
| `npm run test:visual` | Соседний исходный React checkout. Запуск делегируется `test.mjs --visual` |
| `npm run verify:source` | Соседний React checkout и `QA_EVIDENCE_DIR` |
| `node scripts/check-auth-visual.mjs` | `[--acceptance]` выбирает исторический сценарий |
| `node scripts/compare-main.mjs SHA` | SHA Git и `QA_API_TARGET` |
| `node scripts/test-api.mjs` | `PYTHON`, запуск из `frontend/` |
| `node scripts/summarize-visual.mjs` | `QA_EVIDENCE_DIR` |
| `node scripts/verify-postgres.mjs` | Скрипт требует работающий локальный Compose и свободные порты |
| `postgres-runtime.py` | `KAN212_DATABASE_NAME`, mount `/fixture.html` |
| `node --test scripts/stop-child.test.mjs` | Тестовый модуль Node.js |
| `stop-child.mjs` и `backend-python.mjs` | Импортируемые модули, отдельного CLI нет |
