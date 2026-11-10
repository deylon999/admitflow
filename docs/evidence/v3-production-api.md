# T253 — production API/DTO/errors для React v3

2026-11-10, S202. Единый P0-блок заменяет прежнюю мелкую AF-декомпозицию;
история карточек не удаляется. Acceptance записан до реализации в T253.

Реализация: `69275e6d1d43cc29be35c75b98853bd3b93f6a49`.
[Ссылка на коммит](https://github.com/deylon999/admitflow/commit/69275e6d1d43cc29be35c75b98853bd3b93f6a49).
Строгая проверка write acknowledgement 204 и дополнительный тест входят в
завершающий коммит (`git show HEAD`). Коммит локальный, push не выполнялся: удалённая ссылка станет доступна после
публикации владельцем. Локальная проверка: `git show 69275e6`.

## Реализовано

- `shared/api.ts`: единый same-origin HTTP, JSON, безопасные сообщения ошибок,
  credentials/CSRF header, timeout 15 s, AbortSignal, отделение network/HTTP/DTO
  ошибок. Используемые поля DTO проверяются при получении; дополнительные поля
  допускаются для совместимости. HTML SPA fallback не считается данными API.
- `shared/dto.ts` и `catalog/decode.ts`: DTO подписок, событий, покрытия,
  групп, lookup/confirm и каталога; проверки nullable-полей, чисел, дат, URL,
  списков. Нет возврата вымышленных фактов при ошибке.
- `shared/resource.ts` и `ResourceState`: общие loading/error/retry; при
  повторе того же запроса сохраняются прежние сведения с предупреждением.
  Смена параметров отменяет запрос, поздний ответ не заменяет текущий результат.
- 401 скрывает приватные данные; автоматического создания новой сессии нет.
  Пользователь явно начинает гостевой доступ. Изменение владельца в другой
  вкладке очищает данные; epoch запрещает принимать ответы прежней сессии.
  Публичный код/токен подтверждения не сохраняются в URL или localStorage.
- Подписки читаются из существующего API. Добавление: реальные группы,
  доступность lookup, поиск публичного кода, явное подтверждение, POST
  subscriptions. Неуспешное сохранение сохраняет ввод и токен; повтор использует
  ту же серверную операцию. Удаление подтверждается пользователем и сервером.
- Навигация ведёт к сохранённому subscription ID, а не к демо `mtuci-se`.
  Неизвестный ID не заменяется примером. `/app/competitions` — дополнительный
  алиас списка; все исходные 29 URL сохранены.
- Нет API прогнозов, аккаунтов, пользовательских настроек или ЕГЭ-аналитики:
  основной экран объясняет ограничение, макет открывается только через
  `?mode=demo`. Баннер остаётся видимым при переходах внутри демо; выход
  возвращает live/unsupported. Демонстрационные изменения профиля не называют
  себя серверным сохранением. Статические образовательные материалы сохранены.

## Матрица исходных 29 URL

| URL | Режим / данные |
| --- | --- |
| `/` | Статический лендинг; существующие численные примеры помечены demo |
| `/universities` | Live catalog/universities; loading/empty/error/retry |
| `/universities/sgu-saratov` | Live stable university ID + программы; 404 отдельно |
| `/programs` | Live catalog/programs; фильтры кампании не подменяются |
| `/programs/sgu-2026-4588` | Live campaign-scoped program; неизвестные показатели остаются неизвестными |
| `/ege-analytics` | Нет feature API; явный opt-in demo |
| `/how-it-works` | Статическая информация |
| `/faq` | Статическая информация |
| `/auth/login` | Нет account API; явный opt-in demo |
| `/auth/register` | Нет account API; явный opt-in demo |
| `/auth/recovery` | Нет account API; явный opt-in demo |
| `/app` | Live subscriptions; доступ/загрузка/ошибка/пусто/список |
| `/app/profile` | Нет profile API; явный opt-in demo |
| `/app/forecast` | Нет forecast API; явный opt-in demo |
| `/app/forecast/example` | Только opt-in demo, не результат введённых пользователем баллов |
| `/app/forecast/method` | Описание макета методики, не подтверждённая модель |
| `/app/watchlist` | Live subscriptions; legacy local demo только при opt-in |
| `/app/watchlist/add` | Live groups → source lookup → confirm subscription |
| `/app/competitions/mtuci-se` | Live ID lookup: нет подстановки демо при отсутствии ID; opt-in demo сохранён |
| `/app/competitions/mtuci-se/competitors` | Нет feature API персональной аналитики; opt-in demo |
| `/app/compare` | Нет продуктового сравнения/ML API; opt-in demo |
| `/app/history` | Live private changes с курсором, loading/empty/error/retry |
| `/app/notifications` | Live private changes; не вымышленные обновления |
| `/app/settings` | Нет настроек аккаунта; opt-in demo |
| `/app/sources` | Live coverage; каталог/свежие/архивные группы различаются |
| `/app/states/empty` | Образец состояния, только demo |
| `/app/states/error` | Образец состояния, только demo |
| `/app/states/success` | Образец состояния, только demo; не успех операции |
| `/not-found` | Настоящий неизвестный маршрут, без подстановки сущности |

## Проверка

Из `frontend/`:

```powershell
npm run typecheck
npm run lint
npm run build
npm test
```

Все команды exit 0. Финальный Playwright: **84 passed, 0 failed, 0 skipped
(17.0 s)**, Chromium. Включены 29 route smoke, существующие сценарии каталога
и demo interactions, 16 новых API-сценариев: 401/404/422/429/500, сеть,
malformed/null DTO, HTML fallback, retry, реальный ID/DELETE, смена владельца,
background stale/401, отказ от ложного успеха при неверном DELETE acknowledgement, явное включение/выключение demo и lookup/confirm retry.
Существующий late-response тест каталога сохранён. Нативный гостевой запуск
и пустая история проверены с реальным временным FastAPI/SQLite; положительные
lookup/confirm и контролируемые ошибки — явными тестовыми HTTP-ответами.

`npm test` сам владеет временными API/preview и штатно их останавливает.
`python scripts/roadmap.py --render --check` и `git diff --check` проходят.

Ручная сверка: открыть `/app/watchlist`, явно начать гостевой доступ; проверить
настоящий пустой список. В `/app/watchlist/add` выбрать доступный источник и
подтвердить найденную запись; неподключённые группы не позволяют lookup.
В `/app/forecast/example` сначала виден отказ от реального прогноза, пример
открывается только после «Посмотреть демо интерфейса». Отключение API даёт
ошибку с повтором, а не демо-карточки.

## Границы

CSS v3 и четыре композиции каталога не переписаны. CSS asset остаётся
`index-CdCUn9di.css` (53.08 kB); это не утверждение о pixel equality новых
live-состояний с прежними демо-экранами. Полный reference visual suite не
запускался; прежние ожидания default-demo потребуют отдельной осмысленной
адаптации. Cross-browser/hosted CI/deployment в этой сессии не подтверждены.

Backend, SQL-модели, applied migrations и существующие PostgreSQL данные не
изменялись. Native PG/Docker-блокер T250 остаётся; SQLite не является его
приёмкой. Новые feature API остаются отдельной последующей работой. Это
завершение frontend P0-блока, а не готовность всего продукта к выпуску.
