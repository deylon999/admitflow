# API AdmitFlow

Сверено с `main@a3f5078` 21 ноября 2026 года. FastAPI использует JSON camelCase,
даты с timezone и `null` для неизвестных фактов. Локальная OpenAPI-схема
генерируется приложением на `/api/openapi.json`. В production OpenAPI отключена
в приложении и закрыта публичным proxy. Ответы API используют `Cache-Control: no-store`. Записи
требуют same-origin и `X-Requested-With: abiturient`.

## Публичный каталог v3

| Метод / путь | Параметры и результат |
| --- | --- |
| GET `/api/v1/catalog/universities` | q/region ≤120, offset 0..100000, limit 1..50 (12 default), sort name/name-desc; items/total/nextOffset/regions/registryEdition/accreditationDate |
| GET `/api/v1/catalog/universities/{id}` | stable ID, name/legalName/region/isBranch/officialUrl, provenance, knownProgramCount, years, accreditation либо null; additive displayName/displayNameSource/nameAliases/branchInfo |
| GET `/api/v1/catalog/programs` | q/universityId/year/subject, offset/limit/sort; items/total/nextOffset/years/subjects |
| GET `/api/v1/catalog/programs/{id}` | campaign-scoped ID, вуз/код/название, year, форма/funding/category/seats, provenance; examRequirements: испытания по порядку документа, варианты на выбор, minScore или null, additionalTests ([] = нет, null = не собрано), benefits всегда null, notes, source (url, дата документа, sha256, дата проверки, сверка). null, если проверенных правил для этого года, кода и формы нет. historicalCutoff/forecast пока null |

Unknown ID →404, invalid filters →422. Year 2000..2100, отсутствие совпадения
не подменяется другой кампанией. `knownProgramCount` и `years` учитывают
записи публичного каталога, включая сохранённые архивные конкурсы. Это
подтверждённая часть перечня вуза. `subjects` пока пуст, заданный предмет
не совпадает с unknown.

Provenance: url, verifiedAt, sourceUpdatedAt nullable, kind monitoring/archive/
accreditation/admissions, edition и originalSha256 при наличии. Review/capture date не называется
датой публикации. MICCEDU edition 2025 не равен кампании поступления 2026.
`id` остаётся ключом маршрута. `programId` — отдельная идентичность программы
или null для старого архивного конкурса без одной явной связи. `competitionGroups`
содержит подтверждённые конкурсы с собственными ID и provenance или `[]`.
`code`, `studyForm`, `funding`, `category` и `seats` допускают null, если
условие не подтверждено. [Согласование и полный пример](sources/program-catalog/contract.md).

После миграций старый архивный набор устанавливает `python -m app.catalog_import`.
Оператор публикует проверенный документ через `python -m app.program_catalog_import`
или выполняет [пакетную публикацию](KAN-218-PR3.md#запуск-и-восстановление).
Только текущие verified-ревизии участвуют в публичном чтении. Исходные документы,
черновики, заменённые ревизии и ошибки разбора остаются внутри системы.

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

Точный актуальный набор маршрутов задаёт OpenAPI запущенного backend.
[Инвентарь этапа очистки v3](evidence/foundation-cleanup/api-inventory.json)
сохраняет датированный срез до последующих изменений.
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

## Клиент React v3

Единый клиент и runtime DTO используют только существующие контракты.
Гостевой POST session выполняется по явному действию, 401 не вызывает
автоматический restart. Подписки читаются/удаляются по настоящему ID, добавление
идёт через source lookup/confirm. History/notifications читают changes, sources —
coverage. Account UI использует отдельные auth endpoints. Отдельные API
прогноза и подбора по ЕГЭ не реализованы. Подтверждённые требования ЕГЭ
читаются из карточки программы при точном совпадении условий.
Датированный frontend smoke: [T253](evidence/v3-production-api.md).

KAN-212/S209: публичные backend DTO не менялись. Frontend дополнительно проверяет
ISO calendar dates, идентификаторы, rank/count/null и обязательные потребляемые
nested поля; catalog ID/year/universityId ответа должны соответствовать запросу.
Неизвестные admission факты остаются null. HTTP 401 не создаёт гостя автоматически.
Проверки маршрутов и негативных сценариев KAN-212: [отчёт](KAN-212-FRONTEND-REPORT.md).

## Аккаунты и почта

Текущие операции под `/api/v1/auth` определены в
[account_api.py](../backend/app/account_api.py). Флаг `AUTH_ENABLED` по
умолчанию `false`. Включению нужен стабильный `AUTH_RATE_KEY`. Гостевые
сессии `/api/v1/session` живут отдельно от аккаунтов.

| Операция | Метод и суффикс |
| --- | --- |
| Получение CSRF и чтение сессии | `GET /csrf`, `GET /session` |
| Регистрация и вход | `POST /register`, `POST /login` |
| Ротация токенов и выход | `POST /refresh`, `POST /logout` |
| Подтверждение адреса | `POST /verification/request`, `POST /verification/confirm` |
| Восстановление доступа | `POST /recovery/request`, `POST /recovery/confirm` |

Изменяющие операции используют связанный CSRF-контекст и лимиты. Refresh
ротирует credentials, logout отзывает текущую семью сессии. Email-запросы
возвращают общий `202` при успешной обработке, ошибка транспорта — `503`.
Подтверждение и сброс возвращают `204` без автоматического входа. Сброс
отзывает сессии пользователя. Frontend включает экраны входа, подтверждения
и восстановления. [Проверенные контракты React](KAN-214-PR5.md#final-implementation-and-contracts-t299)

SMTP по TLS включается явной [конфигурацией](operations/smtp.md).
Автоматические тесты с записью почты подтверждают сценарии, а внешняя SMTP
доставка и HTTPS staging требуют отдельных доказательств. Поэтапная история
контрактов находится в отчётах [PR2](KAN-214-PR2.md), [PR3](KAN-214-PR3.md) и
[PR4](KAN-214-PR4.md).
