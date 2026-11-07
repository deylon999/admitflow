# Очистка и инфраструктура AdmitFlow

2026-11-08, S201, T248–T252. Ветка `chore/product-foundation-cleanup` создана
от чистого `2a7835f`. Новые функции не разрабатывались. Main и предыдущие
ветки сохраняются; push/deployment не выполнялись.

## Аудит и удаление

[KEEP / REFACTOR / DELETE](../foundation-cleanup-audit.md) охватывает frontend,
backend, API, persistence, миграции, тесты/fixtures, зависимости, Docker, CI,
operations и документы. [Инвентарь Python imports](foundation-cleanup/python-module-imports.json)
сохранён до удаления; runtime импорты frontend и scripts проверены поиском
и сборкой, а не только отсутствием вызовов из нового frontend.

Удалены **42 файла**:

| Группа | Файлы / количество |
| --- | --- |
| Дублирующие статические previews | 31 файл `frontend/preview/`: 30 HTML и interactions.js |
| Отдельный screenshot/renderer stack | build-offline-preview.cjs, render-preview.py, validate-all.py |
| Устаревшие инструкции frontend | PROMPT_FOR_CODEX.md, CHANGES_v3.md, VISUAL_QA.md |
| Старый frontend E2E/CI stand | scripts/serve_source_e2e.py, advance_source_e2e.py, install_playwright_ci.sh |
| Тест удалённого manual assess wrapper | backend/tests/test_assessment.py и shared/assessment-cases.json |

**[Полный список 42 путей с SHA и commit восстановления](foundation-cleanup/deleted-files.json).**
История Git, sibling-источник и исторические доказательства не удалены.
Удалён dead `routeLabels` export, использовавшийся только offline renderer.
V3 Calculator, исходные demo-наборы и все действующие React-страницы сохранены.

Из зависимостей убран неиспользуемый `@vitejs/plugin-react` и 46 lock entries
его ветки. Чистая offline установка: **116 пакетов вместо 162**.
React/ReactDOM/Vite/TypeScript версии не изменились:
[dependency diff](foundation-cleanup/dependency-changes.json).
Scripts offline/screenshots удалены. QA теперь пишет в ignored test-results
по умолчанию; `QA_EVIDENCE_DIR` явно выбирает новый отчёт, не перезаписывая
предыдущие подтверждения.

## Backend и данные

Удалены только stateless HTTP `/api/v1/calculate` и `/api/v1/assess`, их
wrapper DTOs и obsolete assessment tests. Нет frontend/worker потребителей;
это ручная арифметика прежней концепции, не ML. В OpenAPI путей нет, валидный
same-origin POST получает 404. Write-origin исключения для этих путей убраны.
Protocol/body/validation/privacy tests перенесены на действующие APIs.

Общий CamelModel вынесен в schema_base.py без изменения JSON-конвенций.
Catalog/source/history/backup DTOs больше не импортируют base из старого
calculation-модуля. Версионированная арифметика сохранённых snapshot остаётся.

Сохранены University/Campaign/CompetitionGroup; Source/Snapshot/entries;
normalization, reviewed parsers/registry/profiles; atomic publishing и
история; subscriptions/changes/scenarios; jobs/leases/retry/worker; diagnostics,
backup/restore и полезные capture/review/load/rehearsal scripts.
Исторические manual persistence APIs сохраняются из-за текущих данных,
backup/privacy и совместного direction budget, с отдельным планом вывода;
они не возвращаются в новый UI.

**Ни одной миграции, модели SQL или volume не удалено.** Applied Alembic
0001–0011 и существующая локальная legacy-БД совпали с hashes до очистки.
Это проверка файла local DB и кода миграций, не проверка содержимого
недоступного PostgreSQL. [Подтверждение](foundation-cleanup/preservation.json).
Потенциально необратимые шаги вынесены в план: inventory → backup/restore →
политика чтения/хранения → отдельная новая миграция, без автоматического drop.

## Визуальная сохранность и маршруты

Все **29 runtime URL** открылись, включая каталог с реальными stable IDs.
Исходные компоненты, JSX render-код, стили, тексты, навигация и обработчики
v3 не менялись; отличие src — только dead route map.

- 20 сравнений четырёх каталог/деталь страниц × 390/768/1024/1280/1440 px
  с PNG из commit `2a7835f`: **0 отличающихся пикселей**.
- 125 сравнений остальных 25 страниц с реально запущенным sibling React:
  100 raw reference и 25 с четырьмя прежними разрешёнными demo-подписями.
  Нулевой pixel diff; новых нормализаций при очистке нет.
- Строгий threshold 0, maxDiffPixels 0; одинаковые fonts/Chromium/light,
  dpr1, locale ru-RU, Europe/Moscow, viewport height900, browser zoom100%.
- Нет горизонтального переполнения. Положительные пути/маршруты не дают
  console.error/pageerror. Отказы API намеренно проверяются отдельно.

**[Browser summary и 20 baseline checks](foundation-cleanup/browser-results.json)**,
[125 reference checks](foundation-cleanup/visual-results.json),
[source guard](foundation-cleanup/design-preservation.json).
Production build names/sizes совпадают с предыдущим зафиксированным билдом:
JS index-CjjI_tS8.js 304.54 kB, CSS index-CdCUn9di.css 53.08 kB.
На старте dist отсутствовал, поэтому byte identity со старым dist не заявляется.
Render hashes и реальные PNG являются доказательствами сохранения интерфейса.

| Страница | Desktop | Mobile |
| --- | --- | --- |
| Каталог вузов | [1440](foundation-cleanup/1440/universities.png) | [390](foundation-cleanup/390/universities.png) |
| Вуз | [1440](foundation-cleanup/1440/university.png) | [390](foundation-cleanup/390/university.png) |
| Направления | [1440](foundation-cleanup/1440/programs.png) | [390](foundation-cleanup/390/programs.png) |
| Направление | [1440](foundation-cleanup/1440/program.png) | [390](foundation-cleanup/390/program.png) |

## Проверки и фактические границы

| Команда / область | Результат |
| --- | --- |
| npm ci --offline --no-audit --no-fund | exit0, 116 установленных пакетов |
| npm run typecheck | exit0 |
| npm run lint | exit0, src + tests + scripts/config |
| npm run build | exit0, 56 modules |
| npm run verify:source | exit0, явное разрешение только прежних интеграционных отличий и dead map |
| npm run test:visual | **193 passed, 0 failed/skipped/flaky**, 54.2 s; API/previews штатно остановлены |
| Перенесённые HTTP safety/origin tests | **33 passed** |
| Доступная Windows backend часть | **549 passed, 35 skipped**, 182.05 s, после исправления fixture encoding |
| Полный backend collect на Windows | exit2: 12 модулей зависят от Linux-only resource |
| Compose config --quiet | exit0, предупреждение о запрещённом Docker config |
| Compose up -d db | exit1, permission denied к Docker Engine |
| Native PG / Docker build+smoke | **Не выполнены из-за блокера**, не заменены SQLite |

Backend полный collect сначала обнаружил Linux `resource` dependency в 12
модулях pipeline/worker. Они **не удалены и не ослаблены**; Linux CI по-прежнему
собирает весь набор с `--require-postgres`. Windows запуск явно исключает
эти модули и описан в [windows-limits](foundation-cleanup/windows-limits.json).
Все 35 оставшихся skip имеют причину «Requires a disposable PostgreSQL test database».
[Итоговый backend XML](foundation-cleanup/portable-backend.xml).

Первый portable run: 548 passed / 35 skipped / 1 failure. Причина — старый
тест читал UTF-8 SGU manifest системной Windows-кодировкой. Исправлен лишь
encoding='utf-8'; fixture/hash/privacy assertions сохранены. Повторный запуск
всех 584 доступных cases зелёный. Ранние protocol tests также скорректированы:
после удаления публичного калькулятора теперь передают обязательный origin
header для достижения body-budget проверки; таймауты и лимиты не менялись.
Предупреждения Starlette/httpx и sqlite datetime deprecation не являются
падениями, зависимости под них в этом этапе не обновлялись.

## PostgreSQL / Docker

Сделана настоящая попытка `docker compose -f compose.yaml up -d db`.
Ошибка: `permission denied` при подключении к
`npipe:////./pipe/docker_engine`; чтение Docker config тоже запрещено.
Docker доступы/DOCKER_HOST/config не менялись, привилегии не повышались,
sandbox не обходился. Не выполнялись down -v, volume rm, SQL delete/drop,
автоматический reset или миграция рабочей БД.

Нельзя подтвердить ни текущее состояние PostgreSQL, ни подключение, native
миграции/API или browser journey поверх Compose. **T250 остаётся blocked**.
[Машинная запись попытки](foundation-cleanup/infrastructure.json).
SQLite E2E использовал существующий временный test-контур того же FastAPI,
без создания нового сервиса/production-БД. Hosted CI и Docker/Nginx runtime
не подтверждены в этой сессии.

## Документы и остановка

README, frontend README, архитектура, продукт, API, визуальный эталон и
roadmap приведены к v3. Прежние версии сохранены в docs/archive с исправленными
относительными ссылками. Исторические done tasks и evidence не переписаны.
Старые release/ML задачи отложены с условиями пересмотра, а не помечены done.
Реестр/STATE/CHECKLIST обновляются только roadmap.py.

Очистка завершена; native инфраструктурный пункт блокирован. Новые функции
не начинаются. Возобновить T250 можно в разрешённом Docker/PG окружении:
Compose db/backend/frontend → migrations/health → catalog_import → четыре
catalog APIs → браузерный путь. Не удалять существующие volumes или данные.
