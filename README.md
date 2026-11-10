# AdmitFlow

React/TypeScript-интерфейс v3 и FastAPI/PostgreSQL backend. Дизайн v3 —
визуальный эталон. Все 29 маршрутов сохраняются. Реально подключены каталог
вузов, программы, гостевые подписки, поиск/подтверждение записи и события.
Неподключённые feature API явно обозначены; демо открывается отдельно.
ML не подключена.

Каталог использует датированный справочник MICCEDU и два проверенных архивных
конкурса СГУ 2026. Неизвестные проходные и требования ЕГЭ не выдумываются.

## Полный локальный запуск одной командой

Нужны Git, Python **3.10+**, запущенный Docker Engine с Linux-контейнерами и
Docker Compose **v2+ с поддержкой --wait**. На Windows сначала запустите Docker
Desktop и дождитесь готовности Engine. Первый build требует доступа к registry
и пакетам. Node/npm и Python-зависимости на хосте для этого запуска не нужны.

Из корня клонированного репозитория:

```powershell
python scripts/local_smoke.py
```

Скрипт проверяет Compose, поднимает PostgreSQL, **до миграций** сохраняет и
проверяет `pg_dump`, собирает backend/frontend, применяет существующий Alembic
upgrade, проверяет `current == heads` и `alembic check`, дважды импортирует
проверенные metadata и проверяет API/SPA/assets. Затем пересоздаёт контейнеры
на прежних volumes и проверяет сохранность двух снимков собственной тестовой
гостевой истории. Удаляет только свою тестовую сессию; стек остаётся запущенным.

Откройте **http://localhost:8080** или **http://localhost:8080/programs**.
Backend доступен через `/api` этого же адреса, PostgreSQL — внутри Compose-сети.

Успех — exit code 0 и `PASS`. Отчёт JSON и приватная резервная копия находятся в
ignored `test-results/local-start/`; старые отчёты и backup не перезаписываются.
При ошибке — ненулевой код с причиной, без подмены PostgreSQL на SQLite.
После исправления причины команду можно повторить. Для уже собранных образов:
`python scripts/local_smoke.py --no-build`.

Для другого порта скопируйте `.env.example` в `.env` и измените `WEB_PORT`.
Например, `WEB_PORT=8081` даст http://localhost:8081. Не редактируйте credentials
существующего PostgreSQL volume ради нового запуска: это не меняет пароль в БД.
Compose использует локальные dev credentials и HTTP, не production-настройки.

### Данные и остановка

Проект Compose остаётся **admitflow**, volumes — `admitflow_postgres_data` и
`admitflow_raw_data`. Они переиспользуются, applied migrations не переписываются.
На время smoke не выполняйте параллельных записей/импортов: сравнение истории
предполагает спокойный локальный стек. Backup содержит данные БД — не публикуйте
его и храните до проверки обновления. Скрипт не восстанавливает backup поверх
текущей базы и не запускает downgrade.

```powershell
docker compose ps
docker compose exec -T backend python -m alembic current
docker compose exec -T backend python -m alembic heads
docker compose exec -T backend python -m alembic check
docker compose stop
```

`stop` сохраняет данные. Не используйте `docker compose down -v`, удаление
volumes или prune с volumes для обновления проекта. Обычный ручной
`docker compose up --build -d --wait` запускает те же сервисы, но backup,
импорт и полная приёмка выполняются smoke-командой выше.
Worker подключается отдельно через профиль `automation`; импорт каталога не
включает сбор источников и не создаёт персональных source-backed значений.

Подробности импорта и отдельный frontend dev server:
[catalog-runbook](docs/catalog-runbook.md). Для frontend из `frontend/`:
`npm ci`, `npm run dev`, localhost:5173. Proxy по умолчанию localhost:8000;
адрес задаётся `API_PROXY_TARGET`. SQLite test runner — отдельный
frontend-контур, он не доказывает PostgreSQL-совместимость.

Проверки из frontend: `npm run typecheck`, `npm run lint`, `npm run build`,
`npm test`. Полное сравнение с read-only sibling: `npm run test:visual`.
Нужны backend requirements-dev и установленный Chromium.

- [Текущая архитектура](docs/ARCHITECTURE.md)
- [API и удалённые старые endpoints](docs/API.md)
- [KEEP / REFACTOR / DELETE и план сохранности данных](docs/foundation-cleanup-audit.md)
- [Результаты очистки и ограничения инфраструктуры](docs/evidence/foundation-cleanup.md)
- [Состояние и задачи](docs/STATE.md)

Фактические результаты Compose/PostgreSQL и ограничения:
[полный локальный старт](docs/evidence/local-postgresql.md).
Документация прежнего ручного продукта находится в
[архиве](docs/archive/readme-before-foundation.md), код — в Git-истории.
