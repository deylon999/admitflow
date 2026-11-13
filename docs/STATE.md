# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-13. Последняя сессия: S210.

## Продолжение

- Текущая задача: T274.
- Следующая задача: T274.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

KAN-214 PR1 foundation only. PR2-6 remain open. Review/merge required before continuing sequence.

## Последняя завершённая работа

- T273: Six independent account tables and additive0012 implemented.39 tests pass incl native PG uniqueness race, constraints, cleanup/replay retention, guest preservation and standalone schema agreement; no user DB/volume touched.

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Знаменатель вузов взят из выгрузки реестра аккредитации 2026-11-10; программы, правила ЕГЭ и живые списки по стране не собраны. Живая кампания 2027 и суточное наблюдение не подтверждены.

## Проверенное окружение

- S209: npm ci/lint/typecheck/build exit0;147 current Chromium/unit tests against real existing PostgreSQL API passed. Initial hosted dc5205c:frontend146,backend719/0skip,ETL55+1 explicit dataset skip,migrations0011/head/check success. Final hosted SHA/run in PR13 description.
- After final public401 fix:116 screenshot pairs identical to main07526c3 across29 routes x390/1440 xdefault/demo; text equal,no overflow/pageerrors. Viewport galleries inspected.58 direct nginx openings with current JS asset passed.
- Real FastAPI/PostgreSQL guest->lookup->confirm201->subscription->rows50->page/reload51->summary above2 passed with explicit archive fixture in an isolated DB. All owned API containers/test DBs/previews removed; no source activated in user DB.
- User Docker PostgreSQL/backend/frontend healthy on127.0.0.1:8080. Protected history fingerprint unchanged; Alembic0011=head; named volumes retained. No backend source, applied migration,CSS,dependency or workflow changes. PR13 open,no review submitted,no merge; no HTTPS production/live2027 claim.

## Готовность к выпуску

Принятые gates в STATE.json: не зафиксированы.
Технические результаты и внешние условия — [RELEASE_GATES.md](RELEASE_GATES.md).
Завершение задач не означает автоматическую приёмку gate.

## Чтение по задаче

Карта документов — [README.md](README.md). Полный TASKS, журнал и исследования
источников не входят в стартовый контекст. Старые передачи — [архив](archive/state-before-optimization.md).
