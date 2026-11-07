# Frontend AdmitFlow: Feature-Sliced Design

**Функциональный срез S200:** дизайн и History API router v3 сохранены.
`src/catalog/` содержит DTO, API-клиент, cancellable resource/filter state,
UI parts и четыре композиции. Они используют исходные shared/UI и Shell;
старый FSD/калькулятор не возвращаются. Vite/Nginx дают same-origin `/api`.
Новый read facade `backend/app/product_catalog.py` публикует только reference
организации и совпадающие с reviewed metadata группы. Явный атомарный importer
использует существующие University/Campaign/CompetitionGroup, без новой схемы
или источников/worker. Старые backend-контракты независимы и сохранены.
[Модели, API, зависимости и границы](product-functional-audit.md).

**Актуальное состояние с T242 (2026-11-08):** по прямому запросу пользователя
frontend полностью заменён исходной структурой v3: `App.tsx`, `app/`,
`components/`, `pages/`, `shared/UI.tsx`, `data/demo.ts`, два исходных CSS.
React Router/React Query/FSD и бизнес-логика прежнего frontend удалены из
активного приложения. Работает оригинальный History API router; backend
не подключён. Ниже сохранено описание прежней архитектуры как история.
[Файлы, запуск и доказательства точного копирования](evidence/frontend-v3-exact.md).

Миграция T230 начата с чистого commit `3f8eee8`. Функциональность, DOM,
дизайн, backend API и правила расчёта сохраняются. Стек React/TypeScript,
React Query, React Router и обычный CSS остаётся прежним. По указанию
пользователя коммиты и push в этом подходе не выполняются.

Основание: официальные [слои](https://fsd.how/docs/reference/layers/),
[публичные API](https://fsd.how/docs/reference/public-api/),
[миграция](https://fsd.how/docs/guides/migration/from-custom/) и
[TanStack Query](https://fsd.how/docs/guides/tech/with-react-query/).

## Границы после аудита

- `app`: запуск, маршруты, lazy loading, shell, query provider, обработка
  глобальных ошибок/изменения гостевого доступа и глобальные стили.
- `pages/landing`, `pages/tracker`, `pages/sources`: композиция конкретных
  экранов. Локальные секции лендинга и координация нескольких действий
  остаются в странице. Widgets добавляются только при реальном повторном
  использовании крупной композиции.
- `features`: осмысленные сценарии расчёта, редактирования/восстановления,
  удаления, импорта/экспорта/печати, сравнения и истории, управления доступом,
  поиска/сохранения записи источника и просмотра сохранённых сценариев.
- `entities/manual-direction`: Watch/Snapshot, ручная формула, строгие
  контракты, сравнение и представления расчёта. `university`: справочник
  и контролируемые варианты выбора. `admission-source`: группы, provenance,
  сохранённые записи источников, история фактов и покрытие.
  `admission-scenario`: сохранённые условные сценарии и связанные изменения.
- `shared`: HTTP/таймаут/лимиты, технический singleton гостевого доступа,
  общая валидация, JSON/time/text/download и универсальное подтверждение.
  Здесь нет формул, Watch, SourceGroup или предметных API агрегаторов.

Импорты направлены `app → pages → features → entities → shared`.
Слайсы одного слоя изолированы. Снаружи используются явные `index.ts`,
внутри слайса — относительные импорты. Общий barrel всего слоя запрещён.
`@/` указывает на `src`. Привязанные к странице композиции не выносятся
в widgets только ради заполнения слоя. Сущности связаны на верхних слоях;
общие валидаторы не должны создавать ложные связи сущностей.

## Инварианты миграции

Сохраняются query keys, idempotency keys, expected snapshot headers,
session epoch/Web Locks и единственный экземпляр классов ошибок. Отмена
чтения не отменяет bootstrap других потребителей. Public catalog не
создаёт гостя. Старые private данные скрываются/очищаются при reset и смене
доступа. Черновик сохраняет TTL и ключ уже отправленного запроса.

Открытые/закрытые архивные истории обновляются явно; immutable comparison
не переписывается. Отсутствие строки не означает отказ; unknown остаётся
unknown. Квота20 включает ручные и архивные направления, JSON/сравнение/
печать — только ручные. Печать использует отфильтрованный список и актуальное
время beforeprint. Классы, labels, тексты, focus и accessibility сохраняются.

Этапы и фактические проверки: [evidence](evidence/fsd-migration.md).

## Backend и хранение

FastAPI создаётся в `backend/app/main.py`; там подключаются ручные маршруты,
`source_api.py`, `scenario_api.py` и `changes.py`. HTTP-контракты — [API.md](API.md).
SQLAlchemy-модели ручного пути и ownership находятся в `database.py`,
предметные University/Campaign/CompetitionGroup/Source, версии списков,
подписки, assessments и события — в `admissions.py`; задания/leases — в `jobs.py`.
Схема развивается миграциями, а не редактированием опубликованных снимков.

| Область | Реализация | Граница ответственности |
| --- | --- | --- |
| Ручные направления и импорт | `main.py`, `operations.py`, `importing.py`, `calculation.py` | Ownership, транзакции, идемпотентность; отдельный manual-v1 |
| Каталоги | `national_catalog.py`, `source_catalog.py`, `source_catalog.py::groups` | Справочник вузов отдельно от подключённых источников; SQL after/limit для групп |
| Источники | `sources/`, `worker.py`, `jobs.py` | Закрытый registry, безопасная загрузка, валидация, leases и публикация |
| Подписки и факты | `source_api.py`, `source_history.py`, `source_tokens.py` | Подтверждённый lookup, ownership и неизменяемая история |
| Условные сценарии и изменения | `scenarios.py`, `scenario_storage.py`, `scenario_api.py`, `changes.py` | Сохранённые версии; чтение не пересчитывает и не подтверждает событие |
| Эксплуатация | `maintenance.py`, `backup.py`, `diagnostics.py`, `observability.py` | Очистка, восстановление, безопасная диагностика |

Worker получает задание с lease, загружает источник через безопасный fetcher,
применяет зарегистрированный адаптер и проверки, затем публикует согласованную
версию в транзакции. Неуспешная проверка не делает неполный список текущим.
Сырые ответы хранятся приватно; строки списка не копируются заново в каждый Watch.
Факты архива и ручная формула не объединяются в обещание поступления.

## Развёртывание и ограничения

`compose.yaml` и `compose.prod.yaml` описывают API, worker, PostgreSQL и frontend;
production предусматривает HTTPS reverse proxy. Наличие конфигурации не означает,
что внешний сервис уже выпущен. Конкретные команды — [RUNBOOK.md](RUNBOOK.md),
условия выпуска — [RELEASE_GATES.md](RELEASE_GATES.md), семантика — [DATA_RULES.md](DATA_RULES.md).

Предыдущий проектный план сохранён в [архиве](archive/architecture-before-fsd.md).
Его старые пути и будущие формулировки не описывают текущую реализацию.
