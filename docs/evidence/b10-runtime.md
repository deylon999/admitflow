# B10 — проверка реального runtime, 2026-11-03

Запрос: десять задач, двумя подходами по пять. Начало: `33a962b`, чистый checkout. Linux, Python 3.14.8, Node 22.23.1; зависимости из текущих requirements/package-lock. Docker Engine 29.9.2 доступен после предоставления доступа. Существующий проект radar не изменяется.

Первые пять: T103, T014, T017, T067, T168. Вторые пять: отдельные проверки PostgreSQL queue/fencing, атомарной публикации, восстановления PostgreSQL, выдачи production assets и перезапуска Compose. Автоматические источники и staging не объявляются готовыми на основании локального синтетического стенда.

## T103 — legacy PostgreSQL

PostgreSQL **17.11**, image `postgres:17-alpine`, digest `sha256:266d3c257594e195b309ae9d1805e54c788f1d7b375f56bf6c367aac6c917e7b`. Отдельный контейнер `admitflow-b10-pg`, localhost:55439, disposable database `admitflow_test_b10`; каждый тест создаёт и удаляет только собственную schema.

Из `backend/`: `TEST_DATABASE_URL=<local disposable PG> .venv/bin/python -m pytest -q tests/test_migrations.py -k 'postgres_adopts or postgres_refuses' --tb=short` → **6 passed, 15 deselected, exit 0**, 2.18s. Обе legacy-схемы приняты, исходный ID/название/история и результат74 сохранены. Изменённые операторы, регистр строк, NOT VALID и логика CHECK отклонены с сохранением записей. Blind stamp, удаление прежних volumes и изменение рабочих БД не применялись.

Первый запуск до готовности нового PG получил6 connection errors; после `pg_isready` повторён весь выбранный набор. Существующие Starlette/httpx warning и warning SQLAlchemy при намеренном NOT VALID не скрыты. Это не миграция пользовательского production volume.

## T014 — native migrations и воспроизводимый runner

`backend/.venv/bin/python scripts/test_postgres.py --python "$PWD/backend/.venv/bin/python"` → **21 passed, exit0**, 3.71s (7 native PG, 14 SQLite/offline). Fresh upgrade, repeat, model alignment, downgrade/base/upgrade и legacy проверены на отдельной schema. Production не создаёт схему автоматически: существующие strict settings/readiness проверки сохранены.

Отказ: та же команда с `tests/test_calculation.py` проходит доменные assertions, но итоговый **exit1**: Required PostgreSQL checks were absent. Контейнер останавливается и удаляется и при отказе. Runner ждёт TCP readiness и выбирает свободный localhost port, устраняя наблюдённую startup race. Production backup/rollout этим не подтверждены; обратимые downgrade выполняются исключительно на disposable schema.
