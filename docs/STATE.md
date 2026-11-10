# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-10. Последняя сессия: S203.

## Продолжение

- Текущая задача: нет.
- Следующая задача: не назначена.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

T254/T250 complete: Docker PostgreSQL running at http://localhost:8080. Repeat python scripts/local_smoke.py;read docs/evidence/local-postgresql.md. Keep volumes/backups;stop with docker compose stop. No push. New feature APIs/deployment remain separate tasks.

## Последняя завершённая работа

- T254: one-command full Docker Compose startup with backup,migrations,import,API and history persistence check;full build and no-build passed.
- T250: actual native PostgreSQL verification unblocked and complete;Alembic observability metadata fixed in881422f;11native PG+5launcher unit tests passed;Chromium catalog390/1440 viewed.

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Опорный мониторинг не включает все лицензированные вузы. 2026-11-05 islod.obrnadzor.gov.ru/rlic timeout; нужна доступная официальная выгрузка для T056. Живая кампания 2027 и суточное наблюдение не подтверждены.

## Проверенное окружение

- S203 actual Docker29.9.2/Compose/PostgreSQL17.11;db/backend/frontend healthy at127.0.0.1:8080. Alembic current=head0011 and check pass;repeat import1257universities/2reviewedprograms;HTTP/assets/SPA smoke pass.
- Existing admitflow_postgres_data and admitflow_raw_data retained across container recreation. Runtime two-snapshot synthetic history preserved;own guest cleaned;original history fingerprints match. Pre-upgrade dumps kept in ignored test-results/local-start.
- 11native PG tests passed in isolated test database/schemas;test DB removed.5launcher unit tests passed. Fresh Chromium actual PG catalog/detail at390/1440:0pageerrors,nooverflow,PNGs viewed.
- Applied migration versions and React/CSS v3 unchanged. Local stack intentionally left running;no worker/profile automation or source activation. Hosted CI/public release/production restore not claimed;no push.

## Готовность к выпуску

Принятые gates в STATE.json: не зафиксированы.
Технические результаты и внешние условия — [RELEASE_GATES.md](RELEASE_GATES.md).
Завершение задач не означает автоматическую приёмку gate.

## Чтение по задаче

Карта документов — [README.md](README.md). Полный TASKS, журнал и исследования
источников не входят в стартовый контекст. Старые передачи — [архив](archive/state-before-optimization.md).
