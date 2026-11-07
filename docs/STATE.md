# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-08. Последняя сессия: S201.

## Продолжение

- Текущая задача: нет.
- Следующая задача: не назначена.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

Stop after completed cleanup as requested. Read docs/evidence/foundation-cleanup.md and docs/foundation-cleanup-audit.md. T250 remains blocked: Docker Compose PostgreSQL startup denied docker_engine/config access. Resume only with permitted Docker/PostgreSQL environment and explicit next work; verify native migrations/API/catalog without deleting volumes. No new features or redesign.

## Последняя завершённая работа

- T248-T249: dependency audit and KEEP/REFACTOR/DELETE decisions; 42 stale files and two old stateless calculator HTTP endpoints removed; CamelModel isolated; 46 unused lock entries removed (162 ->116 install).
- T251: frontend TS/ESLint/build/source guard pass; 193 Chromium passed, 29 runtime routes; 20 catalog baseline +125 reference pixel comparisons zero diff. Portable Windows backend549passed/35PG skips; 12 Linux-resource modules retained and uncollectable here.
- T252: current v3 docs/architecture/API and registry aligned; old release/ML tasks deferred, historical done/evidence retained. Protected UI/migration/local DB hashes verified. T250 native PG/Docker blocked; cleanup stopped without new features.

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Опорный мониторинг не включает все лицензированные вузы. 2026-11-05 islod.obrnadzor.gov.ru/rlic timeout; нужна доступная официальная выгрузка для T056. Живая кампания 2027 и суточное наблюдение не подтверждены.

## Проверенное окружение

- Actual docker compose config --quiet exit0; up -d db exit1 permission denied on docker_engine, Docker config access denied. No permission/config workaround, no volume deletion or working PostgreSQL connection/migration claim.
- Final portable backend549passed/35native PG skips (182.05s); initial full collection12resource errors on Windows, Linux CI suite remains intact. UTF8 fixture-read test fixed without altering source fixtures.
- Chromium193passed/0failed/skipped/flaky (54.2s). All29routes; 20 catalog PNGs identical to2a7835f and125 source comparisons under existing demo-label rules. All render files/CSS unchanged except dead routeLabels removed.
- No frontend static preview/parallel renderer or unused React plugin. npm ci116; lint source/tests/scripts, tsc, Vite build pass. Production asset names/sizes match prior recorded build; initial dist absent, raw byte comparison not claimed.
- Applied migrations and local legacy DB hashes unchanged; SQL models and source/normalization/history/jobs/backup kept. Hosted CI/native PG/Docker runtime not verified. QA servers stopped cleanly; no push/deployment/main changes.

## Готовность к выпуску

Принятые gates в STATE.json: не зафиксированы.
Технические результаты и внешние условия — [RELEASE_GATES.md](RELEASE_GATES.md).
Завершение задач не означает автоматическую приёмку gate.

## Чтение по задаче

Карта документов — [README.md](README.md). Полный TASKS, журнал и исследования
источников не входят в стартовый контекст. Старые передачи — [архив](archive/state-before-optimization.md).
