# Архитектура AdmitFlow

Текущий контур React v3 и FastAPI, сверено с `main@a3f5078` 21 ноября 2026 года.
[Эксплуатация](RUNBOOK.md) · [Публичные контракты](API.md)

| Слой | Реализация / ответственность |
| --- | --- |
| Frontend entry/router | `src/main.tsx`, App, History API navigation; 29 исходных страниц + алиас списка конкурсов |
| UI | Исходные `components/`, `shared/UI.tsx`, Shell, styles.css/internal.css v3; неизменный визуальный эталон |
| Catalog | `src/catalog/types`, api, cancellable state, parts и четыре композиции; loading/error/empty, ID/year/source |
| Demo | AppPages/AuthPages/data/demo только при явном mode=demo; отсутствующие feature API показывают unsupported |
| HTTP | FastAPI main, origin/body/timeout/host protection, гостевая изоляция, no-store |
| Общие DTO | `schema_base.CamelModel`; каталог и pipeline не зависят от старой арифметики |
| Product catalog | `product_catalog` и DTO: справочник MICCEDU/аккредитации, проверенные архивные конкурсы СГУ и текущие опубликованные ревизии программ |
| Persistence | PostgreSQL, SQLAlchemy: University, Campaign, Program, CompetitionGroup, явные M:N связи, ревизии документов, snapshots списков, подписки и задания |
| Импорт программ | `program_catalog_batch` для ограниченного захвата и отдельной публикации. `program_catalog_import` сверяет исходник и переключает указатель в транзакции на документ |
| Списки и worker | Аттестованные профили, проверки scope/полноты, отдельный fetch/parser/publish, история и очередь с lease/backoff |
| Аккаунты | `account_api` и `account_mail`, отзывные сессии, подтверждение email и восстановление. Включение по `AUTH_ENABLED`, гостевой контур независим |
| Operations | Миграции, backup/restore, retention, diagnostics/ops; старые сохранённые данные защищены |

Единственный Alembic head — `0014`. `0012` вводит хранение аккаунтов и их
сессий. `0013` добавляет идентичности программ и явные связи с кампаниями и
конкурсами. `0014` добавляет версии исходных документов и фактов, журнал
импорта и указатели опубликованных ревизий. Прежние ID сохраняются.
Применённые миграции остаются неизменными. SQLite используется в dev/test.
Проверка миграций и конкурентного поведения PostgreSQL выполняется отдельно.
[Миграции](../backend/alembic/versions) · [CI](operations/ci.md)

HTTP выдаёт новые программы после явной публикации verified-ревизии.
Поиск, подсчёт и пагинация списка выполняются в SQL, в PostgreSQL внутренние
запросы каталога читают согласованный снимок. `id` сохраняет идентичность
публичного маршрута. `programId` отдельно обозначает программу, а
`competitionGroups` содержит подтверждённые связи. [Контракт](API.md#публичный-каталог-v3)

Обычный Compose сохраняет пользовательские volumes. Ранняя проверка Compose
на схеме `0011` остаётся датированным [доказательством](evidence/local-postgresql.md).
Команды текущего старта находятся в [runbook](catalog-runbook.md).

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

## Клиент API React v3

`shared/api.ts` — транспорт/ошибки/timeout/session epoch; `shared/dto.ts` и
`catalog/decode.ts` — проверка используемых DTO; `shared/resource.ts` и
`ResourceState` — отмена, loading/error/retry/stale/401. Каталог сохраняет прежние
композиции. LivePages/AddSource используют существующие subscriptions, changes,
coverage, groups и source lookup/confirm. Account UI использует отдельные auth
routes, а demo открывается по явному параметру `mode=demo`.
Матрица маршрутов и проверка: [evidence](evidence/v3-production-api.md).

KAN-212/S209: существующий request поддерживает типизированный json и Headers,
проверяет отмену/session epoch после body; конкретные decoders строят DTO без
generic casts. Resource очищает private данные при смене/истечении сессии и
авторитетных 403/404/410; при временном сбое сохраняет подтверждённые данные с
меткой stale. Public catalog/groups/coverage не зависят от владельца. Сессия
передаёт разные события change/expiry между вкладками, без автоматического POST
и циклов повторов. Router остаётся History API; ID декодируется один раз,
auth имеет точный allowlist, query/hash/history сохраняются. Дизайн/CSS прежние.
Актуальная матрица, ограничения и проверка: [отчёт KAN-212](KAN-212-FRONTEND-REPORT.md).
