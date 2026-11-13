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
| GET `/api/v1/catalog/programs/{id}` | campaign-scoped ID, вуз/код/название, year, форма/funding/category/seats, provenance; examRequirements: испытания по порядку документа, варианты на выбор, minScore или null, additionalTests ([] = нет, null = не собрано), benefits всегда null, notes, source (url, дата документа, sha256, дата проверки, сверка). null, если проверенных правил для этого года, кода и формы нет. historicalCutoff/forecast пока null |

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

## React v3 binding — S202

Единый клиент и runtime DTO используют только существующие контракты.
Гостевой POST session выполняется по явному действию, 401 не вызывает
автоматический restart. Подписки читаются/удаляются по настоящему ID, добавление
идёт через source lookup/confirm. History/notifications читают changes, sources —
coverage. Account/forecast/EGE/profile feature API по-прежнему отсутствуют.
Контрактный frontend smoke и границы: [T253](evidence/v3-production-api.md).

KAN-212/S209: публичные backend DTO не менялись. Frontend дополнительно проверяет
ISO calendar dates, идентификаторы, rank/count/null и обязательные потребляемые
nested поля; catalog ID/year/universityId ответа должны соответствовать запросу.
Неизвестные admission факты остаются null. HTTP 401 не создаёт гостя автоматически.
Актуальные 29 маршрутов и негативные сценарии: [отчёт](KAN-212-FRONTEND-REPORT.md).

## KAN-214 PR2 account API (disabled by default)

`AUTH_ENABLED=false` by default. Enabled auth requires a stable `AUTH_RATE_KEY`;
existing production HTTPS/PostgreSQL/Secure guards remain. Separate guest API
`/api/v1/session` and owner_hash contracts are unchanged.
Implemented `/api/v1/auth/csrf` GET, `/register` POST, `/login` POST, `/session` GET.
DTOs, statuses, rate policy, CSRF and safe rollout: [KAN-214-PR2.md](KAN-214-PR2.md).
No refresh/logout/confirmation/recovery endpoint yet. Without a registration mail
transport, register returns503 globally rather than claiming email delivery.
Do not enable the incomplete lifecycle for production users before PR3-6 acceptance.
