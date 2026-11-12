# KAN-212 — стабилизация React v3

Дата аудита: 2026-11-13. Ветка `fix/kan-212-stabilization` от `origin/main`
`07526c3`. Последние merged PR: [#12](https://github.com/deylon999/admitflow/pull/12)
(CI), [#11](https://github.com/deylon999/admitflow/pull/11) (каталог/гость),
[#9](https://github.com/deylon999/admitflow/pull/9) (контракт examRequirements).
Исторический frontend/API PR [#4](https://github.com/deylon999/admitflow/pull/4)
уже в main. Его механизмы переиспользуются.

## Аудит до изменений

Прочитаны App, navigation, RouteLink, Shell, shared API/DTO/resource/ResourceState,
catalog API/decode/state/types/pages/parts, pages, demo, inventory и тесты.
Контракты сверяются с `backend/app/main.py`, `product_catalog_schemas.py`,
`competition_api.py`, guest lookup/subscriptions/changes и national coverage.
Один fetch уже существует; каталог, отмена useResource, opt-in demo,
гостевая сессия по действию пользователя, error/retry и cursor событий работают.
Статические страницы и отсутствие будущих feature API дефектами не считаются.

Baseline: `npm ci` exit 0; `npm test` **94 passed**, 0 skipped/failed (20.1 s).
Тестовый runtime использует временную SQLite; это browser contract stand,
не доказательство PostgreSQL-интеграции. Последняя будет проверена отдельно.

Подтверждённые исходниками пробелы и минимальные исправления:

| ID | Дефект | Исправление / проверка |
| --- | --- | --- |
| A01 | Проверка session epoch только после headers; тело старого ответа может прийти после смены владельца | Проверять epoch и отмену перед выдачей DTO; гонка на body в тесте |
| A02 | Сессия меняется в другой вкладке, но локальные приватные mutation/results не защищены после body; start не уведомляет свою вкладку | Единое событие смены сессии, очистка приватного состояния и отмена mutation |
| A03 | HeadersInit распространяется как object, Headers/tuples теряются; JSON пишется в компонентах | Headers API и типизированное JSON body в существующем request; никаких автоматических retries POST |
| A04 | Date.parse принимает нормализованную неверную дату; пустые IDs, нулевой rank, отсутствующие обязательные nested counters проходят | Строгие date/identifier/year/positive helpers, полные проверки потребляемых DTO и null |
| A05 | Catalog generic разрешает caller объявить произвольный T; provenance checksum не проверен | Decoder возвращает конкретные типы; hook принимает Decoder; сохранить provenance |
| A06 | Неизвестный auth URL открывает login; malformed percent encoding роняет route; public IDs не декодируются | Точный allowlist auth, безопасное однократное декодирование ID, 404 |
| A07 | Hash-навигация теряет изменённый query/history, startsWith(origin) и игнорирование defaultPrevented перехватывают лишние ссылки | Сравнение URL origin, корректная history/query/hash, уважение native anchor semantics |
| A08 | После сохранения subscription ID отправляется в competitions/{groupId} | Ссылка watchlist/{subscriptionId}; E2E lookup/confirm/detail |
| A09 | Индекс конкурсов загружает только первые 50 groups; пустая отфильтрованная страница объявляет отсутствие списков вообще | Cursor navigation и честное пустое состояние текущей страницы |
| A10 | Competitors скрывает ошибку metadata запроса; разные private страницы используют один экземпляр state | ResourceState metadata + summary; remount по пути, очистка приватного состояния при session change |

## Матрица исходных 29 маршрутов

Режим — при обычном открытии. Demo доступен только по явному `mode=demo`.
Для API-строк ошибки проходят ApiError → ResourceState, loading/error/retry,
пусто только после валидного ответа. Для Static/Unsupported запросы не нужны.
Динамические примеры не считаются существующими backend ID.

| URL | Назначение | Режим | Endpoint / DTO | Ошибки | Навигация / параметры | Дефект / решение |
| --- | --- | --- | --- | --- | --- | --- |
| `/` | Лендинг | Static | —; числовые примеры отмечены demo | — | anchors, CTA | A07 |
| `/universities` | Каталог вузов | Live | catalog/universities / UniversityResults | ResourceState | q, region, sort, offset | A04/A05/A07 |
| `/universities/sgu-saratov` | Вуз и программы | Live | catalog/universities/{id}, catalog/programs / University, ProgramResults | 404, ResourceState | id, year, offset | A04/A05/A06 |
| `/programs` | Каталог программ | Live | catalog/programs / ProgramResults | ResourceState | q, subject, year, universityId, sort, offset | A04/A05/A07 |
| `/programs/sgu-2026-4588` | Условия программы | Live | catalog/programs/{id} / CatalogProgram | 404, ResourceState | id | A04/A05/A06 |
| `/ege-analytics` | Аналитика ЕГЭ | Unsupported | — | Нет feature API | opt-in Demo | Сохранить |
| `/how-it-works` | Информация | Static | — | — | ссылки | Сохранить |
| `/faq` | Вопросы | Static | — | — | FAQ | Сохранить |
| `/auth/login` | Вход | Unsupported | — | Нет account API | точный auth route, Demo | A06 |
| `/auth/register` | Регистрация | Unsupported | — | Нет account API | точный auth route, Demo | A06 |
| `/auth/recovery` | Восстановление | Unsupported | — | Нет account API | точный auth route, Demo | A06 |
| `/app` | Обзор подписок | Live | subscriptions / Subscription[] | 401, ResourceState | ссылки subscription/group, Demo | A01/A02/A04/A10 |
| `/app/profile` | Профиль | Unsupported | — | Нет feature API | Demo | Сохранить |
| `/app/forecast` | Ввод ЕГЭ | Unsupported | — | Нет feature API | Demo | KAN-223 отдельно |
| `/app/forecast/example` | Пример прогноза | Unsupported | — | Нет feature API | Demo | Сохранить явную маркировку |
| `/app/forecast/method` | Пример методики | Unsupported | — | Нет feature API | Demo | Сохранить |
| `/app/watchlist` | Подписки | Live | subscriptions / Subscription[] | 401, ResourceState | Demo изолирован, delete | A01/A02/A04/A10 |
| `/app/watchlist/add` | Поиск и подписка | Live | groups, sources/{id}/lookup, subscriptions / Group, lookup, saved | 401/409/410/422, ResourceState | q, cursor, подтверждение | A02/A04/A08 |
| `/app/competitions/mtuci-se` | Список по group ID | Live | competitions/{id}, rows / CompetitionInfo, CompetitionRow | 404, ResourceState | id, фильтры, пагинация; opt-in Demo | A04/A06 |
| `/app/competitions/mtuci-se/competitors` | Анализ конкурса | Unsupported | — для исторического design ID | Нет объекта/API для design ID | Demo; реальные ID → summary | A06/A10 |
| `/app/compare` | Сравнение | Unsupported | — | Нет feature API | Demo | Сохранить |
| `/app/history` | События подписок | Live | changes / Events | 401, ResourceState | before cursor | A01/A02/A04/A10 |
| `/app/notifications` | События подписок | Live | changes / Events | 401, ResourceState | before cursor | A01/A02/A04/A10 |
| `/app/settings` | Настройки | Unsupported | — | Нет feature API | Demo | Сохранить |
| `/app/sources` | Доступность источников | Live | coverage / coverage | ResourceState | /app/coverage | A04 |
| `/app/states/empty` | Образец empty | Unsupported | — | Только Demo | opt-in | Сохранить |
| `/app/states/error` | Образец error | Unsupported | — | Только Demo | opt-in | Сохранить |
| `/app/states/success` | Образец success | Unsupported | — | Только Demo, не операция | opt-in | Сохранить |
| `/not-found` | Неизвестная страница | Static | — | 404 UI | каталог | A06 |

Дополнительные уже существующие маршруты: `/app/competitions` (groups,
CompetitionGroup, A09), `/app/watchlist/{id}` (subscriptions, A06/A08),
`/app/competitions/{id}/competitors` (competition + summary, A10),
`/app/coverage` (coverage/national, NationalCoverage, A04). Они тоже сохраняются.

## План и критерии

T265: аудит, baseline и матрица до кода. T266: единый API и строгие DTO,
низкоуровневые негативные/конкурентные тесты. T267: session/server state,
mutation lifecycle и честные состояния существующих интеграций. T268:
маршрутизация/ссылки, 29 routes, dynamic/unknown/history. T269: итоговые
проверки, PostgreSQL, визуальная регрессия относительно исходного main,
PR и hosted checks. Review/merge выполняет владелец; до принятия KAN-212
не объявляется Done. Backend-контракты, CSS, миграции и данные не меняются.

## Результаты реализации и приёмки

T266: существующий request принимает Headers/tuples и типизированный `json`,
проверяет Content-Type точно, отмену и session epoch также после чтения body.
401 не создаёт сессию; session start/delete рассылает событие своей вкладке и
другим вкладкам. Ошибки decoder становятся 502, сеть/timeout различаются.
Автоматических повторов нет. DTO строятся из проверенных полей без `as unknown
as`; каталог принимает конкретный Decoder и проверяет ID/год/universityId
ответа относительно запроса. Provenance/checksums сохраняются. API backend не менялся.

Проверки T266: lint/typecheck/build exit 0, **27 unit + 94 существующих = 121
passed**, 0 skipped (повторный полный прогон). Первый полный прогон: 120 passed,
один `net::ERR_NO_BUFFER_SPACE` при page.goto, до выполнения приложения;
повтор без изменения теста прошёл. CSS asset совпадает с baseline:
`index-CE7INdrk.css`. Аудит и эти проверки не заменяют финальную приёмку.

T267: useResource отменяет активный приватный запрос и очищает данные при
session change/expiry; публичный каталог/groups/coverage не перезапрашиваются.
Событие смены сессии своей вкладки поддержано. Между вкладками expiry передаётся
отдельно от смены владельца: это исключает цикл взаимных 401/refetch. Lookup и
DELETE отменяются при уходе/смене сессии; старый результат не показывает успех.
Прямой add после 401 предлагает явный старт гостя и не повторяет POST автоматически.
Индекс groups использует after cursor; manual-only страница не объявляет весь
каталог пустым. Competitors показывает ошибки и metadata, и summary.

T267 verification: lint/typecheck и **131 tests passed**, включая две вкладки,
отменённый lookup, explicit guest recovery, pagination/history/reload и отказ
от программы другой кампании. Реальный Compose/PostgreSQL startup smoke exit 0,
backup/import/migrations/persistence подтверждены; текущий frontend ещё проверяется
против этого стека отдельно. Существующие volumes и история сохранены.

T268: allowlist auth, безопасное однократное decode ID, отсутствие demo fallback
для неизвестных competition ID, корректная ссылка watchlist/{subscriptionId}.
URL filters конкурса переживают reload/Back/Forward; hash переход сохраняет query
и history; download, target, foreign origin и prevented clicks не перехватываются.
Opt-in Demo сохраняет query/hash; явный выход из demo работает. Private страницы
получают key по пути, чтобы состояние соседнего экрана не переносилось.

T268 verification: **143 passed**, 0 skipped/failed (25.9 s), lint/typecheck pass.
Каждый из 29 маршрутов проверен прямым открытием, reload, внутренним переходом,
Back и Forward. Дополнительно unknown auth, encoded/malformed IDs, query/hash,
ссылка после реального по контракту тестового confirm и demo link isolation.
Начальный расширенный тестовый прогон выявил ошибку размещения тестовой ссылки
вне scroll container; исправлен harness, проверки и timeout не ослаблены.
Vite preview возвращает 500 на malformed percent encoding до React; такие пути
проверены клиентским переходом, nginx HTTP-граница проверяется отдельно в T269.

## Изменённые файлы и API/DTO

| Файлы | Изменение и причина |
| --- | --- |
| shared/api.ts | Единственный fetch; typed JSON/Headers, статусы, timeout/abort/body/session boundary |
| shared/dto.ts, catalog/decode.ts | Конкретные проверенные типы вместо generic casts; null, обязательные nested поля, даты/IDs/ranks/checksums; сохраняется metadata |
| catalog/state.ts, CatalogPages, DetailPages, api.ts | Hook принимает decoder; ответ ограничен ID/year/universityId запроса; удалена неиспользуемая generic обёртка |
| shared/resource.ts, ResourceState | Отмена/очистка при смене/истечении сессии, 403/404/410; временная ошибка оставляет валидные stale данные; session start только явно |
| App, navigation, RouteLink | Точные auth routes, безопасный ID, история/query/hash и native ссылки; прежний router сохранён |
| AddSource, LivePages, CompetitionPages | Mutation lifecycle, корректный subscription link, pagination, metadata errors, URL filters |
| api-unit/api/routes tests, playwright.config | 28 unit + негативные API + all-route/history/ID regression; существующие тесты сохранены |
| scripts/test.mjs | Дополнительный opt-in локальный API target; обычный CI stand прежний |
| scripts/compare-main.mjs | Сравнение 116 пар со свежим Git reference, без обновления baseline |
| scripts/verify-postgres.mjs, postgres-runtime.py | Реальный positive E2E в отдельной PostgreSQL БД с archive fixture; cleanup своих ресурсов |
| docs, README, inventory, roadmap | Матрица, evidence, инструкции, границы и передача review |

Backend source, schemas, parsers, applied migrations, shared historical fixtures,
CSS и GitHub Actions не изменены. Новых зависимостей нет. Проверены существующие
FastAPI contracts catalog universities/programs (включая KAN-219 exams), groups,
subscriptions, source lookup/confirmation, changes, competitions metadata/rows/
summary, coverage и coverage/national. `SourceStatus` отражается через group metadata,
warnings и национальный dashboard; отдельный новый source API не создан.

## Ошибки и состояния

| Проверка | Реакция |
| --- | --- |
| 400/401/403/404/409/410/422/429/500/503 | Контролируемое сообщение, без backend detail/stack; нет автоматического повтора POST |
| 401 | Приватные данные и token/code очищаются; явный guest start; две вкладки без циклов |
| 403/404/410 после success | Прежние записи удаляются из состояния; не показываются как доступные |
| Временный 5xx при refresh | Предыдущие валидные данные с меткой stale и retry |
| Network/timeout | Ошибка с retry, не empty и не вечная загрузка |
| Caller abort/unmount/быстрый переход | Запрос отменяется, старый ответ не перезаписывает экран |
| Неверный JSON/Content-Type/DTO/date/ID/rank/count | 502 и понятное error state, без успешной загрузки |
| Валидные []/null | Настоящее empty или «Нет данных», без выдуманного 0/false/процента |
| Demo/Unsupported | Только opt-in; нет скрытого fallback, серверного сохранения или успешного login |

## Финальные локальные проверки

Все npm-команды из frontend. Финальная последовательность `npm ci`, `npm run lint`,
`npm run typecheck`, `npm run build`, `QA_API_TARGET=http://127.0.0.1:8080 npm test`
завершилась exit 0: **146 passed, 0 failed/skipped, 27.0 s**, Chromium. Переменная
окружения в PowerShell задаётся через `$env:QA_API_TARGET`; см. frontend/README.
Обычный contract runtime ранее прошёл 143 теста; финальный обычный runtime прошёл
146 тестов в неизменном hosted frontend job. SHA/run указаны ниже.

`python scripts/local_smoke.py`: exit 0, PostgreSQL 17, Alembic **0011=head**, model
check/import/backup/persistence pass. После browser проверок повторно сравнен весь
контрольный набор protected history — хеши совпадают. Пользовательские volumes сохранены.

`node scripts/verify-postgres.mjs`: exit 0. Настоящие FastAPI + PostgreSQL и текущая
production-сборка, без HTTP intercept: guest start204 → groups → archive lookup
(rank3) → confirm201 → subscription detail → list50 → next/reload (rank51) → summary
(aboveMe2). Данные — существующий derived SGU archive fixture на 573 строки, **не
production capture**. Созданная БД и API-контейнер удалены. Официальные источники
в пользовательской БД не активировались. Raw score screenshots не публикуются.

Malformed percent URLs на настоящем nginx возвращают **400**, без stack trace;
переход к таким URL в SPA даёт 404 UI, без pageerrors. Оба уровня проверены.
`python scripts/roadmap.py --render --check` и `git diff --check` проходят.

Производительность: каталог продолжает получать страницы по 12 записей, groups по
20/50, rows по 50. Positive PostgreSQL scenario подтверждает переход 1–50 → 51–100
из 573, а не загрузку всего списка. Старые запросы отменяются; public данные не
перезагружаются при смене сессии. Production p95/масштаб 10k строк не измерялись;
спекулятивных оптимизаций и новых state dependencies нет.

## Визуальная проверка

`node scripts/compare-main.mjs 07526c3`: exit 0, **116/116 PNG пар побайтово
совпадают**: 29 маршрутов × 390/1440 × default/demo. Text equal, 0 pageerrors,
0 horizontal overflow. Свежий reference извлечён из Git, CSS asset по-прежнему
`index-CE7INdrk.css`; baseline не обновлялся. Для сравнения обеим версиям передавались
одинаковые read-only ответы локального API (временные timestamps зафиксированы).
Это visual replay, отдельный от настоящих PostgreSQL проверок выше.

Визуально просмотрены viewport-галереи всех 29 default экранов на 390/1440;
дополнительно полные PNG программы на обеих ширинах, Unsupported и guest state.
Кнопки, шрифты, палитра, header/sidebar и композиции сохранены. Полная UX/adaptive
приёмка остаётся KAN-213; исторический sibling comparator не объявляется новой
приёмкой live-экранов. Evidence: ignored frontend/test-results/compare-main-*;
компактные метрики — [kan-212-stabilization.json](evidence/kan-212-stabilization.json).

## Pull Request, ограничения и продолжение

Изменение оформляется одним follow-up PR к уже merged #4: небольшой согласованный
набор исправлений разбит на отдельные audit/API/state/navigation/regression коммиты.
API/session и routing исправления зависят друг от друга, поэтому самостоятельный
merge пяти веток не требуется. Review владельца и merge не выполняются агентом.
Ссылка и hosted проверки добавляются после открытия PR; KAN-212 до принятия остаётся
**In Review**, T269 не отмечается done.

Нерешённые продуктовые функции: account login/register/recovery (KAN-214), подбор
ЕГЭ (KAN-223), saved/ML и будущие API (KAN-222). Они честно Unsupported; отсутствие
этих API не блокирует стабилизацию. Национальное покрытие и живая кампания 2027 не
заявляются. Vite preview malformed-encoding HTTP500 — отдельная граница dev-server;
nginx безопасно возвращает400, React переход не падает. Новых дефектов production
frontend в выполненных сценариях не осталось. HTTPS deploy и приёмка owner не
подтверждены. Самостоятельный merge/force push не выполняется.

Основа для KAN-223/214/222 подготовлена: типизированный request+decoder, session
invalidation, cancellable resource, error/retry/unsupported и устойчивые маршруты.
Это совместимость для последующей интеграции, не реализация этих feature-задач.

## Передача на review

[PR #13](https://github.com/deylon999/admitflow/pull/13) открыт; merge не выполнялся.
Реализация проверена на SHA `dc5205c784eff44deaaef237ce701cf68203c141`.
Hosted [run 43313647129](https://github.com/deylon999/admitflow/actions/runs/43313647129):
**success**: frontend146, backend719/0skip, ETL55+1 explicit missing-dataset skip,
migrations0011/head/schema check. Review submissions на момент проверки отсутствуют.
Окончательный SHA документации/latest Checks — в
описании PR, чтобы этот отчёт не требовал бесконечной цепочки self-referencing SHA.

Дополнительная финальная проверка нашла public401 boundary: ApiError теперь
различает session-bound и public 401. Публичный каталог предлагает только GET retry,
не гостевую сессию; private 401 сохраняет явный guest recovery. Новый regression
подтверждает успешный retry и 0 session POST. После этого изменения локально
**147 tests passed (28.5 s)**, lint/typecheck/build pass и повторно **116/116**
visual pairs equal. Окончательный source SHA/latest hosted run — в описании PR13;
ранее завершённые hosted результаты выше относятся к первому набору dc5205c.

Локальный nginx обновлён текущей сборкой: JS asset побайтово совпадает с dist;
**58 direct openings** (29×390/1440), unknown auth404 и 0 pageerrors. Backend/db/
frontend healthy на http://127.0.0.1:8080; worker не запускался. Тестовые API,
preview и все временные тестовые БД/контейнеры удалены; пользовательский
стек оставлен работающим. Компактный evidence не содержит cookies, токенов,
публичных кодов поступающих или raw scores.
