# Очистка фундамента: аудит KEEP / REFACTOR / DELETE

2026-11-08, S201. База ветки: `2a7835f`, новая ветка
`chore/product-foundation-cleanup`. Новые функции не разрабатываются.
Полный функциональный аудит 29 страниц остаётся в
[product-functional-audit.md](product-functional-audit.md).

## Классификация

| Область | Решение | Проверенные зависимости и основание |
| --- | --- | --- |
| Все v3 React pages/components/CSS, включая Calculator | KEEP | Calculator — исходный ЕГЭ/demo-блок v3, не прежний rank/excluded калькулятор. Удаление изменило бы эталон. Все 29 страниц сохраняются |
| `src/catalog/*`, History API router, AppShell | KEEP | Реальные catalog APIs, состояния/фильтры и переходы; рабочий вертикальный срез |
| `data/demo.ts` данные программ/аналитики/списков | KEEP | Используются AppPages/PublicPages; модель не подключена, demo-подписи сохраняются |
| Неиспользуемый export `routeLabels` | DELETE | Единственные потребители — удаляемый offline generator. Runtime router его не читает; export tree-shaken при production build |
| `frontend/preview/*` | DELETE | Второй комплект устаревших HTML с demo-каталогом, без реального API. Не участвует в Vite entry/import graph, Docker копирует только dist |
| `build-offline-preview.cjs` | DELETE | Самописный JSX renderer подменяет React hooks и не выполняет useEffect/API; не является приложением или проверкой текущего каталога |
| `render-preview.py`, `validate-all.py` | DELETE | Только HTML-превью; требуют незакреплённые Python Playwright/Pillow и Linux-specific chromium path. Заменены actual React Playwright tests |
| `PROMPT_FOR_CODEX.md`, `CHANGES_v3.md`, `VISUAL_QA.md` в frontend | DELETE | Инструкции прежнего переноса и статических previews, вводят в заблуждение после интеграции. История и исходный sibling сохранены |
| `@vitejs/plugin-react` и только его transitive dependencies | DELETE | Не импортируется vite.config/dev/test/reference builds. JSX уже компилируется Vite/esbuild; внешний вид проверяется build и pixel tests |
| React/ReactDOM, TS/Vite, ESLint, Node Playwright | KEEP | Runtime/compiler/актуальные проверки имеют прямые импорты и scripts. Новых зависимостей не требуется |
| `scripts/serve_source_e2e.py`, `advance_source_e2e.py` | DELETE | Нужны удалённому frontend E2E на порту 8013/control-файле. Текущий Playwright использует catalog_runtime.py. Backend parser fixtures и publishing tests сохраняются |
| `scripts/install_playwright_ci.sh` | DELETE | Workaround старого workflow с sudo-переписыванием apt mirror; текущий CI его не вызывает и использует штатный install --with-deps |
| `/api/v1/calculate`, `/api/v1/assess` | DELETE | Две старые stateless HTTP-обёртки ручного rank/excluded/noConsent расчёта. В новом frontend и production worker нет клиентов. Не являются ML или статистикой текущего продукта |
| `AssessmentInput`, `ScenarioAssessment`, `assess_scenario` | DELETE | Только обёртка retired `/assess`; единственные иные потребители — её устаревшие тесты. Не путать с admissions.Assessment и source scenarios |
| `test_assessment.py`, `shared/assessment-cases.json` | DELETE | Проверяют удаляемый mock/manual assess API, нового frontend-клиента нет. Тесты source scenarios/history остаются |
| HTTP validation/body budget/origin tests | REFACTOR | Проверяют полезную инфраструктуру; перенести проверки с retired `/calculate` на действующие session/watch APIs, не удалять privacy/bounds coverage |
| Общий `CamelModel` внутри calculation.py | REFACTOR | Catalog, source APIs, backup и scenarios импортируют DTO base из старой арифметики. Вынести неизменный base в schema_base.py; расчёт не должен быть инфраструктурной зависимостью каталога |
| `calculate_versioned`, MANUAL_CALCULATORS, CalculationInput/Result | KEEP | main snapshot reader, импорт/экспорт сохранённых manual записей и history-version tests; удаление сделало бы существующие данные нечитаемыми |
| Watch/Snapshot/OperationRecord и старые CRUD/import/export | REFACTOR, без удаления сейчас | Есть реальные persistency/backup/retention связи, совместный direction budget с subscriptions, privacy и история. Причина сохранения — сохранность и доступность данных, не UI-совместимость. План вывода ниже |
| University/Campaign/CompetitionGroup, catalog artifacts/importer | KEEP | Нужны реальным четырём страницам; year/source/null validation и стабильные ID |
| Старый `/universities`, `/groups`, `/coverage` | KEEP | Первый объединяет operator/reference scope, groups раскрывает metadata/status архивов; v3 audited facade имеет другой контракт. Это не дубли одинакового результата |
| Source/SourceSnapshot/CandidateEntry, normalization, parsers/registry/profiles | KEEP | Проверенные источники, quarantine, scoped IDs, независимые attestations. Отсутствие frontend-клиента не делает pipeline устаревшим |
| Publishing/history/changes/scenarios/subscriptions | KEEP | Immutable factual history и scoped conditional list analysis. Не вероятность ML; не связаны с удаляемой AssessmentInput-обёрткой |
| Jobs/worker/leases/retry/fetch budgets/diagnostics | KEEP | Полезные фоновые механизмы и tests. Worker требует Linux resource/process limits; отсутствие Windows resource — ограничение платформы, не основание удаления |
| Backup/restore, ops, source research/capture/review/load/rehearsal scripts | KEEP | Защита существующих данных и доказательства нормализации/нагрузки. Load stand содержит реальную source-pipeline ветку, не только старый UI |
| SQLAlchemy models, Alembic 0001–0011 | KEEP, immutable | Существующие таблицы/версии БД. Никаких drop/truncate/down -v/rewrite миграций |
| Dockerfiles, Compose dev/prod, Nginx/Caddy | KEEP / минимальная очистка build context | Один текущий backend и PostgreSQL. .npm-cache/.qa-tools не должны попадать в Docker context; volumes и network model сохраняются |
| CI | KEEP / уточнить проверки | Актуальные Node/browser checks и независимый PostgreSQL job. Native тесты не объявлять пройденными по SQLite |
| Исторические evidence/passports/tasks | KEEP | Доказательства и история; не переписывать статусы done или immutable profile SHA. Активные README/architecture/product/API/roadmap должны описывать текущий продукт |
| T051–T055, T060–T065 | DEFER | Старый автоматизированный MVP/release и будущие расширения требуют новых критериев v3; ML запрещён до данных/метрик. Не отмечать выполненными |

## Инфраструктура

Выполнены `docker compose -f compose.yaml config --quiet` и попытка
`docker compose -f compose.yaml up -d db`. Запуск упирается в запрет доступа
к `npipe:////./pipe/docker_engine`; Docker config также выдаёт Access denied.
Не меняются DOCKER_HOST/config, привилегии или sandbox. Состояние PostgreSQL
не подтверждено; запуск/миграции/API/browser через Compose остаются блокером
T250, а не успешной проверкой. SQLite может подтвердить application behavior,
но не native PostgreSQL и Docker smoke.

## План потенциально необратимого вывода legacy persistence

Автоматического удаления на этом этапе нет. Перед отдельным решением:

1. В доступном PostgreSQL инвентаризовать Watch/Snapshot/operations и связи
   владельцев, сроки хранения; не выводить персональные строки в отчёт.
2. Сделать backup средствами существующего контура и восстановить его в
   изолированную БД. Проверить counts, FK, timestamp/model_version и историю.
3. Определить чтение/экспорт/удаление legacy-данных и совместный лимит с
   subscriptions. Запрет новых записей — отдельное изменение API/политики,
   не случайный побочный эффект очистки.
4. Только после утверждения data-retention решения подготовить **новую**
   миграцию. Применённые миграции не менять. Нужен проверенный rollback /
   restore plan; удаление volume и каскадное уничтожение данных запрещены.

## Проверка сохранности

До изменений сохранены hashes frontend/src, миграций и существующей local DB:
[baseline](evidence/foundation-cleanup/baseline.json). После очистки проверить
неизменность render-кода/CSS (кроме удаления dead routeLabels), миграций/DB,
build assets и все 29 runtime маршрутов. Точный перечень удалённых файлов,
выполненные проверки и ограничения — в итоговом evidence.
