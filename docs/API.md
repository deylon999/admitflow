# API AdmitFlow

Актуально на S201. Один FastAPI backend, JSON camelCase, даты с timezone,
unknown facts — null. Dev OpenAPI: `/api/openapi.json`; production docs закрыты.
Все ответы no-store; записи требуют same-origin и X-Requested-With: abiturient.

## Публичный каталог v3

| Метод / путь | Параметры и результат |
| --- | --- |
| GET `/api/v1/catalog/universities` | q/region ≤120, offset 0..100000, limit 1..50 (12 default), sort name/name-desc; items/total/nextOffset/regions/registryEdition |
| GET `/api/v1/catalog/universities/{id}` | stable ID, name/legalName/region/isBranch/officialUrl, provenance, knownProgramCount, years |
| GET `/api/v1/catalog/programs` | q/universityId/year/subject, offset/limit/sort; items/total/nextOffset/years/subjects |
| GET `/api/v1/catalog/programs/{id}` | campaign-scoped ID, вуз/код/название, year, форма/funding/category/seats, provenance; historicalCutoff/examRequirements/forecast пока null |

Unknown ID →404, invalid filters →422. Year 2000..2100, отсутствие совпадения
не подменяется другой кампанией. knownProgramCount — число подтверждённых
импортированных конкурсов, не весь перечень программ вуза. Требования ЕГЭ
неизвестны: subjects пуст, заданный предмет не совпадает с unknown.

Provenance: url, verifiedAt, sourceUpdatedAt nullable, kind monitoring/archive,
edition и originalSha256 при наличии. Review/capture date не называется
датой публикации. MICCEDU edition 2025 не равен кампании поступления 2026.
Явный атомарный metadata import: `python -m app.catalog_import` из backend
после миграций. Без него программы пусты; sources/worker не включаются.

## Сохранённые механизмы

| Группа | Действующие контракты / смысл |
| --- | --- |
| Health | GET `/api/live`, `/api/health`, `/api/ready`; operational `/api/status` не открыт публичным proxy |
| Операторский каталог | GET `/api/v1/universities`, `/groups`, `/coverage`; operator/reference и source-status scope отличается от audited facade |
| Source metadata | GET `/api/v1/sources/{id}/status`, `/checks`; freshness/архив/ошибка не смешиваются |
| Гостевой доступ | POST/GET/DELETE `/api/v1/session`; HttpOnly SameSite cookie, owner isolation |
| Подписки и факты | POST source lookup/confirm, GET/POST/DELETE subscriptions, source history/archive-export, direction-budget; без публичных персональных досье |
| Условные сценарии списков | GET subscription scenario/scenario-history/scenario by assessment ID; versioned допущения, **не ML probability** |
| События | GET changes, POST change seen; scoped private history |
| Legacy persistence | Watches/snapshots/history, manual export/import остаются для истории, приватности, backup/retention и совместного бюджета; текущий v3 их не вызывает |

Точные пути/методы перечислены в
[машинном инвентаре](evidence/foundation-cleanup/api-inventory.json).
Существующие legacy data contracts не удаляются вместе с таблицами без
[отдельного плана данных](foundation-cleanup-audit.md).

## Удалённые контракты

POST `/api/v1/calculate` и `/api/v1/assess` удалены: это старые stateless
ручные rank/excluded/noConsent обёртки, не калькулятор ЕГЭ v3 и не ML.
Их нет в OpenAPI; валидный same-origin запрос с обязательным header получает
404. Неправильный origin/header отклоняется общей middleware до маршрутизации.
AssessmentInput/ScenarioAssessment и их fixture-only wrapper tests удалены.
`admissions.Assessment`, source scenarios и история не удалены.

Версионированная ручная арифметика сохранена для чтения/импорта ранее
сохранённых snapshot. Common CamelModel вынесен в `schema_base.py`;
DTO каталога не зависят от этой арифметики. Публичного forecast API нет.

Исторический полный контракт прежнего продукта:
[api-before-foundation](archive/api-before-foundation.md).
