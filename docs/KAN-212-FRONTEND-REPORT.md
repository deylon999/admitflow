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
