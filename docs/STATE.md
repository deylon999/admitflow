# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-11. Последняя сессия: S204.

## Продолжение

- Текущая задача: нет.
- Следующая задача: не назначена.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

Work branch zarbondo (PR #7). Done: T056/KAN-217, T255/KAN-221, T256/KAN-228. Next Jira cards of Vadim: KAN-220 adapters, KAN-218/219/227 data, KAN-24 report template. RAOO refresh: python scripts/build_accreditation_registry.py <zip>.

## Последняя завершённая работа

- T256 (KAN-228): real competition list/competitors pages on snapshot API, official order, no identifiers, own row only after confirmation.
- T255 (KAN-221): /app/coverage and /api/v1/coverage/national: four separate layers on the 785 denominator, years, gaps, regions, sources, queue, reproducible JSON report.
- T056 (KAN-217): accreditation register denominator 785 (2026-11-10), 675 catalog heads matched, 109 register-only organisations added to the catalog API/UI with source and date; report docs/evidence/kan-217-national-denominator.md.

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
