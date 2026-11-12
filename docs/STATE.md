# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-13. Последняя сессия: S209.

## Продолжение

- Текущая задача: нет.
- Следующая задача: не назначена.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

KAN-212 implementation and verification delivered in PR13; T265-T268 done, T269 review. Owner review/acceptance required; do not mark KAN-212 Done or merge autonomously. All four hosted jobs green at dc5205c/run43313647129. Final documentation-only SHA/latest checks are in PR13 description. User PostgreSQL stack healthy at http://127.0.0.1:8080, volumes/history preserved. After acceptance the requested next feature is KAN-223; no EGE/auth implementation started.

## Последняя завершённая работа

- T268: All29 direct/reload/internal/Back/Forward checks and dynamic/auth/unknown/query/hash boundaries passed; saved link and URL filters fixed. Full143 tests pass, lint/typecheck pass. Malformed percent encoding tested through SPA because Vite rejects it before React; nginx HTTP check remains T269.
- T267: Session-aware resource invalidation and cancelled private mutations implemented; explicit guest recovery, cross-tab expiry without loops, bounded group pagination and metadata errors verified. lint/typecheck and131 tests passed. PostgreSQL local_smoke exit0 with backup and persistence; frontend against PG next.
- T266: Reused request and concrete decoders; safe JSON/Headers, strict dates/IDs/ranks/nested fields, provenance and scoped catalog validation. 27 unit tests and full121 passed; lint/typecheck/build pass. First run had transient browser ERR_NO_BUFFER_SPACE before app; unchanged repeat passed.
- T265: Audit completed before code: current main07526c3 and merged PR12/11/9 checked, 29-route API/DTO/mode/navigation matrix and ten minimal fixes recorded. npm ci and baseline94 browser tests passed; SQLite browser stand is not PostgreSQL evidence.

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Знаменатель вузов взят из выгрузки реестра аккредитации 2026-11-10; программы, правила ЕГЭ и живые списки по стране не собраны. Живая кампания 2027 и суточное наблюдение не подтверждены.

## Проверенное окружение

- S209: npm ci/lint/typecheck/build exit0;146 Chromium/unit tests against real existing PostgreSQL API passed. Hosted frontend146, backend719/0skip, ETL55+1 explicit missing-dataset skip; migrations0011/head/schema check success.
- Final source dc5205c:116 screenshot pairs identical to main07526c3 across29 routes x390/1440 xdefault/demo; text equal,no overflow/pageerrors. Viewport galleries inspected.58 direct nginx openings with current JS asset passed.
- Real FastAPI/PostgreSQL guest->lookup->confirm201->subscription->rows50->page/reload51->summary above2 passed with explicit archive fixture in an isolated DB. All owned API containers/test DBs/previews removed; no source activated in user DB.
- User Docker PostgreSQL/backend/frontend healthy on127.0.0.1:8080. Protected history fingerprint unchanged; Alembic0011=head; named volumes retained. No backend source, applied migration,CSS,dependency or workflow changes. PR13 open,no review submitted,no merge; no HTTPS production/live2027 claim.

## Готовность к выпуску

Принятые gates в STATE.json: не зафиксированы.
Технические результаты и внешние условия — [RELEASE_GATES.md](RELEASE_GATES.md).
Завершение задач не означает автоматическую приёмку gate.

## Чтение по задаче

Карта документов — [README.md](README.md). Полный TASKS, журнал и исследования
источников не входят в стартовый контекст. Старые передачи — [архив](archive/state-before-optimization.md).
