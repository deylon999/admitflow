# Возобновление и эксплуатация

## Начало каждой сессии

1. Прочитать корневой AGENTS.md и STATE.md.
2. Из `abiturient/` выполнить `python scripts/roadmap.py --check`, `--next`, `git status --short`.
3. Открыть карточку задачи и её зависимости, прочитать последние записи LOG.
4. Проверить наличие частичных файлов, процессов и результатов прерванных команд. Старый PID не считать живым без проверки команды/порта.
5. Выбрать доступную задачу, поставить `in_progress`, задать `currentTask`. При изменении приоритета объяснить причину в LOG.
6. Сформулировать ожидаемый наблюдаемый результат и проверку перед изменением кода.

При остановке сохранить маленькую передачу: задача, какие файлы изменены, какая последняя команда завершилась, что остаётся, точная следующая команда. Одной фразы «продолжить backend» недостаточно.

## Статусы задач

`todo` → `in_progress` → `review` → `done`.

`blocked` требует непустого `blockedReason` и условия снятия. `deferred` — перенос объёма с записью ADR/LOG. Отмена старого требования не стирает задачу: её помечают deferred с причиной. Для возврата done в работу очистить старый статус, сохранить старое evidence в журнале и добавить причину повторной проверки.

Все зависимости задачи должны быть done до начала её реализации. Исследовательские задачи с независимыми входами оформляются отдельно, чтобы блокировка сборки не задерживала исследование источников. Состояние `review` не считается выполненной зависимостью.

## Команды приложения

### Docker

Нужен запущенный Docker Desktop с Linux containers. Из корня репозитория:

```powershell
docker compose up --build
```

Сайт — http://localhost:8080, API-документация — http://localhost:8080/api/docs. Nginx отдаёт React и проксирует API с того же адреса. PostgreSQL и API доступны только внутри Docker-сети: хостовый порт 8000 не нужен. Зависимости устанавливаются внутри образов; локальные Node/Python не требуются.

```powershell
docker compose down          # остановить; данные сохранятся
docker compose logs backend # логи API
docker compose ps           # состояние сервисов
```

База хранится в volume `postgres_data`. Не добавлять `--volumes` к down, если данные нужно сохранить. Перед API контейнер выполняет `alembic upgrade head`; create_all в Compose отключён. Это локальный development-запуск с тестовыми реквизитами PostgreSQL. Production/HTTPS остаются отдельными задачами.

Если 8080 занят, задать `$env:WEB_PORT='8081'` перед запуском. При недоступном Docker Engine сначала дождаться готовности Docker Desktop. В текущей ограниченной среде `docker compose config --quiet` проходит, но сборка/запуск контейнеров пока не подтверждены из-за доступа к Engine и контексту сборки.

При `Unexpected check constraints in snapshots` на старой БД первая миграция могла отвергать PostgreSQL-представление того же CHECK: сервер возвращает SQL после разбора со скобками/casts, а прежняя проверка сравнивала текст с исходником. Исправление T103 сравнивает обе стороны после обработки тем же сервером. Пустая временная таблица содержит только замороженные колонки/CHECK миграции, удаляется после проверки и имеет ON COMMIT DROP; пользовательские таблицы/строки не копируются и не меняются этой проверкой. Реальные отличия выражений, строковых литералов, NOT VALID/NO INHERIT по-прежнему отклоняются. Нужна обычная привилегия TEMP в БД; при её отсутствии проверка остановится, а не пропустит constraints. Причина формата описана в [PostgreSQL pg_get_constraintdef](https://www.postgresql.org/docs/17/functions-info.html).

После получения исправленного кода из корня репозитория: `docker compose up --build -d`, затем `docker compose ps` и `docker compose logs --tail=80 backend`. Пересборка необходима: код API копируется в образ, bind mount исходников нет. Команда сохраняет существующий volume. Не сбрасывать БД и не выполнять stamp для обхода проверки. Если ошибка остаётся, посмотреть только определения ограничений, без пользовательских строк:

```powershell
docker compose exec -T db psql -U admitflow -d admitflow -c "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'snapshots'::regclass AND contype = 'c';"
```

Локальные SQLite-регрессии и PG offline SQL не подтверждают исправность запуска PostgreSQL. T103 остаётся review до успешного upgrade существующей PG-схемы с сохранением IDs/истории и healthy backend; в TEST_DATABASE_URL включены отдельные реальные PG-регрессии в изолированных тестовых схемах.

Для быстрой проверки уже запущенного сайта из `backend/`: `.venv/Scripts/python.exe tests/runtime_smoke.py`. Другой локальный порт: `--base-url http://127.0.0.1:8081`. Требуется httpx из requirements-dev.txt; удалённые адреса и реквизиты в URL не принимаются. Скрипт создаёт две новые гостевые сессии, проверяет readiness/OpenAPI, CRUD, безопасный повтор, два сохранения после нового HTTP-соединения, экспорт и ownership. В finally пытается удалить только эти сессии; ошибка cleanup означает неуспешную проверку. Отчёт без cookies/owner hashes и конкретных watch IDs — docs/evidence/t103-docker-smoke.json. Это HTTP smoke, он не определяет движок БД, commit образа или revision и не доказывает сохранность данных после миграции/перезапуска. Не выдавать 15 успешных запросов за семь реальных PG migration-тестов.

### Без Docker

T002/T003 выполнены: сборка и unit-тесты проходят. Frontend и backend запускаются из своих директорий.

```powershell
# Из abiturient/frontend/
npm ci
npm run dev
npm run build
npm test
```

Dev: `http://127.0.0.1:5173`; preview: `http://127.0.0.1:4173`. В обоих локальных режимах proxy `/api` направлен на `127.0.0.1:8000`. В production нужен отдельный reverse proxy.

```powershell
# Из abiturient/backend/
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
# Только при первом запуске, если .env ещё отсутствует:
Copy-Item .env.example .env
.venv/Scripts/python.exe -m uvicorn app.main:app --env-file .env --host 127.0.0.1 --port 8000 --no-access-log
.venv/Scripts/python.exe -m pytest -q
```

Нужен Python 3.12. `--env-file .env` явно загружает настройки при запуске Uvicorn; приложение само не читает файл. Без флага используются переменные процесса и defaults. Локальная SQLite при development lifespan обновляется миграциями; production upgrade выполняется отдельно. Серверные тесты запускаются из собственной .venv проекта. Чистая установка ещё требует отдельного подтверждения: pip ранее блокировался WinError 10013.

```powershell
# Из abiturient/frontend/, один раз при установке браузера:
npx playwright install chromium
npm run test:e2e
# Для реального сквозного CRUD сначала запустить API, затем:
$env:E2E_API='1'
npm run test:e2e
```

Без E2E_API тесты, требующие реального API, явно skipped. С E2E_API=1 выполняется полный набор; актуальное число и результат — docs/STATE.md. Используется обычный Chromium: один worker локально, два в CI. Режим single-process не используется: он зависает при повторном создании контекста. При зависании остановки дочернего Vite на Windows запустить `npm run dev` в отдельном терминале до тестов — Playwright переиспользует сервер.

`.github/workflows/ci.yml` устанавливает зависимости, проверяет TS/Python/roadmap и запускает браузерный CRUD с настоящим API. Удалённый прогон ещё не выполнен, T006 остаётся открытой.

### Гостевые сессии

### Миграции

Из backend с настроенными переменными окружения: `.venv/Scripts/python.exe -m alembic upgrade head`. Состояние — `-m alembic current`, соответствие моделей — `-m alembic check`. В Docker upgrade выполняется перед запуском API и при ошибке не запускает приложение.

Начальная ревизия содержит замороженную схему, не импортирует текущие модели приложения. Старые базы create_all принимаются только при совместимых колонках, ключах и CHECK-ограничениях; существующие направления и история сохраняются. Неожиданная структура останавливает upgrade до изменения доменных таблиц. Перед миграцией рабочей БД нужен backup. Нельзя решать ошибку удалением volume или слепым stamp.

Начиная с 0003 development API при AUTO_CREATE_SCHEMA=true выполняет Alembic upgrade head вместо create_all. Историческая схема 0001/0002 принимается с проверкой; новая произвольная unversioned-схема не угадывается. В production миграция остаётся отдельным шагом. SQLite batch 0003 временно отключает FK только в migration connection и проверяет foreign_key_check перед завершением; обычные соединения сохраняют FK. Существующие source snapshots получают неизвестный parser/provenance, без выдуманной аттестации. Downgrade после нескольких parser versions одного raw может быть невозможен из-за прежнего unique constraint; использовать backup, не форсировать откат.

Локально проверены пустая/старая/несовместимая SQLite, повторный upgrade, downgrade только в одноразовой тестовой БД, и компиляция SQL для PostgreSQL. Реальный PostgreSQL-тест включается TEST_DATABASE_URL с именем базы admitflow_test*; в CI есть отдельный PostgreSQL service. Пока удалённого результата нет, T014 остаётся review.

Срок доступа — 30 дней с создания, без продления при открытии страницы. GET `/api/v1/session` возвращает дату истечения. DELETE этого же endpoint удаляет сессию, направления и историю; запись требует обычного защитного заголовка. Просроченный cookie не создаёт новую сессию автоматически. При потере cookie локальная отметка требует явного подтверждения нового начала. Если браузер удалил одновременно cookies и localStorage, отличить его от первого посещения невозможно; предупреждение о сроке постоянно видно в кабинете.

API очищает просроченные сессии раз в час. Локальный запуск с автоматическими миграциями также делает очистку при старте. Ручная команда из backend с настроенным DATABASE_URL: `.venv/Scripts/python.exe -m app.maintenance cleanup-sessions`. Данные чужих активных сессий не затрагиваются.

## Перед релизом — будущий процесс

1. Убедиться, что release candidate соответствует конкретному commit; working tree и версия документированы.
2. Прогнать unit, API, PostgreSQL integration и E2E на кандидате.
3. Собрать frontend/backend images с закреплёнными версиями; сохранить идентификаторы.
4. Выполнить backup и проверить доступность предыдущего release.
5. Применить миграции в staging, затем в целевой среде. Потенциально разрушающие миграции отделять от обычного запуска.
6. Развернуть API/worker/frontend, проверить health/readiness и наблюдать первый цикл источников.
7. Smoke: новая сессия, поиск, сохранение, обновление, история, источник, смена темы, удаление и изоляция.
8. Записать фактический URL, версию, время, результаты и ограничения. Только после этого gate G6 пройден.

Если площадка недоступна, оставить готовый локальный результат и точный блокер. Не создавать новый Site/аккаунт/ресурс для обхода ошибки. Не сохранять credentials в STATE/LOG.

## Инциденты

Граница fetch-процесса не использует Pipe.recv после частичной готовности: parent ждёт завершения дочернего процесса в общем monotonic deadline (по умолчанию 50 секунд). Child пишет private bounded spool (до 5 MiB bytes и 16 KiB metadata), parent проверяет size/hash/schema после завершения. Частичный результат, неверный envelope или незавершённый процесс не публикуются; известные временные файлы удаляются без рекурсивного обхода. Завершение/kill имеют отдельные ограниченные join, это не hard realtime SLA и не проверка живого источника.

Несохранённая форма направлений защищена при закрытии, смене формы и переходе по обычной ссылке: отказ от подтверждения сохраняет ввод. Успешное сохранение и неизменённая форма подтверждения не требуют. Для обновления/закрытия вкладки используется browser beforeunload, если браузер его поддерживает. Это не полная проверка навигации всех платформ: back/forward внутри SPA, аварийное закрытие и восстановление браузера остаются частью T026/T045; черновик не сохраняется на диск или сервер автоматически.

B05: удаление редактируемого направления сначала подтверждает потерю черновика, при ошибке записи форма сохраняется. Inline-подтверждения ставят фокус на безопасную отмену; Escape возвращает к кнопке. При сбросе в другой вкладке прежний черновик скрывается для защиты сменившейся ownership; нужна явная readonly синхронизация. Межвкладочное событие требует доступного localStorage и не отменяет уже совершённую запись.

Кнопка «Обновить направления» и возврат в вкладку перечитывают серверные ручные записи. Ошибка фонового чтения оставляет кешированные карточки с предупреждением и исходными датами, 401 скрывает их. Форма сохраняет локальный ввод при обновлении. Срок гостевого доступа показан по expiresAt сервера, не продлевается просмотром.

Печатный отчёт содержит отфильтрованные сохранённые направления, исходные числа/дату/ссылку и ограничения. Браузерный print-dialog позволяет печать/PDF; в тесте проверен Chromium print media, физический принтер/все браузеры не проверены. Таблицы истории имеют именуемую область фокуса и горизонтальную прокрутку стрелками; выбор пары относится к уже загруженным страницам. Общий total/остаток500 виден после загрузки истории, не блокирует серверную проверку лимита.

Readiness теперь требует текущей Alembic revision. После выкладки нового кода старую/пустую БД нельзя считать ready только по доступности соединения. /api/live остаётся200 при отказе БД; /api/ready и /api/health дают503 при ошибке/несовместимой revision. Не исправлять readiness ручным stamp: сначала проверить схему и выполнить штатные миграции. Runtime HTTP smoke на8080 из S059 не доказывает наличие более нового кода B05 в том образе.

B06 production configuration: ENVIRONMENT принимает только development/production; SECURE_COOKIE/AUTO_CREATE_SCHEMA — только true/false (регистр boolean не важен). Неизвестное значение останавливает запуск, вместо перехода в development. Production требует PostgreSQL, HTTPS PUBLIC_ORIGIN, SECURE_COOKIE=true и AUTO_CREATE_SCHEMA=false, включая прямой Settings-конструктор. Прежнее явное AUTO_CREATE_SCHEMA=true больше не игнорируется молча: исправить конфигурацию. Ожидание PostgreSQL connection по умолчанию5секунд, connect_timeout в URL разрешён1–10; ожидание свободного соединения pool5секунд. Statement/runtime timeout всей БД этим не проверен. Тест с локальным TCP-партнёром, который не завершает PG handshake, не является настоящим PostgreSQL migration-тестом.

Сборщик отвергает обрезанное тело при несовпадении Content-Length (incomplete_response, retry60), критичные повторные заголовки и противоречивое framing. Политика консервативна: не восстанавливать неоднозначный ответ догадкой. Основание — [RFC9112, message body length](https://www.rfc-editor.org/rfc/rfc9112.html#section-6.3). FetchPolicy требует immutable frozenset точных lowercase DNS-имён, размер1..5MiB, конечный timeout до30секунд, redirects0..5 и поддерживаемые MIME. Wildcard/IP/изменяемое множество/NaN/bool вместо числа отклоняются до сети. Adapter declaration требует настоящий bool attested, version token и callable; это проверка объявления, не аттестация содержимого parser.

fetch_cleanup_incomplete/fetch_process_cleanup_incomplete — безопасный код неполной очистки private spool/process. Ошибка очистки не подменяет исходный результат fetch, остальные известные файлы проверяются; рекурсивного обхода нет. Возможны приватные остатки в temp, их автоматическая retention ещё не реализована. Не трактовать код как raw payload/URL, не расширять права для обхода отказа. Eligible explicit enqueue применяет новые interval/max_attempts; running и backoff job остаются без изменений до разрешённого перехода.

Ошибка lazy-модуля/React render показывает fallback с фокусом заголовка и явной перезагрузкой. Автоматического retry или POST session этот экран не делает; загрузку самого начального bundle при полном отказе сети он не восстанавливает. Скриншот error-recovery-mobile.png — контролируемая имитация отказа модуля, не объявление постоянной недоступности сайта. Начальная конкуренция вкладок проверена в Chromium с Web Locks; браузеры без Web Locks не получили гарантии атомарного первого bootstrap.

В кабинете ручную историю можно перенести через «Скачать данные (JSON)» → «Восстановить из JSON». Клиент проверяет файл до 8 MiB и показывает число направлений/сохранений; запись только после подтверждения. Перед отправкой JSON нормализуется без форматирующих пробелов. Лимит проверен на 20×500 снимках с полными IDs/числами; прежние 6 MiB могли отклонить собственную максимальную выгрузку. Ключ импорта определяется нормализованным содержимым, поэтому повтор файла в той же сессии безопасен даже после потери ответа. Отмена выбора ничего не записывает. Ошибочный файл не отправляется; сервер отдельно проверяет даты/лимиты/формулы и записывает всё одной транзакцией. Файл не переносит cookie и не открывает старую сессию. Не публиковать выгрузки с личными названиями направлений.

### Локальная резервная копия SQLite

После настройки DATABASE_URL и RAW_STORE_PATH из backend: `.venv/Scripts/python.exe -m app.backup create --output ./var/backups`. Команда использует SQLite online backup и под общей raw-блокировкой копирует только исходные файлы, на которые ссылается сохранённая БД, включая старые снимки. Manifest содержит SHA-256 БД и список raw; незавершённая копия не появляется под именем backup-*. Timeout/отсутствующий raw не выдаются за успешную копию. Каталог приватный и исключён из Git; он содержит всю ручную историю и ownership hashes, не публиковать. Это локальная SQLite-процедура; PostgreSQL backup/restore, внешний носитель, расписание и измеренные RPO/RTO ещё не проверены.

Проверка: `.venv/Scripts/python.exe -m app.backup verify ПАПКА_КОПИИ`. Восстановление: `.venv/Scripts/python.exe -m app.backup restore ПАПКА_КОПИИ --destination ./var/recovery-НОВОЕ_ИМЯ`. Назначение должно отсутствовать; занятая папка не перезаписывается. Проверяются hash БД/raw, integrity/FK, revision, полнота ссылок и отсутствие неожиданных views/triggers; затем файлы копируются в новое окружение и проверяются снова. Папка резервируется атомарным mkdir; проверенные файлы передаются через hard links в пределах одного файлового тома, без замены существующих файлов. Нужна поддержка hard links файловой системой. Ошибка после резервирования оставляет `restore.pending`: verify, миграции и запуск API отказываются использовать такую папку. Не удалять маркер для обхода проверки: повторить restore в новую отсутствующую папку, затем отдельно осмотреть остаток. Хеш — проверка целостности, не подпись доверенного автора: брать только свои копии. Для запуска на восстановленной БД явно указать DATABASE_URL=sqlite:///./var/recovery-ИМЯ/database.sqlite3 и RAW_STORE_PATH=./var/recovery-ИМЯ/raw; сначала миграции и smoke, без переключения рабочего API вслепую. Существующие cookies сохраняют ownership только если сессия ещё не истекла; новая сессия не получает чужие направления.

HTTP-диагностика: /api/live проверяет процесс без БД; /api/ready и совместимый /api/health проверяют SELECT 1, при недоступной БД — 503. Ответы содержат новый X-Request-ID, клиентский ID не отражается. Журнал admitflow.http пишет JSON: requestId, method, шаблон route (без подставленных ID/query), status, durationMs. Тело, cookie, IP, заголовки и текст исключения не пишутся. Uvicorn запускать с --no-access-log, чтобы стандартный журнал не дублировал сырой URL; Docker/CI-команды обновлены. Неожиданная ошибка JSON endpoint получает общий 500 с requestId; streaming endpoints не используются.

Для production обязательны точные ALLOWED_HOSTS (например admitflow.example) и PUBLIC_ORIGIN (например https://admitflow.example). Wildcard, лишний путь, иной host и HTTP origin не принимаются. Это дополняет PostgreSQL/SECURE_COOKIE; домен здесь только пример, реальная площадка не выбрана. Nginx передаёт Host, публичный Origin сравнивается с явной настройкой и не определяется из недоверенного X-Forwarded-Host.

### Worker и управление источниками

Из backend с настроенным DATABASE_URL и после `.venv/Scripts/python.exe -m alembic upgrade head`:

```powershell
.venv/Scripts/python.exe -m app.sources.cli list
.venv/Scripts/python.exe -m app.sources.cli status SOURCE_ID
.venv/Scripts/python.exe -m app.sources.cli enqueue SOURCE_ID
.venv/Scripts/python.exe -m app.sources.cli disable SOURCE_ID
.venv/Scripts/python.exe -m app.worker once
.venv/Scripts/python.exe -m app.worker loop --poll-seconds 5
```

CLI/worker читают переменные окружения, сами .env не загружают. RAW_STORE_PATH задаёт приватное хранилище, по умолчанию ./var/raw относительно backend. Для production — отдельный writable volume и проверенные права, не web root. Worker запускается отдельным процессом; в Compose текущего API он автоматически не включён.

Registry production сейчас пуст: CLI enqueue отклоняет неподключённый/неаттестованный адаптер до загрузки. Тестовые адаптеры не доступны из CLI, нет флага обхода аттестации и регистрации произвольного URL. `once` без заданий выводит idle/exit 0; ошибка задания — failed/exit 1; loop продолжает bounded polling. Конфигурацию источника, сезон, правила и адаптер нужно аттестовать кодом и реальными fixtures перед enable. Disable отзывает lease, не удаляет историю и не возвращает coverage автоматически.

Загрузка выполняется в отдельном дочернем процессе с общим пределом 50 секунд, включая DNS; затем parse/validate/store/publish. При публикации повторно проверяются binding, enabled и token аренды. Запоздалый worker не может публиковать за нового владельца. Падение после DB commit до подтверждения задания безопасно воспроизводится без второго снимка. Неизвестные ошибки записываются как internal_error, текст исключения/raw/public ID не логируются. После crash/unavailable следующий claim возможен по lease/backoff; постоянный форматный отказ требует оператора.

RawStore хранит исходные bytes вне web root (`backend/var/raw` по умолчанию), имена — SHA-256. Каталог исключён из Git; его нельзя публиковать Nginx или отдавать через API. Запись через временный файл/fsync/атомарное создание ссылки, повтор проверяет существующий hash. На Unix новые файлы/каталог имеют ограничения временного файла/0700; на Windows необходимо проверить ACL владельца при развёртывании. Сроки очистки и backup сырого хранилища остаются частью T049, автоматическое удаление пока не включено.

Локальная очистка orphan raw: `.venv/Scripts/python.exe -m app.sources.retention --days 7` выводит dry-run; только `--apply` удаляет. Удаляются лишь файлы SHA-256 старше указанного возраста (1–365 дней), не упомянутые ни одним SourceSnapshot. Symlink/неизвестные имена не обходятся, ошибка чтения БД останавливает удаление. Межпроцессная .store.lock удерживается от raw put до commit публикации и на всём cleanup, чтобы orphan не стал referenced во время удаления. Cleanup не удаляет историю БД, capture bundles и незавершённые .writing-файлы. При файловом отказе после части удалений CLI сообщает partialDeletionPossible; повторить dry-run. Расписание очистки не включено автоматически; production retention/PG restore остаются T049.

Очередь source_jobs (0004): одна строка на источник, queued/running/idle/failed. После успеха — idle до следующего интервала (по умолчанию 900 секунд); после временного отказа — ограниченный backoff с Retry-After и интервалом. 5 попыток по умолчанию, затем failed до явного enqueue после cooldown. Claim выдаёт новый token с lease 120 секунд; предыдущий token после expiry/повторного claim не может подтвердить результат. SQLite конкурентный claim проверен; PostgreSQL FOR UPDATE SKIP LOCKED пока только скомпилирован, настоящий многопроцессный PG-тест остаётся обязательным. Disable отзывает lease и сохраняет последний опубликованный снимок.

Для изолированной браузерной проверки можно запустить API на 8001, frontend с `$env:API_TARGET='http://127.0.0.1:8001'` и `npm run dev -- --port 5180`. Перед тестами задать `$env:E2E_API='1'` и `$env:E2E_BASE_URL='http://127.0.0.1:5180'`. Без переопределений остаются порты 8000/5173. Не останавливать занятые процессы, не установив их владельца и назначение.

### Некорректный список

Остановить публикацию этого источника → сохранить предыдущий valid snapshot → показать ошибку/устаревание → сохранить обезличенный failing fixture → исправить adapter → выполнить contract/regression → повторить импорт → проверить diff → вернуть статус.

### Ошибка модели

Отключить затронутую оценку → сохранить входы и model version → воспроизвести тестом → исправить новую версию → пересчитать с маркировкой → проверить, какие пользовательские выводы изменились. Старый результат не перезаписывать как будто он всегда был другим.

### Падение worker

Проверить workerState в status → поднять worker → убедиться, что просроченные задания восстановились → проверить отсутствие двойных событий. Expired/failed не показываются свежими даже при недавнем lastSuccessfulCheckAt; last good snapshot остаётся опубликованным. После исчерпания попыток job не перезапускается бесконечно: проверить причину и выполнить явный enqueue после разрешённого next_run_at. Диагностика читает очередь без изменения порядка write-locks; реальная конкуренция PostgreSQL ещё требует проверки.

### Повреждение/утрата БД

Остановить записи → создать отдельное окружение восстановления → восстановить backup и raw store → проверить схему, количество и контрольные hashes, ownership → определить возможное потерянное окно → переключить только после проверки. Практическая цель MVP: RPO до 24 часов, RTO до 4 часов, подтверждённые упражнением; не заявлять их как SLA до измерения.

### Ошибка релиза

Откатить приложение на предыдущий совместимый образ. Если схема несовместима, использовать проверенную backup/restore-процедуру, а не вслепую `downgrade`. Проверить данные после отката и зафиксировать incident в LOG.

### Проверка перезапуска ручного API

Из backend: `.venv/Scripts/python.exe -m pytest -q tests/test_restart.py`. Тест поднимает три отдельных локальных процесса Uvicorn на одной временной SQLite-базе. Проверяет историю, неизменный срок доступа, ownership, повторы create/update и сохранение tombstone после удаления. Все запущенные им процессы завершаются в finally; пользовательский сервер и базы не затрагиваются. Вторая проверка закрывает истёкшую сессию после нового lifespan. Это не проверка PostgreSQL, контейнерного тома или production recovery.

Для PDF-проверки: E2E_API=1 и E2E_BASE_URL текущего preview, затем `npm run test:e2e -- tests/e2e/manual-quality.spec.ts`. Chromium создаёт A4 PDF выбранного ручного направления в test-results; фильтром исключённая запись и элементы управления не входят в печатную область. RECORD_EVIDENCE=1 дополнительно обновляет docs/evidence/manual-report.png; обычный тест не изменяет файлы репозитория.

При409 на экспорте из-за времени проверить серверные часы и сохранённые даты. Не менять историю и не подставлять вымышленный exportedAt. Импорт допускает до5 минут в будущем, поэтому до наступления сохранённого времени экспорт может оставаться недоступен. При ошибке кодировки файла скачать исходный JSON заново; не сохранять испорченный текст после автоматической замены символов.

### Проверка локального черновика B08

В frontend запустить `npm test -- tests/draft-store.test.ts tests/draft-scope.test.ts`, затем при E2E_API=1/E2E_BASE_URL текущего preview: `npm run test:e2e -- tests/e2e/draft-recovery.spec.ts tests/e2e/draft-navigation.spec.ts tests/e2e/session-tabs.spec.ts`. Потерянный ответ проверяется после настоящего server commit, с reload и повтором того же ключа. Отдельные случаи: новая версия снимка, cookie replacement без storage event,30-minute expiry, отказ/quota storage и320px/две темы. Тесты создают только изолированные гостевые данные.

Если браузер не сохраняет черновик, предупреждение не блокирует обычное сохранение на сервер. Не предлагать очистку cookies как восстановление: она теряет гостевой доступ. При конфликте409 перечитать кабинет и проверить новые цифры, не обходить X-Expected-Snapshot. Черновик удалённого направления можно просмотреть, но он не создаёт заново удалённую запись.

Для нового frontend нужен API с draftScope и X-Expected-Snapshot; namespace вычисляется, схема остаётся0004. Не считать старую Docker-сборку текущей до явной пересборки без удаления volume и smoke. Совместимость без scope оставляет базовую форму, но не обещает локальное восстановление. Скриншоты B08 не закрывают Figma/fonts/PG/real-source gates.

### Обязательная проверка PostgreSQL и диагностика B09

CI запускает backend с `python -m pytest -q --require-postgres --junitxml=test-results/backend.xml`. Нужен TEST_DATABASE_URL на отдельную PostgreSQL-базу admitflow_test*. Без него обязательный режим завершится кодом4. Пропуск, исключение через -k/-m или незавершённый native case также дают неуспех. Обычный локальный `pytest -q` сохраняет явные skips. Изоляция каждого native migration-test — отдельная случайная схема; upgrade/downgrade больше не работает в public. Это подготовка проверки, не результат недоступного remote CI.

Из backend: `python -m app.diagnostics` читает DATABASE_URL. Для работающего нового контейнера: `docker compose exec -T backend python -m app.diagnostics`. Вывод — один JSON с dialect, expected/observed revisions и агрегатами sessions/watches/snapshots/operations. Код0 означает только текущую ревизию и наличие ручных таблиц; код1 — unavailable/schema_mismatch/restore_incomplete. Значения строк, токены, host/DSN/пароль не выводятся. Неизвестный текст ревизии заменяется на unknown.

Команда не мигрирует, не создаёт схему, не удаляет данные и не исправляет restore.pending. SQLite открывается через mode=ro и query_only, отсутствующий файл не создаётся. Для PostgreSQL используется read-only repeatable-read transaction с statement timeout5s/lock timeout2s; фактическое выполнение на PG ещё не проверено. Синтаксис и границы read-only: [PostgreSQL SET TRANSACTION](https://www.postgresql.org/docs/17/sql-set-transaction.html).

Для снятия T103 нужен реальный PG upgrade и сверка сохранённых данных до/после. Совпадение четырёх counts само по себе не доказывает сохранность содержимого. При старой остановленной API-сборке можно сначала собрать новый backend image, затем выполнить `docker compose run --rm --no-deps backend python -m app.diagnostics` при работающем db: command заменяет стартовый CMD и не запускает Alembic. Старый image без модуля diagnostics не является новой проверкой. Не использовать blind stamp, downgrade или удаление volume для обхода ошибки.

### Отдельный worker в Compose

По умолчанию запускаются db/backend/frontend. Worker описан в профиле automation: `docker compose --profile automation up -d --build`. Проверка конфигурации без Engine: `docker compose config --quiet` и `docker compose --profile automation config --quiet`. Профили работают согласно [Docker Compose profiles](https://docs.docker.com/compose/how-tos/profiles/).

Worker использует тот же backend image, напрямую запускает app.worker loop, ждёт здоровые db/backend и не запускает миграцию параллельно API. Backend/worker разделяют raw_data:/app/var/raw; этот каталог подготовлен в image для пользователя app. Worker не публикует портов. Пустой production registry и выключенные источники сохраняются: профиль сам не подключает вуз и не подтверждает автоматизацию. Health API не доказывает продвижение worker.

Если в прежнем контейнере уже были raw-файлы вне volume, сохранить и проверить их до пересоздания: новое монтирование скрывает старый каталог слоя контейнера. Не удалять postgres_data/raw_data и не переносить приватные raw в Git. В этой среде проверена только конфигурация профилей; сборка image, права volume, перезапуск worker и настоящие циклы PG/source ещё не приняты. T047/T067 и релизные gates остаются открыты.

### Воспроизводимая локальная PostgreSQL-проверка (B10)

Из корня на Linux: `backend/.venv/bin/python scripts/test_postgres.py --python "$PWD/backend/.venv/bin/python"`. Нужны Docker Engine и установленные backend requirements-dev. Скрипт создаёт собственный PostgreSQL17 контейнер со случайным именем/localhost-портом и disposable database, ждёт TCP готовность (временный initdb socket не достаточен), запускает migrations с `--require-postgres`, останавливает только свой контейнер в finally. Рабочие volumes не используются. Позиционными аргументами можно передать другие native test files; набор без native cases отказывается считаться успешным. Ctrl-C завершает контейнер штатно; после kill -9 проверить `docker ps -a --filter name=admitflow-test-` вручную.

B10: все21 migration-теста выполнены, включая7 actual PostgreSQL cases, на PG17.11; legacy adoption/неподходящие CHECK, fresh upgrade/downgrade/repeat и Alembic model alignment проверены. Это локальная проверка, remote CI и миграция production данных отдельно.

Native manual concurrency: `backend/.venv/bin/python scripts/test_postgres.py --python "$PWD/backend/.venv/bin/python" tests/test_postgres_writes.py`. Shared retry/20-watch/500-history tests исполняются на мигрированной PG schema. Отдельная гонка использует два независимых app/pool: X-Expected-Snapshot допускает только одного победителя. Браузерные lost-response тесты остаются отдельным уровнем проверки.

### Проверенный Compose запуск B10 (Linux, 2026-11-03)

`WEB_PORT=8089 docker compose -p admitflow-b10 up -d --build --wait` создаёт отдельный проект/volumes и localhost endpoint. На текущем хосте bridge build network не имеет исходящего доступа; без изменения firewall образы собраны командами `docker build --network host --allow network.host -t admitflow-b10-backend -f backend/Dockerfile .` и `docker build --network host --allow network.host -t admitflow-b10-frontend -f frontend/Dockerfile .`, затем `WEB_PORT=8089 docker compose -p admitflow-b10 up -d --no-build --wait`. Host network применяется только к сборке; runtime использует обычную приватную Compose сеть. Это локальный workaround, на хосте с рабочей build-сетью достаточно первой команды.

Все3 сервиса healthy, реальная БД PostgreSQL17.11/revision0004. `backend/.venv/bin/python backend/tests/runtime_smoke.py --base-url http://127.0.0.1:8089 --output docs/evidence/b10-compose-smoke.json` проверяет реальные15 HTTP действий и удаляет только свои две guest sessions. Ключ --output позволяет сохранить исторические отчёты. `/tracker` и неизвестный SPA route отдаются; backend/db порты не опубликованы. `docker compose -p admitflow-b10 exec -T backend python -m app.diagnostics database` фактически проверен на PG: readOnly/revision_current и aggregate counts. HTTPS/staging и реальные источники остаются отдельными этапами.

### Браузерная проверка собранного приложения

Из frontend: `API_TARGET=http://127.0.0.1:8000 E2E_API=1 E2E_SERVER=preview E2E_BASE_URL=http://127.0.0.1:4189 npm run test:e2e`. Preview mode каждый раз выполняет build, затем поднимает vite preview без reuse старого сервера. CI выбирает этот режим. Для уже собранного Compose: `E2E_API=1 E2E_SERVER=external E2E_BASE_URL=http://127.0.0.1:8089 npm run test:e2e`. External mode намеренно не запускает сервер; актуальность image проверяется отдельно. Неизвестный E2E_SERVER даёт exit1; обычный dev mode остаётся значением по умолчанию. Регрессия lazy-load перехватывает как dev TrackerPage.tsx, так и emitted assets/TrackerPage-*.js.
