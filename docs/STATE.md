# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-12. Последняя сессия: S208.

## Продолжение

- Текущая задача: T263.
- Следующая задача: не назначена.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

KAN-238 ci/kan-238-hardening: Linux Python3.12/PostgreSQL17 full pytest:774 passed,1 explicit missing-dataset skip; required native guard passed.32 migration tests passed; separate clean database upgrade/head0011/check passed;17 repository tests passed; actionlint and pip check passed. Next: T263

## Последняя завершённая работа

- T262: Linux Python3.12/PostgreSQL17 full pytest:774 passed,1 explicit missing-dataset skip; required native guard passed.32 migration tests passed; separate clean database upgrade/head0011/check passed;17 repository tests passed; actionlint and pip check passed.
- T261: npm ci/lint/typecheck/build passed; 94 Chromium tests passed including all 29 routes; 3 child shutdown tests passed. JUnit, screenshot, trace and bounded teardown added. Hosted proof tracked separately in T264.
- T260: Audit completed before implementation; baseline hosted run 43084056846 success at e4d59b4. Confirmed gaps and preserved checks recorded in report.
- T258 (KAN-219): reviewed entrance tests for SGU 09.03.04/02.03.03 from the official 2026 document, builder checks every value against the text, conflicting physics minimum kept null; API, page and coverage layer 1/785.
- T257 (KAN-220): reviewed JSON/CSV adapters through the common Adapter/Registry, enqueue-all with same-domain spreading, PostgreSQL re-import/failure tests; PDF not done, JSON/CSV profiles empty until reviewed.

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Знаменатель вузов взят из выгрузки реестра аккредитации 2026-11-10; программы, правила ЕГЭ и живые списки по стране не собраны. Живая кампания 2027 и суточное наблюдение не подтверждены.

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
