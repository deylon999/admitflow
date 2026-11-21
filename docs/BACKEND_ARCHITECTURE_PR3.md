# Backend architecture PR 3

## 1. Исходная архитектура

База от 2026-11-21 — `origin/main` на `29c5902c02d05dd16c03070a74173d3460b365b7`. История и GitHub API подтверждают merge [документационного cleanup PR #32](https://github.com/deylon999/admitflow/pull/32) в этот коммит. `chore/product-foundation-cleanup` также есть в истории `main` (`79593a5`). На момент `git fetch origin` рабочая копия была чистой, локальной и удалённой веток с именем `refactor/backend-auth-organization` не было. Ветка создана прямо от проверенного SHA.

[PR #33 по организации evidence](https://github.com/deylon999/admitflow/pull/33) оставался открытым при проверке базы. Его изменения относятся к документации, архиву evidence и скрипту аудита. Общие файлы `docs/STATE*` и `docs/LOG.md` могут потребовать согласования при последовательном merge.

`app.main:create_app` создаёт engine, связывает lifespan, middleware, гостевые сессии, watchlist и установщики account, product catalog и competition API. `app.main:app` остаётся ASGI entrypoint для Docker и Uvicorn. `database.py` владеет `Base`, engine и историческим guest/watch/operation persistence. `admissions.py` описывает таблицы каталога, конкурсных групп, источников, публикаций и подписок. `product_catalog.py` собирает публичные проекции из каталога, admissions и опубликованных фактов. `program_catalog_import.py` проверяет ревью и публикует данные через каталог, блокировки и `sources.storage`. `sources/` содержит реестр, загрузку, адаптеры, хранилище и CLI. Прямых импортов четырёх account-модулей из этих каталогов и source pipeline нет.

## 2. Импорты и зависимости до переноса

| Модуль | Зависимости внутри `app` | Потребители и используемые символы |
| --- | --- | --- |
| `account_api` | `account_dto`, `account_actions`, `account_limits`, `account_mail`, `account_security`, `accounts`, `http` | `main.create_app` лениво импортирует `install`, передаёт `database`, `config`, `engine`, опциональный mailer. `install` включает `APIRouter` с `AuthRoute` под `/api/v1/auth`, сохраняет `Depends` для доступности, rate limits и DB. Тесты читают cookie-константы и подменяют `datetime`, `lock_family`, `verify_password`, `current_account`. `tests/auth_runtime.py` меняет `account_api.datetime` для браузерных тестов. |
| `accounts` | `database.Base`; SQLAlchemy | `account_api`, `account_actions`, `account_limits`, `maintenance`, `alembic/env.py` и account-тесты. При импорте регистрирует шесть account-таблиц на общей `Base.metadata`. Потребители используют `AccountUser`, `AccountSession`, `AccountRefreshToken`, `AccountActionToken`, `AccountCsrfContext`, `AccountRateBucket`. Alembic дополнительно импортирует `admissions`, `program_catalog_models`, `jobs`, `observability`. |
| `account_security` | Внутренних импортов нет; Argon2 и стандартная библиотека | `account_api`, `account_dto`, `account_actions`, `account_mail`, `smtp_check`, `Settings.__post_init__` (ленивый импорт при валидации SMTP) и тесты. Используются `normalize_email`, `validate_password`, `hash_password`, `verify_password`, `new_token`, `credential_digest`, исключения и `PasswordCheck`. В модуле живут Argon2 hasher и ограничитель параллелизма. |
| `account_mail` | `account_security`; `ssl`, `smtplib`, `email` | `account_api.install` и `smtp_check` вызывают `configured_mailer`. Тесты импортируют mailer и `MailDeliveryError`, подменяют `smtplib.SMTP`/`SMTP_SSL` и проверяют `_SEND_SLOTS`. API выбирает внедрённый или сконфигурированный mailer. Регистрация, повторная отправка и восстановление используют тот же транспорт. |

Все production-импорты этих модулей в `app` относительные. Alembic, тесты и тестовые Python runtimes используют абсолютные пути `app.*`. Проверка `importlib`, `__import__`, строковых путей, patching и скриптов сборки установила следующие связи:

- Docker копирует `backend/app` целиком, затем запускает `python -m alembic upgrade head` и `python -m uvicorn app.main:app`. Worker запускается через `python -m app.worker`, SMTP-диагностика через `python -m app.smtp_check`, очистка через `python -m app.maintenance`. У CLI импорта программ и source CLI собственные точки входа. Переносимые модули сами CLI не предоставляют.
- `conftest.py` импортирует `create_app` и создаёт отдельные тестовые БД. Account-тесты и `tests/auth_runtime.py` используют старые пути и изменяют globals. Frontend test runner запускает `auth_runtime.py` и `catalog_runtime.py`. Строковых точек запуска auth-модулей и загрузки их по файловым путям в Docker, CI, скриптах и worker нет. Alembic revisions не импортируют переносимые модули.
- В import graph переносимых модулей циклов нет. `account_api → account_actions/account_limits/account_dto → accounts/account_security` и `account_api → account_mail → account_security` идут в одном направлении. `accounts → database` заканчивается в `Base`. `account_security` и `http` не импортируют account API или `config` обратно. `account_mail` принимает объект настроек без импорта `Settings`.
- В repo не найдено сохранённых pickle account-объектов, ссылок на ORM-классы по строковому имени модуля или сериализации `__module__` для auth. Модели хранятся в PostgreSQL, HTTP DTO сериализуются через Pydantic. Совместимость загрузки Python-объектов по прежнему пути проверяется отдельно.

## 3. Проблемы организации

`account_api.py` (491 строка) объединяет маршруты, auth guards, rate limits, доступ к сессиям и SMTP-координацию. `main.py` (391 строка) совмещает composition root и гостевой HTTP API. `product_catalog.py` (309 строк) смешивает HTTP, SQL и display projections. `program_catalog_import.py` (313 строк) объединяет CLI, валидацию и применение импорта. `admissions.py` (254 строки) регистрирует модели разных подсистем и ORM hooks нормализации. В `main` и `account_api` есть однотипное приведение времени к UTC. Гостевой `token_hash` и auth `credential_digest` похожи по назначению, но используются разными протоколами. Порядок операций, общие helpers и алгоритмы в этом PR не пересматриваются.

## 4. Scope и риски

Переносим четыре модуля в `app.auth`. Совместимые пути нужны для существующих абсолютных импортов, mocks, clock overrides и единственного экземпляра ORM-классов, SMTP/Argon2 semaphores. Алиасы должны возвращать один объект модуля при любом порядке импортов. Пустой `auth/__init__.py` по поведению позволит импортировать ORM или security без загрузки FastAPI API.

`account_actions`, `account_dto` и `account_limits` пока сохраняют своё расположение: уже отделены от HTTP, имеют собственных потребителей и не требуют перемещения для этого PR. `config`, `database` и `http` обслуживают и гостевой, и account-контуры. Для них отдельный `core` сейчас увеличил бы число импортных и миграционных изменений без необходимости. Проверки сравнят HTTP и метаданные в одной версии зависимостей и отдельно проверят миграции на чистом PostgreSQL.

Предлагаемая структура:

```text
app/
  auth/
    __init__.py
    account_api.py
    accounts.py
    account_security.py
    account_mail.py
  account_api.py, accounts.py, account_security.py, account_mail.py  # совместимые пути
  main.py
  sources/
```

## 5. Воспроизводимый baseline

Перед переносом со снятого через `git archive` дерева `29c5902` получено девять канонических JSON-снимков. Скрипт [snapshot_backend_contract.py](../backend/tests/snapshot_backend_contract.py) сохраняет OpenAPI целиком с сортировкой ключей, эффективные маршруты FastAPI в порядке регистрации, дерево `Depends`, JSON Schema DTO в режимах validation/serialization, HTTP статусы/ответы и заголовки на безопасных сценариях. Для ORM сохраняются PostgreSQL и SQLite DDL, типы, nullable, клиентские defaults, ключи, ограничения и индексы, а также мапперы, атрибуты и relationships. Отдельно снимок получает metadata через standalone Alembic до импорта `app.main`. Граф миграций включает SHA-256 каждого файла revision. Повторный baseline с `PYTHONHASHSEED=1234` совпал побайтно.

В общем Linux Python 3.12 окружении из `backend/` каждого checkout запустить одну и ту же копию скрипта. `DATABASE_URL` ниже используется для offline Alembic SQL, соединение с этой БД не открывается. HTTP smoke запускается с временной SQLite БД. Для native runtime и реальных миграций ниже используется выделенный PostgreSQL.

```bash
PYTHONPATH=. DATABASE_URL=postgresql+psycopg://fixture:fixture@localhost/fixture \
  python /absolute/path/snapshot_backend_contract.py /absolute/path/before
# В backend/ проверяемого checkout выполнить ту же команду с каталогом after.
diff -ru /absolute/path/before /absolute/path/after
```

На baseline зарегистрировано 53 маршрута, из них 10 auth. В OpenAPI 45 путей, 50 операций и 71 компонентная схема, `securitySchemes` отсутствует, cookie/Origin/CSRF обрабатываются runtime. Есть 11 auth DTO и 34 таблицы/маппера, ORM `relationship()` отсутствуют. Снимки metadata приложения и standalone Alembic совпали. В Alembic 14 revisions, head `0014`. `PYTHONPATH=. python tests/check_migrations.py` на пустой PostgreSQL 17.11 БД выполнила upgrade и `alembic check` без расхождений.

`python -m uvicorn app.main:app` на baseline ответил `200` для `/api/live`, `/api/health`, `/api/openapi.json`. Успешны `--help` для `app.smtp_check`, `app.maintenance`, `app.worker`, `app.program_catalog_import`, `app.program_catalog_batch`, `app.sources.cli`, `app.backup` и `python -m alembic heads`. `python -m pytest --collect-only -q tests/test_account*.py tests/test_smtp_check.py` собрал 274 проверки аккаунтов, security и SMTP. Полный baseline pytest выполнен на неизменяемом tar checkout отдельно от ветки.

## 6. Перемещения и обновлённые импорты

| Старый файл в `backend/app/` | Новый файл в `backend/app/` | Изменения при переносе |
| --- | --- | --- |
| `account_api.py` | `auth/account_api.py` | Импорты соседей из верхнего пакета используют `..` |
| `accounts.py` | `auth/accounts.py` | `Base` импортируется из `..database` |
| `account_security.py` | `auth/account_security.py` | Совпадает побайтно |
| `account_mail.py` | `auth/account_mail.py` | Совпадает побайтно |

`main` использует `.auth.account_api`, `config` и `account_dto` — `.auth.account_security`, `account_actions` — `.auth.accounts` и `.auth.account_security`, `account_limits` и `maintenance` — `.auth.accounts`, `smtp_check` — `.auth.account_mail` и `.auth.account_security`. Alembic регистрирует модели через `from app.auth import accounts`. Внутри `auth` импорты между соседями остаются относительными. `git diff --find-renames` показывает старые файлы изменёнными из-за совместимых путей. `git diff -B -M --stat origin/main` распознаёт исходные реализации и их новые пути с 98–100% схожести.

## 7. Совместимость и зависимости после переноса

Каждый из четырёх старых файлов регистрирует канонический модуль в `sys.modules` под старым ключом. Оба пути возвращают один объект, поэтому patch меняет globals исполняемого кода. Хранилище ORM, классы исключений и состояние семафоров тоже общие. Тесты и `tests/auth_runtime.py` продолжают использовать старые пути. У создаваемых теперь Python объектов `__module__` содержит канонический путь. Тесты подтверждают чтение старых ссылок pickle в новой версии и round trip в новой версии. Чтение нового pickle старым checkout не входит в контракт проекта.

```text
main → auth.account_api → auth.accounts → database.Base
                        → auth.account_mail → auth.account_security
                        → account_dto → auth.account_security
                        → account_actions → auth.accounts, auth.account_security
                        → account_limits → auth.accounts
                        → http
alembic.env, maintenance → auth.accounts
config → auth.account_security
smtp_check → auth.account_mail, auth.account_security
app.<old_module> → app.auth.<old_module>
```

Проверка графа статических импортов, включая ленивые, не нашла циклов через старые и новые auth-модули. Сравнение Python AST 83 исходных модулей `app` после сопоставления новых путей показало только изменения импортов. `python -m pytest -q tests/test_auth_import_compatibility.py` **7 passed** в Linux: динамические импорты в двух порядках из отдельных процессов, единственная регистрация ORM-модели, чтение старых pickle globals, round trip, строковый `unittest.mock.patch` через старый путь до реального FastAPI endpoint. Поведение legacy `monkeypatch` для часов, SQLAlchemy errors и SMTP проверяет существующий suite.

## 8. Сравнение контрактов до и после

`diff -ru before after` завершился с кодом 0, все девять снимков побайтно совпали. Снимки доступны локально в `.qa-tools/pr3/before` и `.qa-tools/pr3/after`; в Git хранятся скрипт воспроизведения и контрольные суммы.

| Снимки | Результат | SHA-256 до и после |
| --- | --- | --- |
| `auth-{off,on}-openapi` | 45 путей, 50 операций, 71 DTO-схема, включая operation IDs и описания ответов | `50e66758c9fa32b5d516aa126df566fb566a439ee1f6d926916a2d3a19bb81cd` |
| `auth-{off,on}-routes` | 53 маршрута в исходном порядке, методы, имена, дерево `Depends` | `cc3098b4310dc22f3db84bdb4d50543abf44bb5cd99e28df211611c2078e34b4` |
| `auth-dtos` | 11 моделей, validation и serialization схемы | `82d68a864b4189049aee412f29e4434741a77d6dd3f458493490d49fc52f7acf` |
| `auth-off-responses` | 6 запросов, включая `403` для write guard и `503` при выключенном auth | `8c1b1be7ec874e7309a48321b4858a317cd3269f5866fb5dbf022a9b24048652` |
| `auth-on-responses` | 7 запросов, включая `401` без сессии, `403` для CSRF и `422` для невалидного DTO | `9c7460f09480f4252aee70a883b6b8cedafa9ae56084fd83443987e7aaf9284a` |
| `app-metadata`, `alembic-metadata` | 34 таблицы и маппера, совпадают PostgreSQL/SQLite DDL и Python defaults. ORM relationships отсутствуют в обоих снимках | `295626cfc9a59a5e5e47e5712d7e0c5d04fe2f0bc752fb84a0832f62e5ccd3ae` |
| `alembic` | 14 revisions, граф и контрольные суммы revisions, head `0014` | `5c1a122802e4e2cb766017e4acecb589a91a052cebea01c21a8f03a9fde65c48` |

Существующий `check_migrations.py` на двух отдельных пустых БД PostgreSQL 17.11 выполнил upgrade и подтвердил head `0014` с `No new upgrade operations detected` в обоих случаях. `pg_dump --schema-only --no-owner --no-privileges` с одним fixture `--restrict-key` дал одинаковые дампы схемы на обеих БД. SHA-256 `b809984992691f3a13e230e7e3dbe2e2ac6c6a50da613dee90fe5a041474a7ff`. После переноса вывод `--help` семи CLI, Alembic heads и Uvicorn smoke совпал побайтно с исходным. Это проверяет точки входа без запуска реальной отправки почты или обновления источников.

На обеих изолированных PostgreSQL БД `python -m app.maintenance cleanup-accounts` завершилась с кодом 0 и сообщила о нуле удалённых строк. `python -m app.smtp_check` с синтетической SMTP-конфигурацией обеих версий завершилась с кодом 0 и тем же сообщением. Команда без `--send` проверяет конфигурацию без сетевого подключения.

## 9. Backend, frontend и Compose

Из `backend/` запущен полный `python -m pytest -q -ra --require-postgres --junitxml=<file>` с `TEST_DATABASE_URL` на двух отдельных БД в одном временном контейнере PostgreSQL 17.11. Linux Python 3.12.16, зависимости из `requirements-dev.txt` и `constraints.txt`, `pip check` завершился успешно.

| Код | Passed | Skipped | Failures/errors | Время |
| --- | ---: | ---: | ---: | ---: |
| Baseline `29c5902` | 1216 | 1 | 0 | 603,45 с |
| Перенос `5fbcbebf337bd9344d0770045ef3f53351ec2e25` | 1223 | 1 | 0 | 569,92 с |

JUnit до и после показал одинаковые результаты для всех 1217 исходных тестов. Пройдены 274 исходных account/security/SMTP теста, включая регистрацию, отказ, session/refresh/replay, CSRF, TLS и сбои транспорта. Добавились только семь проверок совместимости импортов. `--collect-only -m postgres` нашёл 387 native cases в итоговом suite, все они прошли под `--require-postgres`. В обоих прогонах пропущен `tests/test_admission_history.py::test_committed_dataset_and_passport_agree` из-за отсутствующего внешнего MICCEDU dataset. Четыре исходных предупреждения совпали. PostgreSQL контейнер и отдельная сеть удалены после проверок. Снимки и XML остались в ignored `.qa-tools/pr3`.

- В `frontend/` выполнены `npm ci`, `npm run lint`, `npm run typecheck`, `npm run build` и `npm test`. Chromium прошёл **387 тестов** за 1,7 мин, включая API-интеграцию через штатный Python catalog runtime. Локально использовались Windows и Node 24.21.0. Полный backend пройден отдельно в Linux.
- `npm run test:auth` с реальным PostgreSQL дал **6 passed** в Chromium и **6 passed** в Firefox. Windows WebKit на версии Playwright из lockfile дал **4 passed, 1 failed, 1 did not run**. Сбой `cookie.sameSite` (`None` при ожидаемом `Lax`) и те же итоги воспроизведены на неизменяемом `29c5902` командой `AUTH_BROWSER_E2E=1 AUTH_TEST_BROWSER=webkit npm test` с теми же зависимостями. Серверный `Set-Cookie` отдельно проверяет `test_login_real_credentials_new_session_cookie_and_reload` из native suite.
- `docker compose -p admitflow-pr3-smoke -f compose.yaml -f .qa-tools/pr3/compose-tmpfs.yaml --profile automation config --quiet` и `up --build --wait` прошли. Запущены DB, backend, frontend и worker, в логах worker штатное `idle`. Через frontend получены `200` для `/`, `/api/live`, `/api/health`. Прямой backend вернул OpenAPI `200`, через nginx получен предусмотренный конфигом `404`. `python -m alembic current` в контейнере показал `0014 (head)`. БД и raw storage тестового стека работали через `tmpfs`. После `docker compose … down` проект завершён, именованные volumes не создавались.
- `docker compose -f compose.prod.yaml -f compose.auth.yaml config --quiet` с тестовыми значениями переменных прошёл. Для реальных SMTP-провайдера, staging и доставки письма проверки не выполнялись. SMTP покрыт тестовым транспортом, включая TLS, ошибки провайдера, таймауты и порядок отправки.
- `python scripts/roadmap.py --render --check` и `python scripts/check_doc_links.py` прошли. `python -m pytest -q scripts/tests/test_roadmap.py scripts/tests/test_check_doc_links.py` дал **13 passed**.

## 10. Последующие PR

1. `catalog` — выделить публичные read projections, отдельно проверить importer, канонические идентификаторы и регистрацию catalog-моделей.
2. `competitions` — выделить HTTP и сценарные операции, сохраняя границы между admissions, источниками и calculation.
3. `watchlist` — отделить гостевой watchlist и subscriptions от `main`, сохранить guest owner и контракт idempotency.
4. `core` — после выделения потребителей оценить границы настроек, HTTP middleware, `Base` и engine, отдельно проверить standalone Alembic.
5. `operations` — разложить maintenance, backup, restore и worker orchestration, сохраняя документированные `python -m` entrypoints и правила доступа к данным.

## 11. Pull Request

[PR #34](https://github.com/deylon999/admitflow/pull/34) открыт из `refactor/backend-auth-organization` в `main`. Локально проверен код `5fbcbebf337bd9344d0770045ef3f53351ec2e25`. Состояние проверок текущего SHA доступно в [Checks](https://github.com/deylon999/admitflow/pull/34/checks).
