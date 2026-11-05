# Журнал работы

Записи добавляются в конец. Старые выводы не переписывать; исправления оформлять новой записью с ссылкой на предыдущую. Время старых действий, не подтверждённое логом, не придумывать.

## S001 — 2026-10-31 — аудит и дорожная карта

**Запрос:** подготовить полный подробный roadmap MVP и механизм продолжения после потери контекста.

**Состояние на входе:** React/API-код частично создан в предыдущих сессиях; подтверждённого успешного полного запуска нет. Проверены дерево файлов, package.json, README, backend-модули, API-клиент и Git status.

**Доказательства аудита T001:**

- `npm run build` из корня проекта: exit 1; TS2339 в `src/pages/TrackerPage.tsx:44`, доступ к `place` и `seats` у union без корректного сужения.
- `npm test`: exit 1; Vitest не находит suite в `tests/calculator.test.mjs`. Файл использует node:test и старый dist.
- Проверка наличия `playwright.config.ts`, `backend/tests`, `backend/alembic`: все отсутствуют.
- `git status --short`: файлы проекта untracked; не фиксировался проверенный SHA.

**Изменение плана:** отражены цель всех вузов, поэтапное измеримое покрытие, отделение сценарного расчёта от статистического прогноза. Написание дорожной карты не означает завершения MVP.

**Что не выполнялось:** исправление найденных ошибок приложения, миграции БД, интеграция с вузами и production-развёртывание. Они остаются задачами плана.

**Продолжение:** T002, затем T003; аудит источников T009 доступен как независимый поток. Результат проверки целостности самих документов записывается следующей записью после выполнения команды.

## S002 — 2026-11-01 — roadmap v1 и проверка памяти проекта

**Результат:** созданы PRODUCT, ROADMAP, ARCHITECTURE, DATA_RULES, QUALITY, RISKS, RUNBOOK, DECISIONS, STATE, TASKS, шаблоны сессии и источника. README приведён в соответствие с React/API и фактическими ограничениями. AGENTS.md в workspace и репозитории задают порядок продолжения.

**Реестр:** 65 задач, 8 этапов, 7 контрольных точек. 55 задач относятся к пути MVP, 10 — к дальнейшему развитию. Единственная закрытая задача — аудит T001. Остальные требуют реализации/проверки.

**Проверка:** `python scripts/roadmap.py --render --check --self-test --next` — exit 0. Проверены зависимости, ссылки, evidence-файлы, актуальность генерируемых карточек, указатель продолжения и отсутствие ложного закрытия gates. Шесть негативных сценариев отклонены: повтор ID, цикл, done без evidence, потерянная зависимость, ложный gate и уже закрытая следующая задача. Скрипт не подтверждает истинность результатов приложения вместо тестов.

**Источники:** использованы официальные документы React/FastAPI/Alembic/Playwright для технических оснований и страница СГУ для предварительной предметной проверки. Нормативный аудит сезона и реальные адаптеры остаются задачами T009/T010 и последующих этапов.

**Предел работы:** исходники приложения не исправлялись; найденные build/test failures остаются исходной точкой. Выпуск, автоматические интеграции и прогноз вероятности не объявлены готовыми.

**Следующий шаг:** T002 — корректное сужение union в TrackerPage и успешный build; T003 — Vitest на исходном TypeScript. Независимые доступные задачи — T004 и T009.

## S003 — 2026-11-01 — стабилизация и очистка прототипа

**Запрос:** продолжить реализацию по подготовленному промпту; привести проект в чистое, аккуратное состояние. Цикл начат 2026-11-01. Изменения исходников не закоммичены; проверенного release SHA нет.

**T002:** исправлено сужение union в форме TrackerPage без any/подавлений TS. `npm run build` — exit 0. Добавлен Playwright-тест пустой формы, корректного результата 74/90 и невозможной суммы групп. Превью не появляется для ошибочных данных; запись не отправляется.

**T003:** удалён тест старого dist на node:test; Vitest импортирует текущий TS. Добавлены общие JSON fixtures для TS/Python: границы мест, первое место, лимиты, отрицательные/дробные/непересекающиеся группы, null и boolean. Исправлен приём boolean как числа в TS. `npm test` — exit 0, 26 passed. Фраза «при любом сценарии» заменена в TS/Python на «В пределах мест в обоих рассмотренных сценариях» согласно DATA_RULES; арифметика manual-v1 не менялась.

**T004 и подготовка последующих проверок:** создана собственная `backend/.venv`. Команда `backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt` — exit 1, WinError 10013 при подключении к PyPI. Недоступность сети не доказывает отсутствие закреплённых версий. В RUNBOOK/README описан явный запуск с `--env-file .env`. Чистый setup остаётся blocked.

Для проверки существующего API использован только как тестовый инструмент ранее установленный `C:/Users/pc/pdf-flashcards/backend/.venv/Scripts/python.exe`; сторонняя среда не менялась и не добавлялась в конфиги/зависимости проекта. Написаны предварительные тесты T005 и конфигурация T006; их задачи не переведены в done из-за незакрытого T004 и отсутствия remote CI. Это подготовка диагностики установки, а не переход gate G0.

**Сервер:** запуск указанным тестовым интерпретатором из backend: `-m pytest -q` — exit 0, 36 passed. Проверены health/calculate, общие fixtures, CRUD/неизменность истории/каскадное удаление, два владельца, истечение cookie, заголовок записи, невалидный ввод и последовательный лимит направлений. Есть предупреждение Starlette об устаревающем httpx TestClient; обновление зависимостей не выполнялось. Конкурентные лимиты, PostgreSQL и миграции этим не проверены.

**Браузер:** `PLAYWRIGHT_SINGLE_PROCESS=1 E2E_API=1 npm run test:e2e` (PowerShell env) — exit 0, 6 passed. Проверены light/dark, отсутствие горизонтального переполнения при 320/390/768/1440, калькулятор, FAQ, форма с mocked API и отдельный CRUD с реальным API: создание → перезагрузка → обновление → история → удаление. Для API использовалась отдельная игнорируемая SQLite `artifacts/e2e.db`. Неподтверждённые шрифты/точное совпадение с PNG не относятся к этим проверкам и остаются T007/T008. При первом автоматическом запуске Vite на Windows остановка дочернего процесса зависла: сервер PID 15468 остановлен явно, итог 5 passed / 1 skipped / exit 0. Повтор с отдельно запущенным Vite прошёл штатно за 5.2 сек.

**Очистка:** удалены устаревшие scripts/browser-qa.mjs, serve.mjs и fetch-fonts.py (последний писал только в старый dist). Остаются обычные Vite/Vitest/Playwright entry points и roadmap.py. Разделены конфигурации unit/E2E; обе проверяются TypeScript. Preview теперь имеет такой же локальный API proxy, как dev. CI-конфигурация выполняет сборку, unit, backend и browser CRUD; внешнего запуска пока нет. README/RUNBOOK актуализированы.

**Продолжение:** T007 (локальные шрифты и лицензии), затем T008 (визуальное сравнение с PNG); независимая T009 — аудит официальных источников. T004 разблокируется только после успешной установки и smoke из собственной .venv; T005/T006 требуют повторения проверок в чистой среде/remote CI. Не выдавать ручной прототип за автоматизированный MVP.

## S004 — 2026-11-01 — короткий README

По запросу пользователя README сокращён: назначение AdmitFlow, реализованный ручной режим, стек, запуск frontend и ссылки на инструкции API/roadmap. Изменения только документации. После прерывания S003 синхронизирован STATE.md и перегенерирован TASKS.md; статусы реализации не менялись. Проверка: roadmap --render --check — exit 0.

## S005 — 2026-11-01 — структура frontend/backend (T066)

**Запрос:** удалить ненужное, разделить frontend/backend и упорядочить проект. Добавлена отдельная задача T066; продуктовый объём не изменён.

**Структура:** React-код, public, npm-манифест/lockfile, node_modules, TS/Vite/Vitest/Playwright-конфиги и frontend-тесты перенесены в frontend/. Backend остался в backend/. Общий набор TS/Python перенесён в shared/calculations.json; импорты исправлены. Исходные PNG перенесены из родительских Desktop/Mobile в docs/design/desktop и docs/design/mobile, поэтому макеты входят в Git-репозиторий. Все перемещения проверены на нахождение внутри разрешённого workspace; история Git сохранена.

**Удалено:** старые корневые dist/, artifacts/ со скриншотами/QA-логами/тестовой БД, test-results/, .sites-runtime/ с временным npm-cache, неиспользуемые docs/templates/ и устаревший конфиг хостинга. Удалён только локальный конфиг хостинга; сам удалённый Site не менялся. Его ID сохранён в ADR-017. Перед очисткой остановлены старые dev/API-сессии. Пути удаления проверены по абсолютному корню проекта.

**Документация и автоматизация:** обновлены README, RUNBOOK, ARCHITECTURE, STATE, AGENTS в проекте/workspace, .gitignore, пути TASKS.json. CI использует frontend как cwd для npm и frontend/package-lock.json для cache; Python устанавливается/тестируется из backend. Старые записи LOG не переписывались. Подробные документы roadmap сохранены по исходному требованию пользователя.

**Проверки после переноса:**

- Из frontend: `npm test` — exit 0, 26 passed; `npm run build` — exit 0, результат frontend/dist/.
- Из backend доступным тестовым интерпретатором S003: `-m pytest -q` — exit 0, 36 passed. Собственная .venv не установлена из-за ограничения сети (T004), статус задачи не менялся.
- Из frontend с PLAYWRIGHT_SINGLE_PROCESS=1 и E2E_API=1: `npm run test:e2e` — exit 0, 6 passed, 4.9 сек. Проверен реальный API с отдельной SQLite в памяти.
- Из корня: `python scripts/roadmap.py --render --check --self-test --next` — exit 0; ссылки и состояние согласованы. Remote CI ещё не запускался.

**Процессы:** frontend session 91197 на 5173, временный API session 22556 / PID 18760 на 8000. Это preview; API использует БД в памяти и внешний тестовый интерпретатор. Перед повторным запуском проверить их фактическое состояние.

**Следующее:** T007 — локальные шрифты в frontend/public/fonts, затем T008; T004 требует чистой установки зависимостей после восстановления сети. Реорганизация не закрывает gates автоматического MVP.

## S006 — 2026-11-01 — Conventional Commits и GitHub

**Запрос:** разбить работу на осмысленные английские Conventional Commits от аккаунта пользователя для https://github.com/deylon999/admitflow.

**Авторство:** использованы существующие настройки Git deylon999 / deylon.shevtsov@yandex.ru, без изменения глобальной конфигурации. Репозиторий до этого не имел коммитов и remote. Создан origin с URL пользователя. GitHub-атрибуция email и авторизация push отдельно не подтверждены.

**История:** b11fb72 — `feat(api): implement manual admissions tracking`; c449432 — `feat(web): add admissions landing page and tracker`. Документация, макеты, правила продолжения и roadmap объединены в `docs: document MVP roadmap and development workflow`; workflow отдельно — `ci: run frontend backend and end-to-end checks`. Это начальная фиксация уже существующих файлов по назначению; прежняя история не переписывается.

**Проверка:** просмотрены списки staged-файлов и diff --check; найденные пустые строки EOF в генераторе карточек и CI убраны при финализации CI-коммита. Окружения, .env, node_modules, базы и отчёты исключены .gitignore. Тесты приложения не повторялись: исходники приложения не менялись со времени проверенного S005. Генератор roadmap после исправления прошёл --render --check --self-test.

**Сеть:** git ls-remote https://github.com/deylon999/admitflow.git завершился ошибкой соединения с github.com:443. GitHub CLI не установлен. Обычный push выполняется после создания локальной истории; успешная публикация не предполагается без подтверждения ответа Git. При восстановлении сети проверить удалённую историю и выполнить обычный push; force push не разрешён.

**Продолжение разработки:** T007. Статусы реализации и gates не менялись. Предпочтение английских Conventional Commits сохранено в AGENTS.md.

## S007 — 2026-11-01 — нейтральные формулировки документации

По запросу пользователя убраны названия инструментов разработки из текущих документов; ответственные обозначены по роли. Сохранены инструкции продолжения, roadmap, критерии и результаты проверок. Код приложения и история Git не менялись. Изменения оформлены отдельным Conventional Commit. Проверка: поиск по отслеживаемым текстовым файлам, roadmap --render --check и git diff --check.

## S008 — 2026-11-01 — локальный Docker Compose (T067)

**Запрос:** добавить простой запуск через Docker после конфликта ручного API с портом 8000. Старый тестовый API остановлен; проверка socket показала свободный 8000.

**Изменения:** compose.yaml с PostgreSQL 17, API на Python 3.12 и multi-stage frontend (Node 24 → Nginx). API/БД не публикуют порты на хост; один web-порт 127.0.0.1:8080 с WEB_PORT override. Nginx проксирует /api и поддерживает SPA /tracker. База в постоянном postgres_data; запуск ждёт healthcheck PostgreSQL и API. .dockerignore исключает окружения, базы, .env, кэши и артефакты. Frontend build context включает общие TS fixtures. README/RUNBOOK обновлены под docker compose up --build.

**Проверка:** docker compose config --quiet — exit 0. Docker/Compose CLI установлены. Docker Desktop запущен скрыто, но из среды не найден docker_engine pipe, конфиг Docker недоступен по ACL. docker compose build — exit 1 (Access denied при подготовке build context, Buildx plugin недоступен). Образы и запуск контейнеров не проверены; T067 остаётся review. Существующий production-план T047 и миграции T014 не закрываются локальным development Compose.

**Регрессия:** backend/.venv/Scripts/python.exe -m pytest -q из backend — exit 0, 36 passed; теперь использована собственная среда проекта, установленная пользователем. Чистую установку зависимостей заново не выполняли; T004 пока не закрыта. Исходники приложения не менялись, повтор frontend-тестов не требовался.

**Границы:** локальные development-настройки, автоматическое create_all, тестовые реквизиты PostgreSQL и HTTP. Production требует отдельных миграций/HTTPS/секретов; worker отсутствует. История Git дополняется отдельным build-коммитом. Следующий шаг для проверки Docker — выполнить compose up --build в пользовательском терминале с готовым Docker Desktop, затем проверить health/CRUD и сохранность данных после down/up.

## S009 — 2026-11-01 — аудит источников и границы данных

**Продолжение MVP:** проверены пять официальных кандидатов, сохранены source-audit и pilot. СГУ выбран первым техническим кандидатом, СГУПС вторым; фактическая интеграция не объявлена. У МИРЭА 403, СПбПУ недоступен веб-инструменту, МИФИ требует дополнительного исследования динамических данных. В shell исходящий HTTP по-прежнему блокируется WinError 10013.

**Правила:** исследованы разделы VII–VIII правил СГУ 2026 (82–90). Зафиксированы границы: сохранить официальный порядок, не объединять группы/квоты/сезоны, не выдумывать приоритеты и не исключать строки без проверенного основания. До аттестации конкретной группы автоматический вывод unsupported. Отдельная магистерская таблица СГУ не выдаётся за бакалавриат; запрос бакалавриата завершился timeout. T010 закрывает описание границ, не аттестацию адаптера.

**Данные:** data-policy фиксирует минимальный набор, область ID, сроки raw/сессий/backup, удаление и вопросы до внешнего запуска. Реальные идентификаторы кандидатов не копировались в Git. Условия массового получения не подтверждены, автоматический сбор не включён.

**Среда:** собственная backend/.venv имеет все закреплённые прямые зависимости, версии сверены через importlib.metadata; pip check — exit 0. В S008 из неё прошли 36 тестов, включая health/calculate/CRUD и общие TS/Python fixtures. Запуск из собственного checkout с собственным интерпретатором подтверждён; прежний блокер T004 снят, T005 закрыта. Это не утверждение о доступности скачивания из текущего shell или готовности Docker/CI.

**Статусы:** T004/T005/T009/T010/T011 done; T007 blocked (нет лицензированных файлов шрифтов, загрузка запрещена сетью); T067 review (Docker API теперь существует, но access denied). Следующая работа — T016, жизненный цикл гостевой сессии. Документы и зависимости проверяются roadmap перед коммитом.

## S010 — 2026-11-01 — гостевые сессии (T016)

**Изменения:** GET session с датой expiry, явный DELETE с каскадным удалением направлений/истории, отклонение старого token при POST вместо тихого создания новой сессии. Клиент сохраняет только признак прежней сессии, перестал повторно создавать её после 401; кабинет объясняет срок 30 дней, потерю cookies и предлагает подтверждённый новый старт. Добавлено удаление всех своих данных с отменой/подтверждением. При утрате одновременно cookie и localStorage отличить повторное посещение от первого нельзя; ограничение описано в RUNBOOK. Утраченный token нельзя восстановить по локальному признаку.

**Очистка:** отдельная команда maintenance cleanup-sessions, автоматическая очистка при локальном старте и раз в час. Удаляются только истёкшие сессии, каскады проверены; активные записи остаются. Команда не импортирует HTTP app и не выводит секреты.

**Проверки:** pytest из собственной .venv — exit 0, 41 passed. npm test — exit 0, 26 passed; npm run build — exit 0. Playwright с настоящим API — exit 0, 8 passed: прежний CRUD, потеря cookies без молчаливой новой сессии, отмена/подтверждение полного удаления. Предварительный запуск с single-process дал зависание создания нового контекста; этот workaround удалён, обычный Chromium стабильно проходит на одном worker. Повторять такой режим не нужно.

**Граница:** PostgreSQL-проверка и remote CI ещё недоступны. TTL/чистка проверены на изолированной SQLite; конкурентные записи решаются отдельно в T017. T016 done. Следующая задача T015 — каноническая модель и затем миграции T014.

## S011 — 2026-11-01 — каноническая модель (T015)

Добавлены сущности в admissions.py: вуз/филиал, кампания, группа, источник, общий снимок, строки, указатель публикации, подписка и оценка. Уникальность группы включает кампанию; кампании включают вуз/год/уровень. Составные FK защищают source/group/snapshot/subscription от смешивания. Официальный порядок хранится отдельно от баллов; неизвестные согласие/приоритет/места остаются null. Автоматическое coverage требует версии правил. Ручные Watch/Snapshot сохранены без изменения колонок.

Проверка: pytest из собственной среды — exit 0, 48 passed. Дополнительные интеграционные случаи: одинаковые внешние ID в разных сезонах/филиалах, null semantics, rollback дублей порядка, чужой snapshot в опубликованном указателе, перенос snapshot в другую кампанию и несовместимая assessment-группа отклоняются БД. Проверки пока SQLite; PostgreSQL проверяется отдельной T014. Реальные данные не импортировались, автоматический режим не объявлен готовым.

T015 done. Далее T014 — миграции и отдельная проверка PostgreSQL; задача может остаться review при недоступном Engine. Независимо доступен T012 — начальный каталог кандидатов.

## S012 — 2026-11-01 — Alembic и сохранение старых данных (T014)

Добавлены Alembic environment и замороженная initial schema из 12 таблиц. Начальная ревизия не импортирует модели приложения: её содержимое не изменится при будущем изменении ORM. Совместимая старая create_all-схема дополняется без удаления направлений/истории; несовместимые колонки/ключи/CHECK останавливают upgrade. Индексы также проверяются/создаются. Docker применяет upgrade перед API; AUTO_CREATE_SCHEMA=false в Compose.

Проверки: pytest — exit 0, 54 passed / 1 skipped. Миграции: пустая база, повторный upgrade, model alignment, перенос старого Watch/Snapshot с сохранением результата 74, отклонение лишней колонки и изменённого CHECK, downgrade/upgrade одноразовой БД, PostgreSQL offline SQL. Настоящий PostgreSQL-тест явно skipped без TEST_DATABASE_URL. В CI добавлен PostgreSQL 17 service и отдельный тестовый URL. Docker config и git diff --check проходят.

Основания реализации: официальная документация Alembic tutorial и autogenerate API. T014 остаётся review до реального PostgreSQL-прогона; offline SQL не считается его заменой. T047/T067 также не закрыты. Следующая независимая задача — T012, каталог с явным manual coverage.

## S013 — 2026-11-01 — начальный каталог (T012)

Добавлен каталог двух исследованных вузов с официальными URL, provenance и фиксированной датой проверки. Seed идемпотентен, допускает конкурентный startup через ON CONFLICT DO NOTHING и не перезаписывает правки существующих записей. GET universities?q= работает без сессии, поддерживает кириллицу/пробелы и возвращает items/total с лимитом 50. Оба вуза явно manual: подключённые автоматические группы не выдумывались. Полнота и ограничения описаны в catalog-coverage.

Проверка: pytest — exit 0, 58 passed / 1 PostgreSQL skipped. Проверены provenance/coverage, русскоязычный поиск, пустой результат, литеральный %, ограничение длины и повторный seed с сохранением изменения имени. Новая таблица/миграция не потребовалась: используется T015 University. T012 done. Далее T018 — проверка ответа на границе API/frontend перед каталогом в интерфейсе.

## S014 — 2026-11-01 — контракт на границе API (T018)

Добавлен contracts.ts с runtime parsers: корректные типы/диапазоны, источник и версия ручной модели, timezone в датах, безопасные URL, уникальные ID и согласованность latest/history. Числа/статус пересчитываются из входов; противоречащий серверный результат не показывается как достоверный. request возвращает unknown вместо доверенного generic cast. Catalog и session также проверяются. Backend отклоняет credentials в URL.

Общий shared/manual-watch.json получен из изолированного FastAPI и обезличен; backend-тест сравнивает актуальный endpoint с fixture, frontend-тест проверяет тот же ответ и повреждённые варианты. api-contract описывает текущие DTO, ошибки/лимиты/retry и границы будущих automatic/archive, которые пока отклоняются.

Проверки: pytest — exit 0, 60 passed / 1 PostgreSQL skipped; Vitest — exit 0, 40 passed; build — exit 0. Playwright с настоящим API и отдельным mocked испорченным ответом — exit 0, 9 passed. Неверное place не рисуется карточкой; показана ошибка. Первый запуск JSON fixture в Playwright требовал import attribute type=json, исправлено для Node 24. T018 done.

Следующая задача — T022, поиск/выбор вузов. Пока каталог содержит только manual-кандидатов без аттестованных групп; полный фильтр групп не объявляется реализованным заранее.

## S015 — 2026-11-01 — выбор вуза в кабинете (часть T022)

Добавлен UniversityPicker: поиск в официально исследованном наборе, выбор названия и provenance URL, ссылка на официальный список и постоянная маркировка manual. Неизвестный вуз разрешён через ручной ввод. При отказе каталога введённый текст сохраняется. Новая форма не обращается к внешним сайтам — только к собственному API. Выбор не означает автоматического обновления и не создаёт неаттестованную конкурсную группу.

Проверки: build — exit 0; Playwright — exit 0, 11 passed, включая поиск кириллицей, выбор/заполнение URL, неизвестный вуз и 503 каталога без потери ввода. API для проверки перезапущен из собственной .venv с временной SQLite (session 32844, PID 17304). Старый test API session 18965 остановлен.

T022 остаётся review: фильтры кампаний/групп и пагинация требуют аттестованных групп источников, сейчас их нет. Следующая независимая задача T028 — безопасная загрузка зарегистрированного источника; выполнение тестов через mock transport не выдаётся за реальную загрузку из worker.

## S016 — 2026-11-01 — ограниченная загрузка источника (T028)

Реализован fetcher для доверенного registry: HTTPS/443, точный allowlist доменов, проверка всех DNS-адресов и повторная проверка redirect. Соединение привязано к проверенному публичному IP; TLS/SNI проверяет исходный hostname без повторного lookup. Отклоняются private/multicast/reserved/site-local, credentials, внешние redirect, сжатие, неподдержанный MIME и переполнение 5 MiB. 401/403/challenge не обходятся. Retry-After ограничен, ошибки не содержат URL/тело. Возвращаются bytes/charset/hash/fetchedAt; валидность конкурсного списка определяет отдельный адаптер.

Проверки: pytest — exit 0, 96 passed / 1 PostgreSQL skipped. 36 тестов fetcher покрывают URL/DNS/redirect/rebinding, TLS hostname при pinned IP, потоковый лимит, HTTP-ошибки/challenge/encoding, retry и безопасные исключения. Внешние HTTP-загрузки не выполнялись и не объявлены успешными: сеть процесса по-прежнему ограничена. DNS ограничен системным resolver, общий таймаут задания/частота остаются обязанностью worker (T032). Инструмент не выставлен как endpoint произвольной загрузки.

T028 done. Для T017 выделен отдельный проверяемый шаг T068 — атомарность ручных записей и идемпотентность на SQLite. PostgreSQL-проверка остаётся в T014/T017 и не считается выполненной. Это уточнение последовательности позволяет продолжать независимую реализацию при недоступном Engine.

## S017 — 2026-11-01 — атомарные ручные операции (T068)

Добавлены owner write-lock и operation_records с миграцией 0002. На SQLite используется BEGIN IMMEDIATE, на PostgreSQL запрошен FOR UPDATE владельца. Проверка лимита и запись выполняются в одной транзакции. Idempotency-Key связан с owner/path/нормализованным телом; ответ сохраняется вместе с изменением и возвращается при повторе. Несовместимый повтор — 409. Удаление направления стирает сохранённые payload; tombstone возвращает 410 вместо воссоздания. Полная очистка сессии удаляет ключи каскадом. Лимит ключей 12000.

Интерфейс сохраняет один ключ при повторе неизменённого ввода, новый ввод получает новый ключ. Во время сохранения поля и переход на другую форму блокируются; это предотвращает потерю черновика. Записи автоматически не повторяются. Browser test имитирует потерю ответа уже после server commit и проверяет успешный повтор с тем же ключом без второго направления.

Миграции дополнительно проверены на полном development create_all schema без version table. Начальная ревизия не меняет посторонние таблицы, следующая валидирует собственную уже существующую таблицу и не stamp-ит несовместимую схему. Сохранность старых ручных данных проверена.

Проверки: backend — exit 0, 106 passed / 1 PostgreSQL skipped; frontend unit — 40 passed, build exit 0; browser — 12 passed. Конкурентные тесты: 30 создающих запросов дают ровно 20 успехов; 3 запроса при 499 снимках дают ровно один успех; 12 одновременных повторов одного ключа дают один Watch. T068 done, T017 по-прежнему требует PostgreSQL. Следующий вспомогательный шаг — подготовка исходных HTML и лицензированных шрифтов для снятия внешнего блокера.

## S018 — 2026-11-01 — сохранение результата и визуальный отчёт

По просьбе пользователя закончена текущая работа без запуска новых этапов. T068 сохранена коммитом 818b129. Подготовлен PROGRESS с оценкой около 25% автоматического MVP и календарным D1/30; это оценка, а не процент успешных задач. Точный счёт: 15 done из 68, 3 review, 1 blocked; релизные gates ещё открыты.

Сняты desktop/mobile previews реального интерфейса с синтетическим shared/manual-watch.json. Демонстрационная сессия после снимков удалена. Первоначальная передача русского текста через stdin PowerShell исказила тестовые строки; снимки перезаписаны с чтением UTF-8 JSON. Исходники приложения и пользовательские данные не менялись. Локальный preview перезапущен: frontend session 42855 на 5173, API session 91154 / PID 12192 на 8000, собственная .venv и временная .pytest_cache/preview.db. Старые процессы после смены активной сессии не считались живыми без проверки.

Состояние, задачи и инструкция продолжения сохранены; следующая задача T020. Исходные HTML, локальные шрифты, реальные PostgreSQL/Docker/CI и автоматический импорт остаются невыполненными. Успешный push из ограниченной среды не подтверждён; локальные коммиты готовы к обычной отправке.

## S019 — 2026-11-01 — простой чек-лист

По запросу пользователя добавлен корневой CHECKLIST.md: все 68 задач сгруппированы по этапам, 15 done отмечены [x], незавершённые и частичные — [ ]. Генерация и проверка встроены в roadmap.py, поэтому чек-лист обновляется из единого TASKS.json и не расходится с подробным планом. Ссылка добавлена в README, правило обновления — в AGENTS. Статусы реализации не менялись. Проверены render/check и соответствие каждой галочки реальному статусу задачи; приложение не изменялось.

## S020 — 2026-11-01 — подход B01, задача 1/5 (T020)

Пользователь выбрал подходы по пять задач. B01: T020 (границы сценария), T069 (ручное объяснение), T070 (сравнение ручной истории), T071 (полный экспорт), T072 (клавиатура/фокус). Последние четыре выделены как самостоятельные проверяемые части более широких задач; T023/T025/T039 и проверки автоматического режима остаются открытыми.

T020: добавлены ready/insufficient_data/unsupported в Python/TS и readonly POST assess. Автоматический/архивный режим без аттестации и неизвестная версия правил не возвращают числа. Пустая форма не окрашивается как неуспех поступления; подписи и статусы ограничены введёнными данными. Формула manual-v1 не менялась. Общие fixtures проверяют одинаковые границы на обеих сторонах.

Проверки: 112 backend passed / 1 PG skipped; 46 frontend passed; build exit 0; 4 браузерных landing-теста на 320/390/768/1440 passed. T020 done. Следующая T069.

## S021 — 2026-11-01 — B01, задача 2/5 (T069)

Добавлен раскрываемый блок «Как получен результат» в калькуляторе и ручной карточке. Формулы используют действительные входы и результаты: текущие согласия и согласие всех указанных выше. Интерпретация меняется вместе с границей мест; предположения и отсутствие гарантии написаны явно. Для некорректного ввода блок не формируется.

Проверки: 49 frontend tests passed, build exit 0. Первый browser-прогон выявил, что FAQ-тест выбирал любой details по индексу; после добавления объяснения он попадал в другой блок. Локатор ограничен .faq-list, повторный прогон — 4 passed / exit 0. Проверены привязка к числам, условный сценарий при изменении мест и исчезновение объяснения при пустом поле. Код backend не менялся. T069 done; T039 остаётся широкой задачей автоматических объяснений. Следующая T070.

## S022 — 2026-11-01 — B01, задача 3/5 (T070)

В истории ручного направления показано сравнение двух последних сохранений: изменение места, каждого входа и отдельно изменение положения относительно границы. Первый снимок и неизменные числа имеют понятный текст. Вычисление не меняет старые записи и не приписывает причины изменения официальному источнику.

Проверки: 53 frontend tests passed, build exit 0; 4 браузерных tracker API-теста passed, в том числе реальное обновление 74→90 и сравнение в истории. Unit-проверки покрывают улучшение/ухудшение, изменение числа мест без движения позиции и первый/повторный снимок. T070 done; широкая T023 ещё требует автоматического/PG пути. Следующая T071.

## S023 — 2026-11-01 — B01, задача 4/5 (T071)

Добавлена выгрузка JSON всех направлений владельца с полной историей, включая записи за пределами обычных последних 100. Endpoint берёт согласованный набор под блокировкой владельца, не включает служебные ключи и чужие данные. Клиент проверяет версию формата и структуру перед скачиванием. Выгрузка не обещает обратный импорт.

Проверки: 116 backend passed / 1 PostgreSQL skipped; 54 frontend passed; build exit 0; 5 tracker API E2E passed / exit 0. Проверены 150 снимков, отсутствие чужих данных/секретов, необходимость сессии, пустая выгрузка, повреждённый формат и действительное скачивание файла браузером. Для независимого прогона добавлены API_TARGET/E2E_BASE_URL; тестовый API на 8001 использует .pytest_cache/batch01.db, frontend на 5180. T071 done; следующая T072.

## S024 — 2026-11-01 — B01, задача 5/5 (T072) и checkpoint

Форма получает фокус на заголовке и возвращает его к вызвавшей кнопке при закрытии; если кнопка первого направления исчезла после сохранения, фокус возвращается к основной кнопке добавления. Escape сперва закрывает справочник и возвращает фокус к его полю, затем закрывает форму. Кнопки справочника доступны по Tab/Enter. Во время сохранения закрытие и Escape заблокированы, черновик не теряется. Это проверенный ручной путь; широкая T025 и общая приёмка доступности остаются открытыми.

Файлы: frontend/src/pages/TrackerPage.tsx, components/UniversityPicker.tsx, tests/e2e/keyboard.spec.ts. Финальные команды из текущего checkout:

- backend: `.venv/Scripts/python.exe -m pytest -q` → exit 0, 116 passed / 1 PostgreSQL skipped, 1 предупреждение зависимости Starlette/httpx.
- frontend: `npm test` → exit 0, 54 passed; `npm run build` → exit 0, TypeScript и production bundle собраны.
- frontend с E2E_API=1 и E2E_BASE_URL=http://127.0.0.1:5180: `npm run test:e2e -- --reporter=line` → exit 0, 16 Chromium tests passed. Новые 3 проверки проходят полный ввод клавиатурой на 390/1440 и задержанный POST с Escape. Остальные охватывают калькулятор на 320/390/768/1440, справочник, CRUD, историю, экспорт, ошибочный ответ, повтор записи и сессию.
- Синтетические preview-desktop.png / preview-mobile.png пересняты Playwright из UTF-8 shared/manual-watch.json с дополнительным сохранением 74→90; обе картинки просмотрены. Демонстрационная сессия удалена, DELETE → 204. Исходные макеты и пользовательские данные не менялись.

B01 завершён 5/5; 20 done из 72. Около 25% автоматического MVP, D1/30: ручные улучшения не закрывают отсутствующие реальные адаптеры, worker и release gates. STATE/PROGRESS/checklist обновлены. T006/T013 — следующие доступные P0; remote CI, исходные HTML, PostgreSQL/Docker и локальные шрифты требуют снятия прежних ограничений. Успешный push и production не заявлены. Приложение оставлено для просмотра на 5180/API 8001 в изолированной тестовой БД.

## S025 — 2026-11-01 — подход B02: десять задач

Пользователь запросил следующие 10 задач. Проверены GitHub (git ls-remote:443 недоступен) и Docker (доступ к Engine запрещён); T006/T014/T067 не закрываются. B02: T073–T082, самостоятельные части ручного пути и инфраструктуры импорта. Широкие задачи сохраняют требования реальных fixtures, PostgreSQL и аттестации. Нельзя выдавать синтетический цикл за интеграцию вуза. Последовательность: transport, history, comparison, registry, validation, raw store, publication, freshness, queue, worker/CLI.

## S026 — 2026-11-01 — B02 1/10 (T073)

Transport bounds response and body to 15s, supports AbortSignal and never retries writes. npm test: 57 passed; npm run build: exit 0; recovery + tracker API E2E: 6 passed. Files: transport.ts, api.ts, TrackerPage, transport/recovery tests. External CI unchanged.

## S027 — 2026-11-01 — B02 2/10 (T074)

Keyset history pages support all 500 saves without duplicate rows during concurrent insert; cursor scoped to watch/owner. Backend targeted pytest: 2 passed; frontend 58 passed; build exit 0; recovery and real API browser tests: 7 passed. UI retains first page on failed next-page request. Preview now 5182/API8002, isolated batch02.db.

## S028 — 2026-11-01 — B02 3/10 (T075)

Added selection of 2-3 manual directions with inputs, both scenarios, save times and official links; no cross-group ranking/probability. Build exit 0; 2 real-API Chromium tests passed at 390/1440, including selection limit, deletion and no page overflow. Files: WatchComparison.tsx, tracker.css, comparison.spec.ts.

## S029 — 2026-11-01 — B02 4/10 (T076)

Frozen strict adapter DTOs preserve unknowns and official order; HMAC identities scoped by source/group/year. Closed registry checks domain/version/enabled/attestation; production registry empty. First collection found incorrect fetcher helper import; replaced with static URL binding validation, DNS remains fetcher responsibility. pytest contract+fetcher: 39 passed / exit 0. Real adapters remain unattested.

## S030 — 2026-11-01 — B02 5/10 (T077)

Strict normalized-list validation rejects wrong identity/season, incomplete pagination, duplicate identities/references, rank gaps/order, unconfirmed emptiness, future/regressed timestamps and configured large drops. Unknown fields retained; equal scores never reordered. pytest validation+contract: 13 passed / exit 0. QualityPolicy thresholds documented as review signals; synthetic samples only.

## S031 — 2026-11-01 — B02 6/10 (T078)

Private bounded SHA-256 raw store uses fsync and atomic no-overwrite linking; verifies hash on read/repeat, rejects path traversal and oversized data. pytest tests/test_raw_store.py: 3 passed / exit 0, including 24 concurrent writers and corrupt existing object. Raw files ignored by Git and never exposed through HTTP. Windows ACL and retention/restore remain deployment gates.

## S032 — 2026-11-01 — B02 7/10 (T079)

Atomic source publication stores immutable rows/provenance and swaps latest under source lock; repeat keyed by raw hash plus parser version. New migration 0003 preserves populated old snapshots and FK references; development startup now uses Alembic. First migration tests exposed old head/unversioned-latest assumptions; updated historical fixture to frozen 0001/0002 and added explicit future-schema rejection. pytest publishing+migrations+API: 27 passed / 1 real PG skipped / exit 0; includes concurrent repeat, rollback after row-write failure, parser version change, legacy preservation, PG offline SQL. Real PG still unverified.

## S033 — 2026-11-01 — B02 8/10 (T080)

Public bounded status separates season/dataKind and checked/success/fetched/source timestamps; no rows, raw or hashes. Archive/disabled/errors/unknown/unsupported never fresh; successful live content checks expire by policy. Late old errors do not replace newer success. pytest status+publication: 6 passed, final status subset 3 passed / exit 0. Production registry still empty and assessmentAvailable always false.

## S034 — 2026-11-01 — B02 9/10 (T081)

Durable source_jobs migration 0004; one job/source, atomic claims, token fencing, expiry recovery, bounded retry/backoff/Retry-After and periodic scheduling. Disable revokes active lease. pytest queue+migrations: 14 passed / 1 PG skipped / exit 0, including 16 concurrent enqueues/claims, retry exhaustion, stale owner rejection and populated upgrade preservation. PostgreSQL SKIP LOCKED code is not claimed runtime-tested.

## S035 — 2026-11-01 — B02 10/10 (T082)

Separate worker once/loop and local source CLI now connect queue/fetch/parse/validate/store/publish. Production registry has no real adapters and CLI has no bypass. Eight worker tests cover synthetic success/quarantine, revoked and expired leases, retry, process-wide fetch timeout, crash after publication replay and redacted parser errors. Final full pytest: 154 passed / 1 real PG skipped / exit 0; frontend npm test: 58 passed, build exit 0; full Chromium E2E: 20 passed after explicit API restart on migrated 0004, plus final comparison subset 2 passed. Initial CLI smoke failed because development reload had not migrated the old preview DB; stopped only own session 15194, explicitly ran alembic upgrade/check, restarted own API session 45338/PID15852, verified OpenAPI status route and revision 0004; worker once then idle and source list empty, exit 0. Final review added mobile table-scroll hint and keyboard scroll and fixed CSS token. Synthetic previews refreshed, demo session deleted (204). T082 done; B02 10/10. Current preview 5182/API8002, backend/.pytest_cache/batch02.db. GitHub:443 and Docker ACL remain blocked; real sources/PG/remote CI/hosting/fonts and release gates remain open. Overall engineering estimate approximately 35%, D1/30; 30 of 82 cards done, not a release claim.

## S036 — 2026-11-01 — подход B03: десять задач

Пользователь запросил ещё 10 задач. GitHub:443 и Docker ACL всё ещё недоступны. Web-инструмент повторно прочитал индексы СГУ/СГУПС; оригинальный список СГУ 4588 — timeout, профиль СГУПС 1348 — cache miss. Извлечённый текст индекса не сохраняется как оригинальный HTML. PostgreSQL tools/server локально не найдены. B03: T083 capture bundle, T084 request budgets, T085 origin/host, T086 safe diagnostics, T087 raw retention, T088 SQLite backup, T089 restore, T090 manual import API, T091 import UI, T092 coverage. Полные T013/T014/T029/T049 и PG/production gates не закрываются локальными подшагами.

## S037 — 2026-11-01 — B03 1/10 (T083)

Closed pilot capture CLI stores original bytes plus bounded manifest/hash in private folder, verifies binding and tampering, never attests/enables a source. pytest tests/test_capture.py: 3 passed / exit 0. Real capture command failed with network_error/captured=false/exit 1; no original fixture obtained and T013 stays open. Official indices only support candidate URLs, not parser structure. Commands and handoff documented in sources/pilot.md.

## S038 — 2026-11-01 — B03 2/10 (T084)

Pure ASGI middleware limits actual request bytes to 8 MiB and total body receive to 10 seconds, handles false/missing length, disconnect and 400/408/413 before endpoint. Matching Nginx limits configured, runtime still unverified. pytest budget+API: 17 passed, final budget subset 3 passed / exit 0. Files http.py/main.py/nginx.conf and tests; public limits documented.

## S039 — 2026-11-01 — B03 3/10 (T085)

Trusted Host allowlist and exact production HTTPS PUBLIC_ORIGIN supplement custom-header CSRF guard; cross-site/null/foreign origins cannot write. Local dev ports work for trusted loopback hosts; readonly calculations unchanged. pytest origin+config+API: 20 passed / exit 0. Production config now fails closed without explicit host/origin. Docs/env updated; no actual domain or deployment claimed.

## S040 — 2026-11-01 — B03 4/10 (T086)

Generated request IDs and structured route-template/status/duration logs exclude raw URLs, query, cookie and exception text; unexpected JSON errors return safe 500. Liveness is DB independent, readiness/health return safe 503 on DB failure. Initial test found duplicate Cache-Control header; middleware now replaces diagnostic headers consistently. Targeted diagnostics/origin/budget pytest: 8 passed / exit 0. Uvicorn no-access-log configured for Docker/CI/runbook; real remote/container runtime not claimed.

## S041 — 2026-11-01 — B03 5/10 (T087)

Raw retention is dry-run unless explicit apply; only old unreferenced SHA-256 files are eligible, all historical snapshot refs are retained, symlinks skipped and DB lookup failure precedes deletion. Shared reentrant interprocess lock spans raw put through publication commit and cleanup. pytest retention/store/publication/worker: 18 passed / exit 0, including process lock, GC-vs-commit race, historical refs and DB failure. Transient storage lock failures use bounded retry. No automatic production cleanup enabled.

## S042 — 2026-11-01 — B03 6/10 (T088)

SQLite online backup plus all raw refs from the saved DB are captured under store lock into a private atomically finalized bundle. Manifest hashes DB and references; timeout/missing raw cleans staging and never reports ready. pytest tests/test_backup.py: 3 passed / exit 0, covering manual watch/history, multiple source versions/raw, orphan exclusion and failed copies. Local SQLite only; production PostgreSQL backup/restore remains open.

## S043 — 2026-11-01 — B03 7/10 (T089)

SQLite backup verification checks DB/raw hashes, integrity/FK, revision and exact raw references; unexpected views/triggers, symlinks, corruption and existing destination refused. Restore copies to new private environment and verifies again. pytest backup+restore: 6 passed / exit 0; actual restored FastAPI preserves watch IDs/history and cookie ownership, a new owner sees 404; source raw bytes verified. No working DB switched; PostgreSQL/production restore gate stays open.

## S044 — 2026-11-01 — B03 8/10 (T090)

Atomic manual-export-v1 import validates full file before insert: arithmetic, safe URLs, manual model, dates/timezones, uniqueness/order and 20/500 limits. New IDs/owner preserve manual dates and equal-timestamp ordering. Mandatory idempotency key caches only counts; replay after deletion cannot resurrect records. pytest import+export: 14 passed / exit 0, including 500 records, invalid/partial files, conflict/replay, owner isolation and rollback on DB error. Formula unchanged, provenance remains manual.

## S045 — 2026-11-01 — B03 9/10 (T091)

Import UI checks file size/content before network, previews counts and requires confirmation; cancel never writes. Deterministic content key survives reselect/retry, new-session transfer preserves both history records/dates and generates new owner IDs. npm test: 60 passed; build exit 0; 2 real API Chromium import tests passed including lost committed response replay and invalid/oversized file with zero POSTs. New isolated preview 5183/API8003 using batch03.db; API started explicitly without reload/access-log.

## S046 — 2026-11-01 — B03 10/10 (T092)

Coverage API/UI separates catalog size from attested enabled automatic sources with group rules and complete published versions. National denominator is unknown/null, archive is never fresh, request failure is not zero. Backend coverage subset 2 passed; final full pytest: 188 passed / 1 real PostgreSQL skipped; frontend: 62 passed and build exit 0; full Chromium E2E: 24 passed on explicitly restarted current API, final import/coverage subset: 4 passed. Maximum pretty export 20x500 with full IDs/numbers exceeded 6 MiB, so UI limit corrected to 8 MiB with a regression test; HTTP normalized body remains bounded to 8 MiB. Final CSS heading/font tokens corrected after visual review. Desktop/mobile screenshots refreshed, synthetic import preview not submitted, demo session deleted (204). SQLite CLI backup/verify/restore smoke passed on isolated batch03.db, schema 0004/rawCount0, no working DB switch; retention dry-run 0 deletions. B03 10/10; 40/92 done, approximately 40 percent automated MVP, D1/30. T006/T013 now explicitly blocked on GitHub access/remote run and original source captures; real adapters/PG/production gates remain open. Preview 5183/API8003, API session 38488/PID18244, frontend session24508; all commits local, push unconfirmed.

## S047 — 2026-11-01 — B04: аудит десяти дефектов

Пользователь запросил ещё 10 задач. GitHub:443 и Docker ACL вновь недоступны, локальный PostgreSQL не обнаружен. Попытка получить font bytes через разрешённый web API тоже недоступна; шрифты не выдумываются. Задан асинхронный вопрос о путях реальных HTML/шрифтов/PG. Пока выделены конкретные дефекты имеющегося кода: unsafe wording, import replay at quota, date/history parsing, field errors, draft loss, inconsistent 401, unbounded RLock, blocking IPC recv, destination rename race, exhausted jobs hidden by fresh. Это исправления, не новый синтетический источник; критический путь и оценка MVP не закрываются числом карточек.

## S048 — 2026-11-01 — B04 1/10 (T093)

Removed universal actual-place/consent assertions from landing, diagram, metadata and tracker captions; manual assumptions and no double subtraction explicit, feature availability separated. Interview remains an attributed story, formula unchanged. Build exit 0; 4 landing Chromium checks passed at 320/390/768/1440 in both themes, including copy boundaries and overflow. Visual font/design acceptance remains open.

## S049 — 2026-11-01 — B04 2/10 (T094)

Confirmed UI quota bug with a 20-direction export: capacity check blocked an idempotent replay before server could return cached success. UI now offers explicit replay check at quota; server still rejects a new file with 409 and no writes. Build exit 0; 3 real-API import E2E passed, including reload/reselect at 20, successful replay, changed-file refusal and exact final count20.

## S050 — 2026-11-01 — B04 3/10 (T095)

Strict calendar/offset/microsecond parser rejects Date.parse rollover and compares exact UTC microseconds before ID tiebreak. Full export and combined pages validate order, uniqueness and timestamp bounds. Initial tests exposed old synthetic ascending-ID fixtures and a test typing issue; corrected fixtures to the documented server order and typed snapshots through runtime parser. Final npm test: 65 passed; build exit 0; import/recovery/real-API E2E: 10 passed. Own 20x500 export still accepted.

## S051 — 2026-11-01 — B04 4/10 (T096)

Client validates trimmed names, URL scheme/credentials/canonical length and numeric groups before HTTP, links errors to fields with aria-invalid/describedby and focuses first invalid input. Native validation no longer swallows custom errors. npm test: 67 passed; build exit 0; 6 form/keyboard Chromium tests passed, including zero writes for credential URL, first-error focus, group error association and existing keyboard save flow.

## S052 — 2026-11-01 — B04 5/10 (T097)

Unsaved form signature guards cancel, different-form switch and ordinary link navigation; dismiss keeps draft, successful save bypasses confirmation, clean form is unchanged. Browser beforeunload added without automatic draft persistence. Build exit0; 5 draft/keyboard Chromium tests passed, including accepted switch, dismissed cancel/link and save without prompt. SPA back/forward/crash recovery not claimed; broader browser/navigation gates remain open.

## S053 — 2026-11-01 — B04 6/10 (T098)

Central QueryCache/MutationCache handler makes 401 consistent across history/export/delete/import/save, disables 401 retries and hides old form/cards/comparison/file. New session only explicit reset, with private query cancellation/refetch before reopening. Initial build required a literal return-type fix for the disabled access-state query. Final npm test67/build passed; 9 real-API session/action/CRUD E2E passed with dirty form, exact session-start count and empty new owner. No automatic cookie recreation.

## S054 — 2026-11-01 — B04 7/10 (T099)

RawStore timeout now covers in-process RLock wait and OS lock using one monotonic deadline; negative/nonfinite values rejected, nested operations remain reentrant, descriptor closes even if unlock fails. Windows lock-state paths normalized for case. Targeted storage/retention/publication/backup/restore pytest: 18 passed / exit0, including a blocked thread timing out while owner keeps lock, subsequent write, nested two-instance use and existing process lock test.

## S055 — 2026-11-01 — B04 8/10 (T100)

Removed poll-then-blocking-recv exchange: parent now waits for child exit within one deadline, then validates a private bounded bytes/JSON spool (size/hash/schema). Partial envelopes cannot cause an unbounded recv; fixed files cleaned after termination. Targeted fetch-exchange/worker/capture pytest: 13 passed / exit0, including child that demonstrably writes a partial result then stalls, 1MiB completed transfer, malformed envelope, existing timeout and synthetic publication recovery. No real source attestation claimed.

## S056 — 2026-11-01 — B04 9/10 (T101)

Restore reserves destination with exclusive mkdir and installs verified files without overwrite; concurrent attempts yield exactly one success. Failed finalization leaves restore.pending and verify/migration/API reject it. Initial test edit misplaced an existing schema assertion; corrected placement. Final restore/backup/migration pytest: 18 passed, 1 real PostgreSQL skipped. Hard-link filesystem requirement and partial-folder recovery documented.

## S057 — 2026-11-01 — B04 10/10 (T102)

Read-only diagnostics now expose bounded workerState and treat expired/final-failed jobs as source_error without overwriting source fields or published snapshots. Live/archive tests cover lease boundary, exhaustion, recovery and fresh coverage. Targeted status/queue/coverage/worker: 19 passed. Final full backend: 196 passed / 1 PostgreSQL skipped; frontend67 and production build passed; all32 Chromium E2E passed on explicitly restarted current API8003 (session98287/PID19396, isolated batch04.db). No real adapters or release gates unlocked.

Final verification commands (2026-11-01, current checkout):
- backend: `.venv/Scripts/python.exe -m pytest -q` → 196 passed, 1 PostgreSQL skipped, exit0; existing dependency warning only.
- frontend: `npm test` → 67 passed; `npm run build` → exit0.
- frontend with E2E_API=1/E2E_BASE_URL=http://127.0.0.1:5183: `npm run test:e2e -- --reporter=line` → 32 Chromium passed, exit0, current restarted API session98287/PID19396, isolated batch04.db.
- `python scripts/roadmap.py --render --check --self-test` and `git diff --check` → results below/checkpoint commit; TASKS.md and CHECKLIST.md generated, not hand-edited.
- Files: backend/app/sources/status.py, backend/app/schemas.py, backend/tests/test_source_status.py, docs/DATA_RULES.md, docs/api-contract.md, docs/RUNBOOK.md, docs/STATE.*, docs/PROGRESS.md, docs/evidence/preview-{desktop,mobile}.png.

Screenshots refreshed at 1440 and390: bounded manual captions, synthetic cards, coverage2/0/0, form field error/focus, no horizontal overflow. First screenshot helper used a value still valid for the newest card and timed out awaiting an error; corrected helper to a provably invalid sum. Final captures show unchanged saved card values and an unsent invalid update. Both successful demo sessions deleted through API (204); the first helper's two demo watches/session removed using an exact fixture pair only in isolated batch04.db. No user DB or source record changed. Screenshot files visually inspected; fonts/Figma acceptance remains open. B04 completed10/10,50/102done, estimate40% unchanged, D1/30. No remote push or CI result claimed.
Final checkpoint checks: roadmap render/check passed (102 tasks, 7 gates); self-test rejected all6 invalid states; git diff --check exit0. No active task; nextTask=null until concrete external inputs or a verified independent defect.

## S058 — 2026-11-01 — PostgreSQL legacy migration startup defect (T103)

User reports Docker backend exiting in 0001_initial._validate_existing: Unexpected check constraints in snapshots. Original b11fb72 manual constraints match frozen definitions, but validation compared source SQL text with PostgreSQL decompiled SQL using only whitespace/lowercase. pg_get_constraintdef adds grouping/casts and can rewrite IN as ANY; the same defect exists in 0002. PostgreSQL docs confirm returned text is decompiled, not original: https://www.postgresql.org/docs/17/functions-info.html. Fix compares actual checks with the same server's reflection of frozen checks on an empty temporary table, preserving expression structure, literal case/whitespace and validation/inheritance flags. Domain tables, rows, formula and CHECK definitions remain unchanged. Docker engine/config still denied by ACL to this process; user environment is running PostgreSQL but agent cannot inspect it. No volume deletion, blind stamp or user DB migration executed.

S058 verification (2026-11-01): `.venv/Scripts/python.exe -m pytest -q tests/test_migrations.py` from backend →14 passed,7 skipped,exit0. Full `.venv/Scripts/python.exe -m pytest -q` →200 passed,7 skipped,exit0; existing Starlette/httpx warning. Seven skips are actual PostgreSQL tests, including six new legacy-adoption/negative cases; no simulated result is presented as real PG. SQLite regressions reject changed operator/grouping and changes to case/whitespace INSIDE literals, which the previous normalizer could erase. Frozen table definitions, formula, revision IDs and user data untouched. Test PG scenarios use unique schemas only in an explicitly named admitflow_test* database. `docker compose config --quiet` exit0, with config ACL warnings; `docker info` permission denied at Engine pipe. No Docker build/up or user migration performed.

Files: backend/app/migration_checks.py, frozen revisions0001/0002 (validation only), backend/tests/test_migrations.py, docs/RUNBOOK.md and checkpoint documents. T103 remains review pending actual PostgreSQL upgrade with retained history and healthy backend. Runtime follow-up: from abiturient run docker compose up --build -d; preserve existing postgres_data volume. If still rejected, inspect actual pg_get_constraintdef definitions (readonly RUNBOOK command) before any further migration change. No frontend edit or preview restart; S057 frontend results retained as historical evidence, not PostgreSQL startup proof. Roadmap render/check/self-test and git diff --check will be verified before committing.
S058 final checkpoint: roadmap render/check passed (103 tasks); all6 invalid-state self-tests rejected; git diff --check exit0. Commit uses configured user identity; real PostgreSQL verification remains open.

## S059 — 2026-11-01 — продолжение одной задачи T103

User requested exactly one next task. T103 selected from STATE/roadmap. Working tree initially clean. Docker info/compose ps again denied by Engine/config ACL, local PostgreSQL commands unavailable. New observation: localhost8080/api/ready returns200 (version0.2.0); local preview5183 also200. Proceed with isolated real HTTP CRUD/history/ownership smoke on8080, then delete only created sessions. Asked user whether image was rebuilt after48f118f and original directions retained; no assumption that HTTP health proves schema revision or legacy migration by itself. Native PG tests remain unexecuted until actual evidence.

S059 result: added backend/tests/runtime_smoke.py for repeatable local HTTP verification, with fresh cookies only and finally cleanup, local-origin validation and redacted route report. Command from backend: `.venv/Scripts/python.exe tests/runtime_smoke.py` →15 HTTP checks passed, cleanup204/204, exit0 against localhost8080, nginx/1.28.3. Checks cover ready/OpenAPI, create/replay (one watch), update74→90, reconnect/read same snapshot IDs and both history entries, export, and other-session read/update/delete404. No foreign/user session used, no image restart or migration attempted. Report docs/evidence/t103-docker-smoke.json contains no cookies/owner hashes/concrete IDs.

Docker info/compose ps still denied, native PG tools absent. Seven PG migration tests not rerun or claimed passed. Prior full unit/E2E results not repeated because application unchanged; new smoke ran successfully on current HTTP runtime. User confirmation of image rebuild after48f118f and old directions remaining is pending. T103 returned to review, not done; exactly one task continued and no unrelated task added. Next step remains actual PostgreSQL legacy upgrade evidence and preserved old history. Readiness/card count unchanged50/103. RUNBOOK/STATE/PROGRESS updated; roadmap render/check and diff checks follow before commit.
S059 final checks: roadmap render/check valid103tasks and self-test rejected6invalid states; git diff --check exit0. Current task cleared, nextT103 remains review pending external migration evidence.

## S060 - 2026-11-01 - B05 plan15

User requested15 tasks. Docker Engine and GitHub remain inaccessible; no local fonts found. Select15 independent manual-UX/readiness steps from existing product scenarios, not synthetic adapters. T103 remains review; no native PG claim. Do not increase readiness from card count.

## S061 - 2026-11-01 - B05 1/15 (T104)

Search across university/title, manual-scenario filter, reset/no-results and exact-microsecond date/name sorting without mutating stored data. npm test68/build passed; one Chromium filter/sort check passed on5184. Initial Cyrillic script substitution corrected before verification.

## S062 - 2026-11-01 - B05 2/15 (T105)

Distinct chronological snapshot selectors compare any loaded pair, with safe fallback when selection disappears; default remains latest pair. Build and2 Chromium tools tests passed.

## S063 - 2026-11-01 - B05 3/15 (T106)

History API returns owner-scoped total independent of page size; UI shows remaining capacity out of500, older servers keep unknown total. Targeted backend1, frontend68/build and2 Chromium tools checks passed; current API process will be restarted before final real-API run.

## S064 - 2026-11-01 - B05 4/15 (T107)

History now displays all four saved inputs, both scenario places, model version and full ISO timestamp alongside readable seconds. Chromium history check passed with8columns and original timestamp/model. Formula unchanged.

## S065 - 2026-11-01 - B05 5/15 (T108)

Printable filtered manual report includes saved inputs, both places, original source/time, model and limitations. Print CSS hides controls and supports dark theme. Build and Chromium print-media check passed; no PDF/physical-printer acceptance claimed.

## S066 - 2026-11-01 - B05 6/15 (T109)

Deleting an edited direction requires draft discard confirmation before HTTP. Decline retains values and sends no delete; success closes stale form, failure keeps it. Build and Chromium cancel/confirm test passed.

## S067 - 2026-11-01 - B05 7/15 (T110)

Inline confirmations focus the safe Cancel action, Escape cancels and restores trigger focus; delete controls disabled during writes, removal returns focus to Add. Build and2 Chromium deletion checks passed.

## S068 - 2026-11-01 - B05 8/15 (T111)

Cached cards and dirty form survive a background read error with original dates and explicit retry; initial failure and401 remain separate. Watches refetch on return to tab. Initial test revealed global focus refetch was disabled; enabled only watches. Chromium error/retry check passed.

## S069 - 2026-11-01 - B05 9/15 (T112)

Displays server-provided absolute guest expiry and original ISO value without sliding extension. Reset replaces cached deadline with new session info. Build and Chromium reload test passed; no fabricated date on error.

## S070 - 2026-11-01 - B05 10/15 (T113)

Cross-tab reset hides private cards/drafts, cancels private reads and requires explicit readonly synchronization. Listener lives across routes; cached API session forgotten; no automatic session POST in receiving tab. Build and5 real-API session/tab checks passed. Existing delete401 test now accepts the intentional draft-discard prompt.

## S071 - 2026-11-01 - B05 11/15 (T114)

Skip navigation focuses main; route/hash changes focus destination including lazy headings, and404 has a correct title. Build and Chromium route/skip keyboard check passed; no full screen-reader/browser matrix claimed.

## S072 - 2026-11-01 - B05 12/15 (T115)

Named focusable history region and scoped column headers support keyboard horizontal scrolling. Mobile test first exposed intrinsic grid expansion; constrained tracks/card minimum widths. Final390px Chromium scroll/no-page-overflow check passed.

## S073 - 2026-11-01 - B05 13/15 (T116)

Explicit readonly refresh updates saved cards while preserving unsaved form values, disables duplicate reads and makes no new session POST. Chromium server-change/draft check passed; refresh is not a university fetch.

## S074 - 2026-11-01 - B05 14/15 (T117)

Import preview lists every bounded direction name, original timestamp, history count and source as safe text before POST. Chromium malicious-markup-as-text and cancel-with-zero-imports check passed.

## S075 - 2026-11-01 - B05 15/15 (T118)

Ready/health compare stored Alembic revisions with packaged migration heads; missing/empty/old/future revision503, live stays DB-independent and no automatic repair. Full backend205 passed/7 PG skipped; frontend68/build and44 Chromium passed on explicitly restarted API8004. After minor print-date/dateformatter/grid fixes, build and3 print/history/mobile checks passed again. Screenshots1440/390 refreshed, three history rows visible, no horizontal page overflow, demo sessions deleted204/204. B05 complete15/15; no real-source/PG/CI gate unlocked.

S075 final verification (2026-11-01): backend `.venv/Scripts/python.exe -m pytest -q` →205 passed,7 actual PostgreSQL skipped,exit0, existing Starlette/httpx warning. Frontend `npm test` →68 passed; `npm run build` →exit0. With E2E_API=1/E2E_BASE_URL=http://127.0.0.1:5184, `npm run test:e2e -- --reporter=line` →44 Chromium passed,exit0. Current API explicitly restarted after history-total/readiness changes: session89467/PID14168, isolated batch05.db on8004; initial session85040 stopped. Frontend session54579/API_TARGET8004. Docker8080 and old preview processes untouched; no working DB or volume switch.

Final review fixed empty report-generation date, reused datetime formatter and constrained filter/grid sizing; after those changes build and3 print/history/mobile checks passed, then route/skip assertion passed after small selector-layout correction. Screenshot1440/390 refreshed and visually inspected: synthetic watches, two-stage history74→94, all saved inputs, remaining497, guest deadline, file names/source/date preview without POST. Both final demo sessions deleted204, earlier screenshot sessions also204; page horizontal overflow false. First screenshot retained a focused skip link; final capture moved focus to heading to show normal header, and E2E confirms skip link starts outside viewport and becomes keyboard reachable. No font/Figma, PDF device or screen-reader acceptance claimed.

B05 exactly15 tasks and15 Conventional Commits;65/118done,3blocked,4review,46todo. Readiness estimate40% unchanged, all7release gates open; production adapters0, coverage2/0/0, no ML probability. No network/ACL bypass, push or remote CI. Updated PRODUCT/API/RUNBOOK/STATE/PROGRESS plus generated TASKS/CHECKLIST. Actual task deliverables corrected to modified files. Task T103 remains review; prior pending question about rebuilding48f118f/old data has no answer. Stop adding synthetic integrations: next progress needs real source bytes, fonts, PostgreSQL/Docker and CI. All old completed history remains intact.
S075 final focus review also returns to Add after reset/synchronization; two real API reset/tab checks and final production build passed after that change. Roadmap render/check/self-test valid118tasks and6invalid-state cases rejected; git diff --check exit0. Final screenshots visually inspected after selector alignment; no active task, nextT103 review.

## S076 - 2026-11-01 - B06 plan20

User requested20 tasks. Existing critical path still needs external inputs: Docker Engine/GitHub denied, fonts absent in system/user/JetBrains roots, web source/font API attempts inaccessible. Select20 concrete validation/concurrency/HTTP/runtime defects found in code; no synthetic adapter or coverage claims. T103 remains review.

## S077 - 2026-11-01 - B06 1/20 (T119)

Reject C0/DEL controls before Pydantic URL normalization; client form/import contracts reject them consistently. Targeted backend9 passed; frontend69 passed. No metadata write on invalid input.

## S078 - 2026-11-01 - B06 2/20 (T120)

Request JSON rejects duplicate keys, NaN/Infinity/overflow and depth over64 before writes, preserving normal malformed-JSON validation. Brackets inside strings remain valid. Targeted hardening14 passed; existing8MiB receive budget preserved.

## S079 - 2026-11-01 - B06 3/20 (T121)

Validation422 returns at most20 redacted field paths, no input/context or unknown key values, with matching OpenAPI schema. Targeted hardening/API/body-budget32 passed.

## S080 - 2026-11-01 - B06 4/20 (T122)

Settings fail closed for unknown environment/boolean strings; constructor enforces PostgreSQL, secure cookie and explicit production migrations. Updated prior test to reject an explicit unsafe true instead of silently ignoring it. Config/origin10 passed.

## S081 - 2026-11-01 - B06 5/20 (T123)

PostgreSQL connect timeout defaults5s (allowed1..10), pool checkout5s. Real local TCP peer accepted a connection then stalled: handshake timed out;4 tests passed. This is failure-path wire verification, not a successful PG migration/server test.

## S082 - 2026-11-01 - B06 6/20 (T124)

Manual list and full export batch snapshots instead of one query per watch; bounded full export still validates500 per watch. Twenty-watch query-count/tied-order test plus export/import15 passed (at most3SELECTs per request).

## S083 - 2026-11-01 - B06 7/20 (T125)

Equal-time updates retain exact observed time and use increasing UUID tie-breaks, becoming latest deterministically. Backward clock refuses409 atomically; DATA_RULES updated, formula unchanged. Clock/API15 passed after correcting a nonexistent test filename.

## S084 - 2026-11-01 - B06 8/20 (T126)

Manual DTO timestamps accept only explicit ISO timezone strings up to6fraction digits or aware internal datetimes; numeric/naive/coercible timestamps rejected422. Hardening/import/export32 passed; original timestamps remain unchanged.

## S085 - 2026-11-01 - B06 9/20 (T127)

Import preview enforces the server UTC year2000 floor and inclusive5minute future tolerance before POST. Boundary tested to1microsecond. Frontend70/build passed, maximum20x500 export still accepted.

## S086 - 2026-11-01 - B06 10/20 (T128)

Same-time opaque IDs compare Unicode code points like Python, not UTF16 code units. Text length counts code points, accepting valid100-character supplementary IDs from the server. Unicode ordering/export regression and all71 frontend tests passed.

## S087 - 2026-11-01 - B06 11/20 (T129)

Both HTTPS stream reader and injected reader contract reject declared-length mismatch with retryable incomplete_response; complete bodies remain valid. Fetcher/worker45 passed. No real source attestation implied.

## S088 - 2026-11-01 - B06 12/20 (T130)

Fetch reader rejects duplicate critical headers and conflicting transfer framing; malformed/control-character redirects become safe bounded errors. Fetcher42 passed, including no body read on ambiguity. Conservative framing policy follows RFC9112 section6.3.

## S089 - 2026-11-01 - B06 13/20 (T131)

Immutable fetch policy validates finite timeout up to30s, strict size up to5MiB, redirects0..5, exact lowercase DNS domains and supported content types before network. Fetcher/capture56 passed, including mutable sets, NaN, bool-as-int and wildcard/IP refusals.

## S090 - 2026-11-01 - B06 14/20 (T132)

Spool cleanup attempts all known files, logs only stable safe codes and never masks valid fetch/error outcome. Process cleanup remains bounded without closing a live process. Exchange/worker11 passed; corrected test assumption when an empty folder was already removed.

## S091 - 2026-11-01 - B06 15/20 (T133)

Adapter declarations require an actual boolean attestation, bounded version token, immutable exact domains and callable parser before registry use. Registry/status/worker21 passed; production registry remains empty.

## S092 - 2026-11-01 - B06 16/20 (T134)

Explicit eligible reenqueue applies requested interval/max attempts and resets due time; running and backoff jobs are not modified. Strict integer queue settings reject bool coercion. Queue/worker13 passed.

## S093 - 2026-11-01 - B06 17/20 (T135)

Guest bootstrap and explicit reset serialize across tabs using Web Locks with bounded lock wait; reset avoids nested-lock deadlock. Build and2 real API cross-tab checks passed, including simultaneous first visits producing exactly one session POST. Unsupported Web Locks fallback documented later.

## S094 - 2026-11-01 - B06 18/20 (T136)

Private requests fence epoch changes before headers/errors and after JSON body; superseded reads do not auto-retry. Late bootstrap catch clears only its own pending promise. Two deferred-response regressions and all73 frontend tests/build passed.

## S095 - 2026-11-01 - B06 19/20 (T137)

Browser JSON reader enforces10MiB success/64KiB error bounds, cancels oversize/stalled streams, validates UTF8 and MIME, bounds displayed error strings. Four body regressions and all77 frontend tests/build passed; session epoch fence still covers body completion.

## S096 - 2026-11-01 - B06 20/20 (T138)

Page boundary provides focused recovery UI with explicit reload and no hidden retry/bootstrap. New failure/recovery E2E passed. Final backend269 passed/7 PG skipped, frontend77/build passed,46 Chromium passed on current API8005. First browser run45/46 had a transient Vite module-load failure; unchanged cookie-loss case passed3 repeats and full rerun. Final JSON-media-type bypass and huge-timeout edge corrected before full verification. B06 complete20/20; real data/PG/CI gates unchanged.

S096 final verification,2026-11-01: backend `.venv/Scripts/python.exe -m pytest -q` →269 passed,7 real PostgreSQL skipped,exit0 (existing Starlette/httpx warning). Frontend `npm test` →77 passed; `npm run build` →exit0. E2E_API=1/E2E_BASE_URL=http://127.0.0.1:5185 `npm run test:e2e -- --reporter=line` →46 Chromium passed,exit0 on final explicitly restarted API session9924/PID19008,8005,isolated batch06.db/revision0004. Frontend session10337/API_TARGET8005. Initial API session84682/PID10036 stopped before final run; old previews and Docker8080 untouched. No user database/volume switch, no remote push or CI proof.

First full browser run45/46: failed Vite dynamic import during cookie-loss reload, caught by new recovery boundary. Trace identified module-fetch error, not an assertion waived or a cookie reset accepted. Unchanged case passed3 repeats; final full46/46 passed. Initial backend260 passed before review found missing/vendor JSON Content-Type bypass plus huge integer timeout overflow; fixed both, added regressions and repeated full backend269/7. Last response-reader test now explicitly uses JSON MIME for the declared-size case and separately rejects HTML MIME; frontend suite repeated after that assertion correction.

B06 exactly20 task commits,85/138done,3blocked/4review/46todo, all7release gates still open. Final task priorities classified by actual risk (P0 data/access/safe production, P1 reliability, Unicode edge P2); criteria/evidence retained. Actual deliverables updated. No fresh data/real-source adapters, nationwide coverage, ML probability, native PG success or full Docker acceptance claimed. Formula unchanged; timestamp ordering/refusal documented in DATA_RULES. Native local TCP failure test is only timeout-path proof. Source bytes/font API attempts remained inaccessible. Pending earlier rebuild/data confirmation question still has no reply.

New docs/evidence/error-recovery-mobile.png captures an intentionally failed lazy-module load at390px, keyboard focus and explicit reload; visually inspected, no horizontal overflow, no guest bootstrap for that screen. Existing normal screenshots remain B05 evidence, not new database/visual acceptance. PRODUCT scope unchanged; API/RUNBOOK/env/STATE/PROGRESS/TASKS and generated CHECKLIST updated. Common source/PG/CI blockers preserved. Do not spend the next batch rewriting the finished contour or creating synthetic adapters as a substitute for original bytes/environment.
S096 final checkpoint checks: frontend77 passed after response-test MIME correction; roadmap render/check valid138tasks, all6 invalid-state self-tests rejected, git diff --check exit0. No active task; nextT103 review. Configured user identity preserved;20task commits remain local.

## S097 - 2026-11-01 - B07 plan15

User requested15 tasks. Git clean at c27e851; roadmap valid138. Docker Engine/config ACL denied and GitHub:443 still unreachable. Select manual import/session/form/date defects and concrete manual quality/restart checks, not synthetic adapters. Source/PG/CI/font blockers and all release gates remain open.

## S098 - 2026-11-01 - B07 1/15 (T139)

npm test -- tests/json.test.ts tests/import.test.ts:7 passed. Strict structural parser rejects decoded duplicate keys, depth65, nonfinite and malformed tokens; valid escaped strings and maximum-count exports preserved. Files frontend/src/lib/json.ts, import.ts and tests/json.test.ts.

## S099 - 2026-11-01 - B07 2/15 (T140)

npm test -- tests/import.test.ts:5 passed. Fatal UTF-8 byte decoding rejects malformed, truncated and surrogate encodings; valid Cyrillic and BOM roundtrip. ImportData uses arrayBuffer rather than lossy File.text.

## S100 - 2026-11-01 - B07 3/15 (T141)

E2E_API=1 E2E_BASE_URL=5186 Playwright import-cancel.spec.ts:1 passed on isolated API8006. Delayed old File.arrayBuffer explicitly released and two render frames observed after cancellation/new preview; no import POST or data writes. Cancel clears reading and stale selection skips parsing.

## S101 - 2026-11-01 - B07 4/15 (T142)

npm test -- tests/direction.test.ts:4 passed; npm run build exit0. Form counts160/200 Unicode code points and rejects excess; removed conflicting UTF16 HTML maxlength for names. Catalog query truncation preserves complete supplementary characters.

## S102 - 2026-11-01 - B07 5/15 (T143)

npm test -- tests/catalog-cancel.test.ts:1 passed. Real QueryObserver unsubscribe aborts transport fetch, next catalog query succeeds. api.universities consumes the query signal; pending old searches do not keep reading after key change/unmount.

## S103 - 2026-11-01 - B07 6/15 (T144)

Playwright catalog.spec.ts:3 passed on5186/API8006. ArrowDown/Up navigate two actual catalog choices, Escape restores input without closing form, Enter selects name and official source. Existing manual fallback and API failure cases also pass.

## S104 - 2026-11-01 - B07 7/15 (T145)

npm test -- tests/session-state.test.ts:3 passed. Cancel settles before a gated shared bootstrap response; another consumer completes using the same session and only one private fetch. Read epoch checked across bootstrap; abort listeners removed, shared bootstrap not canceled.

## S105 - 2026-11-01 - B07 8/15 (T146)

npm test -- tests/session-state.test.ts:5 passed. ReadableStream cancel spies prove401 and stale-header bodies are canceled exactly once; body results still fenced after access change. No response content exposed.

## S106 - 2026-11-01 - B07 9/15 (T147)

Playwright pending-form.spec.ts and draft.spec.ts:3 passed. A gated unchanged edit blocks current-tab navigation and beforeunload; after response the form closes and link works. Dirty-draft confirmation regressions preserved. SPA back/forward still not claimed.

## S107 - 2026-11-01 - B07 10/15 (T148)

Playwright pending-form.spec.ts:2 passed in final sequential run. During gated actual import, fields/save disabled and synthetic submit dispatch produces0 creates; after import original draft saves once,2 cards total. Initial test had incorrect field label; overlapping rerun collided with Playwright artifacts. Corrected label and waited for all runners before final2/2; application expectations unchanged.

## S108 - 2026-11-01 - B07 11/15 (T149)

Backend test_timestamp_bounds.py:4 passed; frontend time.test.ts:5 passed. Offset under/overflow yields422 before import writes, exact UTC year1/year9999 boundaries accepted. DATA_RULES updated; original accepted timestamps and formula preserved.

## S109 - 2026-11-01 - B07 12/15 (T150)

Backend test_snapshot_clock.py/test_export.py/test_import.py:16 passed. One-microsecond server clock regression causes409 and preserves exact history; export succeeds once clock restored. Read remains owner-locked; DATA_RULES documents imported future tolerance interaction.

## S110 - 2026-11-01 - B07 13/15 (T151)

Playwright manual-quality.spec.ts:2 passed after real overflow fix. Both themes at320px with160/200 unbroken Cyrillic names,1000000 values, expanded history and open edit. Initial test reproduced1919px grid expansion; minmax(0,1fr), bounded sidebar/form and wrapping preview fix it without clipping content.

## S111 - 2026-11-01 - B07 14/15 (T152)

Playwright manual-quality filtered-print case:1 passed. Two real API records, active filter selects only one; print media excludes second record and controls, includes source/model/limitations. Actual Chromium A4 PDF generated in ignored test-results; docs/evidence/manual-report.png visually inspected, clear labels/values. Existing mock-only print regression is preserved.

## S112 - 2026-11-01 - B07 15/15 (T153)

test_restart.py:2 passed: three fresh Uvicorn processes on one temporary SQLite file preserve exact history, owner deadline, create/update replay and deleted-operation410; separate expired-owner lifespan check passes. Initial test-cookie Domain mismatch corrected to real host semantics. Final backend276 passed/7 actual PostgreSQL skipped; frontend87 passed and production build exit0; all53 Chromium passed on final API8006/session26232/PID5096. No PostgreSQL/Compose success claimed.

S112 final checkpoint,2026-11-01: backend `.venv/Scripts/python.exe -m pytest -q` ->276 passed/7 actual PostgreSQL skipped,54.96s,exit0; existing Starlette/httpx warning. Frontend `npm test` ->87 passed; `npm run build` ->exit0. E2E_API=1 E2E_BASE_URL=http://127.0.0.1:5186 `npm run test:e2e -- --reporter=line` ->53 Chromium passed,1.5m,exit0. API explicitly restarted for final schema/export changes: session26232/PID5096,8006,batch07.db/revision0004; first own API session8562/PID19116 stopped. Frontend session91203. Existing previews and Docker8080 untouched.

S112 evidence: docs/evidence/manual-mobile-b07.png from final real API at390px with clearly named manual example, visually inspected; its new test session deleted afterward. manual-report.png visually inspected, chosen real API record with source and limitations; PDF generated in ignored test-results. No Figma/fonts/real-source acceptance claimed. API/RUNBOOK/DATA_RULES/STATE/PROGRESS/task deliverables updated.100done/153total,3blocked,4review,46todo; all7 gates open and estimated automated MVP40% unchanged. GitHub and Docker access still denied; no remote push/CI/native PG proof.

S112 final plan checks: roadmap --render/--check valid153tasks; all6 invalid-state self-tests rejected; git diff --check exit0. B07 contains15 task commits, preserving configured user authorship. No active task; nextT103 review until native PostgreSQL evidence.

## S113 - 2026-11-01 - B08 plan10

User requested10 tasks. Git clean at396440f, roadmap valid153. Docker Engine/config and GitHub still denied; web original pilot pages inaccessible, no new local source/font inputs. Select unfinished form recovery and browser-history protection as10 coherent tasks, preserving all external gates. Session-local30-minute drafts are not server backups or crash guarantees. Data router uses installed dependency, no new framework.

## S114 - 2026-11-01 - B08 1/10 (T154)

npm run build exit0; Playwright landing.spec.ts/tracker-tools.spec.ts16 passed on5187/API8007. Data router preserves routes, lazy failure recovery, hashes,404/title/focus and existing manual tools. Installed React Router7.18.4 exports verified; ADR022 records bounded draft/navigation choice.

## S115 - 2026-11-01 - B08 2/10 (T155)

Playwright draft-navigation/draft/pending-form:5 passed. Native browser back/forward rejects without losing fields, accepts departure once, pending unchanged edit remains protected. Router links skip document guard to avoid double confirmation. Old link test now explicitly waits for async dialog event; initial timing failure documented, refusal assertions retained.

## S116 - 2026-11-01 - B08 3/10 (T156)

Backend draft_scope/timestamp_bounds/sessions10 passed; frontend draft-scope/session-state6 passed. Namespace stable per owner, changes after new session/reset, contains neither cookie nor stored owner hash and cannot authenticate as cookie. Frontend older-API contract remains usable with recovery disabled.

## S117 - 2026-11-01 - B08 4/10 (T157)

npm test -- tests/draft-store.test.ts4 passed; production build exit0. One versioned16KiB sessionStorage record validates Unicode lengths, incomplete values, retry UUID/fingerprint, owner scope,30-minute TTL/session deadline; corrupt/foreign/expired records removed. Quota/access failures return unavailable without throwing.

## S118 - 2026-11-01 - B08 5/10 (T158)

Playwright draft-recovery/draft3 passed and production build exit0. Changed fields persist locally without server writes; route interceptor proves retry key exists in storage before POST dispatch. Failed request retains form and key. Extracted DirectionForm component to keep tracker readable; no autosave POST or false server-success message.

## S119 - 2026-11-01 - B08 6/10 (T159)

Production build exit0; Playwright draft-recovery/navigation3 passed. Reload shows a bounded plaintext preview, restore fills incomplete fields without POST, discard removes only local state and returns focus. Existing draft replacement requires explicit confirmation; restored retry intent preserved. No automatic restore or source fetch.

## S120 - 2026-11-01 - B08 7/10 (T160)

Backend expected_snapshot/writes10 passed; Playwright draft-recovery4 passed on restarted API8007/session62597/PID13052. Stale/missing draft remains plaintext-readable without restore; already open stale edit refuses409 and preserves fields/history. Expected snapshot checked under owner lock after cached replay; malformed header400. DATA_RULES updated; PG concurrency not claimed.

## S121 - 2026-11-01 - B08 8/10 (T161)

Playwright recovery/session-tabs8 passed plus expanded successful-save/cancel case1 passed. TTL expiry removes record without reading renewal;401 and cross-tab reset clear local state before explicit resync; success/cancel leave no record. Form and recovery timers bounded by original expiry; session-info cancellation added to reset. Data policy documents plaintext tab-local limits and suspended-timer caveat.

## S122 - 2026-11-01 - B08 9/10 (T162)

Three real-API Chromium cases passed: lost create and update responses are committed, browser reloaded, explicit restore retries exactly the stored key without extra watch/snapshot; update replay preserves an intervening newer snapshot. Cookie owner replaced without storage event yields no old preview or stored record. No mocked success or inferred owner isolation.

## S123 - 2026-11-01 - B08 10/10 (T163)

Final backend279 passed/7 actual PostgreSQL skipped, frontend92 passed/build exit0, full69 Chromium passed on API8007/session62597/PID13052. Before final expiry fix full68 passed; added wall-clock-only expiry-during-read test and repeated full69 without weakening expectations. Keyboard/320px light-dark and denied/quota storage cases pass. Restore now readonly-revalidates cookie scope and latest records; expiry checked after network wait, restored unchanged drafts retain expiry timer. Mobile evidence visually inspected; example guest/storage cleared.

S123 final checkpoint,2026-11-01: backend `.venv/Scripts/python.exe -m pytest -q` ->279 passed/7 actual PostgreSQL skipped,55.92s,exit0; existing Starlette/httpx warning. Frontend `npm test` ->92 passed; final `npm run build` ->exit0. E2E_API=1 E2E_BASE_URL=http://127.0.0.1:5187 `npm run test:e2e -- --reporter=line` ->69 Chromium passed,2.1m,exit0 on final API8007/session62597/PID13052,batch08.db/revision0004. First full68 passed; final review found TTL could expire during readonly restore check, added wall-clock-only regression and retained original expiry timer for unchanged restored forms; final full69 repeated. No weakened assertion or hidden retry.

S123 runtime/evidence: frontend session83703 API_TARGET8007. Initial own API session51868/PID1504 stopped before draftScope runtime checks, next21434/PID12824 stopped before expected snapshot contract checks. Final process62597/PID13052 unchanged during full checks. Older previews and Docker8080 untouched. docs/evidence/draft-recovery-mobile.png captured at390px with explicitly named local manual example, visually inspected; no watch POST, own guest DELETE204 and sessionStorage cleared afterward. No Figma/font/native PG acceptance claim.

B08 final:10 task commits,110done/163total,3blocked,4review,46todo; all7 release gates open. Estimated automated MVP40% unchanged,day1/30. PRODUCT/DECISIONS/API/DATA_RULES/data-policy/RUNBOOK/STATE/PROGRESS/deliverables updated. Source original bytes still absent, pilot web opens inaccessible, Docker Engine/config ACL and GitHub443 denied. No automatic adapters, national coverage, ML, production deployment, remote push or CI success claimed. Prioritize obtaining real inputs/runtime rather than further cosmetic batches.

S123 plan verification: --render/--check valid163tasks, all6 invalid-state self-tests rejected, git diff --check exit0. No active task, nextT103 review. All10 commits local under configured user identity; generated TASKS.md/CHECKLIST synchronized.

## S124 - 2026-11-01 - B09 plan5

User requested5 tasks. Clean Git at7d41b3f, roadmap valid163. Docker Engine/config ACL and GitHub443 denied again; no new original HTML/fonts. Compose config validation itself succeeds without Engine. Select5 release-preparation tasks addressing verification/runtime gaps, not cosmetic cards. Native PG/Compose/remote CI and source gates remain open.

## S125 - 2026-11-01 - B09 1/5 (T164)

pytest test_pg_support.py/test_migrations.py21 passed/7 actual PG skipped. Upgrade/downgrade now uses the same isolated schema fixture as every native case; no destructive test targets public. SQL compiler/controller regressions prove scoped search_path and cleanup on body/engine-creation errors; failed CREATE never triggers DROP. Native PG execution remains unverified.

## S126 - 2026-11-01 - B09 2/5 (T165)

Guard subprocess regressions8 passed; full collection301 tests succeeds. Actual pytest --require-postgres tests/test_migrations.py exits4 with missing disposable PG configuration, rather than green skipped checks. Guard also rejects filtered native cases and teardown skips. CI now requests mandatory PG and JUnit artifact; remote workflow remains unrun/T006 blocked.

## S127 - 2026-11-01 - B09 3/5 (T166)

Database diagnostic regressions5 passed: actual SQLite counts/read-only rejection, Unicode path, missing file not created, restore marker refusal, legacy/future revision and credential redaction. Real CLI on isolated batch08.db returns revision_current/sqlite/0004 and aggregate counts only. No migrations/repair/session cleanup. PG read-only repeatable-read SQL documented from primary docs, execution unverified.

## S128 - 2026-11-01 - B09 4/5 (T167)

docker compose config --quiet and --profile automation config --quiet exit0 despite Docker config ACL warning. Default services db/backend/frontend; automation adds worker. Shared raw_data path and app-owned image directory, no worker ports or parallel migrations. RUNBOOK includes raw-layer preservation and explicit Engine/image/permissions/runtime limitations; no container started or user volume changed.

## S130 — 2026-11-03 — B10 T103

B10: native PostgreSQL17.11 legacy adoption/refusal: 6 passed, exit0; old IDs/history preserved, incompatible CHECK rejected. See runtime evidence; initial startup-readiness race recorded.

## S131 — 2026-11-03 — B10 T014

B10: disposable Docker runner passed all21 migration cases including7 actual PostgreSQL checks; no-native selection fails exit1 and owned container is cleaned up.

## S132 — 2026-11-03 — B10 T017

B10: 21 write/optimistic tests passed, including11 native PostgreSQL; concurrency enforces20 watches/500 snapshots, retries do not duplicate, two app pools yield201/409.

## S133 — 2026-11-03 — B10 T067

B10: isolated Compose fresh images healthy;15 HTTP smoke checks passed through nginx to native PostgreSQL0004, sessions cleaned204/204; build host-network workaround documented.

## S134 — 2026-11-03 — B10 T168

B10 first5/5:92 frontend tests/build,12 repeated keyboard checks,70/70 full Chromium passed on actual production assets/PostgreSQL API. Fixed stale catalog options and save focus race; CI preview configured, remote unrun.

## S135 — 2026-11-03 — B10 T169

B10:8 native PostgreSQL queue/fencing cases passed; independent spawn workers claim once and SKIP LOCKED completes while another transaction owns the row.

## S136 — 2026-11-03 — B10 T170

B10:7 native PostgreSQL publication cases passed; uncommitted rows remain invisible to another reader, rollback/quarantine preserve last good pointer and crash replay deduplicates.

## S137 — 2026-11-03 — B10 T171

B10:actual pg_dump/raw restoration passed;15 tables exact, ownership/history/replay/tombstone and2 raw versions preserved; corrupt archive rolls back, corrupt raw rejected. Timings and quiesced-only RPO recorded.

## S138 — 2026-11-03 — B10 T172

B10: reproduced missing JS as HTML200, fixed nginx404/nosniff/cache policy;3 actual nginx/chunk-recovery checks passed after fresh image rebuild.

## S139 — 2026-11-03 — B10 T173

B10 complete10/10:owned4-service Compose recreation preserved history/ownership/retries/raw and actual worker resumed safely. Final332 backend/0skip,92 frontend/build,72 Chromium passed; temporary resources cleaned,preview8089 retained.

S139 final checkpoint: B10 ten tasks finished in two groups of five; 124done/173total,3blocked/1review/45todo, no active task, nextT019. Backend332 passed/0skipped with required33 native cases; frontend92 passed/build successful; all72 Chromium passed on current production nginx/PG API. Roadmap --render/--check valid173;6 invalid-state self-tests rejected; git diff --check clean. Updated STATE/PROGRESS/DECISIONS/RUNBOOK and concrete evidence/commands. Preview8089 retained, test PG55439 and all random rehearsal resources removed. Native PG and local Compose no longer blocked; GitHub read-only reachable but gh unauthenticated, remote push/CI unconfirmed. Real source/fonts/staging/release gates remain open. All10 task commits use existing configured author; no published history rewritten.

## S140 — 2026-11-03 — B11 1/30 T019

B11 1/30:manual acceptance audited;10 current Chromium cases passed on PostgreSQL8090, existing exact restart/ownership/retry evidence remains applicable.

## S141 — 2026-11-03 — B11 2/30 T007

B11 2/30:13 licensed variable font subsets vendored with hashes/OFL;actual Latin/Cyrillic FontFace loads pass with external requests blocked,fresh build+5 browser cases passed.

## S142 — 2026-11-03 — B11 3/30 T008

B11 3/30:four real-font screenshots compared to original PNGs,palette tokens match;documented functional copy/focus differences,6 responsive/font tests passed including1024.

## S143 — 2026-11-03 — B11 4/30 T013

B11 4/30:genuine SGU573-row original inspected,DOM-derived anonymized fixture retains exact facts;9 fixture/capture tests passed. STU header-only remains unsupported;source originals private.

## S144 — 2026-11-03 — B11 5/30 T027

B11 5/30:explicit passport/fixture attestation gates implemented;33 contract/registry/coverage/fixture tests passed,unknown/null/HMAC scope preserved.

## S145 — 2026-11-03 — B11 6/30 T174

B11 6/30:trusted8MiB policy/default5MiB verified through child/raw/backup;71+4 targeted checks passed and actual bounded SGU5851174byte fetch succeeded with pinned TLS.

## S146 — 2026-11-03 — B11 7/30 T029

B11 7/30:archive-only SGU adapter attested;all573 original rows independently matched,including16/17boundary and119tie-score groups;35 adapter/fixture/attestation regressions passed.

## S147 — 2026-11-03 — B11 8/30 T030

B11 8/30:25 real-source/quarantine/publishing/size checks passed;bad normalization retains573-row last-good snapshot,unknowns remainnull,publication enforces adapter cap.

## S148 — 2026-11-03 — B11 9/30 T032

B11 9/30:actual SGUHTTPS/573rows/PG worker cycle+idle passed,current replay passed;16 local+11nativequeue+2nativeSGU/API checks verify heartbeat/domain limits and API isolation.

## S149 — 2026-11-03 — B11 10/30 T033

B11 10/30:nativePG573-row retries/rollback/crash/raw provenance/retention passed,11+5 cases;onlyexpiredorphanpurged,productionretention explicitly stillopen.

## S150 — 2026-11-03 — B11 11/30 T175

B11 11/30:explicit disabled/idempotent registration and keyed enable verified in actual Compose;conflicts refused,private key excluded from image context;full396backend/0skip passed.

## S151 — 2026-11-03 — B11 12/30 T022

B11 12/30:real group catalog filters/branch/season/cursor and archive/manual/unsupported UI done;6backend+8contract+10browser+3header/mobile checks passed,currentPGarchive573rows.

## S152 — 2026-11-03 — B11 13/30 T176

B11 13/30:scoped authenticated lookup and owner/snapshot-bound300s confirmation implemented;12local+9nativePG cases passed,no public-code persistence/automatic subscription.

## S153 — 2026-11-03 — B11 14/30 T177

B11 14/30:owner-isolated idempotent subscriptions and combined20-limit done;native37cases passed,including data-preserving0005cascade fix,guest reset/expiry and cache replay safety.

## S154 — 2026-11-03 — B11 15/30 T021

B11 15/30:explicit archive lookup/confirmation UI,shared20limit and session cache isolation;5newChromium+5catalog,101unit,currentbuild,4lookup tests and37native cases passed;0006rate budget added.

## S155 — 2026-11-03 — B11 16/30 T178

B11 16/30:individual archive deletion,owner isolation,cascading personal history and410replay tombstones verified;2nativePG+1newChromium passed,currentbuild.

## S156 — 2026-11-03 — B11 17/30 T179

B11 17/30:immutable atomic source-facts history with keyset/owner/version provenance;3nativePG cases passed,including synthetic consent change and rollback.

## S157 — 2026-11-03 — B11 18/30 T180

B11 18/30:archive history and factual comparison UI verified;2Chromium+10contract checks/currentbuild passed,source/season/cursor validation and session cleanup.

## S158 — 2026-11-03 — B11 19/30 T024

B11 19/30:every archive number has snapshot/source/separate fetched/source-updated/checked times;6backend+9Chromium passed,failed check preserves old dates;manual model/capture clarified.

## S159 — 2026-11-04 — B11 20/30 T023

B11 20/30:manual-v1 calculation pinned to stored version;16nativePG write/history cases and1Chromium comparison passed,500boundary/equal-time/cursor/version refusal verified.

## S160 — 2026-11-04 — B11 21/30 T035

B11 21/30:durable source check history and recovery without refreshing old facts;24nativePG+migration,1nativequarantine and1Chromium passed;schema0007.

## S161 — 2026-11-04 — B11 22/30 T181

B11 22/30:separate owner-only archive-facts-v1 export and actual JSON download verified;1nativePG+1Chromium passed,currentbuild,no identity/access fields.

## S162 — 2026-11-04 — B11 23/30 T182

B11 23/30:actual SGU573x2 PostgreSQL/raw restore exact across17tables;ownership,history,key continuity,replay/tombstones and corruption refusal passed,measured localtimings.

## S163 — 2026-11-04 — B11 24/30 T025

B11 24/30:96Chromium+102unit passed;explicit source error recovery/401privacy/lostDELETE reconciliation;two backend test assumptions corrected and targeted reruns passed.

## S164 — 2026-11-04 — B11 25/30 T026

B11 25/30:manual/archive keyboard and focus recovery,320px/longnames/million values,8contrastpairs/both themes andactualPDF passed;9currentChromium.

## S165 — 2026-11-04 — B11 26/30 T183

B11 26/30:2nativeAPI/Chromium multi-tab archive privacy cases passed;old facts/history and delayed replies hidden,newowneronly after explicitsync,no automaticbootstrap.

## S166 — 2026-11-04 — B11 27/30 T184

B11 27/30:current0007 containers preserve actual573-row archive acrossrecreate,noexternalfetch;2nginxchecks andowned4service worker/raw/persistence rehearsal passed.

## S167 — 2026-11-04 — B11 28/30 T185

B11 28/30:573rows/20subscriptions/4readers measured;p95 202.24→30.90ms,SQL11120→680,80x200;23+1nativePG cases passed;localonly.

## S168 — 2026-11-04 — B11 29/30 T186

B11 29/30:readonly raw/normalized/key-continuity audit implemented;3nativePG+3SQLite passed;actual private573-row archive audited cleanly withoutHTTP or identifieroutput.

## S169 — 2026-11-04 — B11 30/30 T043

B11 30/30:final452backend/71nativePG/0skip,102unit,100Chromium+2actualNginx passed;privacy scan0matches,actualruntime security and archiveaudit clean;production release blockers recorded.

S169 precommit follow-up: final review found processing-time copy in newly appended archive facts. T043 reopened before its commit;new facts now get actual assessment clock,immutable older records stay intact. Full current backend/native verification repeated,not treated as unchanged452test evidence.

## S170 — 2026-11-04 — B11 final30/30 verification

Reopened precommit audit resolved:source-fact processing time is separate from fetch time without rewriting old records. Current full454backend/72nativePG passed,0skipped;102unit,100Chromium and2actualNginx passed. Repeated real-format archive/rawrestore exact17tables/1146rows. Local currentruntime healthy,private scan0matches,disposable runtimes cleaned. T043done;all30B11tasks complete,nextT031 under a new assignment. Full production/second-source/live/staging requirements remain open.

## S171 — 2026-11-04 — B12 старт до рубежа70%

Новое поручение продолжать до70%. Зафиксирован функциональный рубеж,без пересмотра releasegates. Первая пятёрка:T187,T188,T031,T034,T039. ТекущаяT187;исследуется официальный GUAP как независимый источник,STUheaders-only не считается рабочим. Старые454backend/102unit/100+2browser — проверенный baseline B11.

S171/T187done: multi-scope proof registry,legacy compatibility and refusal gates;38tests passed. T188inprogress. Genuine GUAPcontract profile captured privately581candidate rows,14headers;not yet attested or enabled. SGU second group4576 capture in progress;no coverage claim until independent audit.

S171/T188done: one config-driven parser verified against all573SGU+581GUAPoriginal rows through independentstdlibaudits. JSONconfig replaces university-specific algorithms. GUAPcontract0places/unknownconsent preserved. T031nowinprogress:formal scoped proof/registration/native worker/API path. Header-only otherprofiles remain unconnected.

S171/T031done:GUAPindependent581-rowarchive/allrowsaudited/explicitproof+JSONscope;actualboundedHTTPSworker/nativePGsuccess→idle,primaryruntime2universities1154rows.3native+40local+12negative checks passed. Contract0capacity/unknownconsent preserved,not converted tobudgetprediction. T034inprogress;continueB12milestone70,no prematurefinish.

S171/T034done:versionedconditional list-consentbounds/diff with immutableAssessment and explicitrefusals.11domain+3storage/3nativePGcases passed,reproduction/atomicfailure/cursor/owner/retry checked. Group.scenarioAvailable separatefromofficialassessment. T039inprogress;no70%claim yet,needsUI/replay/changefeed.

## S172 — 2026-11-04 — B12 первая пятёрка завершена

T187/T188/T031/T034/T039done:sharedJSONdecoder,two independently auditedofficialsources,actualGUAPworkerHTTP,immutableconditionalmodel/diff,storedexplanations/UI.3scenarioChromium,17TScontracts,16localmodel/storage/template and3nativePGchecks passed. Exactremainingrubric:replay/changefeed/auditedops/coverage/currentlocalacceptance. Nextfive:T036,T040,T037,T038,T189;T036inprogress. Do notfinishatfive orrelabelfrom60to70withoutfunctionalproof.

S172/T036done:two nativePG replayruns,6stages,identicalsemanticoutcomes/0HTTP/cleanuptrue. Genuine-derived baselines+explicitlysyntheticconsent/template/failure/recovery/absence,no live-soakclaim. T040inprogress:ownerchangefeed/seen-state;continue to70rubric.

S172/T040done:private deduped changes,stable seen/cursors,exact storedversioncomparison.3local+3nativePG+23migration+6TScontracts+4actualAPIChromium passed. T037inprogress;remainingops/coverage/finalacceptance.

S172/T037done:0009operatoraudit/explicitcontrols,quarantine fences leases andpublication,resume respectsinterval/refresh_pending.6local+2nativePG+23migration passed. T038inprogress;then fullcurrentacceptance.

S172/T038done:DB-derived reviewed/imported/archive/conditional/automatic metrics anddates,1154rows/2archivegroups/1conditional/0fresh validated.8local+1nativePG+TScontract/build passed. T189inprogress:fullcurrentchecks/deploy/demo/privacy before70claim.

## S173 — 2026-11-04 — B12 10/10, функциональный рубеж около 70%

T189done: все6заранее объявленных критериев выполнены. Текущие0009Dockerобразыhealthy8090,2настоящихархива/1154строки/1условнаягруппа/0fresh.502backend(85nativePG/0skip),115unit,100baseline+4new+2nginxbrowser passed;ещё2coverage повторенына2источниках. Replay2x6identical,exact19table/rawrestore сохраняетscenarios/events/seen;2actualruntimearchiveaudit/private1154codeaudit0matches. Исправлены только изоляция браузерных артефактов и старые mocked-session fixtures,контрольдоступа не ослаблялся. Две пятёрки завершены;statecurrentnull,nextT042. Временныеfixtureпроцессы очищены,основной8090оставленработать. Release/live24h/HTTPS/remoteCI/национальныйохват остаются неподтверждёнными;gates не снижены.

## S174 — 2026-11-05 — B13 работа до MVP и аудит

Поручение: закрыть оставшиеся задачи, проанализировать уязвимости и недочёты, запушить без пометки ассистента. Работа в ветке `mvp-readiness`, main не менялся. T042: карта всех случаев QUALITY, найден ложноположительный статус при завышенном числе мест, добавлены capacity_growth и capacity_mismatch. T041: heartbeat, /api/status, runId и trace. T044: профиль Q12 выявил 49% 5xx и публикацию 23 с; после линейного расчёта и чтения только нужных колонок на том же стенде 0 5xx и 11,9 с под стрессом. Статус review до staging. Независимый аудит: 15 находок, исправления в API, worker, nginx и production-конфигурации, таблица статусов в evidence. T006, T045, T047 закрыты удалённым прогоном 41928404413. Замена reload на location.replace не исправила WebKit-сценарий и отменена, ограничение записано. T046, T048–T052 заблокированы внешними условиями с записанной причиной; ничего из них не объявлено выполненным.


## S175 — 2026-11-05 — национальный охват как ближайший приоритет

## S176 — 2026-11-05 — B14: начало национального каталога

Пользователь поручил выполнять национальный охват. Первая пятёрка T190–T194: опорный официальный перечень и границы; импорт; поиск/API/UI; инвентаризация источников; следующий подтверждённый scope или семейство. T190 in_progress; acceptance — воспроизводимый snapshot, сверка полноты по регионам и явные исключения. Мониторинг MICCEDU выбран первым опорным источником; он не включает все лицензированные организации и не заменяет полный национальный реестр. Старые T056/T057 остаются открытыми, release gates сохраняются.

Пользователь повторно подтвердил необходимый охват всей России. Прежние 80% относятся к ограниченному MVP; национальный процент неизвестен. Проверены catalog.py, reviewed.json, регистрация профилей и отчёты: 2 архивные группы, 1 условный сценарий, nationalTotal=null. T056/T057 перенесены из после-MVP в E1/E3 с P0; зависимость от T055 снята, T057 следует за T056. Суточное наблюдение остаётся обязательным до заявления свежести. Обе задачи todo, done не добавлены. PRODUCT/DECISIONS/STATE и план пяти открытых результатов обновлены. Next T056: официальный датированный реестр и состав каталога; национальные данные ещё не импортированы. Перед уточнением прошли 115 Vitest, production build и 32 backend-теста расчётов; при изменении только плана не повторялись. Проверки: roadmap --render/--check/--next и git diff --check.

S176/T190: 1257 unique institutions, 521 branches, 89 regional pages; headline total matched; offline replay identical; 3 parser checks passed. Monitoring exclusions retained. Evidence: docs/evidence/b14-national-catalog.md. Next: T191.

S176/T191: Validated atomic read-only artifact import, 1257 identities and 521 branches, legacy aliases preserved; 12 targeted checks passed; no Source or user DB mutation. Evidence: docs/evidence/b14-national-catalog.md. Next: T192.

S176/T192: 1257 directory entries searchable with region/branch and pagination; 1166 site URLs, 91 unknown; 21 backend, 116 Vitest/build, compiled Chromium 12 passed/2 fixture-only skips. Screenshot inspected. Evidence: docs/evidence/b14-national-catalog.md. Next: T193.

S176/T193: All 1257 reference institutions inventoried, 1083 unique HTTPS pages, 641 with candidate links; all unknown/errors explicit; 3 tests passed and offline replay identical. No automatic source enabled. Evidence: docs/evidence/b14-national-catalog.md. Next: T194.

S176/T194/B14 final 5/5: новый scope SGU4576, 453 original rows/24 места, независимая сверка и синтетический fixture. Фактический HTTPS выявил перестановку альтернатив экзаменов: добавлена отдельно аттестованная v2 общего parser, v1/старые профили не переписаны. Реальный bounded HTTPS→worker→native PG→stored audit прошёл; schema удалена. Final571 backend passed/0 skipped с require-postgres,116 Vitest/build,77 compiled Chromium passed/32 scoped skips. Все 5 задач отдельными Conventional Commits; T056/T057 не закрыты, национальная автоматизация не объявлена. Next T057: реальные страницы списков и массовые семейства; полный лицензированный реестр T056 отдельно недоступен. Итог docs/evidence/b14-final-verification.json.

## S177 — 2026-11-05 — B15: продолжение национального подключения

Пользователь поручил доделывать. Первая пятёрка этого подхода T195–T199: проверка страниц приёма; повторяемые структуры; масштабируемый реестр профилей; аттестация новых настоящих источников; многоисточниковая очередь/покрытие. Одна active T195, проверки до реализации: offline replay, bounded HTTPS provenance и отсутствие ложной аттестации. B14 baseline571 native backend/116 Vitest/77 Chromium+32scopedskips сохранён, лишний раз не повторяется. T056/T057 остаются широкими открытыми задачами.

S177: T195 review — код и6unit checks готовы, финальный bounded crawl ещё выполняется. Чтобы не ждать сеть, активирована независимая T197 (dependsT194done). Одна in_progress соблюдается; исходные статусы/история B14 не меняются. Проверка T197:1001synthetic profiles, immutable hashes/legacy equivalence и негативные manifest cases.

S177/T197: Immutable manifest/shards preserve all 3 old scopes; 1001 synthetic profiles loaded in 11 shards; 48 native-PG targeted tests passed, 0 skipped. No real coverage added. Evidence: docs/evidence/b15-profile-catalog.md. Next T195.

S177/T195: 1257 reference entries reconciled; 633 institutions/1073 URLs selected and observed; 6 unit checks and identical offline replay passed. Candidate table evidence remains incomplete/unattested; no sources enabled. Evidence: docs/evidence/b15-admissions-inventory.md. Next T196.

S177/T196: 14 verified official child pages; 1 cross-institution structural candidate (MIEPP/UIFR), not automatic eligibility; 8 targeted tests and identical offline replay passed. Empty/header-only pages remain unsupported. Evidence: docs/evidence/b15-format-families.md. Next T198.

S177/T198: 11 reviewed archive scopes across 2 new institutions, 168 independently audited rows; actual bounded HTTPS to worker/PG and 11 stored audits passed. Native targeted 68 passed, completeness follow-up 23 passed, 0 skipped. Evidence: docs/evidence/b15-section-family.md. Next T199.

S177/T199/B15 final5/5: Native PG queue:1000 synthetic jobs/100 domains,12 claim threads,100 fenced recoveries,no duplicate completions. Real HTTPS:14 archive scopes/4 institutions/1775 rows,13 fetches/1 cache hit. Final627 backend/0skip,116Vitest/build,79compiled Chromium/32scopedskips,5actual-nginx checks passed. Evidence: docs/evidence/b15-final-verification.json. Owned disposable PG schemas removed; test containers/network removed. Persistent local demo8091 retained with4services and daily archive rechecks. After API recreation all14stored audits/1775rows passed with same key. Initial broad nginx browser run hit six expected429 and one test-selector error; corrected selector, fullcompiledpreview79pass/32skip and targetednginx5pass without lowering limits. Old artifacts/proofs preserved. NextT057: other exact source families and scale limits; T056/T057 remain open, nationalTotal=null, no full-country or live-release claim.

## S178 — 2026-11-05 — B16

Пользователь поручил продолжать. Пятёрка T200–T204: полный выбор вузов, SQL фильтры групп, atomic batch профилей, исследование следующего формата и итоговая проверка. Одна activeT200, проверки сформулированы до реализации. B15baseline сохранён; demo8091/key/volumes не пересоздавать. T056/T057 открыты.

S178/T200: Full directory search/pagination, retained selection and next-page retry at320px;116Vitest/build and4compiledChromium passed. Evidence: docs/evidence/b16-university-filter.md. Next T201.

S178/T201: SQL filters/count/cursor/limit preserve Unicode and literals;10001 synthetic groups hydrate<=8 for page7. Migration0011 backfill/reversal/offline PG passed;34 targeted+4 expanded native checks,0skipped. Evidence: docs/evidence/b16-sql-catalog.md. Next T202.

S178/T202: Atomic1-100 exact manifest IDs, shared catalog mutex, late-conflict/quarantine rollback and legacy preservation;41targeted+14expanded native checks passed,0skip. Evidence: docs/evidence/b16-profile-batch.md. Next T203.

S178/T203: 5official pages/3institutions, verified linked BGU bachelor with109visible rows; stateful/dynamic/level gaps explicit.3synthetic tests and network-forbidden identical offline replay passed;0sources attested. Evidence: docs/evidence/b16-stateful-research.md. Next T204.

S178/T204/B16 final5/5: Final648backend/0skip,116Vitest/build,83compiledChromium/30scopedskips and12finalactual-nginx checks passed. Restored-copy0010->0011 preserved19tables; actual demo14stored audits/1775rows passed with original key/volumes. Real coverage unchanged14archivegroups/4universities; research0newattestations. Evidence: docs/evidence/b16-final-verification.json. Derived Unicode search fields only; old source facts unchanged. First SQL seed-default compatibility error corrected with explicit folded seed values. Initial duplicate ADR ID corrected to030, SQL decision031. Final visual follow-up aligns fields and passes12affected tests after rebuild. Owned native schemas/testcontainers/network and preview5272 removed; working demo8091 retained with4services/daily archive queue. NextT057: exact stateful BGU bachelor scope; full national denominator and live/staging/release gates remain open.

## S179 — 2026-11-05 — B17

Пользователь поручил идти дальше. Пятёрка T205–T209: точный scope БГУ, общий filtered decoder, независимая аттестация, native worker/lookup, стенд/регрессия. Одна activeT205. В подготовительной диагностике ancestor span захватил строки списка в одном выводе; фильтр исправлен на leaf/no-table, реальные строки не пишутся в tracked reports/fixtures. Далее только агрегаты/public metadata. Минимальный lookup ID должен обходиться без СНИЛС/трёхчастного кода. B16baseline648native/116Vitest/83Chromium+30skip/12edge сохранён, demo8091/key/volumes не заменять.

S179/T205: Fresh official exact contract/full-time construction scope:20seats/109rows/109unique minimal lookup IDs,14explicit enrolled; controls/count/order reviewed,0attestations yet. Evidence: docs/evidence/b17-bgu-scope.md. Next T206.

S179/T206: Generic filtered version,109synthetic rows, closed scope/count/roles/minimal-ID/enrollment checks;65native targeted passed,0skip. Legacy profiles/proofs unchanged; no runtime attestation yet. Evidence: docs/evidence/b17-filtered-family.md. Next T207.

S179/T207: All109original rows independently matched,20seats/14explicit enrolled; immutable exact BGU profile added,old14unchanged.46native targeted passed/0skip; Source not enabled by attestation. Evidence: docs/evidence/b17-attestation.md. Next T208.

S179/T208: Actual bounded HTTPS->worker->native PG->independent/current/stored audit109rows/20seats passed.7native owner/API tests,116Vitest/build and1synthetic browser lookup/privacy/save passed. Evidence: docs/evidence/b17-worker-lookup.md. Next T209.

S179/T209/B17 final5/5: Final666backend/0skip,116Vitest/build,84compiledChromium/31scopedskips,1syntheticBGUlookup and18actual-nginx checks passed. Actual demo15archivegroups/5universities/1884rows, old14snapshots/1775rows unchanged and15stored audits passed. Same key/volumes/schema0011; pagination-focus defect fixed and verified with held real response. Evidence: docs/evidence/b17-final-verification.json. New contract scope20seats/109rows independently checked, minimal5digit lookup only; all current JS/CSS lazy bundles equal localdist. First broad browser run83pass/31skip/1fail; fixed focused-disabled-button blur and final84pass/31skip. Synthetic lookup uses fake data; real demo browser accesses public metadata only. Remaining disposable schemas0, owned B17containers/network removed, temporary8028/5273/5274 stopped; four realdemo services and private backups retained. Original national-catalog-mobile.png restored, new B17desktop/320px screenshots reviewed. NextT057: other exact official source scopes from the inventory; T056/T057/live/staging/release gates remain open.

## S180 — 2026-11-06 — B18 CI repair

Пользователь сообщил2cancelled/3success/1failure и поручил продолжать. Приоритет временно изменён с T057 на пятёрку T210–T214: реальные логи, mobile failure, timeout/Firefox, workflow diagnostics/local checks, push/зелёный remote run. Одна activeT210. Git clean at c44c21c, обычный push разрешён предыдущим указанием. Demo и данные не менять.

S180/T210: Exact remote logs: mobile confirmation focus failure, Firefox2Tab-focus failures, Azure apt mirror22m35s download; checks15m andFirefox25m timeout. Backend666 andcontainers passed. Evidence: docs/evidence/b18-ci-diagnosis.md. Next T211.

S180/T211: Confirmation focus moved to committed preview layout effect; old8cases reproduce3failures, fixed63source cases passed acrossChromium/Firefox/mobileChromium,0skip;116Vitest/build passed. Evidence: docs/evidence/b18-confirmation-focus.md. Next T212.

S180/T212: Firefox scroll-container Tab stop corrected;27keyboard/catalog checks passed across3browser projects,0skip. Ubuntu24.04 pinned; Azure apt mirror replaced with official HTTPS archive; install bounded5min, overalltimeouts unchanged; bash/YAML checks pass. Hosted verification T214. Evidence: docs/evidence/b18-runner-and-firefox.md. Next T213.
