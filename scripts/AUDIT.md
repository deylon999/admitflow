# Аудит служебных скриптов

Основа — дерево `main` на `a3f5078`. Проверены пути из [workflow](../.github/workflows/ci.yml),
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
| KEEP | `roadmap.py` | `--check`, `--render`, карточки и handoff | stdlib, реестры docs | `test_roadmap`, CI CLI | AGENTS, RUNBOOK, docs/README | ROOT, `docs/` |
| REFACTOR | `test_postgres.py` | `python scripts/test_postgres.py` или `python -m scripts.test_postgres`, запуск pytest в отдельном PG | `ops.postgres_runtime`, Docker, pytest | проверка CLI, миграции в CI используют собственный PG, Docker host | README, RUNBOOK | ROOT, subprocess из `backend/` |
| KEEP | `check_auth_acceptance.py` | проверка отчётов JUnit и браузерных результатов | stdlib, JSON-матрица auth | `test_auth_acceptance`, CI CLI | KAN-214-PR6 | cwd, пути отчётов из аргументов |
| KEEP | `requirements-dev.txt` | `pip install -r`, зависимости unit-тестов | requirements-report, pypdf | CI установка | WEEKLY_REPORT, карта scripts | включение файла рядом |
| KEEP | `requirements-report.txt` | `pip install -r`, зависимости PDF | ReportLab, системный шрифт | `test_weekly_report` через requirements-dev | WEEKLY_REPORT | рядом с requirements-dev |

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
Эти CLI не входят в ежедневный GitHub Actions. CI отдельно запускает
backend-тесты миграций, воркера и каталога.

| Имя .py | Назначение | Основные зависимости | Тесты и Docker | Документы | Пути |
| --- | --- | --- | --- | --- | --- |
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
| Еженедельный отчёт | `reports/weekly_report.py`, CLI или импорт | Git, TASKS.json, ReportLab для PDF | `test_weekly_report`, CI тест | WEEKLY_REPORT | ROOT для Git/TASKS, вывод пользовательский или временный |

## KEEP для scripts/tests

| Файл | Что проверяет и как запускается | Зависимости | Потребители и пути |
| --- | --- | --- | --- |
| `test_roadmap.py` | `python -m unittest scripts.tests.test_roadmap` | stdlib, roadmap | CI из корня, временные копии и fixtures |
| `test_weekly_report.py` | `python -m unittest scripts.tests.test_weekly_report` | weekly_report, ReportLab/pypdf для PDF | CI из корня, временные PDF и JSON |
| `test_auth_acceptance.py` | `python -m unittest scripts.tests.test_auth_acceptance` | stdlib, auth validator | CI из корня, временные JUnit/JSON |
| `test_cli_compatibility.py` | новый тест старых и канонических CLI | stdlib, subprocess | CI из корня, тест абсолютного пути из другой cwd |

## KEEP для frontend/scripts

Все Node entrypoints из [frontend/package.json](../frontend/package.json)
и команды `node scripts/...` выполняются из `frontend/`. Стандартный
`npm test` и отдельный `npm run test:auth` вызываются в CI.
Frontend инструменты остаются рядом с зависимостями Vite/Playwright.

| Файл | Точка запуска и назначение | Зависимости | Тесты, CI и Docker | Документы | Пути |
| --- | --- | --- | --- | --- | --- |
| `check-auth-visual.mjs` | node, строгий исторический pixel diff | Git/tar, Vite, Chromium, тестовый API | локальный visual, CI не вызывает | KAN-214-PR5/PR6 | frontend cwd, Git на уровень выше, временная папка |
| `compare-main.mjs` | node с SHA, visual replay | Git/tar, Vite, Chromium, локальный API | локальный visual | frontend README, KAN-212 | import.meta, assets и test-results |
| `dev.mjs` | npm run dev, Vite watch build и preview | Vite, proxy config | запуск разработчиком | frontend README | frontend cwd, выход в node_modules/.cache |
| `postgres-runtime.py` | Python, fixture API внутри контейнера | backend app, uvicorn, PG, fixture | Docker mount из verify-postgres, CI не вызывает | KAN-212 | контейнерные /app, /fixture.html |
| `run-visual-tests.mjs` | npm run test:visual, проверка оригинала и делегирование | test.mjs, соседний v3 | локальный visual | frontend README | frontend cwd, соседний checkout |
| `stop-child.mjs` | импорт, завершение дочерних процессов | Node signals, stdin | stop-child.test, CI тест | KAN-238-CI-REPORT | соседние модули |
| `stop-child.test.mjs` | node --test, проверка завершения | Node test, stop-child | CI CLI | KAN-238-CI-REPORT | импорт соседнего модуля |
| `summarize-visual.mjs` | node, сводка visual | Node fs, результаты Playwright | ручной запуск | frontend README, catalog-runbook | frontend cwd, QA_EVIDENCE_DIR |
| `test-api.mjs` | node, отдельный тестовый FastAPI | Python, catalog_runtime.py | общая fixture-служба также используется test.mjs | catalog-runbook | frontend cwd, subprocess в backend |
| `test-auth-browsers.mjs` | npm run test:auth, три native-PG браузера | Node, Playwright, PG, test.mjs | CI CLI | KAN-214-PR6 | frontend cwd, отдельный results dir каждого браузера |
| `test.mjs` | npm test / test:e2e, owned API и Vite preview | Python, Vite, TypeScript, Playwright | CI CLI | frontend README, KAN-238-CI-REPORT | frontend cwd, subprocess в backend |
| `verify-postgres.mjs` | node, E2E с отдельным PostgreSQL | Docker, Vite, Chromium, fixture API | ручной E2E, Docker host и bind mount | frontend README, KAN-212 | import.meta, путь frontend runtime |
| `verify-source.mjs` | npm run verify:source, сверка сохранности исходника | Node fs/crypto, manifest и соседний v3 | локальная сверка | frontend README, foundation-cleanup | frontend cwd, manifest в docs, соседний checkout |

## KEEP для backend/app/sources/cli.py

Эксплуатационная команда `python -m app.sources.cli` из `backend/` использует
конфигурацию приложения, SQLAlchemy, реестр адаптеров и очередь. В контейнере
её можно вызвать через `docker compose exec` в образе backend. Compose
автоматически запускает `app.worker` для worker-сервиса. CI покрывает операции
через `test_worker` и `test_source_operations`. Параметры, ограничения на
регистрацию и команды приведены в [runbook](../docs/RUNBOOK.md).
