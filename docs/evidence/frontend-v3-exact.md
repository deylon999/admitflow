# Exact copy AdmitFlow Frontend v3 — T242 / S199

Дата: 2026-11-08. Текущая стратегия явно заменена пользователем.
Ветка `feat/frontend-v3-exact-copy` создана **от main**, с чистого рабочего
дерева. Предыдущая `feat/admitflow-ui-redesign` сохранена на `af387ad`.
Backend, shared fixtures, Compose, база данных и история Git не менялись.
Backend не запускался и не интегрировался.

## Что перенесено

Напрямую скопированы 68 файлов из `../admitflow-frontend-v3-main`:

- Все 24 файла `src/`: App/main, оригинальный History API router, Shell,
  RouteLink/navigation, PublicPages/AppPages/AuthPages, demo.ts, shared UI,
  все 12 компонентов лендинга, styles.css/internal.css.
- `index.html`, `tsconfig.json`, исходные зависимости/lockfile.
- `preview/` со всеми исходными HTML, исходные scripts и документы набора.
- Старые frontend src/tests/public и зависимости ручного трекера удалены
  из активного frontend. Их история сохранена в main и предыдущей ветке.

[Полный манифест источника](frontend-v3-exact/source-manifest.json),
[инвентаризация прежнего frontend](frontend-v3-exact/previous-frontend-files.txt).
У источника нет дополнительных assets/font binaries; не добавлялись шрифты,
картинки, новые тексты, цвета, предупреждения или элементы прежнего UI.

## Необходимые технические изменения

1. **Одна type-only правка:** в StatusPage массив вариантов объявлен `as const`.
   Без неё исходный `tsc` падает сTS2322: tone выводится как произвольная string.
   JSX, тексты, данные, CSS и обработчики не менялись. Скомпилированный JS
   оригинала и копии **побайтно одинаковый**.
2. Package scripts дополнены typecheck/Playwright/source verification;
   добавлены только dev-пакеты Playwright. Все исходные записи зависимостей
   в lockfile сохранены без изменения, включая React 19.3.1 / Vite 6.4.5 / TS 5.9.3.
   `npm ci --offline --no-audit --no-fund --logs-dir ../.npm-cache/_logs`
   успешно установил 72 пакета. Метаданные нового тестового пакета сначала были
   недоступны через registry (EACCES); использованы три уже закреплённые
   записи Playwright из main и существующий npm cache. Нет ссылок на локальные
   node_modules в package.json/lockfile.
3. **Dev-запуск в managed Windows:** обычный Vite dependency optimizer падает
   до загрузки приложения, пытаясь читать запрещённые родительские директории.
   `scripts/dev.mjs` использует штатные Vite Rollup watch-build и preview,
   минуя этот оптимизатор. `npm run dev` работает без backend; после правок
   исходников выполняется пересборка, страницу нужно перезагрузить (без HMR).
   Этот launcher не изменяет UI и не нужен production build.
4. Оригинальный React тоже собран Vite напрямую из соседней папки и запущен
   отдельным preview. Его выходные файлы/cache находятся внутри копии,
   исходная папка не записывается. `reference.vite.config.mjs` загружается
   native loader для обхода ограничений esbuild на чтение config.
5. Dockerfile больше не копирует старые shared/calculations в frontend.
   В Nginx разрешены style attributes, необходимые исходным динамическим
   ширинам/высотам графиков; остальные настройки инфраструктуры сохранены.
   Docker/Nginx в этой сессии не запускались, проверка относится к Vite preview.
6. Новый Playwright/CI проверяет этот frontend. Старый workflow архивирован
   в [историю](../archive/frontend-before-exact-copy-ci.yaml); независимый
   backend PostgreSQL pytest job сохранён. Hosted CI здесь не запускался.

[Проверка 26UI/config файлов](frontend-v3-exact/copied-source-check.json):
25 без содержательных изменений, один файл только с указанной type-only правкой.
[Проверка сохранности](frontend-v3-exact/preservation-check.json):68 исходных
файлов источника не изменены; backend/shared/Compose diff пуст;
main/предыдущая ветка и SHA скомпилированного JS зафиксированы.

## Проверки запуска и поведения

**187 passed, 0 failed, 0 skipped** в итоговом запуске Chromium:

- 30 проверок: ровно 29 уникальных маршрутов исходного SCREEN_INVENTORY и их
  HTTP200/React rendering. Включена предусмотренная оригиналом `/not-found`.
  Нет ошибок pageerror/console.error и запросов `/api/`.
- 12 сценариев взаимодействия: оригинальные heading/74%/calculator/FAQ/tabs;
  поиск и город; программы; localStorage tracking/reload; сумма ЕГЭ и результат;
  конкурсная таблица; сравнение до 4 и empty; смена предмета ЕГЭ; профиль;
  settings/theme selector/checkbox/modal; login/register/recovery; SPA Back/
  Forward и мобильная навигация. Сохранена исходная demo-реализация, без API.
- 145 визуальных сравнений, описанных ниже.

TypeScript strict и production build — exit 0. `npm run verify:source` — exit 0.
Сборка:50 модулей, JS 296.34 kB / CSS 51.97 kB до gzip, одинаковые asset names
и содержимое с оригиналом. Dev watch/preview отдельно проверен браузером
на `/`, `/app/forecast`, `/auth/login`, без JS-ошибок.

Первые ошибки проверок были неверными selectors нового test harness:
404 источника использует h2, не h1; исправлены селектор графика и выбор select
темы. Приложение под тесты не переделывалось, таймауты не увеличивались.

## Визуальное сравнение

Эталон — **запущенный оригинальный React**, не HTML-превью и не старый AdmitFlow.
Оба варианта собраны одинаковым Vite и запущены production preview, Chromium,
100% zoom, deviceScaleFactor 1, locale ru-RU, Europe/Moscow, одинаковое исходное
состояние, чистый localStorage, темаlight, одинаковый системный font fallback.
Полной тёмной темы в источнике нет: исходный settings-сценарий сохранён.

29 маршрутов ×390/768/1024/1280/1440 = **145 пар**.
Playwright сравнивает реальные PNG с `threshold: 0, maxDiffPixels: 0`:
**0 отличающихся пикселей во всех 145 парах**, одинаковый DOM-текст,
горизонтальное переполнение 0 во всех вариантах.

[Машинные результаты 145 пар](frontend-v3-exact/visual-results.json).
Все 290PNG оригинала/копии сохранены в подпапках ширин. Gallery позволяет
выбрать любой маршрут/ширину и сравнить рядом или наложением с opacity slider:

**[Открыть интерактивное сравнение](frontend-v3-exact/comparison.html)**

Примеры:

| Экран | Оригинал | Копия |
| --- | --- | --- |
| Landing 1440 | [PNG](frontend-v3-exact/1440/landing-original.png) | [PNG](frontend-v3-exact/1440/landing-copy.png) |
| Кабинет 1440 | [PNG](frontend-v3-exact/1440/app-original.png) | [PNG](frontend-v3-exact/1440/app-copy.png) |
| Вузы 390 | [PNG](frontend-v3-exact/390/universities-original.png) | [PNG](frontend-v3-exact/390/universities-copy.png) |
| Результат 390 | [PNG](frontend-v3-exact/390/app__forecast__example-original.png) | [PNG](frontend-v3-exact/390/app__forecast__example-copy.png) |

Визуально просмотрены оригинал/копия hero, кабинета, мобильной формы и gallery;
остальные страницы проверены полным pixel diff. В измеренных условиях
визуальных расхождений не осталось. Это не утверждение о pixel identity на
разных ОС/браузерах: сравнение всегда требует одинаковых fonts/environment.

## Устаревшие проверки

Старые 150 unit-тестов и suites tracker/source/import/session/manual-calculator,
FSD checker, прежние design-system/typography/font/print проверки больше не
являются критериями этого frontend: их src, маршруты и бизнес-сценарии удалены
по текущему указанию пользователя. Это не результаты нового продукта.
Их перечень содержится в previous-frontend-files.txt, точные версии — в main.
Единственная старая task evidence со ссылкой на удалённый `changes.spec.ts`
сохранена в `docs/archive/retired-frontend/` без изменения содержимого;
статусы исторических задач не переписывались.

Backend pytest в этом этапе не выполнялся: его код не менялся. Новые тесты
не запускают API/PostgreSQL и не адаптируют новый UI к прежнему трекеру.

## Воспроизведение

Из frontend:

```text
npm ci
npm run typecheck
npm run build
npm run dev
```

Dev по умолчанию 5173. Production: `npm run preview -- --port 5301`.
Без backend. Стандартные route/interaction tests: `npm test`.
Полный live comparison с соседней папкой: `npm run test:visual`, затем
`node scripts/summarize-visual.mjs`. Нужен установленный Chromium
(`npx playwright install chromium`). Источник только читается.

Итог: все 29 маршрутов скопированы; интеграция backend/ML не начиналась.
Предыдущая ветка сохранена, main не изменён; push/deployment не выполнялись.

Временные серверы оригинала, копии и dev watch остановлены после проверок;
временная резервная папка инструментов удалена.
