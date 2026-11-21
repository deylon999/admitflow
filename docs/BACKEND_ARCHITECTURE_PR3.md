# Backend architecture PR 3

## 1. Исходная архитектура

База от 2026-11-21 — `origin/main` на `29c5902c02d05dd16c03070a74173d3460b365b7`. История и GitHub API подтверждают merge [документационного cleanup PR #32](https://github.com/deylon999/admitflow/pull/32) в этот коммит. `chore/product-foundation-cleanup` также есть в истории `main` (`79593a5`). На момент `git fetch origin` рабочая копия была чистой, локальной и удалённой веток с именем `refactor/backend-auth-organization` не было. Ветка создана прямо от проверенного SHA.

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
