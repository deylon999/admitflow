# Архитектура AdmitFlow

Актуально на S202, 2026-11-10. Один frontend и один backend; новая БД,
сервис или миграция при очистке не создавались.

| Слой | Реализация / ответственность |
| --- | --- |
| Frontend entry/router | `src/main.tsx`, App, History API navigation; 29 исходных страниц + алиас списка конкурсов |
| UI | Исходные `components/`, `shared/UI.tsx`, Shell, styles.css/internal.css v3; неизменный визуальный эталон |
| Catalog | `src/catalog/types`, api, cancellable state, parts и четыре композиции; loading/error/empty, ID/year/source |
| Demo | AppPages/AuthPages/data/demo только при явном mode=demo; отсутствующие feature API показывают unsupported |
| HTTP | FastAPI main, origin/body/timeout/host protection, гостевая изоляция, no-store |
| Общие DTO | `schema_base.CamelModel`; каталог и pipeline не зависят от старой арифметики |
| Product catalog | product_catalog + DTOs, проверенный national artifact, явный atomic catalog_import |
| Persistence | SQLAlchemy University/Campaign/CompetitionGroup, Source/Snapshot/entries, subscriptions/history/jobs; PostgreSQL |
| Pipeline | Reviewed parser profiles/registry, normalized scoped IDs, fetch budgets, quarantine, publishing, history, worker leases/retry |
| Operations | Миграции, backup/restore, retention, diagnostics/ops; старые сохранённые данные защищены |

Applied Alembic 0001–0011 неизменны. SQLite — изолированный dev/test контур,
не доказательство совместимости native PostgreSQL. Обычный Docker Compose
сохраняет существующие volumes. PostgreSQL и контейнеры в текущем sandbox
не удалось запустить из-за запрета Docker Engine.

Старые stateless `/calculate` и `/assess` удалены. Версионированная арифметика
остаётся только для сохранённых manual snapshot/import/export, а не модели
поступления. Legacy storage APIs пока нужны истории, приватности, backup и
совместному лимиту направлений; их дальнейший вывод требует отдельного
[плана данных](foundation-cleanup-audit.md).

Build: Vite/esbuild + tsc, без неиспользуемого plugin-react. Один Node
Playwright runner владеет временным API и previews и штатно останавливает их.
Тесты не перезаписывают исторические evidence по умолчанию. Linux-worker
проверяется в Linux/CI: POSIX resource limits не эмулируются на Windows.

[API](API.md) · [Аудит модулей](foundation-cleanup-audit.md) ·
[Проверки](evidence/foundation-cleanup.md).
Прежняя FSD/ручная архитектура сохранена в
[архиве](archive/architecture-before-foundation.md); она не описывает v3.

## Production frontend API (T253)

`shared/api.ts` — транспорт/ошибки/timeout/session epoch; `shared/dto.ts` и
`catalog/decode.ts` — проверка используемых DTO; `shared/resource.ts` и
`ResourceState` — отмена, loading/error/retry/stale/401. Каталог сохраняет прежние
композиции. LivePages/AddSource используют существующие subscriptions, changes,
coverage, groups и source lookup/confirm; новые feature API не создаются.
Матрица маршрутов и проверка: [evidence](evidence/v3-production-api.md).
