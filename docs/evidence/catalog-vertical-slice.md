# Каталог вузов и направлений: первый функциональный срез

2026-11-08, S200, T243–T247. Ветка `feat/catalog-vertical-slice` создана от
проверенной v3-копии a6d2f74. Предыдущие ветки и main сохранены; push нет.

## Что работает

Четыре React-композиции используют настоящий FastAPI, без demo fallback:

- `/universities` — 1257 организаций и филиалов датированного справочника
  MICCEDU 2025; поиск по названию/региону/подтверждённой программе, фильтр
  региона, сортировка, страницы по 12 записей.
- `/universities/{id}` — название, регион, источник, официальный сайт при
  его наличии, годы подтверждённых конкурсов и программы выбранного года.
  Число подтверждённых программ не выдаётся за весь перечень программ вуза.
- `/programs` — подтверждённые импортированные конкурсы; поиск по названию
  и коду, universityId, год, сортировка, API pagination. Предметы не выдуманы:
  подтверждённого справочника ЕГЭ нет, список subjects пуст; заданный через
  URL предмет не совпадает с неизвестными требованиями.
- `/programs/{id}` — конкурс конкретного года, код, форма, финансирование,
  число мест, ссылка и дата проверки. Стабильные ID включают кампанию.

Путь, проверенный без подмены успешных API-ответов:
`/universities?q=СГУ+Чернышевского` → `/universities/sgu-saratov` →
`/programs/sgu-2026-4588` → вуз → его каталог программ. Reload и браузерная
история работают. Loading/error/retry/404/empty отделены от успешной выдачи;
устаревший ответ поиска не заменяет текущий. HTML fallback вместо API
обрабатывается как ошибка. Гостевая сессия для публичного каталога не создаётся.

## Подтверждённые данные и ограничения

Справочник — сохранённая редакция участников мониторинга, **не полный реестр
всех лицензированных вузов России**. Источники URL/time/SHA сохранены в
`backend/app/data/national-catalog.json`. Проверены официальный
[индекс](https://monitoring.miccedu.ru/?m=vpo&year=2025) и
[карточка СГУ](https://monitoring.miccedu.ru/iam/2025/_vpo/inst.php?id=258).
Дата опубликованного обновления редакции — 03.02.2026. Даты capture не
переписаны на дату сегодняшней проверки индекса.

Первый импорт намеренно ограничен **двумя архивными конкурсами СГУ 2026**:

| ID | Направление | Общие бюджетные места | Источник / проверка |
| --- | --- | --- | --- |
| sgu-2026-4588 | 09.03.04 Программная инженерия | 16 | [Паспорт](../sources/sgu-4588.md), 03.11.2026 |
| sgu-2026-4576 | 02.03.03 Математическое обеспечение и администрирование информационных систем | 24 | [Паспорт](../sources/sgu-4576.md), 05.11.2026 |

Использованы metadata ранее проверенных official-source профилей и независимые
aggregate audit reports. Кандидатские синтетические fixtures, персональные
строки и баллы не импортируются. Свежие URL СГУ в текущем web-инструменте
недоступны: архив не называется актуальной кампанией 2027.

Нет подтверждённых исторических проходных и требований ЕГЭ: соответствующие
поля API — null, UI — «Нет данных». Число мест не агрегируется между квотами
и формами. Модель ML не создавалась; в реальных карточках нет вероятностей.
Другие имеющиеся source profiles автоматически в продуктовый каталог не
переносятся: расширение требует отдельного review и добавления scope.

## Архитектура и изменения

[Аудит всех 29 страниц и план](../product-functional-audit.md) содержит
назначение, данные, интерактивность, demo/working, API, зависимости и приоритет.

Переиспользованы FastAPI, SQLAlchemy, существующие University/Campaign/
CompetitionGroup, Alembic и PostgreSQL. Нового сервиса, production-БД или
миграции не понадобилось. `catalog_import.py` выполняет явный атомарный
идемпотентный импорт двух reviewed scopes; конфликт — отказ, не overwrite.
Он не создаёт Sources и не включает worker. Без импорта программы пусты.
Операторские/ручные либо изменённые записи не становятся подтверждёнными.

Новые публичные контракты `/api/v1/catalog/*` описаны в [API.md](../API.md).
Старые `/api/v1/universities`, `/groups`, calculate/watch/session/subscriptions/
history/export/import сохранены; существующие backend-функции не удалены.

React-код разделён на `catalog/types`, `api`, `state`, `parts`, CatalogPages
и DetailPages. Используются исходные UI primitives и AppShell. Нет нового
роутера, UI-kit, клиентской БД и runtime-зависимостей. `/universities/mtuci`
и `/programs/mtuci-se` больше не подставляют чужую demo-запись: неподтверждённый
ID показывает корректное состояние 404. Остальные 25 маршрутов сохранены.

Для разработки/preview добавлен same-origin Vite proxy `/api` → localhost:8000,
настраиваемый `API_PROXY_TARGET`. Production Nginx уже проксировал `/api`.
ESLint добавлен как dev-only проверка с закреплёнными cached зависимостями.
На Windows используется существующий watch-build launcher; HMR отсутствует.

## Сохранение дизайна

Исходные `styles.css` и `internal.css` не менялись. Цвета, шрифты, радиусы,
фон, Header/Sidebar и навигация остаются v3. В `catalog.css` только scoped
ограничения для реальных длинных имён, wrapping фильтров/пагинатора и
unknown-state. Длинный hero использует размер PageTitle v3, mobile-карточки —
существующий двухколоночный режим v3. Это предотвращает чрезмерные заголовки
и разрывы названий в узкой колонке. Сверстанные заново старые страницы не
возвращались.

Необходимые изменения содержимого четырёх страниц: реальные названия/числа,
регион вместо недоказанного города, кампании, источник/дата, unknown fields,
поиск/сортировка/пагинация и корректные ссылки. Badge каталога не обещает 2027.
Кнопки реальных записей не ведут к чужому demo forecast/watchlist/compare.

Для выполнения требования о ML в **четырёх существующих подписях** вне
каталога добавлена явная маркировка демо: subtitle ForecastCard, caption
Calculator, status label старой ProgramCard, kicker ForecastResult.
Новые блоки, стили и значения прогноза не добавлялись; расчёты не заменялись.

Итоговый pixel test сравнивает 25 страниц на пяти ширинах:

- 100 сравнений с нетронутым отрендеренным оригиналом — ноль отличий.
- 25 сравнений пяти страниц с demo-подписями — оригинал получает ровно те
  же четыре текстовые замены перед screenshot. Другие тексты, DOM/CSS и числа
  не нормализуются. После этих явно перечисленных замен — ноль отличий.
- Четыре реальные catalog-композиции проверены отдельно на всех пяти
  ширинах и визуально просмотрены. Их новые данные не заявляются pixel-копией
  demo-МТУСИ. Сохранены 20 полноразмерных PNG.

Это сравнение Chromium в одинаковой среде, light, 100% browser zoom, dpr1,
ru-RU, Europe/Moscow, высота viewport 900; не заявление о равенстве разных ОС.
Полной тёмной темы в оригинальном v3 нет; она не добавлялась.

[Результаты pixel diff](catalog-vertical-slice/visual-results.json),
[source/design guard](catalog-vertical-slice/design-preservation.json),
[неизменность 68 файлов источника](catalog-vertical-slice/source-preservation.json).

## Проверки

| Проверка | Результат |
| --- | --- |
| npm ci --offline --no-audit --no-fund | 162 пакета установлены из cache; lock согласован |
| TypeScript strict | exit 0 |
| ESLint src, tests, scripts/config mjs | exit 0 |
| Production build | exit 0, 56 modules, JS 304.54 kB / CSS 53.08 kB до gzip |
| Source guard | 23 UI/config файла проверены, только разрешённые подписи/type-only fix; 3 integration compositions перечислены отдельно |
| Backend tests | **47 passed, 1 skipped**, XML сохранён; новый API + старые catalog/group/manual/session/privacy/contracts |
| Chromium полный запуск | **193 passed, 0 failed/skipped/flaky**, 52.6 s |
| Самостоятельный npm test | **68 passed**, API/preview запущены и штатно остановлены runner-ом |
| Адаптивность четырёх страниц | 390/768/1024/1280/1440 px, без горизонтального переполнения |
| Pixel tests вне каталога | 125 passed, threshold 0 / maxDiffPixels 0, с оговоркой о четырёх demo-подписях выше |

[Backend XML](catalog-vertical-slice/backend-tests.xml),
[Chromium summary](catalog-vertical-slice/browser-results.json).
Fault injection используется только в отказных browser cases (503/HTML/late
response). Успешные search/journey/reload ходят в настоящие endpoints, не mocks.
Первый новый browser case ошибся в exact accessible name select; добавлена
явная метка поля, после чего тесты прошли без увеличения timeout/retries/skips.

## Окружение и что не проверено

Docker API недоступен: `permission denied` на `docker_engine`, config access
denied. Нативная PostgreSQL-проверка добавлена и получает только disposable
schema, но локально пропущена из-за отсутствия TEST_DATABASE_URL. Это реальный
блокер проверки PostgreSQL, а не пройденная проверка.

Browser journey выполнялся на изолированной настоящей SQLite через FastAPI
с текущими миграциями. Существующий `backend/abiturient.db` прочитан **только
read-only**: три legacy-таблицы, без каталога; его данные/схема не менялись.
Проверка не означает миграцию пользовательской базы или deployment.
Hosted CI, Docker/Nginx runtime, Firefox/WebKit и production health в этом
этапе не проверялись. Предыдущие exact-copy evidence не перезаписаны.

Самостоятельный runner корректно останавливает принадлежащие ему Vite
previews и Python через stdin (без WMI/taskkill). Ранний запуск через
Playwright webServer зависал на Windows teardown; он остановлен, runner
заменён и повторно проверен. Две ранние временные папки публичной test-БД
`%TEMP%/admitflow-catalog-xhiql9eb` и `%TEMP%/admitflow-catalog-_wn5xa4d`
остались после принудительной остановки. Их удаление за пределами workspace
отклонено automatic approval policy (sandbox_approval=false); обход не
выполнялся. Рабочая база и исходный проект не изменены.

## Скриншоты

[Галерея всех четырёх страниц](catalog-vertical-slice/gallery.html).

| Страница | Desktop 1440 | Mobile 390 |
| --- | --- | --- |
| Каталог вузов | [PNG](catalog-vertical-slice/1440/universities.png) | [PNG](catalog-vertical-slice/390/universities.png) |
| Вуз | [PNG](catalog-vertical-slice/1440/university.png) | [PNG](catalog-vertical-slice/390/university.png) |
| Каталог направлений | [PNG](catalog-vertical-slice/1440/programs.png) | [PNG](catalog-vertical-slice/390/programs.png) |
| Направление | [PNG](catalog-vertical-slice/1440/program.png) | [PNG](catalog-vertical-slice/390/program.png) |

## Что остаётся прототипом и следующий шаг

Авторизация/профиль/настройки не подключены к аккаунтам; watchlist — demo
localStorage, comparison/list/analytics/history/notifications — demo. Нет ML
и настоящих вероятностей, данных текущей кампании 2027, полного перечня
программ, cutoff dataset и подтверждённых правил ЕГЭ. Реальные ID каталога
не смешиваются с demo-ID сохранённых направлений.

Следующий этап: проверить этот срез на доступном PostgreSQL, расширить
подтверждённые program scopes/кампании и требования из официальных источников,
затем реализовать saved-programs по настоящим ID и годам. Для ML сначала
нужны historical outcomes, data-quality criteria и целевые метрики.
Инструкции запуска: [catalog-runbook.md](../catalog-runbook.md).
