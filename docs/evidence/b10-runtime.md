# B10 — проверка реального runtime, 2026-11-03

Запрос: десять задач, двумя подходами по пять. Начало: `33a962b`, чистый checkout. Linux, Python 3.14.8, Node 22.23.1; зависимости из текущих requirements/package-lock. Docker Engine 29.9.2 доступен после предоставления доступа. Существующий проект radar не изменяется.

Первые пять: T103, T014, T017, T067, T168. Вторые пять: отдельные проверки PostgreSQL queue/fencing, атомарной публикации, восстановления PostgreSQL, выдачи production assets и перезапуска Compose. Автоматические источники и staging не объявляются готовыми на основании локального синтетического стенда.

## T103 — legacy PostgreSQL

PostgreSQL **17.11**, image `postgres:17-alpine`, digest `sha256:266d3c257594e195b309ae9d1805e54c788f1d7b375f56bf6c367aac6c917e7b`. Отдельный контейнер `admitflow-b10-pg`, localhost:55439, disposable database `admitflow_test_b10`; каждый тест создаёт и удаляет только собственную schema.

Из `backend/`: `TEST_DATABASE_URL=<local disposable PG> .venv/bin/python -m pytest -q tests/test_migrations.py -k 'postgres_adopts or postgres_refuses' --tb=short` → **6 passed, 15 deselected, exit 0**, 2.18s. Обе legacy-схемы приняты, исходный ID/название/история и результат74 сохранены. Изменённые операторы, регистр строк, NOT VALID и логика CHECK отклонены с сохранением записей. Blind stamp, удаление прежних volumes и изменение рабочих БД не применялись.

Первый запуск до готовности нового PG получил6 connection errors; после `pg_isready` повторён весь выбранный набор. Существующие Starlette/httpx warning и warning SQLAlchemy при намеренном NOT VALID не скрыты. Это не миграция пользовательского production volume.

## T014 — native migrations и воспроизводимый runner

`backend/.venv/bin/python scripts/test_postgres.py --python "$PWD/backend/.venv/bin/python"` → **21 passed, exit0**, 3.71s (7 native PG, 14 SQLite/offline). Fresh upgrade, repeat, model alignment, downgrade/base/upgrade и legacy проверены на отдельной schema. Production не создаёт схему автоматически: существующие strict settings/readiness проверки сохранены.

Отказ: та же команда с `tests/test_calculation.py` проходит доменные assertions, но итоговый **exit1**: Required PostgreSQL checks were absent. Контейнер останавливается и удаляется и при отказе. Runner ждёт TCP readiness и выбирает свободный localhost port, устраняя наблюдённую startup race. Production backup/rollout этим не подтверждены; обратимые downgrade выполняются исключительно на disposable schema.

## T017 — записи и конкурентные лимиты PostgreSQL

Из backend: `TEST_DATABASE_URL=<local disposable PG> .venv/bin/python -m pytest -q --require-postgres tests/test_postgres_writes.py tests/test_writes.py tests/test_expected_snapshot.py --tb=short` → **21 passed, exit0**, 4.94s, включая11 native PG. Общие assertions сохранены:12 параллельных повторов дают одну запись;30 создающих запросов дают20 успехов/10 конфликтов; при499 снимках конкурентные добавления дают ровно500. Delete tombstone, key collision/owner isolation и replay проверены также на PG. Два независимых app connection pools с одним X-Expected-Snapshot дают один201/один409 и ровно один новый снимок. Первый запуск нового теста обнаружил ошибку самого теста (несуществующий state.settings); исправлено создание второго app из фактического engine URL, assertions не ослаблены.

Это проверка транзакций на реальном PG, не нагрузочное измерение staging и не20/500-квота автоматических списков.

## T067 — реальный Compose

Fresh build backend/frontend завершился exit0 после применения host network **только для build**. Обычный build ранее завершился exit1 (`Network is unreachable` в pip); Compose build host override отвергнут buildx entitlement, затем использованы явные `docker build --network host --allow network.host` (команды в RUNBOOK). Runtime сеть по-прежнему приватная, host runtime не используется.

`WEB_PORT=8089 docker compose -p admitflow-b10 up -d --no-build --wait` → exit0, db/backend/frontend healthy. Actual images: backend `827fe4200a378a0927cd3269fb56371e85ce75d3e6f3d3ae34a1756abfe4ecf7`, frontend `10a409031a11eb6cdaa6def0e1ce2d4b2c4b25eb151362131bc69f80a62e99f6`, PG digest выше. Inspect: backend/db bindings `{}`, frontend только127.0.0.1:8089.

`runtime_smoke.py --base-url http://127.0.0.1:8089 --output docs/evidence/b10-compose-smoke.json` → **15 checks, success:true, cleanup204/204, exit0**. CRUD/history/export/replay/ownership через реальный nginx и PostgreSQL. `/`, `/tracker`, unknown SPA route дают index200. Actual database diagnostics: postgresql/readOnly/revision_current/0004, zero manual counts после cleanup; прямой SELECT revision подтверждает0004. Пересоздание всего проекта и worker recovery — отдельная T173. Existing radar containers/volumes не менялись.

## T168 — built assets и найденные focus defects

Добавлены E2E_SERVER=dev/preview/external, отказ на неизвестном значении. Preview всегда делает fresh build и не переиспользует сервер; CI выбирает preview. External full suite идёт через freshly rebuilt nginx image и текущий PostgreSQL API. Chunk-recovery test перехватывает и dev.tsx, и emitted TrackerPage-*.js. Отдельный preview+fresh build chunk-failure test: **1 passed, exit0**; invalid mode: **exit1**.

Первые два полных прогона завершились68/69, каждый дефект сохранён и исправлен:

1. Deferred catalog мог показывать focusable options старого запроса, исчезающие при Tab; устаревшие варианты теперь скрыты до совпадения query/search. Добавлены явные focus assertions при третьем открытии формы. Одного ожидания заголовка оказалось недостаточно: повтор9 дал5 failures до исправления UI; после исправления9/9.
2. После save requestAnimationFrame иногда фокусировал ещё disabled кнопку, а повтор не происходил. Возврат теперь выполняется после commit с busy=false; при исчерпанном лимите фокусируется h1. Новый real API boundary case создаёт19 направлений и сохраняет20-е через форму. После обоих исправлений **12/12 Chromium**,3 повтора четырёх keyboard cases,30.7s.

Текущие unit/build: **92 passed, build exit0**. Последний compiled TrackerPage `TrackerPage-B-WM742y.js`; финальный полный suite ниже. Remote workflow не запущен: GitHub теперь доступен read-only (remote HEAD33a962b), `gh auth status` не находит авторизованного host. Старый сетевой blockedReason T006 уточнён; CI результат не придуман.

T168 final: `E2E_API=1 E2E_SERVER=external E2E_BASE_URL=http://127.0.0.1:8089 npm run test:e2e -- --reporter=line` → **70/70 Chromium passed, exit0**,2.4m. Actual nginx assets перечислены из контейнера и совпадают с текущей сборкой: TrackerPage-B-WM742y.js/index-KCx9tssS.js. До этого12 repeated keyboard cases passed. Успех не получен скрытыми retries или ослаблением assertions. Firefox/WebKit и exact-font/Figma приёмка этим не подтверждаются.

## T169 — PostgreSQL queue/fencing

`TEST_DATABASE_URL=<local disposable PG> .venv/bin/python -m pytest -q --require-postgres tests/test_postgres_jobs.py --tb=short` → **8 native PG passed, exit0** (повтор после улучшения cleanup порядка locks).16 concurrent enqueue/claim дают ровно одну job/lease; два отдельных spawn-процесса с независимыми engines также дают одного победителя/attempt1. SKIP LOCKED возвращает None в другом соединении, пока первая transaction удерживает lock; после release job доступна. Expiry/retry/backoff/disable и отказ старого worker до publication сохранены. Все дочерние процессы завершаются в finally; это synthetic source, не аттестация реального адаптера.

## T170 — PostgreSQL atomic publish

`TEST_DATABASE_URL=<local disposable PG> .venv/bin/python -m pytest -q --require-postgres tests/test_postgres_publishing.py --tb=short` → **7 native PG passed, exit0**,1.95s. Concurrent repeat/parser-version tests, quarantine, injected row-write failure, crash-after-commit replay и safe parser error cases применяют общие assertions на настоящем PG.

Новый gated writer уже flush-нул snapshot/rows в PostgreSQL, но не commit-нул. Параллельное соединение видит только прежний pointer/1 snapshot/3 rows; после release — новый pointer/2 immutable snapshots/6 rows. Оба исходных raw читаются с проверкой SHA256. Это доказательство transaction visibility на synthetic archive, не реальный список, нагрузка или uptime24h.

## T171 — pg_dump/raw restore rehearsal

`backend/.venv/bin/python scripts/rehearse_postgres_restore.py --output docs/evidence/b10-restore.json` → **exit0, success:true, cleanup:true**. Новый owned PG container,15 таблиц,2 owners/1 watch/2 manual snapshots/3 operation records,2 source snapshots/6 candidate entries/1 queue job. Exact contents всех таблиц совпали; actual API проверил exact history/deadline/scope, чужой404, create/update replay и tombstone410.2 referenced raw восстановлены с точным содержимым/SHA256; orphan не включён.

Truncated archive с `--single-transaction --exit-on-error` дал nonzero и оставил0 таблиц в отдельной refusal DB. Corrupt raw дал raw_hash_mismatch. Dump39268bytes/0.118s; restore+copy+validation0.422s. RPO0 относится только к quiesced synthetic writes; production RPO/RTO и внешний backup не доказаны. Dump/cookies/owner hashes не сохранены в Git, приватная временная папка и контейнер удалены. Полный отчёт b10-restore.json.

Общий owned runtime вынесен в scripts/postgres_runtime.py; после refactor повторён migration runner:21 passed, включая7 actual PG, exit0. Это проверка свежей реализации runner, не ссылка на старый результат.
