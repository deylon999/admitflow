# Карточки задач

Генерируется из [TASKS.json](TASKS.json) командой `python scripts/roadmap.py --render`. Не редактировать вручную.

Общие требования для каждой задачи: [Definition of Done](QUALITY.md), [правила расчёта](DATA_RULES.md), [протокол работы](RUNBOOK.md).

Пути результатов ниже — планируемые файлы; их наличие и готовность подтверждаются статусом и evidence, а не этой таблицей.

## E0. Стабилизация

Плановый интервал: D1–D3 (визуальная сверка до D10).

### T001. Зафиксировать фактическое состояние проекта

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** нет.

**Результаты/файлы:** `docs/STATE.md`; `docs/LOG.md`.

**Шаги:**

1. Прочитать текущие исходники и команды.
2. Выполнить baseline build/test и проверить наличие миграций/E2E.

**Критерии закрытия:**

- Ошибки и отсутствующие компоненты записаны с exit codes.
- Старые проверки отделены от текущей реализации.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S001: аудит исходников, build exit 1, test exit 1, проверка отсутствующих конфигураций; критерий задачи — зафиксировать факт, а не исправить.

### T002. Исправить React production build

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T001.

**Результаты/файлы:** `frontend/src/pages/TrackerPage.tsx`; `frontend/dist/`.

**Шаги:**

1. Исправить сужение CalculationResult/CalculationError без any и подавления TS.
2. Выполнить tsc и Vite build и проверить создаваемый entrypoint.

**Критерии закрытия:**

- npm run build завершается с кодом 0.
- Поля результата доступны только в валидной ветке.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S003: build и браузерная форма exit 0; Vitest 26 passed на текущем TS.

### T003. Перенести проверки калькулятора на Vitest и TS

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T002.

**Результаты/файлы:** `frontend/tests/calculator.test.ts`; `shared/calculations.json`.

**Шаги:**

1. Убрать импорт старого dist и node:test из активного Vitest-набора.
2. Добавить общий набор валидных и невалидных входов с ожидаемыми выходами.

**Критерии закрытия:**

- npm test обнаруживает и выполняет ненулевой набор тестов.
- Изменение текущей TS-формулы приводит к ожидаемому падению контрольного теста.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S003: build и браузерная форма exit 0; Vitest 26 passed на текущем TS.

### T004. Сделать воспроизводимый backend setup

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T001.

**Результаты/файлы:** `backend/requirements.txt`; `backend/.env.example`; `docs/RUNBOOK.md`.

**Шаги:**

1. Создать собственную venv и проверить совместимость закреплённых зависимостей.
2. Определить загрузку окружения и команды старта с корректной cwd.

**Критерии закрытия:**

- API запускается из чистого checkout без путей к чужим проектам.
- Health и calculate проверены и результат записан.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S009: собственная среда и тесты; аудит источников/границы правил и политика данных.

### T005. Покрыть ручной API и Python-расчёт

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T004.

**Результаты/файлы:** `backend/tests/`; `shared/calculations.json`.

**Шаги:**

1. Проверить CRUD/историю/ошибки через TestClient с изолированной БД.
2. Применить общие fixtures к Python-модели и сверить с TS.

**Критерии закрытия:**

- Создание→обновление→история→удаление проходит.
- Невалидные значения не создают записи, расчёты двух реализаций совпадают.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S009: собственная среда и тесты; аудит источников/границы правил и политика данных.

### T006. Настроить CI для проверяемого checkout

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T003, T005.

**Результаты/файлы:** `.github/workflows/ci.yml`; `docs/RUNBOOK.md`.

**Шаги:**

1. Добавить установку по lockfiles, build, unit и backend tests.
2. Сохранять отчёт ошибок без секретов и зависимости от локальных кэшей.

**Критерии закрытия:**

- CI-конфигурация воспроизводима на чистом runner.
- Если remote CI недоступен, внешний прогон помечен непроверенным и задача не закрыта.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [.github/workflows/ci.yml](../.github/workflows/ci.yml) — Конфигурация подготовлена; удалённого запуска нет, задача не закрыта.
- [docs/LOG.md](../docs/LOG.md) — S036/S046: external prerequisite rechecked; concrete resumption condition recorded.
- [docs/evidence/t045-browsers.md](../docs/evidence/t045-browsers.md) — Удалённый прогон 41928404413 на чистых раннерах успешен: lockfile-установка, сборка, unit, backend с обязательным PostgreSQL, E2E.

### T007. Закрепить шрифты и дизайн-токены

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T002.

**Результаты/файлы:** `frontend/public/fonts/`; `frontend/src/styles.css`.

**Шаги:**

1. Получить лицензированные Inter/JetBrains Mono и сохранить лицензии.
2. Проверить загрузку реальных FontFace и цвета/типографику четырёх макетов.

**Критерии закрытия:**

- При отсутствии внешней сети шрифты доступны локально.
- Скриншоты используют реальные шрифты, а не fallback.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 2/30:13 licensed variable font subsets vendored with hashes/OFL;actual Latin/Cyrillic FontFace loads pass with external requests blocked,fresh build+5 browser cases passed.

### T008. Сверить React-лендинг с исходными макетами

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T002, T007.

**Результаты/файлы:** `frontend/tests/e2e/landing.spec.ts`; `docs/evidence/visual.md`.

**Шаги:**

1. Снять light/dark при 1440 и 390 и сравнить блоки с PNG.
2. Проверить 320/768/1024, навигацию, калькулятор и FAQ.

**Критерии закрытия:**

- Нет переполнения и потери текста.
- Существенные визуальные расхождения исправлены или отдельно предъявлены приёмке.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 3/30:four real-font screenshots compared to original PNGs,palette tokens match;documented functional copy/focus differences,6 responsive/font tests passed including1024.

### T066. Разделить frontend/backend и очистить структуру

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T003.

**Результаты/файлы:** `frontend/`; `backend/`; `shared/`; `.github/workflows/ci.yml`.

**Шаги:**

1. Перенести React и зависимости в frontend; вынести общие fixtures.
2. Удалить устаревшие артефакты; поправить CI, документацию и пути.

**Критерии закрытия:**

- Сборка и 26 unit-тестов работают из frontend.
- 36 серверных тестов и 6 E2E проходят после переноса.
- Roadmap проверяется, корень не содержит конфигов и исходников React.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S005: перенос, очистка; build / 26 unit / 36 API / 6 E2E прошли.

### T067. Добавить локальный запуск через Docker Compose

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T066.

**Результаты/файлы:** `compose.yaml`; `frontend/Dockerfile`; `frontend/nginx.conf`; `backend/Dockerfile`; `.dockerignore`.

**Шаги:**

1. Собрать frontend и API в отдельных образах; добавить PostgreSQL и постоянный volume.
2. Настроить same-origin proxy и healthchecks; обновить инструкции.

**Критерии закрытия:**

- docker compose config проходит.
- Сборка и запуск проверены либо конкретный блокер окружения зафиксирован.
- README описывает одну команду запуска и сохранение БД.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S008: Compose config exit 0; build заблокирован доступом среды; запуск не подтверждён.
- [docs/evidence/b10-runtime.md](../docs/evidence/b10-runtime.md) — B10: isolated Compose fresh images healthy;15 HTTP smoke checks passed through nginx to native PostgreSQL0004, sessions cleaned204/204; build host-network workaround documented.

### T103. Fix PostgreSQL legacy CHECK reflection during migration adoption

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T004, T015.

**Результаты/файлы:** `backend/app/migration_checks.py`; `backend/alembic/versions/0001_initial.py`; `backend/alembic/versions/0002_operation_records.py`; `backend/tests/test_migrations.py`; `backend/tests/runtime_smoke.py`; `docs/evidence/t103-docker-smoke.json`.

**Шаги:**

1. Compare PostgreSQL reflected checks with server-rendered frozen checks, preserving semantics.
2. Cover legacy snapshots and operation_records adoption and refusal of incompatible constraints.
3. Document non-destructive Docker restart and real runtime verification limits.

**Критерии закрытия:**

- Formatting differences do not require data deletion or blind stamping.
- Changed expressions, string literals and NOT VALID constraints remain rejected.
- Regression tests and explicit real PostgreSQL verification status are recorded.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S058: fix implemented; migration regressions14 passed/7 real PG skipped, full backend200 passed/7 skipped. Docker runtime blocked by Engine ACL; preserve existing volume, validate real PG before done.
- [docs/evidence/t103-docker-smoke.json](../docs/evidence/t103-docker-smoke.json) — S059: 15 real local HTTP checks passed on8080, two new guest sessions deleted204. Not evidence of image SHA, DB engine/revision or legacy migration; T103 remains review.
- [docs/evidence/b10-runtime.md](../docs/evidence/b10-runtime.md) — B10: native PostgreSQL17.11 legacy adoption/refusal: 6 passed, exit0; old IDs/history preserved, incompatible CHECK rejected. See runtime evidence; initial startup-readiness race recorded.

## E1. Источники и правила

Плановый интервал: D2–D7.

### T009. Исследовать источники и выбрать технический пилот

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T001.

**Результаты/файлы:** `docs/sources/`; `docs/evidence/source-audit.md`.

**Шаги:**

1. Изучить не менее пяти кандидатов с разными форматами, сезонностью и доступностью.
2. Выбрать два независимых источника и объяснить порядок подключения.

**Критерии закрытия:**

- У кандидатов есть официальные URL и проверка доступа.
- Выбор не выдан за подтверждённую поддержку всех вузов.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S009: собственная среда и тесты; аудит источников/границы правил и политика данных.

### T010. Зафиксировать сезон и правила поддержанного конкурса

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T009.

**Результаты/файлы:** `docs/DATA_RULES.md`; `docs/sources/`.

**Шаги:**

1. Найти официальные актуальные правила и описать группу/места/приоритеты/согласия.
2. Составить таблицу поддержанных и неизвестных случаев.

**Критерии закрытия:**

- Каждое исключение участника имеет основание и сезон.
- Непроверенные правила не входят в автоматическую модель.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S009: собственная среда и тесты; аудит источников/границы правил и политика данных.

### T011. Описать доступ к данным и минимизацию

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T009.

**Результаты/файлы:** `docs/data-policy.md`; `docs/sources/`.

**Шаги:**

1. Проверить условия получения и хранения списков, область публичных ID.
2. Определить redaction, retention, удаление и ограничения raw storage.

**Критерии закрытия:**

- В fixtures/logs нет ненужных персональных данных.
- Внешний запуск имеет перечень правовых/организационных вопросов и ответственного, не ложное заявление о готовности.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S009: собственная среда и тесты; аудит источников/границы правил и политика данных.

### T012. Создать начальный каталог с происхождением записей

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T009.

**Результаты/файлы:** `backend/app/catalog.py`; `docs/catalog-coverage.md`.

**Шаги:**

1. Выбрать проверяемый официальный источник каталога и правила вуз/филиал.
2. Сохранить version/date/provenance, нормализовать имена и не смешивать филиалы.

**Критерии закрытия:**

- Каждая опубликованная запись имеет источник.
- Полнота измеряется относительно именованного набора, а не объявляется абсолютной.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S013: provenance/manual coverage и поиск проверены; 58 tests passed, 1 PG skipped.

### T013. Подготовить реальные и негативные fixtures

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T010, T011, T083.

**Результаты/файлы:** `backend/tests/fixtures/sources/`; `docs/sources/`.

**Шаги:**

1. Сохранить разрешённые обезличенные образцы, hashes и описания полей.
2. Извлечь контрольные строки первого источника и проверить схему, добавить архивные/неполные образцы.

**Критерии закрытия:**

- Хотя бы один реальный образец разобран воспроизводимо до G1.
- Синтетические и архивные данные явно маркированы.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S036/S046: external prerequisite rechecked; concrete resumption condition recorded.
- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 4/30:genuine SGU573-row original inspected,DOM-derived anonymized fixture retains exact facts;9 fixture/capture tests passed. STU header-only remains unsupported;source originals private.

### T056. Расширить проверенный каталог до национального охвата

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T012, T038, T192.

**Результаты/файлы:** `backend/app/accreditation_registry.py`; `backend/app/data/accreditation-registry.json`; `scripts/build_accreditation_registry.py`; `docs/catalog-coverage.md`.

**Шаги:**

1. Сверить организации/филиалы/уровни с датированным опорным реестром.
2. Обновлять каталог воспроизводимым импортом и фиксировать исключения.

**Критерии закрытия:**

- Есть понятный знаменатель полноты и дата.
- Полный каталог не называется полным автоматическим сбором.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/kan-217-national-denominator.md](../docs/evidence/kan-217-national-denominator.md) — S204 KAN-217. Rosobrnadzor RAOO open data 2026-11-10 (SHA-256 c86f8e46…): 785 active head organisations with accredited bachelor/specialist, 83 departmental by name, 5 abroad excluded. MICCEDU catalog matched 675 (86.0%; civil 675/702=96.2%), 109 register-only added with source, 59 unmatched and 1 ambiguous OGRN listed. Coverage of catalog only; programmes/EGE/lists not claimed. Whole-file validation, builder on synthetic XML without personal fields, API/UI accreditation source tested.

### T083. Получать проверяемый пакет исходных страниц пилота

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T028, T078.

**Результаты/файлы:** `backend/app/sources/capture.py`.

**Шаги:**

1. Закрытые цели пилота, оригинальные bytes и manifest/hash.
2. Проверить offline отказ и повторное чтение пакета.

**Критерии закрытия:**

- Нет обхода ограничений или production enable.
- Пакет не смешивается с аттестованным адаптером.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S037 / B03 1/10: Closed pilot capture CLI stores original bytes plus bounded manifest/hash in private folder, verifies binding and tampering, never attests/enables a source. pytest tests/test_capture.py: 3 passed / exit 0. Real capture command failed with network_error/captured=false/exit 1; no original fixture obtained and T013 stays open. Official indices only support candidate URLs, not parser structure. Commands and handoff documented in sources/pilot.md.

### T190. Сохранить официальный опорный перечень вузов и границы охвата

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T012, T038.

**Результаты/файлы:** `scripts/capture_catalog.py`; `docs/catalog-coverage.md`.

**Шаги:**

1. Сохранить официальные страницы, даты, hashes и исключения.
2. Сверить региональные перечни и число организаций.

**Критерии закрытия:**

- Есть проверяемый snapshot и воспроизводимая команда.
- Мониторинг не объявлен полным реестром лицензированных вузов.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b14-national-catalog.md](../docs/evidence/b14-national-catalog.md) — 1257 unique institutions, 521 branches, 89 regional pages; headline total matched; offline replay identical; 3 parser checks passed. Monitoring exclusions retained.

### T191. Импортировать национальный опорный каталог без дублей

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T190.

**Результаты/файлы:** `backend/app/national_catalog.py`; `backend/tests/test_national_catalog.py`.

**Шаги:**

1. Валидировать snapshot и provenance до транзакции.
2. Сохранить идентичности существующих вузов, филиалы и отчёт импорта.

**Критерии закрытия:**

- Повтор не создаёт дубли и не меняет подписки.
- Повреждённый импорт отклоняется целиком; неизвестные сайты не выдумываются.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b14-national-catalog.md](../docs/evidence/b14-national-catalog.md) — Validated atomic read-only artifact import, 1257 identities and 521 branches, legacy aliases preserved; 12 targeted checks passed; no Source or user DB mutation.

### T255. KAN-221: дашборд покрытия РФ и контроль свежести

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T056.

**Результаты/файлы:** `backend/app/national_coverage.py`; `frontend/src/pages/CoveragePage.tsx`; `docs/evidence/kan-221-coverage-dashboard.md`.

**Шаги:**

1. Один знаменатель из реестра аккредитации.
2. Раздельные слои каталога, программ, ЕГЭ и списков.
3. Годы, пробелы, регионы, источники и очередь.
4. Воспроизводимая выгрузка с контрольной суммой.
5. Экран v3, тесты и снимки.

**Критерии закрытия:**

- Отдельно показаны доли реестра, программ и подтверждённых требований; филиалы и головные вузы не смешаны.
- stale/ошибки источников видны, отчёт воспроизводим.
- Нет утверждений о покрытии без фактических данных.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/kan-221-coverage-dashboard.md](../docs/evidence/kan-221-coverage-dashboard.md) — S204 API /api/v1/coverage/national, CLI python -m app.national_coverage, screen /app/coverage. Layers on 785: catalog 675 (86.0%), programs/EGE/lists from the DB (test stand 1/0/0). Checksum stable for equal inputs; 6 backend tests incl. failed source, browser test incl. JSON export; screenshots 1440/390 without page overflow.

## E2. Ядро продукта

Плановый интервал: D4–D10.

### T014. Ввести Alembic и PostgreSQL-проверки

**Статус:** `done` · **Приоритет:** P0 · **Размер:** L.

**Зависимости:** T004, T015.

**Результаты/файлы:** `backend/alembic/`; `backend/alembic.ini`; `backend/tests/test_migrations.py`; `scripts/test_postgres.py`.

**Шаги:**

1. Создать миграции текущих и целевых сущностей без потери ручных данных.
2. Проверить upgrade на пустой БД и на предыдущей схеме, описать восстановление.

**Критерии закрытия:**

- Схема PostgreSQL создаётся миграциями.
- Ошибка миграции не скрывается автоматическим create_all в production.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S012: SQLite migration suite и PG offline SQL проходят, реальный PG skipped; CI подготовлен.
- [docs/evidence/b10-runtime.md](../docs/evidence/b10-runtime.md) — B10: disposable Docker runner passed all21 migration cases including7 actual PostgreSQL checks; no-native selection fails exit1 and owned container is cleaned up.

### T015. Утвердить идентичность и каноническую модель данных

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T010.

**Результаты/файлы:** `backend/app/database.py`; `docs/ARCHITECTURE.md`.

**Шаги:**

1. Разделить вуз/филиал/сезон/группу/source snapshot/watch/assessment.
2. Задать уникальность ID, null semantics, времена и версии правил.

**Критерии закрытия:**

- Сезоны и чужие конкурсные группы невозможно спутать в ключах.
- Автоматический список не копируется полностью на каждого владельца.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S011: 48 backend tests; identities, null semantics и межгрупповые FK проверены.

### T016. Довести гостевой доступ и жизненный цикл сессии

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T005, T011.

**Результаты/файлы:** `backend/app/main.py`; `frontend/src/lib/api.ts`; `backend/tests/test_sessions.py`.

**Шаги:**

1. Зафиксировать expiry/refresh/delete-all и UX после потери доступа.
2. Проверить cookies, два клиента, CSRF и отсутствие молчаливой подмены старых сохранений новой сессией.

**Критерии закрытия:**

- Чужие направления недоступны во всех маршрутах.
- Пользователь понимает срок доступа и действие при истечении.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S010: 41 backend, 26 unit, build и 8 E2E проходят; guest expiry/reset/cleanup проверены.

### T017. Сделать записи и лимиты устойчивыми к повторам

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T014, T016, T068.

**Результаты/файлы:** `backend/app/operations.py`; `backend/app/main.py`; `backend/tests/test_writes.py`; `backend/tests/test_postgres_writes.py`.

**Шаги:**

1. Добавить транзакционные гарантии и идемпотентность создающих операций.
2. Протестировать конкурентные запросы, лимиты и потерянный ответ.

**Критерии закрытия:**

- Повтор запроса не дублирует запись в предусмотренном контракте.
- Параллельные операции не обходят установленные лимиты.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b10-runtime.md](../docs/evidence/b10-runtime.md) — B10: 21 write/optimistic tests passed, including11 native PostgreSQL; concurrency enforces20 watches/500 snapshots, retries do not duplicate, two app pools yield201/409.

### T018. Согласовать API-контракты и frontend types

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T005, T015.

**Результаты/файлы:** `frontend/src/lib/api.ts`; `backend/app/schemas.py`; `docs/api-contract.md`.

**Шаги:**

1. Описать DTO режимов manual/automatic/archive и quality/freshness.
2. Зафиксировать ошибки, валидацию границы, пагинацию и правила retry.

**Критерии закрытия:**

- Невалидный response не отображается как достоверные числа.
- Контрактные тесты ловят несовместимое изменение backend/frontend.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S014: общий DTO fixture и runtime parsers; 60 backend/40 frontend/9 E2E, build.

### T019. Завершить ручное сохранение направлений

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T016, T017, T018, T091.

**Результаты/файлы:** `frontend/src/pages/TrackerPage.tsx`; `frontend/tests/e2e/tracker-api.spec.ts`; `frontend/tests/e2e/tracker-form.spec.ts`; `docs/evidence/manual-acceptance.md`.

**Шаги:**

1. Проверить создание/обновление/историю/удаление и pending/error/empty.
2. Сохранить введённые поля при ошибке, исключить двойное нажатие и XSS.

**Критерии закрытия:**

- Сквозной путь работает после reload и перезапуска API.
- Ручные данные не помечены автоматическими.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 1/30:manual acceptance audited;10 current Chromium cases passed on PostgreSQL8090, existing exact restart/ownership/retry evidence remains applicable.

### T020. Уточнить сценарную модель и безопасные формулировки

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T003, T005, T010.

**Результаты/файлы:** `frontend/src/lib/calculator.ts`; `backend/app/calculation.py`; `docs/DATA_RULES.md`.

**Шаги:**

1. Устранить неограниченное обещание «при любом сценарии».
2. Добавить unsupported/insufficient-data и согласовать границы ручной модели.

**Критерии закрытия:**

- Статус объясняет входы и допущения.
- Все граничные cases совпадают с документированной моделью.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S020 / B01 1/5: общий assessment contract; 112 backend / 46 frontend / 4 landing E2E.

### T023. Довести неизменяемую историю и сравнение снимков

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T014, T018, T019, T070, T074.

**Результаты/файлы:** `backend/app/history/`; `frontend/src/pages/TrackerPage.tsx`.

**Шаги:**

1. Добавить стабильную пагинацию истории и model version.
2. Проверить одинаковые timestamps, порядок событий и старый/new assessment.

**Критерии закрытия:**

- История не теряет и не повторяет записи при перелистывании.
- Пересчёт новой версией не переписывает старый результат.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 20/30:manual-v1 calculation pinned to stored version;16nativePG write/history cases and1Chromium comparison passed,500boundary/equal-time/cursor/version refusal verified.

### T068. Реализовать атомарные ручные записи и идемпотентность

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T016, T018.

**Результаты/файлы:** `backend/app/main.py`; `backend/app/database.py`; `backend/tests/test_writes.py`.

**Шаги:**

1. Сериализовать записи владельца и сохранять результат по ключу операции.
2. Проверить конкурентные лимиты и повтор на локальной БД; PG остаётся частью T017.

**Критерии закрытия:**

- Повтор POST с одним ключом не дублирует направление/снимок.
- Конкурентные запросы не обходят 20/500 на локальной БД.
- Удаление направления не оставляет сохранённые payload операций.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S017: 106 backend/40 frontend/12 E2E; concurrent limits and response-loss retry passed. PG remains separately unverified.

### T069. Объяснить ручной сценарий проверяемыми числами

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T020, T018.

**Результаты/файлы:** `frontend/src/components/ScenarioExplanation.tsx`.

**Шаги:**

1. Объяснить ручной сценарий проверяемыми числами.
2. Проверить пользовательский путь и граничные состояния.

**Критерии закрытия:**

- Объяснение связано с введёнными числами и двумя сценариями.
- Нет обещания поступления или выдуманных процентов.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S021 / B01 2/5: numeric explanations; 49 unit / 4 landing E2E / build passed.

### T070. Показать сравнение ручных снимков

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T018, T068.

**Результаты/файлы:** `frontend/src/lib/comparison.ts`.

**Шаги:**

1. Показать сравнение ручных снимков.
2. Проверить пользовательский путь и граничные состояния.

**Критерии закрытия:**

- Изменения места и входных данных показаны отдельно.
- Первый снимок и неизменные данные обработаны корректно.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S022 / B01 3/5: manual history comparison; 53 unit / 4 tracker E2E / build passed.

### T071. Экспортировать свои ручные направления и полную историю

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T016, T018, T068.

**Результаты/файлы:** `backend/app/main.py`; `frontend/src/lib/api.ts`.

**Шаги:**

1. Экспортировать свои ручные направления и полную историю.
2. Проверить пользовательский путь и граничные состояния.

**Критерии закрытия:**

- Экспорт содержит все свои снимки, а не только последние 100.
- Чужие данные и токены не попадают в файл.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S023 / B01 4/5: full private export; 116 backend / 54 frontend / 5 tracker E2E passed; 1 PG skipped.

### T072. Довести управление ручной формой с клавиатуры

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T069, T070, T071.

**Результаты/файлы:** `frontend/src/pages/TrackerPage.tsx`; `frontend/tests/e2e/`.

**Шаги:**

1. Довести управление ручной формой с клавиатуры.
2. Проверить пользовательский путь и граничные состояния.

**Критерии закрытия:**

- Фокус ставится в открытую форму и возвращается после закрытия.
- Escape и клавиатурные действия проверены, сохранение не прерывается.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S024 / B01 5/5: keyboard focus and nested Escape; 16 full Chromium E2E / 54 frontend / 116 backend passed; 1 PG skipped; build passed.

### T073. Таймауты ручного API и восстановление чтения

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T018, T068.

**Результаты/файлы:** `frontend/src/lib/transport.ts`.

**Шаги:**

1. Ограничить ожидание ответа и тела; отмена чтения.
2. Проверить timeout/offline/503 и повтор без потери данных.

**Критерии закрытия:**

- Pending ограничен по времени; запись не повторяется автоматически.
- После ошибки чтения доступен безопасный повтор.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S026 / B02 1/10: Transport bounds response and body to 15s, supports AbortSignal and never retries writes. npm test: 57 passed; npm run build: exit 0; recovery + tracker API E2E: 6 passed. Files: transport.ts, api.ts, TrackerPage, transport/recovery tests. External CI unchanged.

### T074. Загрузка полной ручной истории страницами

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T018, T070.

**Результаты/файлы:** `backend/app/main.py`; `frontend/src/pages/TrackerPage.tsx`.

**Шаги:**

1. Добавить keyset cursor с проверкой владельца.
2. Показать загрузку следующей страницы и ошибку повтора.

**Критерии закрытия:**

- Все 500 снимков доступны без дублей при новом сохранении.
- Чужой или некорректный cursor не раскрывает данные.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S027 / B02 2/10: Keyset history pages support all 500 saves without duplicate rows during concurrent insert; cursor scoped to watch/owner. Backend targeted pytest: 2 passed; frontend 58 passed; build exit 0; recovery and real API browser tests: 7 passed. UI retains first page on failed next-page request. Preview now 5182/API8002, isolated batch02.db.

### T090. Импортировать ручную историю атомарно через API

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T071, T068, T084.

**Результаты/файлы:** `backend/app/importing.py`.

**Шаги:**

1. Проверить export contract, формулы, даты, limits и manual provenance.
2. Новые ownership/IDs и обязательный Idempotency-Key.

**Критерии закрытия:**

- Невалидная запись откатывает весь файл.
- Повтор не дублирует; импорт не восстанавливает чужую сессию.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S044 / B03 8/10: Atomic manual-export-v1 import validates full file before insert: arithmetic, safe URLs, manual model, dates/timezones, uniqueness/order and 20/500 limits. New IDs/owner preserve manual dates and equal-timestamp ordering. Mandatory idempotency key caches only counts; replay after deletion cannot resurrect records. pytest import+export: 14 passed / exit 0, including 500 records, invalid/partial files, conflict/replay, owner isolation and rollback on DB error. Formula unchanged, provenance remains manual.

### T091. Восстанавливать ручную историю из файла в интерфейсе

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T090, T073.

**Результаты/файлы:** `frontend/src/components/ImportData.tsx`.

**Шаги:**

1. Ограничить файл, проверить contract и показать подтверждение.
2. Стабильный ключ повтора и обновление списка после успеха.

**Критерии закрытия:**

- Невалидный файл не отправляется, отмена не пишет.
- Export/import в новой сессии сохраняет историю.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S045 / B03 9/10: Import UI checks file size/content before network, previews counts and requires confirmation; cancel never writes. Deterministic content key survives reselect/retry, new-session transfer preserves both history records/dates and generates new owner IDs. npm test: 60 passed; build exit 0; 2 real API Chromium import tests passed including lost committed response replay and invalid/oversized file with zero POSTs. New isolated preview 5183/API8003 using batch03.db; API started explicitly without reload/access-log.

### T094. Разрешить безопасный replay импорта при заполненном лимите

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T090, T091.

**Результаты/файлы:** `frontend/src/components/ImportData.tsx`.

**Шаги:**

1. Не блокировать проверку уже импортированного файла при 20 записях.
2. Сохранить серверный лимит для нового файла.

**Критерии закрытия:**

- Replay при 20 не создаёт дубли.
- Новый файл при 20 получает 409 без изменений.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S049 / B04 2/10: Confirmed UI quota bug with a 20-direction export: capacity check blocked an idempotent replay before server could return cached success. UI now offers explicit replay check at quota; server still rejects a new file with 409 and no writes. Build exit 0; 3 real-API import E2E passed, including reload/reselect at 20, successful replay, changed-file refusal and exact final count20.

### T095. Проверять действительные даты и порядок полной истории на клиенте

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T074, T091.

**Результаты/файлы:** `frontend/src/lib/contracts.ts`.

**Шаги:**

1. Отклонить невозможные календарные даты.
2. Сверить timezone, микросекунды, порядок и уникальность snapshots.

**Критерии закрытия:**

- Невалидные даты и переставленная история не показываются как корректные.
- Собственный export с равными timestamp принимается.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S050 / B04 3/10: Strict calendar/offset/microsecond parser rejects Date.parse rollover and compares exact UTC microseconds before ID tiebreak. Full export and combined pages validate order, uniqueness and timestamp bounds. Initial tests exposed old synthetic ascending-ID fixtures and a test typing issue; corrected fixtures to the documented server order and typed snapshots through runtime parser. Final npm test: 65 passed; build exit 0; import/recovery/real-API E2E: 10 passed. Own 20x500 export still accepted.

### T098. Согласовать истечение сессии во всех действиях кабинета

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T016, T091.

**Результаты/файлы:** `frontend/src/pages/TrackerPage.tsx`; `frontend/src/components/ImportData.tsx`.

**Шаги:**

1. Обработать 401 из delete/export/import/history.
2. Скрыть старую форму и не создавать новую сессию автоматически.

**Критерии закрытия:**

- Каждый 401 приводит к явному состоянию expiry.
- Новая ownership только по кнопке пользователя.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S053 / B04 6/10: Central QueryCache/MutationCache handler makes 401 consistent across history/export/delete/import/save, disables 401 retries and hides old form/cards/comparison/file. New session only explicit reset, with private query cancellation/refetch before reopening. Initial build required a literal return-type fix for the disabled access-state query. Final npm test67/build passed; 9 real-API session/action/CRUD E2E passed with dirty form, exact session-start count and empty new owner. No automatic cookie recreation.

### T106. Expose exact history totals and remaining snapshot capacity

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T074.

**Результаты/файлы:** `backend/app/main.py`; `backend/app/schemas.py`; `backend/tests/test_history_totals.py`; `frontend/src/lib/contracts.ts`.

**Шаги:**

1. Expose exact history totals and remaining snapshot capacity.
2. Verify success, boundary and relevant failure behavior.

**Критерии закрытия:**

- Owner-only count remains accurate across pagination and UI shows the 500-record limit..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S063: History API returns owner-scoped total independent of page size; UI shows remaining capacity out of500, older servers keep unknown total. Targeted backend1, frontend68/build and2 Chromium tools checks passed; current API process will be restarted before final real-API run.

### T113. Invalidate private state when another tab resets access

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T098.

**Результаты/файлы:** `frontend/src/lib/api.ts`; `frontend/src/lib/query-client.ts`; `frontend/src/main.tsx`; `frontend/src/pages/TrackerPage.tsx`; `frontend/tests/e2e/session-tabs.spec.ts`.

**Шаги:**

1. Invalidate private state when another tab resets access.
2. Verify success, boundary and relevant failure behavior.

**Критерии закрытия:**

- Other tabs hide old cards/forms and require explicit synchronization, without auto session POST..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S070: Cross-tab reset hides private cards/drafts, cancels private reads and requires explicit readonly synchronization. Listener lives across routes; cached API session forgotten; no automatic session POST in receiving tab. Build and5 real-API session/tab checks passed. Existing delete401 test now accepts the intentional draft-discard prompt.

### T119. Reject control characters in manual metadata

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T018.

**Результаты/файлы:** `backend/app/schemas.py`; `backend/tests/test_manual_hardening.py`; `frontend/src/lib/direction.ts`; `frontend/src/lib/contracts.ts`.

**Шаги:**

1. Reject control characters in manual metadata.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- API names and URLs reject raw controls before normalization; client/import contracts agree..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S077: Reject C0/DEL controls before Pydantic URL normalization; client form/import contracts reject them consistently. Targeted backend9 passed; frontend69 passed. No metadata write on invalid input.

### T124. Batch manual direction and export reads

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T018.

**Результаты/файлы:** `backend/app/main.py`; `backend/tests/test_batch_reads.py`.

**Шаги:**

1. Batch manual direction and export reads.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Read query counts stay bounded independently of watch count; latest ordering and full export preserved..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S082: Manual list and full export batch snapshots instead of one query per watch; bounded full export still validates500 per watch. Twenty-watch query-count/tied-order test plus export/import15 passed (at most3SELECTs per request).

### T125. Order same-time snapshots and refuse clock regression

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T068.

**Результаты/файлы:** `backend/app/main.py`; `backend/tests/test_snapshot_clock.py`; `docs/DATA_RULES.md`.

**Шаги:**

1. Order same-time snapshots and refuse clock regression.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Equal-time updates become latest without changing observed time; backward-clock writes refuse atomically..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S083: Equal-time updates retain exact observed time and use increasing UUID tie-breaks, becoming latest deterministically. Backward clock refuses409 atomically; DATA_RULES updated, formula unchanged. Clock/API15 passed after correcting a nonexistent test filename.

### T126. Enforce ISO aware timestamps on manual DTOs

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T090.

**Результаты/файлы:** `backend/app/schemas.py`; `backend/tests/test_manual_hardening.py`.

**Шаги:**

1. Enforce ISO aware timestamps on manual DTOs.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Numeric/coercible timestamps and unsupported precision rejected; actual aware datetimes remain valid internally..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S084: Manual DTO timestamps accept only explicit ISO timezone strings up to6fraction digits or aware internal datetimes; numeric/naive/coercible timestamps rejected422. Hardening/import/export32 passed; original timestamps remain unchanged.

### T128. Compare opaque IDs by Unicode code point

**Статус:** `done` · **Приоритет:** P2 · **Размер:** M.

**Зависимости:** T095.

**Результаты/файлы:** `frontend/src/lib/time.ts`; `frontend/src/lib/contracts.ts`; `frontend/tests/time.test.ts`.

**Шаги:**

1. Compare opaque IDs by Unicode code point.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Same-time ordering agrees with Python for BMP and supplementary Unicode IDs..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S086: Same-time opaque IDs compare Unicode code points like Python, not UTF16 code units. Text length counts code points, accepting valid100-character supplementary IDs from the server. Unicode ordering/export regression and all71 frontend tests passed.

### T135. Serialize guest bootstrap between browser tabs

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T098.

**Результаты/файлы:** `frontend/src/lib/api.ts`; `frontend/tests/e2e/session-tabs.spec.ts`.

**Шаги:**

1. Serialize guest bootstrap between browser tabs.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Concurrent initial tabs share one guest bootstrap when Web Locks is available; no reset deadlock..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S093: Guest bootstrap and explicit reset serialize across tabs using Web Locks with bounded lock wait; reset avoids nested-lock deadlock. Build and2 real API cross-tab checks passed, including simultaneous first visits producing exactly one session POST. Unsupported Web Locks fallback documented later.

### T136. Fence stale session results after access changes

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T135.

**Результаты/файлы:** `frontend/src/lib/api.ts`; `frontend/src/lib/query-client.ts`; `frontend/tests/session-state.test.ts`.

**Шаги:**

1. Fence stale session results after access changes.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Late promises from earlier access cannot clear/replace newer session state or trigger hidden writes..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S094: Private requests fence epoch changes before headers/errors and after JSON body; superseded reads do not auto-retry. Late bootstrap catch clears only its own pending promise. Two deferred-response regressions and all73 frontend tests/build passed.

### T149. Keep manual UTC timestamps inside the supported calendar

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T126.

**Результаты/файлы:** `backend/app/schemas.py`; `frontend/src/lib/time.ts`; `backend/tests/test_timestamp_bounds.py`; `frontend/tests/time.test.ts`; `docs/DATA_RULES.md`.

**Шаги:**

1. Keep manual UTC timestamps inside the supported calendar.
2. Run meaningful success and refusal regressions.

**Критерии закрытия:**

- Offset-normalized dates outside years1..9999 reject as validation errors on server and client..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S108: Backend test_timestamp_bounds.py:4 passed; frontend time.test.ts:5 passed. Offset under/overflow yields422 before import writes, exact UTC year1/year9999 boundaries accepted. DATA_RULES updated; original accepted timestamps and formula preserved.

### T150. Refuse inconsistent exports after clock regression

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T125.

**Результаты/файлы:** `backend/app/main.py`; `backend/tests/test_snapshot_clock.py`; `docs/DATA_RULES.md`.

**Шаги:**

1. Refuse inconsistent exports after clock regression.
2. Run meaningful success and refusal regressions.

**Критерии закрытия:**

- Export refuses if observed saved dates exceed current server time, without rewriting dates or data..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S109: Backend test_snapshot_clock.py/test_export.py/test_import.py:16 passed. One-microsecond server clock regression causes409 and preserves exact history; export succeeds once clock restored. Read remains owner-locked; DATA_RULES documents imported future tolerance interaction.

### T153. Verify manual data across API process restarts

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T018.

**Результаты/файлы:** `backend/tests/test_restart.py`.

**Шаги:**

1. Verify manual data across API lifespan restarts.
2. Run meaningful success and refusal regressions.

**Критерии закрытия:**

- A fresh app using the same isolated SQLite file preserves ownership, history and idempotent operations; expired owners stay denied..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S112: test_restart.py:2 passed: three fresh Uvicorn processes on one temporary SQLite file preserve exact history, owner deadline, create/update replay and deleted-operation410; separate expired-owner lifespan check passes. Initial test-cookie Domain mismatch corrected to real host semantics. Final backend276 passed/7 actual PostgreSQL skipped; frontend87 passed and production build exit0; all53 Chromium passed on final API8006/session26232/PID5096. No PostgreSQL/Compose success claimed.

### T192. Показать национальный каталог и статусы подключения в поиске

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T191.

**Результаты/файлы:** `backend/app/catalog.py`; `frontend/src/components/UniversityPicker.tsx`.

**Шаги:**

1. Добавить ограниченную выдачу и поиск по региону/названию.
2. Разделить наличие в каталоге и автоматическое подключение.

**Критерии закрытия:**

- Поиск работает на реальном опорном каталоге.
- Контракт, русский поиск и интерфейс проверены; нет ложной автоматизации.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b14-national-catalog.md](../docs/evidence/b14-national-catalog.md) — 1257 directory entries searchable with region/branch and pagination; 1166 site URLs, 91 unknown; 21 backend, 116 Vitest/build, compiled Chromium 12 passed/2 fixture-only skips. Screenshot inspected.

## E3. Автоматический сбор

Плановый интервал: D8–D17.

### T021. Найти абитуриента в конкретном источнике

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T018, T029, T176, T177.

**Результаты/файлы:** `backend/app/candidates/`; `frontend/src/components/`.

**Шаги:**

1. Определить допустимый публичный ID и область уникальности.
2. Сделать поиск, подтверждение строки, not-found/ambiguous и rate limit.

**Критерии закрытия:**

- Нет склейки людей по ФИО или чужому ID другого источника.
- Пользователь подтверждает правильную группу и запись до сохранения.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 15/30:explicit archive lookup/confirmation UI,shared20limit and session cache isolation;5newChromium+5catalog,101unit,currentbuild,4lookup tests and37native cases passed;0006rate budget added.

### T027. Определить интерфейс адаптера и registry

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T010, T013, T015, T076.

**Результаты/файлы:** `backend/app/sources/`; `backend/tests/contracts/`.

**Шаги:**

1. Создать ParsedList/Entry/Warnings с версиями и provenance.
2. Добавить registry активных источников и контракт отказа.

**Критерии закрытия:**

- Unknown/null сохраняются.
- Подключение адаптера требует паспорта и fixtures.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 5/30:explicit passport/fixture attestation gates implemented;33 contract/registry/coverage/fixture tests passed,unknown/null/HMAC scope preserved.

### T028. Реализовать ограниченный безопасный fetcher

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T004, T009, T011.

**Результаты/файлы:** `backend/app/sources/fetcher.py`; `backend/tests/test_fetcher.py`.

**Шаги:**

1. Ограничить схемы/домены/DNS/redirects, timeout, размер и тип ответа.
2. Добавить backoff/Retry-After и redaction, исключить внутренние адреса.

**Критерии закрытия:**

- SSRF и redirect на приватный адрес отклоняются.
- CAPTCHA/авторизация/ошибка HTTP не обходятся и не принимаются за список.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S016: pinned DNS/TLS, allowlist и 36 fetcher tests; 96 backend passed, 1 PG skipped.

### T029. Подключить первый официальный источник

**Статус:** `done` · **Приоритет:** P0 · **Размер:** L.

**Зависимости:** T027, T028.

**Результаты/файлы:** `backend/app/sources/adapters/`; `docs/sources/`.

**Шаги:**

1. Реализовать разбор, пагинацию и mapping полей первого формата.
2. Сверить контрольные и граничные строки с оригиналом.

**Критерии закрытия:**

- Contract tests и сверка минимум 50 строк либо всего меньшего списка пройдены.
- Паспорт указывает реальные ограничения и сезон.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 7/30:archive-only SGU adapter attested;all573 original rows independently matched,including16/17boundary and119tie-score groups;35 adapter/fixture/attestation regressions passed.

### T030. Ввести нормализацию и карантин

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T029, T077.

**Результаты/файлы:** `backend/app/sources/validation.py`; `backend/tests/`.

**Шаги:**

1. Проверять дубли, полноту, обязательные поля, сезон и аномальное сокращение.
2. Разделить warning и блокирующие дефекты с reason codes.

**Критерии закрытия:**

- Повреждённый/неполный ответ не заменяет valid snapshot.
- Неизвестное значение не становится нулём.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 8/30:25 real-source/quarantine/publishing/size checks passed;bad normalization retains573-row last-good snapshot,unknowns remainnull,publication enforces adapter cap.

### T031. Подключить второй независимый источник

**Статус:** `done` · **Приоритет:** P0 · **Размер:** L.

**Зависимости:** T029, T030, T187, T188.

**Результаты/файлы:** `backend/app/sources/adapters/`; `docs/sources/`.

**Шаги:**

1. Проверить второй вуз/формат отдельно, даже если платформа похожа.
2. Добавить собственные реальные и негативные fixtures.

**Критерии закрытия:**

- Второй источник проходит те же критерии, что первый.
- Доказательство не основано только на совпадении названий колонок.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b12-progress.md](../docs/evidence/b12-progress.md) — B12:independentGUAP581rowarchiveattested/allrowsaudited,commonJSONparser,native3cases,actualHTTPSworker+localruntime1154rows across2universities verified.

### T032. Реализовать планировщик и отдельный worker

**Статус:** `done` · **Приоритет:** P0 · **Размер:** L.

**Зависимости:** T014, T027, T028, T081.

**Результаты/файлы:** `backend/app/worker.py`; `backend/app/jobs.py`; `backend/tests/test_postgres_jobs.py`; `backend/tests/test_postgres_sgu.py`; `scripts/rehearse_sgu_worker.py`.

**Шаги:**

1. Сделать PostgreSQL jobs, атомарный lease, heartbeat, max retries и лимиты домена.
2. Проверить два worker и восстановление задания после смерти процесса.

**Критерии закрытия:**

- Одно задание не публикуется дважды.
- Worker не блокирует API и не создаёт шторм запросов.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 9/30:actual SGUHTTPS/573rows/PG worker cycle+idle passed,current replay passed;16 local+11nativequeue+2nativeSGU/API checks verify heartbeat/domain limits and API isolation.

### T033. Сохранять и публиковать снимки атомарно

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T014, T030, T032, T079.

**Результаты/файлы:** `backend/app/sources/publishing.py`; `backend/tests/test_postgres_sgu.py`; `docs/data-policy.md`.

**Шаги:**

1. Сохранить raw hash/provenance и normalised snapshot.
2. Переключать latest только после полной проверки, ограничить retention.

**Критерии закрытия:**

- Повтор импорта идемпотентен.
- Падение до commit сохраняет предыдущий latest и не показывает полуготовые данные.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 10/30:nativePG573-row retries/rollback/crash/raw provenance/retention passed,11+5 cases;onlyexpiredorphanpurged,productionretention explicitly stillopen.

### T034. Считать автоматические assessments и diff

**Статус:** `done` · **Приоритет:** P0 · **Размер:** L.

**Зависимости:** T020, T031, T033.

**Результаты/файлы:** `backend/app/assessments/`; `backend/tests/fixtures/`.

**Шаги:**

1. Выполнить модель на подтверждённых группах и сохранить facts/rulesVersion.
2. Сравнить старый/новый снимок и причины изменения, учитывать unknown.

**Критерии закрытия:**

- Результат воспроизводится из snapshot и version.
- Смена мест/согласий/статуса вызывает правильный diff без двойного вычитания.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b12-progress.md](../docs/evidence/b12-progress.md) — B12:immutable server-derived listed-consent-v1 bounds/refusals/diff and readonlyAPI;11domain+3local/3nativePGchecks passed,atomicrollback/oldversions/unknown preserved.

### T035. Обработать отказ и восстановление источника

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T024, T032, T033, T080, T102.

**Результаты/файлы:** `backend/app/sources/`; `frontend/tests/e2e/source-failure.spec.ts`.

**Шаги:**

1. Ввести degradation/stale политики и диагностику ошибок.
2. Проверить падение, карантин, восстановление и переход обратно к актуальному состоянию.

**Критерии закрытия:**

- Последние корректные данные остаются доступны.
- Восстановление не скрывает историю неудач.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 21/30:durable source check history and recovery without refreshing old facts;24nativePG+migration,1nativequarantine and1Chromium passed;schema0007.

### T036. Сделать детерминированный replay архивов

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T013, T031, T034.

**Результаты/файлы:** `backend/tests/replay/`; `docs/evidence/replay.md`.

**Шаги:**

1. Воспроизвести последовательность разрешённых архивных снимков.
2. Разделить source time и replay time и сравнить ожидаемые изменения.

**Критерии закрытия:**

- Повтор replay даёт те же outcomes.
- Архив в UI постоянно отличим от текущей кампании.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b12-replay.json](../docs/evidence/b12-replay.json) — B12:two complete nativePG replay runs/6stages produce identical semantic outcomes;failure/recovery/repeat/absence and dates verified,0HTTP,cleanup.
- [docs/evidence/b12-progress.md](../docs/evidence/b12-progress.md) — Syntheticchanges explicitly separated from genuine-derived baselines;not24h live observation.

### T037. Добавить эксплуатационное управление источниками

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T031, T032, T035, T082.

**Результаты/файлы:** `backend/app/manage.py`; `docs/RUNBOOK.md`.

**Шаги:**

1. Создать CLI/status для enable/disable/retry/quarantine и проверки версий.
2. Защитить управление и исключить вывод секретов.

**Критерии закрытия:**

- Оператор может отключить сломанный источник без изменения чужих данных.
- Все действия прослеживаются в audit log.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b12-progress.md](../docs/evidence/b12-progress.md) — Native operator fencing/rate limit/audit and migration checks passed;safe CLI documented.

### T038. Посчитать честные метрики покрытия

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T012, T031, T035, T092.

**Результаты/файлы:** `backend/app/coverage/`; `docs/catalog-coverage.md`.

**Шаги:**

1. Разделить каталог/адаптер/успешно обновляемую группу/архив.
2. Вывести даты и знаменатели измерений.

**Критерии закрытия:**

- Карточка каталога не увеличивает число работающих интеграций.
- Отчёт воспроизводим по БД и паспортам.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b12-progress.md](../docs/evidence/b12-progress.md) — DB-derived distinct reviewed/imported/archive/conditional/automatic counters verified on native PG and contract/build checks.

### T057. Масштабировать адаптеры по платформам вузов

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** L.

**Зависимости:** T031, T037, T192, T194.

**Результаты/файлы:** `backend/app/sources/adapters/`; `docs/sources/`.

**Шаги:**

1. Использовать national-inventory.json как список кандидатов, сохраняя unknown/error/robots статусы.
2. Проверить страницы приёма и сгруппировать реальные форматы списков, не выводить совместимость из CMS.
3. Расширить хранение профилей по семействам без текущего предела одного JSON и с сохранением старых версий.
4. Для каждого нового источника пройти паспорт, оригинал, независимую сверку и явную регистрацию.
5. Проверить массовую очередь, per-domain лимиты и свежесть до объявления национальной автоматизации.

**Критерии закрытия:**

- Каждая добавленная группа имеет доказательство совместимости.
- Рост покрытия не ухудшает freshness и лимиты источников.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

### T076. Базовый контракт и закрытый реестр адаптеров

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T010, T015, T028.

**Результаты/файлы:** `backend/app/sources/contracts.py`; `backend/app/sources/registry.py`.

**Шаги:**

1. Определить типизированный ParsedList с unknown и provenance.
2. Связать точный source/group/season с зарегистрированным адаптером.

**Критерии закрытия:**

- Неподдержанный источник или версия отклоняется.
- Нет публичного произвольного fetch и нет автоматической аттестации.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S029 / B02 4/10: Frozen strict adapter DTOs preserve unknowns and official order; HMAC identities scoped by source/group/year. Closed registry checks domain/version/enabled/attestation; production registry empty. First collection found incorrect fetcher helper import; replaced with static URL binding validation, DNS remains fetcher responsibility. pytest contract+fetcher: 39 passed / exit 0. Real adapters remain unattested.

### T077. Нормализация и карантин неполного списка

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T076.

**Результаты/файлы:** `backend/app/sources/validation.py`.

**Шаги:**

1. Проверить сезон, группу, строки, порядок и полноту.
2. Сохранить unknown; выявить дубли и резкие изменения.

**Критерии закрытия:**

- Неполный/неверный список не публикуется.
- Равные баллы не меняют официальный порядок; ошибки не содержат PII.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S030 / B02 5/10: Strict normalized-list validation rejects wrong identity/season, incomplete pagination, duplicate identities/references, rank gaps/order, unconfirmed emptiness, future/regressed timestamps and configured large drops. Unknown fields retained; equal scores never reordered. pytest validation+contract: 13 passed / exit 0. QualityPolicy thresholds documented as review signals; synthetic samples only.

### T078. Приватное хранилище исходных ответов

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T028, T076.

**Результаты/файлы:** `backend/app/sources/storage.py`.

**Шаги:**

1. Атомарно сохранить ограниченные bytes по SHA-256.
2. Проверять целостность чтения и ограничения путей.

**Критерии закрытия:**

- Повтор не создаёт дубликат; повреждение обнаруживается.
- Произвольный путь и превышение размера отклоняются.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S031 / B02 6/10: Private bounded SHA-256 raw store uses fsync and atomic no-overwrite linking; verifies hash on read/repeat, rejects path traversal and oversized data. pytest tests/test_raw_store.py: 3 passed / exit 0, including 24 concurrent writers and corrupt existing object. Raw files ignored by Git and never exposed through HTTP. Windows ACL and retention/restore remain deployment gates.

### T079. Атомарная публикация нормализованного снимка

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T077, T078.

**Результаты/файлы:** `backend/app/sources/publishing.py`; `backend/alembic/versions/0003_import_provenance.py`.

**Шаги:**

1. Версионировать provenance и normalized hash.
2. В одной транзакции записать снимок/строки/latest.

**Критерии закрытия:**

- Ошибка не меняет latest и прошлые строки.
- Повтор проверен; смена parser version сохраняет новый снимок.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S032 / B02 7/10: Atomic source publication stores immutable rows/provenance and swaps latest under source lock; repeat keyed by raw hash plus parser version. New migration 0003 preserves populated old snapshots and FK references; development startup now uses Alembic. First migration tests exposed old head/unversioned-latest assumptions; updated historical fixture to frozen 0001/0002 and added explicit future-schema rejection. pytest publishing+migrations+API: 27 passed / 1 real PG skipped / exit 0; includes concurrent repeat, rollback after row-write failure, parser version change, legacy preservation, PG offline SQL. Real PG still unverified.

### T080. Диагностика свежести зарегистрированного источника

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T079.

**Результаты/файлы:** `backend/app/sources/status.py`.

**Шаги:**

1. Разделить fetched/source-updated/checked/success.
2. Выдать bounded status без строк участников и raw.

**Критерии закрытия:**

- Архив всегда помечен; ошибка не маскирует старый снимок.
- Disabled/unknown/stale не выдаются за fresh.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S033 / B02 8/10: Public bounded status separates season/dataKind and checked/success/fetched/source timestamps; no rows, raw or hashes. Archive/disabled/errors/unknown/unsupported never fresh; successful live content checks expire by policy. Late old errors do not replace newer success. pytest status+publication: 6 passed, final status subset 3 passed / exit 0. Production registry still empty and assessmentAvailable always false.

### T081. Очередь обновлений с lease и ограниченными повторами

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T076, T079.

**Результаты/файлы:** `backend/app/jobs.py`; `backend/alembic/versions/0004_source_jobs.py`.

**Шаги:**

1. Дедупликация задания на источник и атомарный claim.
2. Проверить lease expiry, fencing token, backoff и предел попыток.

**Критерии закрытия:**

- Два локальных worker не получают одновременно одно задание.
- Старый token не подтверждает новую аренду; PG отдельно не объявлен проверенным.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S034 / B02 9/10: Durable source_jobs migration 0004; one job/source, atomic claims, token fencing, expiry recovery, bounded retry/backoff/Retry-After and periodic scheduling. Disable revokes active lease. pytest queue+migrations: 14 passed / 1 PG skipped / exit 0, including 16 concurrent enqueues/claims, retry exhaustion, stale owner rejection and populated upgrade preservation. PostgreSQL SKIP LOCKED code is not claimed runtime-tested.

### T082. Worker и локальные команды управления источниками

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T080, T081.

**Результаты/файлы:** `backend/app/worker.py`; `backend/app/sources/cli.py`.

**Шаги:**

1. Связать fetch/parse/validate/store/publish с очередью.
2. Добавить once/loop, status/enqueue/disable и документировать запуск.

**Критерии закрытия:**

- Синтетический сквозной цикл и отказ сохраняют правильный latest.
- Неизвестные адаптеры запрещены; реальные интеграции остаются неаттестованными.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S035 / B02 10/10: Separate worker once/loop and local source CLI now connect queue/fetch/parse/validate/store/publish. Production registry has no real adapters and CLI has no bypass. Eight worker tests cover synthetic success/quarantine, revoked and expired leases, retry, process-wide fetch timeout, crash after publication replay and redacted parser errors. Final full pytest: 154 passed / 1 real PG skipped / exit 0; frontend npm test: 58 passed, build exit 0; full Chromium E2E: 20 passed after explicit API restart on migrated 0004, plus final comparison subset 2 passed. Initial CLI smoke failed because development reload had not migrated the old preview DB; stopped only own session 15194, explicitly ran alembic upgrade/check, restarted own API session 45338/PID15852, verified OpenAPI status route and revision 0004; worker once then idle and source list empty, exit 0. Final review added mobile table-scroll hint and keyboard scroll and fixed CSS token. Synthetic previews refreshed, demo session deleted (204). T082 done; B02 10/10. Current preview 5182/API8002, backend/.pytest_cache/batch02.db. GitHub:443 and Docker ACL remain blocked; real sources/PG/remote CI/hosting/fonts and release gates remain open. Overall engineering estimate approximately 35%, D1/30; 30 of 82 cards done, not a release claim.

### T099. Соблюдать deadline блокировки внутри процесса и между процессами

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T087.

**Результаты/файлы:** `backend/app/sources/storage.py`.

**Шаги:**

1. Ограничить ожидание RLock общим deadline.
2. Проверить вложенные операции и освобождение после timeout.

**Критерии закрытия:**

- Конкурирующий поток получает timeout в срок.
- Reentrant put/read под внешним lock работает.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S054 / B04 7/10: RawStore timeout now covers in-process RLock wait and OS lock using one monotonic deadline; negative/nonfinite values rejected, nested operations remain reentrant, descriptor closes even if unlock fails. Windows lock-state paths normalized for case. Targeted storage/retention/publication/backup/restore pytest: 18 passed / exit0, including a blocked thread timing out while owner keeps lock, subsequent write, nested two-instance use and existing process lock test.

### T100. Ограничить весь обмен результата дочернего fetch-процесса

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T082.

**Результаты/файлы:** `backend/app/worker.py`.

**Шаги:**

1. Убрать неограниченный recv после poll.
2. Ограничить процесс и проверять завершённый bounded result.

**Критерии закрытия:**

- Частичный результат не зависает после deadline.
- Невалидный результат и cleanup не раскрывают raw/URL.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S055 / B04 8/10: Removed poll-then-blocking-recv exchange: parent now waits for child exit within one deadline, then validates a private bounded bytes/JSON spool (size/hash/schema). Partial envelopes cannot cause an unbounded recv; fixed files cleaned after termination. Targeted fetch-exchange/worker/capture pytest: 13 passed / exit0, including child that demonstrably writes a partial result then stalls, 1MiB completed transfer, malformed envelope, existing timeout and synthetic publication recovery. No real source attestation claimed.

### T102. Показывать исчерпанные и истёкшие задания в диагностике источника

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T080, T081.

**Результаты/файлы:** `backend/app/sources/status.py`.

**Шаги:**

1. Учитывать failed/expired queue state при freshness.
2. Вернуть ограниченные worker status без token.

**Критерии закрытия:**

- Исчерпанное задание не маскируется fresh.
- Архивная метка и последний корректный снимок сохраняются.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S057 / B04 10/10: Read-only diagnostics now expose bounded workerState and treat expired/final-failed jobs as source_error without overwriting source fields or published snapshots. Live/archive tests cover lease boundary, exhaustion, recovery and fresh coverage. Targeted status/queue/coverage/worker: 19 passed. Final full backend: 196 passed / 1 PostgreSQL skipped; frontend67 and production build passed; all32 Chromium E2E passed on explicitly restarted current API8003 (session98287/PID19396, isolated batch04.db). No real adapters or release gates unlocked.

### T129. Reject truncated HTTP source responses

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T028.

**Результаты/файлы:** `backend/app/sources/fetcher.py`; `backend/app/sources/publishing.py`; `backend/tests/test_fetcher.py`.

**Шаги:**

1. Reject truncated HTTP source responses.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Content-Length mismatch cannot produce a FetchResult; genuine complete responses remain valid..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S087: Both HTTPS stream reader and injected reader contract reject declared-length mismatch with retryable incomplete_response; complete bodies remain valid. Fetcher/worker45 passed. No real source attestation implied.

### T130. Reject ambiguous HTTP headers and malformed redirects

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T028.

**Результаты/файлы:** `backend/app/sources/fetcher.py`; `backend/tests/test_fetcher.py`.

**Шаги:**

1. Reject ambiguous HTTP headers and malformed redirects.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Critical duplicate headers fail safely; invalid redirect syntax becomes a bounded FetchError..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S088: Fetch reader rejects duplicate critical headers and conflicting transfer framing; malformed/control-character redirects become safe bounded errors. Fetcher42 passed, including no body read on ambiguity. Conservative framing policy follows RFC9112 section6.3.

### T131. Validate immutable fetch policies strictly

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T028.

**Результаты/файлы:** `backend/app/sources/fetcher.py`; `backend/tests/test_fetcher.py`.

**Шаги:**

1. Validate immutable fetch policies strictly.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Nonfinite or wrong-type limits and mutable/unapproved domain policy are rejected before network..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S089: Immutable fetch policy validates finite timeout up to30s, strict size up to5MiB, redirects0..5, exact lowercase DNS domains and supported content types before network. Fetcher/capture56 passed, including mutable sets, NaN, bool-as-int and wildcard/IP refusals.

### T132. Preserve fetch outcome when spool cleanup fails

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T100.

**Результаты/файлы:** `backend/app/worker.py`; `backend/tests/test_fetch_exchange.py`.

**Шаги:**

1. Preserve fetch outcome when spool cleanup fails.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Cleanup attempts every known file and emits only a safe diagnostic without masking original fetch errors..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S090: Spool cleanup attempts all known files, logs only stable safe codes and never masks valid fetch/error outcome. Process cleanup remains bounded without closing a live process. Exchange/worker11 passed; corrected test assumption when an empty folder was already removed.

### T133. Validate adapter declarations before registry use

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T076.

**Результаты/файлы:** `backend/app/sources/registry.py`; `backend/tests/test_registry_contract.py`.

**Шаги:**

1. Validate adapter declarations before registry use.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Attestation is an actual bool; version/domain/callable contract cannot silently admit malformed adapters..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S091: Adapter declarations require an actual boolean attestation, bounded version token, immutable exact domains and callable parser before registry use. Registry/status/worker21 passed; production registry remains empty.

### T134. Apply queue policies on explicit eligible reenqueue

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T081.

**Результаты/файлы:** `backend/app/jobs.py`; `backend/tests/test_queue_policy.py`.

**Шаги:**

1. Apply queue policies on explicit eligible reenqueue.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Changed interval/max attempts apply to eligible jobs; running/backoff jobs remain untouched..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S092: Explicit eligible reenqueue applies requested interval/max attempts and resets due time; running and backoff jobs are not modified. Strict integer queue settings reject bool coercion. Queue/worker13 passed.

### T174. Bound larger verified source responses by explicit adapter policy

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T027.

**Результаты/файлы:** `backend/app/sources/fetcher.py`; `backend/app/worker.py`; `backend/app/sources/storage.py`.

**Шаги:**

1. Keep5MiB default and require an explicit trusted adapter limit up to8MiB for observed SGU response.
2. Carry policy through subprocess exchange/raw storage and prove oversize refusal.

**Критерии закрытия:**

- A5851174byte genuine response fits an explicitly declared8MiB policy; default remains5MiB,exchange validates selected policy and raw/backup retain hashes;8MiB+1 is rejected..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 6/30:trusted8MiB policy/default5MiB verified through child/raw/backup;71+4 targeted checks passed and actual bounded SGU5851174byte fetch succeeded with pinned TLS.

### T175. Register the reviewed archive group through an explicit operator command

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T029, T033.

**Результаты/файлы:** `backend/app/sources/pilots.py`; `backend/app/sources/cli.py`.

**Шаги:**

1. Register the reviewed archive group through an explicit operator command.
2. Verify meaningful success,boundary,refusal and actual PostgreSQL cases.

**Критерии закрытия:**

- Default install creates no enabled source;explicit idempotent registration validates fixed group metadata,requires stable operator key before enable and never accepts arbitrary URL;existing conflicting records are refused..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 11/30:explicit disabled/idempotent registration and keyed enable verified in actual Compose;conflicts refused,private key excluded from image context;full396backend/0skip passed.

### T187. Поддержать конфигурируемые семейства адаптеров с аттестацией каждого источника

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T027.

**Результаты/файлы:** `backend/app/sources/registry.py`; `docs/MILESTONE_70.md`.

**Шаги:**

1. Зафиксировать функциональный рубеж70% до реализации.
2. Разрешить несколько проверенных scopes для общей версии parser без открытия произвольныхURL.

**Критерии закрытия:**

- Каждый подключённый URL/year/kind имеет собственный паспорт/fixture/hash.
- Непроверенный scope отвергается;старые версии и hashes не меняются.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b12-progress.md](../docs/evidence/b12-progress.md) — B12:multi-scope attestation registry and frozen70%milestone;38targeted tests passed,legacy scope preserved.

### T188. Доказать переиспользование общего parser на настоящих конкурсных группах

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T187, T029.

**Результаты/файлы:** `backend/app/sources/adapters/`; `backend/tests/fixtures/`; `docs/sources/`.

**Шаги:**

1. Выделить структурный parser и декларативные настройки профиля.
2. Получить второй настоящий список и независимо сверить строки/места/сезон.

**Критерии закрытия:**

- Один parser обслуживает два реальных профиля без копирования алгоритма.
- Различия схемы или неизвестная полнота отвергаются;национальное покрытие не заявлено.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b12-progress.md](../docs/evidence/b12-progress.md) — B12:one JSON-configured parser independently verified on573SGU+581GUAPoriginal rows;22targetedchecks,privateIDsremoved,legacy preserved.

### T193. Составить воспроизводимую инвентаризацию страниц приёма и форматов

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T190.

**Результаты/файлы:** `scripts/source_inventory.py`; `docs/sources/national-inventory.json`.

**Шаги:**

1. Проверять только официальные сайты из опорного каталога с лимитами.
2. Сохранять факты о ссылках, HTTP и формате без данных абитуриентов.

**Критерии закрытия:**

- Есть датированный машиночитаемый отчёт и явные неизвестные.
- Обнаружение страницы не регистрирует и не включает источник.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b14-national-catalog.md](../docs/evidence/b14-national-catalog.md) — All 1257 reference institutions inventoried, 1083 unique HTTPS pages, 641 with candidate links; all unknown/errors explicit; 3 tests passed and offline replay identical. No automatic source enabled.

### T194. Проверить следующее семейство или новый scope на реальном источнике

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T193.

**Результаты/файлы:** `backend/app/sources/profiles/reviewed.json`; `docs/sources/`.

**Шаги:**

1. Получить оригинал и определить поддержанный scope/сезон.
2. Независимо сверить строки, места и отказы перед регистрацией.

**Критерии закрытия:**

- Совместимость доказана оригинальными данными и тестами.
- Неполный или недоступный источник не закрывает задачу; нет заявления национального охвата.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b14-sgu4576-audit.json](../docs/evidence/b14-sgu4576-audit.json) — 453 original rows independently checked; new fixture uses synthetic candidate values.
- [docs/evidence/b14-sgu4576-runtime.json](../docs/evidence/b14-sgu4576-runtime.json) — Actual bounded HTTPS -> worker -> isolated PostgreSQL -> stored audit; 453 rows/24 seats; schema removed.
- [docs/evidence/b14-final-verification.json](../docs/evidence/b14-final-verification.json) — Final current code: 571 mandatory-PG backend passed/0 skipped; 116 Vitest/build; compiled Chromium 77 passed/32 explicitly scoped skips.

### T195. Проверить найденные страницы приёма и признаки списков

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T193.

**Результаты/файлы:** `scripts/admissions_inventory.py`; `docs/sources/admissions-inventory.json`.

**Шаги:**

1. Выбрать кандидатные страницы по прозрачным правилам, исключая новости/работу.
2. Выполнить ограниченный HTTPS обход с robots, provenance, кэшем и явными отказами.

**Критерии закрытия:**

- Есть воспроизводимый отчёт по всем исходным учреждениям.
- Структурные признаки не выданы за аттестацию или полный импорт.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b15-admissions-inventory.md](../docs/evidence/b15-admissions-inventory.md) — 1257 reference entries reconciled; 633 institutions/1073 URLs selected and observed; 6 unit checks and identical offline replay passed. Candidate table evidence remains incomplete/unattested; no sources enabled.

### T196. Сгруппировать реальные структуры списков для повторного использования

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T195.

**Результаты/файлы:** `scripts/group_source_formats.py`; `docs/sources/format-families.json`.

**Шаги:**

1. Сравнить реальные заголовки/структуру и источники форматов.
2. Выделить группы кандидатов для независимой проверки.

**Критерии закрытия:**

- Повторяемость подкреплена оригинальными страницами из разных scope.
- CMS и одинаковое расширение файла сами по себе не означают совместимость.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b15-format-families.md](../docs/evidence/b15-format-families.md) — 14 verified official child pages; 1 cross-institution structural candidate (MIEPP/UIFR), not automatic eligibility; 8 targeted tests and identical offline replay passed. Empty/header-only pages remain unsupported.

### T197. Масштабировать реестр профилей без одного ограниченного файла

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T194.

**Результаты/файлы:** `backend/app/sources/table_profiles.py`; `backend/app/sources/profiles/`; `backend/tests/test_profile_catalog.py`.

**Шаги:**

1. Разнести проверенные профили по версионированным manifest/shards с hashes.
2. Сохранить прежние bindings/proofs и ограничить память/число/размер файлов.

**Критерии закрытия:**

- Более 100 профилей загружаются без снятия валидации и безопасных ограничений.
- Дубликаты, escape paths, повреждение и несовместимые версии отвергаются; legacy replay сохранён.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b15-profile-catalog.md](../docs/evidence/b15-profile-catalog.md) — Immutable manifest/shards preserve all 3 old scopes; 1001 synthetic profiles loaded in 11 shards; 48 native-PG targeted tests passed, 0 skipped. No real coverage added.

### T198. Аттестовать повторяемое семейство на новых настоящих источниках

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T196, T197.

**Результаты/файлы:** `backend/app/sources/`; `docs/sources/`; `backend/tests/fixtures/`.

**Шаги:**

1. Получить официальные оригиналы и независимо сверить поддержанные поля.
2. Добавить общую реализацию/конфигурации, негативные случаи и native публикацию.

**Критерии закрытия:**

- Есть проверяемое расширение scope/вузов на реальных данных.
- Неполные/закрытые/неизвестные источники не считаются подключёнными; новые fixture синтетические.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b15-section-family.md](../docs/evidence/b15-section-family.md) — 11 reviewed archive scopes across 2 new institutions, 168 independently audited rows; actual bounded HTTPS to worker/PG and 11 stored audits passed. Native targeted 68 passed, completeness follow-up 23 passed, 0 skipped.

### T199. Проверить массовую очередь и отчёт расширенного покрытия

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T198.

**Результаты/файлы:** `backend/tests/`; `scripts/`; `docs/evidence/`.

**Шаги:**

1. Проверить многоисточниковый планировщик и domain leases на native PG.
2. Сверить source/group/archive/fresh/unsupported метрики и оформить evidence.

**Критерии закрытия:**

- Массовые задания не обходят per-domain лимиты и не дублируются.
- Фактическое покрытие и ограничения не подменены синтетическим нагрузочным набором.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b15-mass-queue.md](../docs/evidence/b15-mass-queue.md) — Native PG queue:1000 synthetic jobs/100 domains,12 claim threads,100 fenced recoveries,no duplicate completions. Real HTTPS:14 archive scopes/4 institutions/1775 rows,13 fetches/1 cache hit. Final627 backend/0skip,116Vitest/build,79compiled Chromium/32scopedskips,5actual-nginx checks passed.
- [docs/evidence/b15-final-verification.json](../docs/evidence/b15-final-verification.json) — Full native regression, current compiled UI, actual nginx and separate persistent local demo; limits and release gaps explicit.

### T200. Выбирать вузы во всём каталоге конкурсных групп

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T199.

**Результаты/файлы:** `frontend/src/`; `frontend/tests/e2e/`.

**Шаги:**

1. Добавить поиск и страницы вузов в фильтр источников.
2. Сохранять выбранный вуз при смене запроса и ошибке следующей страницы.

**Критерии закрытия:**

- Доступен вуз за первыми50записями с клавиатуры.
- Ошибка не превращается в пустой результат; нет переполнения320px.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b16-university-filter.md](../docs/evidence/b16-university-filter.md) — Full directory search/pagination, retained selection and next-page retry at320px;116Vitest/build and4compiledChromium passed.

### T201. Фильтровать и ограничивать группы на стороне БД

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T200.

**Результаты/файлы:** `backend/app/source_catalog.py`; `backend/tests/`.

**Шаги:**

1. Перенести фильтры/count/cursor/limit и facets в SQL.
2. Сохранить Unicode-поиск и неизменность курсора на SQLite/PG.

**Критерии закрытия:**

- Не загружаются все ORM группы до ограничения страницы.
- Порядок/count/фильтры/буквальные спецсимволы и Unicode совпадают с контрактом.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b16-sql-catalog.md](../docs/evidence/b16-sql-catalog.md) — SQL filters/count/cursor/limit preserve Unicode and literals;10001 synthetic groups hydrate<=8 for page7. Migration0011 backfill/reversal/offline PG passed;34 targeted+4 expanded native checks,0skipped.

### T202. Подключать набор проверенных профилей атомарно

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T201.

**Результаты/файлы:** `backend/app/sources/`; `backend/tests/`; `docs/RUNBOOK.md`.

**Шаги:**

1. Добавить операторский batch с точными ID из закрытого manifest.
2. Проверить откат конфликтующего набора, повтор и конкуренцию на PG.

**Критерии закрытия:**

- Нельзя регистрировать URL или неизвестные профили.
- Конфликт не оставляет частично подключённый набор; ключ/карантин/история сохраняются.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b16-profile-batch.md](../docs/evidence/b16-profile-batch.md) — Atomic1-100 exact manifest IDs, shared catalog mutex, late-conflict/quarantine rollback and legacy preservation;41targeted+14expanded native checks passed,0skip.

### T203. Исследовать следующий подтверждаемый формат списков

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T196.

**Результаты/файлы:** `scripts/`; `docs/sources/`; `docs/evidence/`.

**Шаги:**

1. Выбрать следующие официальные страницы из инвентаризации.
2. Сохранить ограниченный replayable аудит структуры и неизвестных полей.

**Критерии закрытия:**

- Есть датированные оригиналы/происхождение или точные причины отказа.
- Исследование не считается аттестацией или дополнительным покрытием без независимой проверки.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b16-stateful-research.md](../docs/evidence/b16-stateful-research.md) — 5official pages/3institutions, verified linked BGU bachelor with109visible rows; stateful/dynamic/level gaps explicit.3synthetic tests and network-forbidden identical offline replay passed;0sources attested.

### T204. Проверить масштабирование каталога и итог покрытия B16

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T202, T203.

**Результаты/файлы:** `backend/tests/`; `frontend/tests/`; `docs/evidence/`.

**Шаги:**

1. Проверить native PG, актуальную сборку и реальные фильтры.
2. Обновить отдельный локальный стенд с прежними ключом/volumes и сверить покрытие.

**Критерии закрытия:**

- Проверки относятся к текущим файлам и новой схеме при её изменении.
- Архив/fresh/unsupported и синтетическая нагрузка различаются; T056/T057 не закрыты частично.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b16-integration.md](../docs/evidence/b16-integration.md) — Final648backend/0skip,116Vitest/build,83compiledChromium/30scopedskips and12finalactual-nginx checks passed. Restored-copy0010->0011 preserved19tables; actual demo14stored audits/1775rows passed with original key/volumes. Real coverage unchanged14archivegroups/4universities; research0newattestations.
- [docs/evidence/b16-final-verification.json](../docs/evidence/b16-final-verification.json) — Current native regression, exact compiled assets, restored-copy migration rehearsal and actual local nginx checks; national/release limits explicit.

### T205. Проверить точный GET scope БГУ и места конкурса

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T203.

**Результаты/файлы:** `docs/sources/`; `scripts/`.

**Шаги:**

1. Получить свежий официальный оригинал и сверить выбранные фильтры/план/число строк.
2. Определить порядок, публичный lookup ID и неизвестные поля без вывода строк.

**Критерии закрытия:**

- Доказан точный сезон/форма/финансирование/конкурс и план мест.
- GET по умолчанию не выдан за все21направление; персональные части ID не попадают в отчёты.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b17-bgu-scope.md](../docs/evidence/b17-bgu-scope.md) — Fresh official exact contract/full-time construction scope:20seats/109rows/109unique minimal lookup IDs,14explicit enrolled; controls/count/order reviewed,0attestations yet.

### T206. Добавить общий decoder для таблиц с проверенными фильтрами

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T205.

**Результаты/файлы:** `backend/app/sources/`; `backend/tests/fixtures/`.

**Шаги:**

1. Ввести отдельную версию общего parser с закрытой декларативной конфигурацией.
2. Проверить синтетические fixtures и отказы при изменении фильтра/ID/разметки.

**Критерии закрытия:**

- Старые версии/proofs не меняются.
- Порядок и только проверенные поля сохраняются; чужой scope/неполный список отклоняется.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b17-filtered-family.md](../docs/evidence/b17-filtered-family.md) — Generic filtered version,109synthetic rows, closed scope/count/roles/minimal-ID/enrollment checks;65native targeted passed,0skip. Legacy profiles/proofs unchanged; no runtime attestation yet.

### T207. Независимо сверить и аттестовать архивную группу БГУ

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T206.

**Результаты/файлы:** `scripts/`; `backend/app/sources/profiles/`; `docs/evidence/`.

**Шаги:**

1. Сравнить все оригинальные строки независимым parser.
2. Опубликовать immutable профиль и паспорт после полной сверки.

**Критерии закрытия:**

- Все строки и места подтверждены, новые candidate fixtures полностью синтетические.
- Новая аттестация точная, не разрешает другие настройки/URL автоматически.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b17-attestation.md](../docs/evidence/b17-attestation.md) — All109original rows independently matched,20seats/14explicit enrolled; immutable exact BGU profile added,old14unchanged.46native targeted passed/0skip; Source not enabled by attestation.

### T208. Проверить worker и сохранение записи новой группы

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T207.

**Результаты/файлы:** `backend/tests/`; `frontend/src/`; `frontend/tests/`; `docs/evidence/`.

**Шаги:**

1. Пройти настоящий HTTPS→worker→PG→offline audit.
2. Проверить приватный scoped lookup по минимальному коду без СНИЛС и повтор сохранения.

**Критерии закрытия:**

- Есть настоящий полный импорт нового вуза и proof его сохранения.
- Код не сохраняется в браузере/экспорте/ответах ошибок, платная группа не даёт бюджетный сценарий.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b17-worker-lookup.md](../docs/evidence/b17-worker-lookup.md) — Actual bounded HTTPS->worker->native PG->independent/current/stored audit109rows/20seats passed.7native owner/API tests,116Vitest/build and1synthetic browser lookup/privacy/save passed.

### T209. Обновить стенд и сверить покрытие B17

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T208.

**Результаты/файлы:** `docs/`; `scripts/`; `frontend/tests/`.

**Шаги:**

1. Обновить прежний demo с тем же ключом/volumes.
2. Выполнить актуальную регрессию, аудит старых/нового источников и отчёт.

**Критерии закрытия:**

- Прирост покрытия основан на реальном импорте, архив/fresh разделены.
- T056/T057 не закрываются частично; процессы/ограничения и следующий шаг переданы.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b17-integration.md](../docs/evidence/b17-integration.md) — Final666backend/0skip,116Vitest/build,84compiledChromium/31scopedskips,1syntheticBGUlookup and18actual-nginx checks passed. Actual demo15archivegroups/5universities/1884rows, old14snapshots/1775rows unchanged and15stored audits passed. Same key/volumes/schema0011; pagination-focus defect fixed and verified with held real response.
- [docs/evidence/b17-final-verification.json](../docs/evidence/b17-final-verification.json) — Current mandatory-PG regression, exact compiled lazy assets, real new source import, old facts preserved, daily archive jobs and explicit national/live/release limits.

## E4. Объяснения и UX

Плановый интервал: D15–D22.

### T022. Добавить поиск вузов и групп с coverage

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T012, T018.

**Результаты/файлы:** `backend/app/source_catalog.py`; `frontend/src/pages/SourcesPage.tsx`; `frontend/tests/e2e/source-catalog.spec.ts`; `backend/tests/test_group_catalog.py`.

**Шаги:**

1. Сделать поиск/фильтры/пагинацию по вузу, филиалу, сезону и группе.
2. Показать automatic/manual/archive/unsupported и путь заявки на подключение.

**Критерии закрытия:**

- Неподключённый вуз не выглядит рабочей интеграцией.
- Можно добавить ручное направление без ложного promise автоматического сбора.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S015: выбор вузов и manual fallback проходят E2E; группы/фильтры пока не готовы.
- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 12/30:real group catalog filters/branch/season/cursor and archive/manual/unsupported UI done;6backend+8contract+10browser+3header/mobile checks passed,currentPGarchive573rows.

### T024. Показывать provenance и отдельные времена

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T018, T033.

**Результаты/файлы:** `frontend/src/components/`; `backend/app/schemas.py`.

**Шаги:**

1. Вывести fetched/source-updated/manual-captured без подмены смыслов.
2. Реализовать stale/error/archive/unknown и ссылку на оригинал.

**Критерии закрытия:**

- Ни одно число автоматической карточки не остаётся без источника/снимка.
- Ошибка обновления не освежает старые данные.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 19/30:every archive number has snapshot/source/separate fetched/source-updated/checked times;6backend+9Chromium passed,failed check preserves old dates;manual model/capture clarified.

### T025. Закрыть ошибки загрузки и повторных действий

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T019, T021, T024, T072, T073, T098.

**Результаты/файлы:** `frontend/src/lib/api.ts`; `frontend/src/pages/`; `frontend/tests/e2e/`.

**Шаги:**

1. Добавить timeout/cancel/retry для чтения и явный исход записи.
2. Проверить offline, 401/403/404/409/422/429/503 и recovery.

**Критерии закрытия:**

- Интерфейс не зависает в бесконечном pending.
- Повтор после неизвестного исхода записи безопасен.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 24/30:96Chromium+102unit passed;explicit source error recovery/401privacy/lostDELETE reconciliation;two backend test assumptions corrected and targeted reruns passed.

### T026. Проверить доступность кабинета и мобильный UX

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T008, T022, T025, T075, T097.

**Результаты/файлы:** `frontend/src/tracker.css`; `frontend/tests/e2e/accessibility.spec.ts`.

**Шаги:**

1. Проверить keyboard, labels, focus, live errors и контраст.
2. Проверить длинные названия, крупные числа, таблицу истории, 320px и две темы.

**Критерии закрытия:**

- Основной путь выполним клавиатурой.
- Нет скрытых кнопок/обрезанных чисел и потери смысловых меток.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 25/30:manual/archive keyboard and focus recovery,320px/longnames/million values,8contrastpairs/both themes andactualPDF passed;9currentChromium.

### T039. Объяснять оценку и изменение проверенными фактами

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T020, T034, T069.

**Результаты/файлы:** `backend/app/explanations/`; `frontend/src/components/`.

**Шаги:**

1. Создать шаблоны для текущего сценария, условий, устаревания и неизвестных.
2. Согласовать текст с числами и reason codes.

**Критерии закрытия:**

- Объяснение не обещает поступления и не добавляет несуществующий процент.
- Текст содержит проверяемое основание изменения.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b12-progress.md](../docs/evidence/b12-progress.md) — B12:storedfact-grounded explanations/UIconditionalbounds/refusals/history;16local+3nativePG+17TScontract+3Chromium/currentbuildpassed,320px/boththemes.

### T040. Показать изменения внутри приложения

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T023, T034, T039.

**Результаты/файлы:** `backend/app/changes/`; `frontend/src/pages/`.

**Шаги:**

1. Создавать дедуплицированные события и seen-state владельца.
2. Показать изменение и переход к исходному сравнению.

**Критерии закрытия:**

- Повтор worker не создаёт повторных сообщений.
- Чужие события недоступны, прочтение идемпотентно.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b12-progress.md](../docs/evidence/b12-progress.md) — Owner isolation, idempotent seen-state, atomic event publication and actual PostgreSQL/browser comparison verified.
- [backend/tests/test_changes.py](../backend/tests/test_changes.py) — Owner isolation, idempotent seen-state, atomic event publication and actual PostgreSQL/browser comparison verified.
- [docs/archive/retired-frontend/changes.spec.ts](../docs/archive/retired-frontend/changes.spec.ts) — Owner isolation, idempotent seen-state, atomic event publication and actual PostgreSQL/browser comparison verified. Historical evidence archived during T242; it targets the retired manual UI.

### T075. Сравнение сохранённых ручных направлений

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T020, T070.

**Результаты/файлы:** `frontend/src/components/WatchComparison.tsx`.

**Шаги:**

1. Добавить выбор до трёх направлений.
2. Показать входы, сценарии и даты без общего рейтинга.

**Критерии закрытия:**

- Два разных вуза сравниваются по одинаковым явным полям.
- Удаление выбранной записи не оставляет устаревшую строку.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S028 / B02 3/10: Added selection of 2-3 manual directions with inputs, both scenarios, save times and official links; no cross-group ranking/probability. Build exit 0; 2 real-API Chromium tests passed at 390/1440, including selection limit, deletion and no page overflow. Files: WatchComparison.tsx, tracker.css, comparison.spec.ts.

### T092. Показывать фактическое покрытие источников

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T012, T076, T080.

**Результаты/файлы:** `backend/app/coverage.py`; `frontend/src/components/CoverageSummary.tsx`.

**Шаги:**

1. Отдельно считать каталог, аттестованные источники и опубликованные группы.
2. Не подменять ошибку нулём или количеством вузов в каталоге.

**Критерии закрытия:**

- Начальные 2 manual вуза не считаются автоинтеграциями.
- Нет выдуманного национального процента и stale/fresh смешения.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S046 / B03 10/10: Coverage API/UI separates catalog size from attested enabled automatic sources with group rules and complete published versions. National denominator is unknown/null, archive is never fresh, request failure is not zero. Backend coverage subset 2 passed; final full pytest: 188 passed / 1 real PostgreSQL skipped; frontend: 62 passed and build exit 0; full Chromium E2E: 24 passed on explicitly restarted current API, final import/coverage subset: 4 passed. Maximum pretty export 20x500 with full IDs/numbers exceeded 6 MiB, so UI limit corrected to 8 MiB with a regression test; HTTP normalized body remains bounded to 8 MiB. Final CSS heading/font tokens corrected after visual review. Desktop/mobile screenshots refreshed, synthetic import preview not submitted, demo session deleted (204). SQLite CLI backup/verify/restore smoke passed on isolated batch03.db, schema 0004/rawCount0, no working DB switch; retention dry-run 0 deletions. B03 10/10; 40/92 done, approximately 40 percent automated MVP, D1/30. T006/T013 now explicitly blocked on GitHub access/remote run and original source captures; real adapters/PG/production gates remain open. Preview 5183/API8003, API session 38488/PID18244, frontend session24508; all commits local, push unconfirmed.

### T093. Убрать категоричные обещания из ручного пользовательского пути

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T020.

**Результаты/файлы:** `frontend/src/pages/LandingPage.tsx`.

**Шаги:**

1. Ограничить объяснения ручной моделью.
2. Исправить определение согласия и состояния готовности features.

**Критерии закрытия:**

- Нет обещания официального места или универсального правила согласий.
- Формула и интервью не переписываются как подтверждённый прогноз.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S048 / B04 1/10: Removed universal actual-place/consent assertions from landing, diagram, metadata and tracker captions; manual assumptions and no double subtraction explicit, feature availability separated. Interview remains an attributed story, formula unchanged. Build exit 0; 4 landing Chromium checks passed at 320/390/768/1440 in both themes, including copy boundaries and overflow. Visual font/design acceptance remains open.

### T096. Привязать ошибки ручной формы к полям и фокусу

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T072, T018.

**Результаты/файлы:** `frontend/src/pages/TrackerPage.tsx`; `frontend/src/components/UniversityPicker.tsx`.

**Шаги:**

1. Проверить названия/URL/числа до HTTP.
2. Показать aria-invalid/описание и сфокусировать первое ошибочное поле.

**Критерии закрытия:**

- Неверный URL/credentials не отправляется.
- Ошибка суммы групп указывает соответствующие поля.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S051 / B04 4/10: Client validates trimmed names, URL scheme/credentials/canonical length and numeric groups before HTTP, links errors to fields with aria-invalid/describedby and focuses first invalid input. Native validation no longer swallows custom errors. npm test: 67 passed; build exit 0; 6 form/keyboard Chromium tests passed, including zero writes for credential URL, first-error focus, group error association and existing keyboard save flow.

### T097. Защитить несохранённую форму от случайного переключения

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T072.

**Результаты/файлы:** `frontend/src/pages/TrackerPage.tsx`.

**Шаги:**

1. Отслеживать отличие от исходных значений.
2. Подтверждать только реальное удаление черновика при cancel/switch.

**Критерии закрытия:**

- Отказ от переключения сохраняет ввод.
- Чистая и успешно сохранённая форма не требуют подтверждения.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S052 / B04 5/10: Unsaved form signature guards cancel, different-form switch and ordinary link navigation; dismiss keeps draft, successful save bypasses confirmation, clean form is unchanged. Browser beforeunload added without automatic draft persistence. Build exit0; 5 draft/keyboard Chromium tests passed, including accepted switch, dismissed cancel/link and save without prompt. SPA back/forward/crash recovery not claimed; broader browser/navigation gates remain open.

### T104. Search, filter and sort saved directions

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T018.

**Результаты/файлы:** `frontend/src/lib/watch-list.ts`; `frontend/src/pages/TrackerPage.tsx`; `frontend/tests/watch-list.test.ts`; `frontend/tests/e2e/tracker-tools.spec.ts`.

**Шаги:**

1. Search, filter and sort saved directions.
2. Verify success, boundary and relevant failure behavior.

**Критерии закрытия:**

- Text/status filters, exact date/university sorting, reset and no-results preserve the full list..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S061: Search across university/title, manual-scenario filter, reset/no-results and exact-microsecond date/name sorting without mutating stored data. npm test68/build passed; one Chromium filter/sort check passed on5184. Initial Cyrillic script substitution corrected before verification.

### T105. Compare any two loaded manual snapshots

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T070, T074.

**Результаты/файлы:** `frontend/src/components/HistoryComparison.tsx`; `frontend/tests/e2e/tracker-tools.spec.ts`.

**Шаги:**

1. Compare any two loaded manual snapshots.
2. Verify success, boundary and relevant failure behavior.

**Критерии закрытия:**

- Two distinct loaded snapshots can be selected; deleted/stale selection falls back safely..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S062: Distinct chronological snapshot selectors compare any loaded pair, with safe fallback when selection disappears; default remains latest pair. Build and2 Chromium tools tests passed.

### T107. Show all saved inputs and exact timestamps in history

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T074.

**Результаты/файлы:** `frontend/src/pages/TrackerPage.tsx`; `frontend/tests/e2e/tracker-tools.spec.ts`.

**Шаги:**

1. Show all saved inputs and exact timestamps in history.
2. Verify success, boundary and relevant failure behavior.

**Критерии закрытия:**

- History includes both disjoint groups, worst scenario, model and exact timestamp..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S064: History now displays all four saved inputs, both scenario places, model version and full ISO timestamp alongside readable seconds. Chromium history check passed with8columns and original timestamp/model. Formula unchanged.

### T108. Print a readable manual directions report

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T075.

**Результаты/файлы:** `frontend/src/components/ManualReport.tsx`; `frontend/src/tracker.css`; `frontend/tests/e2e/tracker-tools.spec.ts`.

**Шаги:**

1. Print a readable manual directions report.
2. Verify success, boundary and relevant failure behavior.

**Критерии закрытия:**

- Print layout shows saved manual values, source/time and limitations without action controls..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S065: Printable filtered manual report includes saved inputs, both places, original source/time, model and limitations. Print CSS hides controls and supports dark theme. Build and Chromium print-media check passed; no PDF/physical-printer acceptance claimed.

### T109. Guard deletion of the direction being edited

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T097.

**Результаты/файлы:** `frontend/src/pages/TrackerPage.tsx`; `frontend/tests/e2e/tracker-tools.spec.ts`.

**Шаги:**

1. Guard deletion of the direction being edited.
2. Verify success, boundary and relevant failure behavior.

**Критерии закрытия:**

- Cancelling draft discard preserves form; deleting its watch closes the stale form after success..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S066: Deleting an edited direction requires draft discard confirmation before HTTP. Decline retains values and sends no delete; success closes stale form, failure keeps it. Build and Chromium cancel/confirm test passed.

### T110. Manage focus and Escape for delete confirmations

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T072.

**Результаты/файлы:** `frontend/src/components/DeleteConfirmation.tsx`; `frontend/tests/e2e/tracker-tools.spec.ts`.

**Шаги:**

1. Manage focus and Escape for delete confirmations.
2. Verify success, boundary and relevant failure behavior.

**Критерии закрытия:**

- Confirmation receives focus, Escape cancels, successful removal leaves a useful focused control..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S067: Inline confirmations focus the safe Cancel action, Escape cancels and restores trigger focus; delete controls disabled during writes, removal returns focus to Add. Build and2 Chromium deletion checks passed.

### T111. Retain saved cards after background read failure

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T098.

**Результаты/файлы:** `frontend/src/pages/TrackerPage.tsx`; `frontend/tests/e2e/tracker-tools.spec.ts`.

**Шаги:**

1. Retain saved cards after background read failure.
2. Verify success, boundary and relevant failure behavior.

**Критерии закрытия:**

- Cached data remains visible with an error/retry; initial error and 401 remain separate..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S068: Cached cards and dirty form survive a background read error with original dates and explicit retry; initial failure and401 remain separate. Watches refetch on return to tab. Initial test revealed global focus refetch was disabled; enabled only watches. Chromium error/retry check passed.

### T112. Display the exact guest access deadline

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T016.

**Результаты/файлы:** `frontend/src/pages/TrackerPage.tsx`; `frontend/tests/e2e/tracker-tools.spec.ts`.

**Шаги:**

1. Display the exact guest access deadline.
2. Verify success, boundary and relevant failure behavior.

**Критерии закрытия:**

- Server expiry is shown without extending session; failure is not a fabricated date..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S069: Displays server-provided absolute guest expiry and original ISO value without sliding extension. Reset replaces cached deadline with new session info. Build and Chromium reload test passed; no fabricated date on error.

### T114. Add skip navigation and focus route headings

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T072.

**Результаты/файлы:** `frontend/src/main.tsx`; `frontend/src/styles.css`; `frontend/tests/e2e/tracker-tools.spec.ts`.

**Шаги:**

1. Add skip navigation and focus route headings.
2. Verify success, boundary and relevant failure behavior.

**Критерии закрытия:**

- Skip link reaches main; client navigation and missing routes focus the correct heading..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S071: Skip navigation focuses main; route/hash changes focus destination including lazy headings, and404 has a correct title. Build and Chromium route/skip keyboard check passed; no full screen-reader/browser matrix claimed.

### T115. Make history overflow usable from the keyboard

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T074.

**Результаты/файлы:** `frontend/src/pages/TrackerPage.tsx`; `frontend/src/tracker.css`; `frontend/tests/e2e/tracker-tools.spec.ts`.

**Шаги:**

1. Make history overflow usable from the keyboard.
2. Verify success, boundary and relevant failure behavior.

**Критерии закрытия:**

- Named focusable region, column headers and narrow-screen keyboard scroll work..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S072: Named focusable history region and scoped column headers support keyboard horizontal scrolling. Mobile test first exposed intrinsic grid expansion; constrained tracks/card minimum widths. Final390px Chromium scroll/no-page-overflow check passed.

### T116. Refresh saved directions without losing a form draft

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T097.

**Результаты/файлы:** `frontend/src/pages/TrackerPage.tsx`; `frontend/tests/e2e/tracker-tools.spec.ts`.

**Шаги:**

1. Refresh saved directions without losing a form draft.
2. Verify success, boundary and relevant failure behavior.

**Критерии закрытия:**

- Explicit readonly refresh retrieves updates, keeps draft, disables duplicate reads and reports failure..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S073: Explicit readonly refresh updates saved cards while preserving unsaved form values, disables duplicate reads and makes no new session POST. Chromium server-change/draft check passed; refresh is not a university fetch.

### T117. Preview direction names before confirming file import

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T091.

**Результаты/файлы:** `frontend/src/components/ImportData.tsx`; `frontend/tests/e2e/tracker-tools.spec.ts`.

**Шаги:**

1. Preview direction names before confirming file import.
2. Verify success, boundary and relevant failure behavior.

**Критерии закрытия:**

- Preview lists all names/counts, uses safe text and cancellation performs no import..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S074: Import preview lists every bounded direction name, original timestamp, history count and source as safe text before POST. Chromium malicious-markup-as-text and cancel-with-zero-imports check passed.

### T127. Align import preview date rules with server validation

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T091.

**Результаты/файлы:** `frontend/src/lib/import.ts`; `frontend/tests/import.test.ts`.

**Шаги:**

1. Align import preview date rules with server validation.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Files too old or beyond server future tolerance rejected before POST; boundary is deterministic in tests..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S085: Import preview enforces the server UTC year2000 floor and inclusive5minute future tolerance before POST. Boundary tested to1microsecond. Frontend70/build passed, maximum20x500 export still accepted.

### T138. Recover from lazy page loading failures

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T018.

**Результаты/файлы:** `frontend/src/components/PageErrorBoundary.tsx`; `frontend/src/main.tsx`; `frontend/tests/e2e/tracker-tools.spec.ts`; `docs/evidence/error-recovery-mobile.png`.

**Шаги:**

1. Recover from lazy page loading failures.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Friendly fallback and explicit reload replace blank screen; no automatic retry/session creation..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S096: Page boundary provides focused recovery UI with explicit reload and no hidden retry/bootstrap. New failure/recovery E2E passed. Final backend269 passed/7 PG skipped, frontend77/build passed,46 Chromium passed on current API8005. First browser run45/46 had a transient Vite module-load failure; unchanged cookie-loss case passed3 repeats and full rerun. Final JSON-media-type bypass and huge-timeout edge corrected before full verification. B06 complete20/20; real data/PG/CI gates unchanged.

### T139. Reject ambiguous JSON import files

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T091.

**Результаты/файлы:** `frontend/src/lib/import.ts`; `frontend/src/lib/json.ts`; `frontend/tests/json.test.ts`.

**Шаги:**

1. Reject ambiguous JSON import files.
2. Run meaningful success and refusal regressions.

**Критерии закрытия:**

- Duplicate decoded keys, nonfinite numbers and excessive nesting fail before preview or POST..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S098: npm test -- tests/json.test.ts tests/import.test.ts:7 passed. Strict structural parser rejects decoded duplicate keys, depth65, nonfinite and malformed tokens; valid escaped strings and maximum-count exports preserved. Files frontend/src/lib/json.ts, import.ts and tests/json.test.ts.

### T140. Reject invalid UTF-8 import files

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T091.

**Результаты/файлы:** `frontend/src/components/ImportData.tsx`; `frontend/src/lib/import.ts`; `frontend/tests/import.test.ts`.

**Шаги:**

1. Reject invalid UTF-8 import files.
2. Run meaningful success and refusal regressions.

**Критерии закрытия:**

- Invalid bytes cannot silently replace names; BOM and valid Unicode exports remain readable..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S099: npm test -- tests/import.test.ts:5 passed. Fatal UTF-8 byte decoding rejects malformed, truncated and surrogate encodings; valid Cyrillic and BOM roundtrip. ImportData uses arrayBuffer rather than lossy File.text.

### T141. Cancel import preparation safely

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T091.

**Результаты/файлы:** `frontend/src/components/ImportData.tsx`; `frontend/tests/e2e/import-cancel.spec.ts`.

**Шаги:**

1. Cancel import preparation safely.
2. Run meaningful success and refusal regressions.

**Критерии закрытия:**

- Cancel during reading permits a new selection; late results cannot replace the new preview..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S100: E2E_API=1 E2E_BASE_URL=5186 Playwright import-cancel.spec.ts:1 passed on isolated API8006. Delayed old File.arrayBuffer explicitly released and two render frames observed after cancellation/new preview; no import POST or data writes. Cancel clears reading and stale selection skips parsing.

### T142. Align form Unicode length limits with the API

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T018.

**Результаты/файлы:** `frontend/src/lib/direction.ts`; `frontend/src/components/UniversityPicker.tsx`; `frontend/src/pages/TrackerPage.tsx`; `frontend/tests/direction.test.ts`.

**Шаги:**

1. Align form Unicode length limits with the API.
2. Run meaningful success and refusal regressions.

**Критерии закрытия:**

- Supplementary Unicode counts as one character in names and catalog queries; excess is still rejected..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S101: npm test -- tests/direction.test.ts:4 passed; npm run build exit0. Form counts160/200 Unicode code points and rejects excess; removed conflicting UTF16 HTML maxlength for names. Catalog query truncation preserves complete supplementary characters.

### T143. Cancel abandoned catalog searches

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T018.

**Результаты/файлы:** `frontend/src/components/UniversityPicker.tsx`; `frontend/src/lib/api.ts`; `frontend/tests/catalog-cancel.test.ts`.

**Шаги:**

1. Cancel abandoned catalog searches.
2. Run meaningful success and refusal regressions.

**Критерии закрытия:**

- Superseded or unmounted catalog requests receive cancellation without an error replacing the current search..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S102: npm test -- tests/catalog-cancel.test.ts:1 passed. Real QueryObserver unsubscribe aborts transport fetch, next catalog query succeeds. api.universities consumes the query signal; pending old searches do not keep reading after key change/unmount.

### T144. Navigate university choices with the keyboard

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T018.

**Результаты/файлы:** `frontend/src/components/UniversityPicker.tsx`; `frontend/tests/e2e/catalog.spec.ts`.

**Шаги:**

1. Navigate university choices with the keyboard.
2. Run meaningful success and refusal regressions.

**Критерии закрытия:**

- Arrow keys enter and navigate choices; Escape returns focus without closing the direction form..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S103: Playwright catalog.spec.ts:3 passed on5186/API8006. ArrowDown/Up navigate two actual catalog choices, Escape restores input without closing form, Enter selects name and official source. Existing manual fallback and API failure cases also pass.

### T145. Stop canceled private reads after session bootstrap

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T098.

**Результаты/файлы:** `frontend/src/lib/api.ts`; `frontend/tests/session-state.test.ts`.

**Шаги:**

1. Stop canceled private reads after session bootstrap.
2. Run meaningful success and refusal regressions.

**Критерии закрытия:**

- Canceled consumers never dispatch a private read after shared bootstrap finishes; other consumers remain functional..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S104: npm test -- tests/session-state.test.ts:3 passed. Cancel settles before a gated shared bootstrap response; another consumer completes using the same session and only one private fetch. Read epoch checked across bootstrap; abort listeners removed, shared bootstrap not canceled.

### T146. Release response bodies discarded by session fencing

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T136.

**Результаты/файлы:** `frontend/src/lib/api.ts`; `frontend/tests/session-state.test.ts`.

**Шаги:**

1. Release response bodies discarded by session fencing.
2. Run meaningful success and refusal regressions.

**Критерии закрытия:**

- Unauthorized and stale-header responses cancel their unread body without exposing its contents..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S105: npm test -- tests/session-state.test.ts:5 passed. ReadableStream cancel spies prove401 and stale-header bodies are canceled exactly once; body results still fenced after access change. No response content exposed.

### T147. Guard navigation while a save is pending

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T018.

**Результаты/файлы:** `frontend/src/pages/TrackerPage.tsx`; `frontend/tests/e2e/pending-form.spec.ts`.

**Шаги:**

1. Guard navigation while a save is pending.
2. Run meaningful success and refusal regressions.

**Критерии закрытия:**

- Current-tab links cannot discard the pending operation; unload is guarded even for an unchanged edit..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S106: Playwright pending-form.spec.ts and draft.spec.ts:3 passed. A gated unchanged edit blocks current-tab navigation and beforeunload; after response the form closes and link works. Dirty-draft confirmation regressions preserved. SPA back/forward still not claimed.

### T148. Prevent form submission during another mutation

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T018.

**Результаты/файлы:** `frontend/src/pages/TrackerPage.tsx`; `frontend/tests/e2e/pending-form.spec.ts`.

**Шаги:**

1. Prevent form submission during another mutation.
2. Run meaningful success and refusal regressions.

**Критерии закрытия:**

- Import and save cannot overlap through an already open form; values survive the pending interval..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S107: Playwright pending-form.spec.ts:2 passed in final sequential run. During gated actual import, fields/save disabled and synthetic submit dispatch produces0 creates; after import original draft saves once,2 cards total. Initial test had incorrect field label; overlapping rerun collided with Playwright artifacts. Corrected label and waited for all runners before final2/2; application expectations unchanged.

### T151. Verify long manual cards at320px in both themes

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T018.

**Результаты/файлы:** `frontend/tests/e2e/manual-quality.spec.ts`; `frontend/src/tracker.css`.

**Шаги:**

1. Verify long manual cards at320px in both themes.
2. Run meaningful success and refusal regressions.

**Критерии закрытия:**

- Long labels and maximum numeric values stay usable with no page overflow in light and dark modes..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S110: Playwright manual-quality.spec.ts:2 passed after real overflow fix. Both themes at320px with160/200 unbroken Cyrillic names,1000000 values, expanded history and open edit. Initial test reproduced1919px grid expansion; minmax(0,1fr), bounded sidebar/form and wrapping preview fix it without clipping content.

### T152. Verify filtered manual report printing

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T108.

**Результаты/файлы:** `frontend/tests/e2e/manual-quality.spec.ts`; `docs/evidence/manual-report.png`.

**Шаги:**

1. Verify filtered manual report printing.
2. Run meaningful success and refusal regressions.

**Критерии закрытия:**

- Print media contains only selected manual records, sources and limitations; interactive controls are hidden..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S111: Playwright manual-quality filtered-print case:1 passed. Two real API records, active filter selects only one; print media excludes second record and controls, includes source/model/limitations. Actual Chromium A4 PDF generated in ignored test-results; docs/evidence/manual-report.png visually inspected, clear labels/values. Existing mock-only print regression is preserved.

### T154. Enable data-router navigation blocking

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T138.

**Результаты/файлы:** `frontend/src/main.tsx`; `docs/DECISIONS.md`.

**Шаги:**

1. Enable data-router navigation blocking.
2. Verify success and meaningful refusal cases.

**Критерии закрытия:**

- Routes, lazy failure recovery, titles and hash navigation remain functional with the installed router..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S114: npm run build exit0; Playwright landing.spec.ts/tracker-tools.spec.ts16 passed on5187/API8007. Data router preserves routes, lazy failure recovery, hashes,404/title/focus and existing manual tools. Installed React Router7.18.4 exports verified; ADR022 records bounded draft/navigation choice.

### T155. Protect unsaved forms on browser back and forward

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T154, T147.

**Результаты/файлы:** `frontend/src/pages/TrackerPage.tsx`; `frontend/src/components/DirectionForm.tsx`; `frontend/src/components/Layout.tsx`; `frontend/tests/e2e/draft-navigation.spec.ts`; `frontend/tests/e2e/draft.spec.ts`; `frontend/tests/e2e/pending-form.spec.ts`.

**Шаги:**

1. Protect unsaved forms on browser back and forward.
2. Verify success and meaningful refusal cases.

**Критерии закрытия:**

- Rejecting back/forward preserves the form; accepting leaves once; pending saves cannot be discarded by SPA navigation..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S115: Playwright draft-navigation/draft/pending-form:5 passed. Native browser back/forward rejects without losing fields, accepts departure once, pending unchanged edit remains protected. Router links skip document guard to avoid double confirmation. Old link test now explicitly waits for async dialog event; initial timing failure documented, refusal assertions retained.

### T156. Expose an isolated guest draft namespace

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T016.

**Результаты/файлы:** `backend/app/schemas.py`; `backend/app/main.py`; `backend/tests/test_draft_scope.py`; `frontend/src/lib/contracts.ts`; `frontend/tests/draft-scope.test.ts`.

**Шаги:**

1. Expose an isolated guest draft namespace.
2. Verify success and meaningful refusal cases.

**Критерии закрытия:**

- Session returns a stable one-way local draft scope, different between owners/reset; no token or owner hash exposed..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S116: Backend draft_scope/timestamp_bounds/sessions10 passed; frontend draft-scope/session-state6 passed. Namespace stable per owner, changes after new session/reset, contains neither cookie nor stored owner hash and cannot authenticate as cookie. Frontend older-API contract remains usable with recovery disabled.

### T157. Validate bounded session-local draft storage

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T156.

**Результаты/файлы:** `frontend/src/lib/draft.ts`; `frontend/tests/draft-store.test.ts`.

**Шаги:**

1. Validate bounded session-local draft storage.
2. Verify success and meaningful refusal cases.

**Критерии закрытия:**

- One versioned draft per tab is bounded, scope/expiry checked, malformed data discarded and storage failure reported honestly..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S117: npm test -- tests/draft-store.test.ts4 passed; production build exit0. One versioned16KiB sessionStorage record validates Unicode lengths, incomplete values, retry UUID/fingerprint, owner scope,30-minute TTL/session deadline; corrupt/foreign/expired records removed. Quota/access failures return unavailable without throwing.

### T158. Save form drafts and retry keys locally

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T157.

**Результаты/файлы:** `frontend/src/pages/TrackerPage.tsx`; `frontend/src/components/DirectionForm.tsx`; `frontend/tests/e2e/draft-recovery.spec.ts`.

**Шаги:**

1. Save form drafts and retry keys locally.
2. Verify success and meaningful refusal cases.

**Критерии закрытия:**

- Changed fields persist locally without POST; operation key is stored before sending; storage failure leaves form functional..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S118: Playwright draft-recovery/draft3 passed and production build exit0. Changed fields persist locally without server writes; route interceptor proves retry key exists in storage before POST dispatch. Failed request retains form and key. Extracted DirectionForm component to keep tracker readable; no autosave POST or false server-success message.

### T159. Offer explicit draft restore and discard

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T158.

**Результаты/файлы:** `frontend/src/components/DraftRecovery.tsx`; `frontend/src/pages/TrackerPage.tsx`; `frontend/src/components/DirectionForm.tsx`; `frontend/src/tracker.css`; `frontend/tests/e2e/draft-recovery.spec.ts`.

**Шаги:**

1. Offer explicit draft restore and discard.
2. Verify success and meaningful refusal cases.

**Критерии закрытия:**

- Reload offers an accessible preview; restore fills fields without posting, discard removes only the draft..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S119: Production build exit0; Playwright draft-recovery/navigation3 passed. Reload shows a bounded plaintext preview, restore fills incomplete fields without POST, discard removes only local state and returns focus. Existing draft replacement requires explicit confirmation; restored retry intent preserved. No automatic restore or source fetch.

### T160. Refuse stale draft updates without losing retry safety

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T159.

**Результаты/файлы:** `backend/app/main.py`; `backend/tests/test_expected_snapshot.py`; `frontend/src/lib/api.ts`; `frontend/src/components/DirectionForm.tsx`; `frontend/src/components/DraftRecovery.tsx`; `frontend/src/pages/TrackerPage.tsx`; `docs/DATA_RULES.md`.

**Шаги:**

1. Refuse stale draft updates without losing retry safety.
2. Verify success and meaningful refusal cases.

**Критерии закрытия:**

- Expected latest snapshot fences fresh writes; cached retry still replays; stale/missing restored edits cannot silently overwrite newer data..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S120: Backend expected_snapshot/writes10 passed; Playwright draft-recovery4 passed on restarted API8007/session62597/PID13052. Stale/missing draft remains plaintext-readable without restore; already open stale edit refuses409 and preserves fields/history. Expected snapshot checked under owner lock after cached replay; malformed header400. DATA_RULES updated; PG concurrency not claimed.

### T161. Clear local drafts when access or saved data changes

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T159.

**Результаты/файлы:** `frontend/src/pages/TrackerPage.tsx`; `frontend/src/main.tsx`; `frontend/src/lib/query-client.ts`; `frontend/src/components/DirectionForm.tsx`; `frontend/tests/e2e/draft-recovery.spec.ts`; `frontend/tests/e2e/session-tabs.spec.ts`; `docs/data-policy.md`.

**Шаги:**

1. Clear local drafts when access or saved data changes.
2. Verify success and meaningful refusal cases.

**Критерии закрытия:**

- Success, explicit discard/reset, expiry and cross-tab access change remove local recovery state and do not resurrect it..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S121: Playwright recovery/session-tabs8 passed plus expanded successful-save/cancel case1 passed. TTL expiry removes record without reading renewal;401 and cross-tab reset clear local state before explicit resync; success/cancel leave no record. Form and recovery timers bounded by original expiry; session-info cancellation added to reset. Data policy documents plaintext tab-local limits and suspended-timer caveat.

### T162. Verify draft recovery across real browser reloads

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T160, T161.

**Результаты/файлы:** `frontend/tests/e2e/draft-recovery.spec.ts`.

**Шаги:**

1. Verify draft recovery across real browser reloads.
2. Verify success and meaningful refusal cases.

**Критерии закрытия:**

- Real API reload recovery and lost-response retry create no duplicates and preserve original owner boundaries..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S122: Three real-API Chromium cases passed: lost create and update responses are committed, browser reloaded, explicit restore retries exactly the stored key without extra watch/snapshot; update replay preserves an intervening newer snapshot. Cookie owner replaced without storage event yields no old preview or stored record. No mocked success or inferred owner isolation.

### T163. Verify keyboard and narrow-screen draft recovery

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T162.

**Результаты/файлы:** `frontend/tests/e2e/draft-recovery.spec.ts`; `frontend/src/pages/TrackerPage.tsx`; `frontend/src/components/DirectionForm.tsx`; `frontend/tests/e2e/session-tabs.spec.ts`; `docs/evidence/draft-recovery-mobile.png`.

**Шаги:**

1. Verify keyboard and narrow-screen draft recovery.
2. Verify success and meaningful refusal cases.

**Критерии закрытия:**

- Recovery and failure states remain usable at320px in both themes, by keyboard and with unavailable storage; current evidence captured..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S123: Final backend279 passed/7 actual PostgreSQL skipped, frontend92 passed/build exit0, full69 Chromium passed on API8007/session62597/PID13052. Before final expiry fix full68 passed; added wall-clock-only expiry-during-read test and repeated full69 without weakening expectations. Keyboard/320px light-dark and denied/quota storage cases pass. Restore now readonly-revalidates cookie scope and latest records; expiry checked after network wait, restored unchanged drafts retain expiry timer. Mobile evidence visually inspected; example guest/storage cleared.

### T176. Find a candidate by scoped public code and issue owner-bound confirmation

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T022, T029.

**Результаты/файлы:** `backend/app/source_api.py`.

**Шаги:**

1. Find a candidate by scoped public code and issue owner-bound confirmation.
2. Verify meaningful success,boundary,refusal and actual PostgreSQL cases.

**Критерии закрытия:**

- Authenticated lookup uses source/group/year HMAC,never logs/persists public code;short-lived signed confirmation is bound to owner/source/snapshot and refuses stale or unsupported source..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 13/30:scoped authenticated lookup and owner/snapshot-bound300s confirmation implemented;12local+9nativePG cases passed,no public-code persistence/automatic subscription.

### T177. Save owner-isolated source subscriptions within combined direction limits

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T176, T017.

**Результаты/файлы:** `backend/app/source_api.py`; `backend/tests/test_subscriptions.py`.

**Шаги:**

1. Save owner-isolated source subscriptions within combined direction limits.
2. Verify meaningful success,boundary,refusal and actual PostgreSQL cases.

**Критерии закрытия:**

- Confirmation creates one subscription idempotently under owner lock;foreign/tampered/expired tickets fail,manual+archive directions share20-limit,guest reset/expiry removes subscriptions..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 14/30:owner-isolated idempotent subscriptions and combined20-limit done;native37cases passed,including data-preserving0005cascade fix,guest reset/expiry and cache replay safety.

### T178. Удалять отдельную архивную запись без её восстановления повтором

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T177, T021.

**Результаты/файлы:** `backend/app/source_api.py`; `frontend/src/components/ArchiveDirections.tsx`.

**Шаги:**

1. Проверить ownership и каскад истории.
2. Обезвредить повторы старых подтверждений и вернуть общий лимит.

**Критерии закрытия:**

- Чужое удаление возвращает404.
- Удалённая запись не воскресает при replay подтверждения.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 16/30:individual archive deletion,owner isolation,cascading personal history and410replay tombstones verified;2nativePG+1newChromium passed,currentbuild.

### T179. Сохранять и читать неизменяемую историю фактов одного архивного источника

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T177, T033.

**Результаты/файлы:** `backend/app/source_history.py`; `backend/tests/test_source_history.py`.

**Шаги:**

1. Добавить фактические версии без числового прогноза.
2. Стабильная пагинация и изоляция владельца.

**Критерии закрытия:**

- Повтор не создаёт дубли и не меняет прежние факты.
- Cursor не теряет записи при одинаковом времени.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 17/30:immutable atomic source-facts history with keyset/owner/version provenance;3nativePG cases passed,including synthetic consent change and rollback.

### T180. Показывать историю и сравнение подтверждённых архивных фактов

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T179, T021.

**Результаты/файлы:** `frontend/src/components/ArchiveHistory.tsx`; `frontend/tests/e2e/source-history.spec.ts`.

**Шаги:**

1. Вывести датированные факты и сравнение полей.
2. Отделить неизвестное от отсутствия записи и отзыва.

**Критерии закрытия:**

- Виден источник и снимок каждой версии.
- Сравнение не выдаёт изменение строки за прогноз зачисления.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 18/30:archive history and factual comparison UI verified;2Chromium+10contract checks/currentbuild passed,source/season/cursor validation and session cleanup.

### T215. Закрепить читаемый стиль frontend и команды форматирования

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T214.

**Результаты/файлы:** `frontend/`; `docs/evidence/`.

**Шаги:**

1. Версия formatter закреплена, настройки/команды проверены, базовая сборка зафиксирована.

**Критерии закрытия:**

- Версия formatter закреплена, настройки/команды проверены, базовая сборка зафиксирована.
- Общая Definition of Done выполнена; только форматирование, поиск и документация дефектов..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b19-format-tools.md](../docs/evidence/b19-format-tools.md) — Prettier3.9.10 pinned with LF/100columns/JSX attributes per line; npm format/check commands configured and tooling files formatted. npm install/version/config checks passed; runtime dependencies unchanged.

### T216. Развернуть библиотечный TypeScript в многострочный код

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T215.

**Результаты/файлы:** `frontend/`; `docs/evidence/`.

**Шаги:**

1. Все frontend/src/lib файлы отформатированы без изменений логики.

**Критерии закрытия:**

- Все frontend/src/lib файлы отформатированы без изменений логики.
- Общая Definition of Done выполнена; только форматирование, поиск и документация дефектов..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b19-library-format.md](../docs/evidence/b19-library-format.md) — All17library TypeScript files expanded into readable blocks; targeted Prettier check passed. Frontend LF attributes keep formatting stable on Windows. No intentional behavior changes; complete unit/build/equivalence verification T218.

### T217. Сделать JSX компонентов, страниц и стили читаемыми

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T216.

**Результаты/файлы:** `frontend/`; `docs/evidence/`.

**Шаги:**

1. Компоненты/страницы/entrypoint/CSS многострочные, функциональные изменения не внесены.

**Критерии закрытия:**

- Компоненты/страницы/entrypoint/CSS многострочные, функциональные изменения не внесены.
- Общая Definition of Done выполнена; только форматирование, поиск и документация дефектов..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b19-jsx-format.md](../docs/evidence/b19-jsx-format.md) — 23components/3pages/main and2CSS files expanded. Targeted formatter check/build passed. Normalized semantic AST of44TS/TSX source files matches5440410; no logic fixes. CSS asset remains identical; JSX layout changes bundle representation.

### T218. Привести тесты к тому же стилю и проверить поведение

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T217.

**Результаты/файлы:** `frontend/`; `docs/evidence/`.

**Шаги:**

1. Тесты/конфиги читаемы, format check/unit/build и проверка семантики пройдены.

**Критерии закрытия:**

- Тесты/конфиги читаемы, format check/unit/build и проверка семантики пройдены.
- Общая Definition of Done выполнена; только форматирование, поиск и документация дефектов..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b19-tests-format.md](../docs/evidence/b19-tests-format.md) — All56TypeScript test files formatted; format check/116Vitest/build passed.79compiledChromium passed/36scopedskips/0fail.100source+test normalized semantic ASTs match5440410; assertions unchanged, CSS identical. CI checks format after npmci.

### T219. Подтвердить и описать найденные ошибки frontend

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T218.

**Результаты/файлы:** `frontend/`; `docs/evidence/`.

**Шаги:**

1. Отчёт содержит воспроизведение, влияние и точные места; функциональные ошибки не исправлены без запроса.

**Критерии закрытия:**

- Отчёт содержит воспроизведение, влияние и точные места; функциональные ошибки не исправлены без запроса.
- Общая Definition of Done выполнена; только форматирование, поиск и документация дефектов..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b19-frontend-audit.md](../docs/evidence/b19-frontend-audit.md) — 10 frontend defects confirmed, including destructive cross-tab recovery and old-owner cache after reset. Only formatting implemented:100TS/TSX semantic ASTs match baseline,116Vitest/build,79Chromium/36scopedskips passed. Long lines>200 reduced218→2(text literals). Ten fixes T220–T229 remain todo; no functional fixes/push.

### T220. Не терять новую сессию при синхронизации вкладок

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T219.

**Результаты/файлы:** `frontend/`; `docs/evidence/`.

**Шаги:**

1. После указания исправлять воспроизвести F01, внести минимальное исправление и проверить существенную границу..

**Критерии закрытия:**

- Сценарий F01 из docs/evidence/b19-frontend-audit.md проходит без прежней ошибки..
- Проверены соседний успешный/error сценарий и отсутствие регрессии; Definition of Done выполнена..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b20-session-synchronization.md](../docs/evidence/b20-session-synchronization.md) — Native WebLocks and fallback recovery preserve the new guest;126Vitest/build,8Chromium/Firefox cases passed. Queued reset intents and stale responses guarded; no destructive retry after transient401.

### T221. Очищать старые карточки после сброса гостевой сессии

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T219.

**Результаты/файлы:** `frontend/`; `docs/evidence/`.

**Шаги:**

1. После указания исправлять воспроизвести F02, внести минимальное исправление и проверить существенную границу..

**Критерии закрытия:**

- Сценарий F02 из docs/evidence/b19-frontend-audit.md проходит без прежней ошибки..
- Проверены соседний успешный/error сценарий и отсутствие регрессии; Definition of Done выполнена..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b20-session-cache.md](../docs/evidence/b20-session-cache.md) — F02 fixed: private UI/query gate while resetting; cancel/remove owner caches on success and failure.8Chromium/Firefox cache boundary tests passed; final 126Vitest/format/build,85compiledChromium/36scopedskips and12critical CI-mode/two-worker cases passed. Only F01/F02 fixed; other8 remain todo.
- [docs/evidence/b20-final-verification.json](../docs/evidence/b20-final-verification.json) — Observed red/green regression, epoch guards, cache ownership boundaries and actual final frontend checks; no new coverage or release claim.

### T222. Не восстанавливать отменённые значения черновика

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T219.

**Результаты/файлы:** `frontend/`; `docs/evidence/`.

**Шаги:**

1. После указания исправлять воспроизвести F03, внести минимальное исправление и проверить существенную границу..

**Критерии закрытия:**

- Сценарий F03 из docs/evidence/b19-frontend-audit.md проходит без прежней ошибки..
- Проверены соседний успешный/error сценарий и отсутствие регрессии; Definition of Done выполнена..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b21-draft-revert.md](../docs/evidence/b21-draft-revert.md) — Reverted drafts cleared; pending retry intent and unchanged recovery TTL preserved. 126Vitest/build/format;22Chromium and7Firefox passed.

### T223. Обновлять открытую историю вместе с архивной карточкой

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T219.

**Результаты/файлы:** `frontend/`; `docs/evidence/`.

**Шаги:**

1. После указания исправлять воспроизвести F04, внести минимальное исправление и проверить существенную границу..

**Критерии закрытия:**

- Сценарий F04 из docs/evidence/b19-frontend-audit.md проходит без прежней ошибки..
- Проверены соседний успешный/error сценарий и отсутствие регрессии; Definition of Done выполнена..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b21-archive-refresh.md](../docs/evidence/b21-archive-refresh.md) — Refresh updates mutable archive queries, closed histories and changes; waits for new snapshot reads and retains dated facts on failure. Build/format;8Chromium+Firefox passed.

### T224. Разделить ошибку каталога и подтверждённую пустоту

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T219.

**Результаты/файлы:** `frontend/`; `docs/evidence/`.

**Шаги:**

1. После указания исправлять воспроизвести F05, внести минимальное исправление и проверить существенную границу..

**Критерии закрытия:**

- Сценарий F05 из docs/evidence/b19-frontend-audit.md проходит без прежней ошибки..
- Проверены соседний успешный/error сценарий и отсутствие регрессии; Definition of Done выполнена..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b21-catalog-error.md](../docs/evidence/b21-catalog-error.md) — Catalog outages no longer imply empty coverage; failed append retains cards and retry works. Build/format;4Chromium+Firefox passed.

### T225. Согласовать branch facets frontend и backend выше100

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T219.

**Результаты/файлы:** `frontend/`; `docs/evidence/`.

**Шаги:**

1. После указания исправлять воспроизвести F06, внести минимальное исправление и проверить существенную границу..

**Критерии закрытия:**

- Сценарий F06 из docs/evidence/b19-frontend-audit.md проходит без прежней ошибки..
- Проверены соседний успешный/error сценарий и отсутствие регрессии; Definition of Done выполнена..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b21-catalog-scale.md](../docs/evidence/b21-catalog-scale.md) — Global branch facets accept101 through20000 while preserving validation/resource bounds.136Vitest/build/format;2Chromium+Firefox pagination/filter cases passed.

### T226. Показывать изменение мест при отсутствии записи

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T219.

**Результаты/файлы:** `frontend/`; `docs/evidence/`.

**Шаги:**

1. После указания исправлять воспроизвести F07, внести минимальное исправление и проверить существенную границу..

**Критерии закрытия:**

- Сценарий F07 из docs/evidence/b19-frontend-audit.md проходит без прежней ошибки..
- Проверены соседний успешный/error сценарий и отсутствие регрессии; Definition of Done выполнена..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b21-archive-capacity.md](../docs/evidence/b21-archive-capacity.md) — Capacity changes displayed independently of candidate presence; unknown values and absence warning preserved. Build/format;10Chromium+Firefox passed. First five complete.

### T227. Очищать сообщение ошибки при отмене импорта

**Статус:** `done` · **Приоритет:** P2 · **Размер:** S.

**Зависимости:** T219.

**Результаты/файлы:** `frontend/`; `docs/evidence/`.

**Шаги:**

1. После указания исправлять воспроизвести F08, внести минимальное исправление и проверить существенную границу..

**Критерии закрытия:**

- Сценарий F08 из docs/evidence/b19-frontend-audit.md проходит без прежней ошибки..
- Проверены соседний успешный/error сценарий и отсутствие регрессии; Definition of Done выполнена..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b21-import-cancel.md](../docs/evidence/b21-import-cancel.md) — Cancel resets failed import UI; retry key/body survive until explicit cancel, pending controls remain locked, success cleanup verified. Build/format;10Chromium+Firefox passed.

### T228. Обновлять время отчёта при штатной печати браузера

**Статус:** `done` · **Приоритет:** P2 · **Размер:** S.

**Зависимости:** T219.

**Результаты/файлы:** `frontend/`; `docs/evidence/`.

**Шаги:**

1. После указания исправлять воспроизвести F09, внести минимальное исправление и проверить существенную границу..

**Критерии закрытия:**

- Сценарий F09 из docs/evidence/b19-frontend-audit.md проходит без прежней ошибки..
- Проверены соседний успешный/error сценарий и отсутствие регрессии; Definition of Done выполнена..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b21-report-print-time.md](../docs/evidence/b21-report-print-time.md) — Browser beforeprint commits current report timestamp synchronously; repeated events, own button and filtered Chromium PDF checked. Build/format;7passed/1FirefoxPDFskip.

### T229. Восстановить границы секций поиска и сравнения

**Статус:** `done` · **Приоритет:** P2 · **Размер:** S.

**Зависимости:** T219.

**Результаты/файлы:** `frontend/`; `docs/evidence/`.

**Шаги:**

1. После указания исправлять воспроизвести F10, внести минимальное исправление и проверить существенную границу..

**Критерии закрытия:**

- Сценарий F10 из docs/evidence/b19-frontend-audit.md проходит без прежней ошибки..
- Проверены соседний успешный/error сценарий и отсутствие регрессии; Definition of Done выполнена..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b21-section-borders.md](../docs/evidence/b21-section-borders.md) — Both section borders use existing --line; actual computed1px solid and correct light/dark colors verified. Build/format/diff passed; all8 fixes complete, final integrated verification follows.

### T230. Полная миграция frontend AdmitFlow на Feature-Sliced Design

**Статус:** `done` · **Приоритет:** P1 · **Размер:** L.

**Зависимости:** T229.

**Результаты/файлы:** `frontend/src/`; `frontend/scripts/`; `docs/ARCHITECTURE.md`; `docs/evidence/fsd-migration.md`.

**Шаги:**

1. Аудит исходников, сценариев, зависимостей и официальных принципов FSD..
2. Фундамент app/shared, импорты и публичные API..
3. Бизнес-сущности, типы, формулы, контракты и предметные API..
4. Действия пользователя и модели форм, сессий, импорта, истории и сравнения..
5. Декомпозиция страниц и композиция без изменения DOM/дизайна..
6. Удаление старой параллельной структуры и лишних зависимостей..
7. Typecheck, ESLint, Prettier, build, unit/E2E, зависимости/циклы и итоговая статистика..

**Критерии закрытия:**

- Все исходные сценарии, бизнес-формулы, API-форматы и визуальный дизайн сохранены..
- Зависимости направлены вниз; sibling imports/deep imports/циклы отсутствуют..
- Нет src/lib/src/components или старых фасадов, дублирующих FSD..
- Крупные страницы/формы/API разделены по реальным обязанностям..
- Все фактически выполненные проверки и ограничения записаны в evidence..
- Никаких автоматических коммитов/push или изменений backend..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/fsd-migration.md](../docs/evidence/fsd-migration.md) — Full FSD migration;147unit, typecheck/lint/format/build,119modules/279dependencies/no cycles,12exact screenshots,105Chromium/104Firefox passed. Scoped skips documented. No commits/push.

### T231. Единая визуальная дизайн-система AdmitFlow

**Статус:** `done` · **Приоритет:** P1 · **Размер:** L.

**Зависимости:** T230.

**Результаты/файлы:** `frontend/src/shared/ui/`; `frontend/src/app/styles/`; `docs/DESIGN_SYSTEM.md`; `docs/evidence/design-system.md`.

**Шаги:**

1. Аудит существующих размеров, CSS, тем и неоформленных элементов..
2. Единые design tokens и типографика..
3. UI primitives Button/Input/Select/Card/Badge/Alert и подключение в текущие страницы..
4. Очистка конфликтующих стилей без изменений UX и бизнес-логики..
5. Typecheck/lint/format/build, короткая визуальная проверка обеих тем..

**Критерии закрытия:**

- Все страницы используют общую типографическую шкалу и состояния управления..
- Нет неоформленных кнопок, темы согласованы; интерфейс работает на320px..
- Сценарии, модели, API и архитектура не изменены..
- Фактические проверки и ограничения зафиксированы; нет commits/push..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/design-system.md](../docs/evidence/design-system.md) — Unified tokens/type scale/shared UI and both themes. typecheck/lint/build/format/architecture pass;147unit,12page and4editor/state checks. No long E2E/UX/API/model changes/commits/push.

### T232. Redesign tracker information architecture and direction cards

**Статус:** `done` · **Приоритет:** P1 · **Размер:** L.

**Зависимости:** T231.

**Результаты/файлы:** `frontend/src/pages/tracker/`; `docs/evidence/tracker-redesign.md`.

**Шаги:**

1. Audit existing capabilities.
2. Prioritize directions.
3. Unify cards.
4. Group history and tools.
5. Verify and document.

**Критерии закрытия:**

- Direction list and add action first; clear calculated place, seats, manual date and available position change.
- Preserve capabilities, API and calculations; technical tools disclosed below; critical warnings visible.
- Responsive keyboard accessible UI using existing design system; typecheck/lint/build verified; no commits.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/tracker-redesign.md](../docs/evidence/tracker-redesign.md) — Tracker IA/cards/tools redesigned. typecheck/lint/build/format/architecture pass;147unit,38 distinct compiled Chromium tests,12design+4editor checks.2API-dependent skips. No backend/API/formula/FSD migration or commits.

### T233. Clarify frontend loading, empty, error and success states

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T232.

**Результаты/файлы:** `frontend/src/pages/tracker/`; `docs/evidence/frontend-states.md`.

**Шаги:**

1. Audit request states.
2. Separate loading empty and failure.
3. Deduplicate critical and local errors.
4. Preserve stale data and acknowledge actions.
5. Test and document.

**Критерии закрытия:**

- Tracker empty state requires successful manual and archive reads; server/network failure never appears empty.
- One critical recoverable message; compact local failures; keep cached results and drafts during background updates.
- Human-readable success and progress; network/empty/retry tests; typecheck/lint/build; no backend/API/architecture changes or commits.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/frontend-states.md](../docs/evidence/frontend-states.md) — Distinct loading/empty/error/success, one blocking tracker failure, compact local feedback, preserved cache/drafts, lazy optional reads and truthful success. typecheck/lint/build/format/architecture pass;150unit,56Chromium passed/2external-fixture skips;final14state cases passed. No backend/contracts/calculations/architecture migration/commits.

### T234. Simplify direction creation and editing form UX

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T233.

**Результаты/файлы:** `frontend/src/features/edit-manual-direction/`; `docs/evidence/direction-form-ux.md`.

**Шаги:**

1. Audit form and data rules.
2. Group fields and explain inputs.
3. Unify hints and inline errors.
4. Clarify save progress failure and success.
5. Verify mobile and relevant regressions.

**Критерии закрытия:**

- One clear form with field groups, human labels, examples, contextual help and explicit required/optional distinction.
- Field-linked validation; preserve input on save failure; clear pending/error/success; usable on mobile and keyboard.
- No business-validation/formula/API/storage changes; typecheck/lint/build and relevant tests pass; no commits.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/direction-form-ux.md](../docs/evidence/direction-form-ux.md) — One guided form; required/optional distinction; field-linked errors and safe save/retry UX. typecheck/lint/build/format/architecture pass;150unit,43compiledChromium/0skips,12design+4editor checks. Mobile screenshots reviewed. Model/validation/API/storage unchanged. Prior local T233 preserved;no commits.

### T235. Audit and align remaining frontend pages with the design system

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T234.

**Результаты/файлы:** `frontend/src/app/`; `frontend/src/pages/landing/`; `frontend/src/pages/sources/`; `docs/evidence/frontend-consistency-audit.md`.

**Шаги:**

1. Audit routes and shell.
2. Review landing and calculator.
3. Align sources UI.
4. Review project content and utility routes.
5. Verify themes mobile and regression checks.

**Критерии закрытия:**

- Audit all existing routes, shell and embedded calculator/project content in light/dark and mobile; document concrete findings.
- Fix confirmed typography/controls/spacing/forms/states/navigation inconsistencies using existing tokens and primitives; preserve content and behavior.
- No tracker page redesign/backend/business/FSD changes; standard checks and relevant tests; no commits.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/frontend-consistency-audit.md](../docs/evidence/frontend-consistency-audit.md) — Remaining routes/shell audited; consistent navigation/mobile menu, surfaces/headings, source states, calculator validation and utility pages. typecheck/lint/build/format/architecture;150unit;59Chromium passed/2API-fixture skips;final37audit cases +12design/4editor checks passed. Viewed PNGs. Tracker hashes unchanged;no backend/business/FSD/commits.

### T242. Replace frontend with an exact copy of the v3 source

**Статус:** `done` · **Приоритет:** P0 · **Размер:** L.

**Зависимости:** нет.

**Результаты/файлы:** `frontend/src/`; `frontend/tests/`; `docs/evidence/frontend-v3-exact.md`.

**Шаги:**

1. Create clean branch from main preserving previous redesign branch.
2. Copy original frontend sources directly without old logic/API.
3. Install and run both React projects.
4. Compare all 29 routes at five widths and test interactions.

**Критерии закрытия:**

- Source UI files remain identical; only documented technical setup changes.
- All29routes run with original demo behavior, no old backend/API integration.
- Typecheck/build/install and Playwright interactions/routes/console/overflow; paired original-vs-copy screenshots and pixel diff at390/768/1024/1280/1440.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/frontend-v3-exact.md](../docs/evidence/frontend-v3-exact.md) — Implementation 3e50540: direct copy of all 29 source routes; one type-only fix, identical compiled JS/CSS. Install/typecheck/build/source verification passed. Chromium 187 passed, zero failed/skipped; 145 live pixel comparisons at five widths, zero different pixels and no horizontal overflow. All 290 PNGs and interactive gallery saved. Backend/shared/Compose and main/previous branch unchanged. No API integration, push or deployment.

### T243. Audit all 29 v3 routes and backend reuse

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** нет.

**Результаты/файлы:** `docs/product-functional-audit.md`.

**Шаги:**

1. Implement the scoped work with source evidence and preserve v3 styling.

**Критерии закрытия:**

- 29-route table covers data, controls, demo/working state, required APIs, dependencies and priority; backend reuse and slice plan documented.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/product-functional-audit.md](../docs/product-functional-audit.md) — All 29 routes audited; backend reuse, source limits, API/model map and implementation sequence documented after source inspection.

### T244. Implement verified campaign-scoped catalog API

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T243.

**Результаты/файлы:** `backend/app/product_catalog.py`.

**Шаги:**

1. Implement the scoped work with source evidence and preserve v3 styling.

**Критерии закрытия:**

- Public read API uses audited identities, nullable unknowns, campaign years and provenance; no synthetic production facts.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [backend/tests/test_product_catalog.py](../backend/tests/test_product_catalog.py) — Public read facade and atomic audited import implemented. Targeted new + legacy catalog tests: 31 passed, 1 native PostgreSQL skipped (Docker permission denied). Provenance/year/null/conflict and legacy compatibility covered.

### T245. Connect v3 catalog and detail pages to real API

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T244.

**Результаты/файлы:** `frontend/src/catalog/`.

**Шаги:**

1. Implement the scoped work with source evidence and preserve v3 styling.

**Критерии закрытия:**

- Four React pages use stable IDs and real API with search, filters, pagination, loading/error/empty states, no demo fallback.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [frontend/src/catalog/DetailPages.tsx](../frontend/src/catalog/DetailPages.tsx) — Four v3 compositions now use real public API, stable campaign IDs and provenance. Search/filters/pages, cancellation/retry/404 and no demo fallback. Catalog E2E 27 passed at five widths; TypeScript/ESLint/build passed. Long-name constraints reuse v3 responsive primitives.

### T246. Verify catalog APIs, flows and unchanged design

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T245.

**Результаты/файлы:** `docs/evidence/catalog-vertical-slice.md`.

**Шаги:**

1. Implement the scoped work with source evidence and preserve v3 styling.

**Критерии закрытия:**

- TypeScript, ESLint, build, backend API tests and desktop/mobile Playwright pass; unavailable environment explicitly recorded.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/catalog-vertical-slice.md](../docs/evidence/catalog-vertical-slice.md) — Final 193 Chromium passed, no failures/skips/flaky; standalone runner 68 passed and graceful teardown verified. 47 backend passed, 1 PostgreSQL skipped (Docker denied). ESLint source/tests/scripts, TS/build/install passed. 100 raw +25 exact demo-label-normalized pixel comparisons zero diff, 20 catalog PNGs across five widths, source68 unchanged. Real positive API calls and error/empty/late-response cases checked. Two earlier temp DB folder removals denied by approval policy; no workaround.

### T247. Document product foundation and remaining demo modules

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T246.

**Результаты/файлы:** `docs/STATE.json`.

**Шаги:**

1. Implement the scoped work with source evidence and preserve v3 styling.

**Критерии закрытия:**

- Run instructions, API/model map, evidence, statuses and next steps are accurate.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/catalog-runbook.md](../docs/catalog-runbook.md) — All 29-route audit/API/model plan, real-vs-demo boundaries, explicit import and existing PostgreSQL/isolated local run instructions documented. Evidence gallery20 and final test summaries retained. Main/source/previous branches preserved; no push. Next: actual PostgreSQL verification, reviewed program/year/exam coverage, then saved real IDs; no ML yet.

### T248. Audit and classify product foundation modules

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** нет.

**Результаты/файлы:** `docs/foundation-cleanup-audit.md`.

**Шаги:**

1. Complete scoped cleanup/infrastructure work without new product features.

**Критерии закрытия:**

- Dependencies and current product audited across frontend/backend/APIs/models/migrations/tests/deps/Docker/CI/docs; KEEP/REFACTOR/DELETE justified.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/foundation-cleanup-audit.md](../docs/foundation-cleanup-audit.md) — Audited source imports, active UI/build/test dependencies, backend consumers, persisted data, migrations, CI and docs. KEEP/REFACTOR/DELETE decisions and irreversible retirement plan recorded.

### T249. Remove confirmed obsolete tooling and calculator endpoints

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T248.

**Результаты/файлы:** `docs/evidence/foundation-cleanup/deleted-files.json`.

**Шаги:**

1. Complete scoped cleanup/infrastructure work without new product features.

**Критерии закрытия:**

- Only confirmed obsolete code removed; useful backend/source/history/models and applied migrations preserved; no v3 design changes.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/foundation-cleanup/deleted-files.json](../docs/evidence/foundation-cleanup/deleted-files.json) — 42 audited files removed; old calculate/assess HTTP wrappers and assessment-only types retired. DTO base isolated; all migration/model data protected. Unused React plugin removed: clean install116 vs162 packages; lint/TS/build passed, browser193 and catalog baseline20 zero pixel diff. Actual protocol validation/origin/budget tests retained and retargeted, 33 passed.

### T250. Verify Compose PostgreSQL migrations and live catalog

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T248.

**Результаты/файлы:** `docs/evidence/foundation-cleanup/infrastructure.json`.

**Шаги:**

1. Complete scoped cleanup/infrastructure work without new product features.

**Критерии закрытия:**

- Actual Docker Compose PostgreSQL startup, connection/migrations/API/catalog browser path executed; permission denial is a blocker, never a success.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/foundation-cleanup/infrastructure.json](../docs/evidence/foundation-cleanup/infrastructure.json) — Compose syntax check performed and actual db startup attempted. PostgreSQL and container smoke not verified; no workaround or volume deletion.
- [docs/evidence/local-postgresql.md](../docs/evidence/local-postgresql.md) — S203 actual existing-volume Docker Compose full command including build exit0;PG17.11/current=head0011/alembic check/import twice/API/SPA;two-snapshot history and mount identities survive recreate.11native PG tests+5launcher unit tests passed;Chromium390/1440 viewed. Alembic metadata fix881422f,applied migrations intact. No SQLite substitute,push or release-gate claim.

### T251. Run current backend and frontend regression checks

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T249.

**Результаты/файлы:** `docs/evidence/foundation-cleanup.md`.

**Шаги:**

1. Complete scoped cleanup/infrastructure work without new product features.

**Критерии закрытия:**

- TS/ESLint/build/current backend and API/browser suites plus visual preservation; exact outcomes and environment limits recorded.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/foundation-cleanup.md](../docs/evidence/foundation-cleanup.md) — Final portable Windows backend549passed/35native PostgreSQL skips; 12 Linux resource modules explicitly uncollectable on Windows and retained for Linux CI. Browser193passed, 29routes, catalog20 baseline PNG diffs0 +125 reference comparisons; TS/ESLint/build/clean install/source guard passed. Docker startup denied, T250 remains blocked.

### T252. Align documentation and stop after cleanup

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T251.

**Результаты/файлы:** `docs/STATE.json`.

**Шаги:**

1. Complete scoped cleanup/infrastructure work without new product features.

**Критерии закрытия:**

- Current architecture, removed files, preserved mechanisms and irreversible-change plan documented; registry regenerated, small commits, no main changes or new features.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/foundation-cleanup.md](../docs/evidence/foundation-cleanup.md) — Current v3 architecture/API/product/design/README/runbooks replace stale manual-product instructions; old docs archived with rebased links. Old release/ML tasks deferred, no false done. Removal manifest42, protected hashes, current API inventory31, dependency report and final tests recorded. Cleanup complete, T250 blocked; no new features or main/DB changes.

### T256. KAN-228: рабочие страницы конкурсных списков и конкурентов v3

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T255.

**Результаты/файлы:** `backend/app/competition_api.py`; `frontend/src/pages/CompetitionPages.tsx`; `docs/evidence/kan-228-competition-pages.md`.

**Шаги:**

1. API списка, строк и агрегатов по опубликованному снимку.
2. Официальный порядок, фильтры по неперсональным признакам, переход к месту.
3. Своя строка только для подтвердившего гостя.
4. Страницы v3 списка и конкурентов, перенос сохранённого направления в /app/watchlist/{id}.
5. Тесты и ручная проверка на архиве.

**Критерии закрытия:**

- Реальные списки открываются с меткой времени и ссылкой.
- Позиции и приоритеты не выдуманы; неполные списки и неподдержанные правила помечены.
- E2E и защита персональных данных.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/kan-228-competition-pages.md](../docs/evidence/kan-228-competition-pages.md) — S204 /api/v1/competitions/{id}, /rows, /summary; pages /app/competitions, /{id}, /{id}/competitors. Official order only, no identifiers in responses (tested), frontend rejects extra row fields, own row only after confirmation. 4 backend tests, 4 browser tests; SGU archive 573 rows viewed at 1440/390.

### T257. KAN-220: JSON/CSV адаптеры через общий интерфейс и массовая очередь

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T255.

**Результаты/файлы:** `backend/app/sources/structured_family.py`; `backend/app/jobs.py`; `backend/tests/test_structured_family.py`; `docs/evidence/kan-220-source-adapters.md`.

**Шаги:**

1. Строгие декодеры JSON и CSV по проверенному профилю.
2. Подключение к runtime registry только с аттестацией.
3. enqueue_all: массовая постановка с разносом по доменам и без дублей.
4. Интеграционные тесты PostgreSQL: повторный импорт и сбой.
5. Ручная проверка на 6 зарегистрированных источниках.

**Критерии закрытия:**

- Не меньше 3 типов источников через общий интерфейс.
- Повторный импорт не дублирует, сбой не затирает проверенный снимок.
- Лог ошибок, ограничение нагрузки, тесты PostgreSQL.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/kan-220-source-adapters.md](../docs/evidence/kan-220-source-adapters.md) — S205 HTML (SGU, 4 table variants), JSON and CSV through one Adapter/Registry; enqueue-all spreads same-domain starts, skips unattested by reason; 18 new tests incl. PostgreSQL worker; manual run on 6 sources/5 domains. PDF not done; JSON/CSV PROFILES empty until a source is reviewed.

### T258. KAN-219: требования вступительных испытаний из официальных документов

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T255.

**Результаты/файлы:** `scripts/build_exam_requirements.py`; `backend/app/exam_requirements.py`; `backend/app/data/exam-requirements.json`; `docs/sources/exam-rules/sgu-2026.json`; `docs/evidence/kan-219-exam-requirements.md`.

**Шаги:**

1. Ревью официального документа вуза с якорями и строками-доказательствами.
2. Сборщик сверяет хеш документа и каждое значение с текстом.
3. Строгий парсер и выдача только при точном совпадении года, кода, формы и уровня.
4. API и страница программы, слой покрытия ЕГЭ.
5. Тесты на повреждения, воспроизводимость и несовпадающие правила.

**Критерии закрытия:**

- Для опубликованной группы читается полный состав известных требований, неизвестное null, источник проверяем.
- Импорт идемпотентен.
- E2E на реальном документе и несовпадающих правилах.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/kan-219-exam-requirements.md](../docs/evidence/kan-219-exam-requirements.md) — S206 SGU 09.03.04 and 02.03.03 (2026): math 40, informatics 46 or physics (null: document says 41 and 40), Russian 40; source PDF 2026-06-08 sha256 936121ed, cross-check sgu.ru/cpk. Builder refuses facts not in the document; artifact rebuilt byte-identical. Layer 1/785. Benefits not collected; other universities not reviewed.

### T259. KAN-24: еженедельный отчёт: шаблон и PDF для чата команды

**Статус:** `done` · **Приоритет:** P2 · **Размер:** S.

**Зависимости:** нет.

**Результаты/файлы:** `docs/WEEKLY_REPORT.md`; `scripts/weekly_report.py`; `scripts/requirements-report.txt`; `scripts/tests/test_weekly_report.py`.

**Шаги:**

1. Шаблон: сделано, на проверке, в работе, заблокировано, сроки, доказательства, ответственный.
2. Генератор из git и TASKS.json: Done только после слияния в main, сроки не выдумываются.
3. PDF во временной папке для отправки в чат; отчёты в проекте не хранятся.
4. Первый отчёт за 2026-W46 отправлен в чат.

**Критерии закрытия:**

- Шаблон содержит сделано, в работе, заблокировано, сроки, доказательства, ответственного.
- Отчёт выходит PDF-файлом со ссылками на коммиты и evidence и не хранится в проекте.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/WEEKLY_REPORT.md](../docs/WEEKLY_REPORT.md) — S207 PDF via reportlab with embedded Cyrillic font and clickable commit links; extra rows and risks from --extra; 7 unit tests incl. PDF text and links via pypdf. Reports are not committed (.gitignore admitflow-weekly-*.pdf); 2026-W46 sent to chat. Agreement with the team lead is a team step.

## E5. Качество и эксплуатация

Плановый интервал: D20–D27.

### T041. Добавить наблюдаемость API/worker/источников

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T032, T035, T037, T086.

**Результаты/файлы:** `backend/app/observability/`; `docs/RUNBOOK.md`.

**Шаги:**

1. Добавить структурированные логи, request/import IDs, freshness и worker heartbeat.
2. Отделить здоровье API от доступности источников и убрать персональные поля.

**Критерии закрытия:**

- По ошибке можно восстановить цепочку source→run→snapshot→assessment.
- Мёртвый worker и устаревший источник видны отдельно от HTTP health.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [backend/app/observability.py](../backend/app/observability.py) — Heartbeat worker, /api/status отдельно от /api/health, runId связывает лог с source_checks и snapshot, trace без данных абитуриентов.
- [backend/tests/test_observability.py](../backend/tests/test_observability.py) — Проверены success и failure цепочки, отсутствие текста исключений в событиях, старение worker, degraded.

### T042. Собрать регрессию правил и качества данных

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T020, T034, T036.

**Результаты/файлы:** `backend/tests/`; `frontend/tests/fixtures/`; `docs/evidence/regression.md`.

**Шаги:**

1. Проверить весь перечень доменных случаев QUALITY.md.
2. Включить неподдержанный конкурс, tie-break и неполные поля.

**Критерии закрытия:**

- Нет расхождений с подтверждёнными expected outcomes.
- Все невычислимые случаи дают явный отказ/ограничение.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/regression.md](../docs/evidence/regression.md) — Все 12 доменных случаев QUALITY и Q03 сопоставлены с тестами; карта проверяется тестом. Найден и закрыт ложноположительный статус при завышенном числе мест.

### T043. Проверить безопасность и пользовательские данные

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T016, T017, T028, T033, T085, T095.

**Результаты/файлы:** `backend/tests/security/`; `docs/evidence/security.md`.

**Шаги:**

1. Проверить ownership, CSRF, SSRF, XSS, rate limits, raw access и cleanup.
2. Проверить логи/backup/fixtures на лишние данные и конфигурацию production.

**Критерии закрытия:**

- Нет критичных утечек и обхода доступа.
- Retention и удаление проверены, открытые организационные вопросы явно блокируют публичный запуск.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 30/30,finalcurrent:454backend/72nativePG/0skip,102unit,100Chromium+2actualNginx passed;separate processing clock/retry,privacy scan0matches,PG/rawrestore and runtime checks passed;release blockers recorded.

### T044. Измерить нагрузку и устранить узкие места

**Статус:** `review` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T034, T041.

**Результаты/файлы:** `scripts/load/`; `docs/evidence/performance.md`.

**Шаги:**

1. Зафиксировать профиль из QUALITY.md и реальные максимальные размеры.
2. Измерить p95/5xx/память, N+1, jobs lag и экономию одного fetch на группу.

**Критерии закрытия:**

- Порог качества достигнут на именованном стенде.
- Измерения включают большую группу и параллельное обновление, а не только пустую БД.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/t044-load.md](../docs/evidence/t044-load.md) — Полный профиль 100 сессий, 20 направлений, 10 000 строк и параллельная публикация на стенде dev-container-2cpu. Узкие места устранены. Повтор на staging ожидает T048.

### T045. Проверить браузеры и визуальные состояния

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T026, T039, T040.

**Результаты/файлы:** `playwright.config.ts`; `frontend/tests/e2e/`; `docs/evidence/visual.md`.

**Шаги:**

1. Настроить Chromium/Firefox/WebKit и desktop/mobile/light/dark.
2. Пройти landing, tracker, history, source error и keyboard.

**Критерии закрытия:**

- Существенные расхождения исправлены.
- Непроверенная платформа явно записана и не считается поддержанной по тестам.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/t045-browsers.md](../docs/evidence/t045-browsers.md) — Chromium, Firefox, WebKit и два мобильных профиля пройдены в CI; ограничения платформ записаны.

### T046. Наблюдать циклы импорта и свежесть

**Статус:** `blocked` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T035, T038, T041.

**Результаты/файлы:** `docs/evidence/source-soak.md`.

**Шаги:**

1. Провести 24-часовое наблюдение доступных официальных источников.
2. Дополнительно имитировать изменения, отказ и восстановление через replay.

**Критерии закрытия:**

- Есть фактические timestamps и outcomes попыток.
- Успешный архивный replay не выдан за live-soak.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

**Причина блокировки/переноса:** 2026-11-05: нужны 24 реальных часа на сервере с разрешённым доступом к источникам; из среды разработки сайты вузов недоступны. Процедура в RUNBOOK. Условие снятия: T048.

### T047. Подготовить контейнерный контур

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T006, T014, T032.

**Результаты/файлы:** `compose.yaml`; `Dockerfile`; `backend/Dockerfile`; `Caddyfile`.

**Шаги:**

1. Собрать frontend/API/worker/PostgreSQL с healthchecks и volumes.
2. Проверить fresh install, migrations, restart, same-origin routing и deep links.

**Критерии закрытия:**

- После restart данные сохранены и worker возвращается в работу.
- БД и административные порты не открыты наружу.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [compose.prod.yaml](../compose.prod.yaml) — Production-стек с закрытой внутренней сетью и лимитами.
- [docs/evidence/t045-browsers.md](../docs/evidence/t045-browsers.md) — Пересоздание с сохранением данных, возврат worker и закрытые порты проверены в CI. Первый запуск prod-конфигурации относится к T048.

### T048. Развернуть staging с HTTPS

**Статус:** `blocked` · **Приоритет:** P0 · **Размер:** L.

**Зависимости:** T047.

**Результаты/файлы:** `docs/deployment.md`; `docs/evidence/staging.md`.

**Шаги:**

1. Зафиксировать площадку, домен, бюджет и регион до оплачиваемых действий.
2. Выполнить deployment, secure-cookie smoke и проверить API вместе с UI.

**Критерии закрытия:**

- Есть фактический доступный URL и версия всего контура.
- Статический frontend без работающего API не считается staging MVP.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

**Причина блокировки/переноса:** 2026-11-05: не выбраны сервер, домен, бюджет и регион; без них нельзя получить URL и TLS. Готовы compose.prod.yaml, Caddyfile и инструкция в RELEASE_GATES.md. Условие снятия: решение владельца и доступ к серверу.

### T049. Проверить backup, restore и retention

**Статус:** `blocked` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T043, T048, T089, T101.

**Результаты/файлы:** `scripts/backup/`; `docs/evidence/restore.md`; `docs/RUNBOOK.md`.

**Шаги:**

1. Создать копию PostgreSQL/raw и восстановить в отдельную БД.
2. Сверить записи/ownership/hashes, проверить cleanup и измерить RPO/RTO.

**Критерии закрытия:**

- Данные восстановлены проверкой, а не только наличием файла.
- Результаты времени и известное окно потери записаны.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

**Причина блокировки/переноса:** 2026-11-05: скрипт и проверка восстановления работают в CI, но acceptance требует staging и утверждённых сроков хранения. Условие снятия: T048 и решение оператора данных.

### T050. Настроить эксплуатационные сигналы и откат

**Статус:** `blocked` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T041, T048.

**Результаты/файлы:** `docs/RUNBOOK.md`; `docs/evidence/operations.md`.

**Шаги:**

1. Настроить readiness, worker stale, source quarantine, ошибки и размер БД.
2. Проверить совместимый rollback и действия при несовместимой схеме.

**Критерии закрытия:**

- Есть проверенный путь обнаружения и восстановления основных сбоев.
- Секреты и персональные данные не попадают в сигналы.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

**Причина блокировки/переноса:** 2026-11-05: scripts/ops_check.py и порядок отката готовы, но сигнал надо проверить на настоящем сервере. Условие снятия: T048.

### T051. Пройти полный путь автоматизированного MVP

**Статус:** `deferred` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T021, T022, T024, T034, T040, T048.

**Результаты/файлы:** `frontend/tests/e2e/mvp.spec.ts`; `docs/evidence/e2e.md`.

**Шаги:**

1. Пройти выбор источника/группы/ID, сохранение, новый снимок, diff и историю.
2. Проверить два владельца, удаление, stale и восстановление.

**Критерии закрытия:**

- Пользовательский путь подтверждён на staging с реальным API.
- Внешний fetch при тестах не зависит от недетерминированной случайной выдачи.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

**Причина блокировки/переноса:** Deferred by S201 product cleanup: previous automated/manual MVP release scope or future prediction/expansion work is not the current v3 cleanup. Resume only after v3 acceptance criteria and dependencies are reviewed in a separately authorized phase; ML additionally requires verified outcomes/data and predefined metrics. Historical status and evidence remain in Git.

### T052. Провести продуктовую приёмку

**Статус:** `deferred` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T039, T045, T051.

**Результаты/файлы:** `docs/evidence/acceptance.md`.

**Шаги:**

1. Дать задания первого расчёта, поиска причины изменения и проверки источника.
2. Записать фактические наблюдения пользователя/тестеров и устранить критичные непонимания.

**Критерии закрытия:**

- Понятность оценена по PRODUCT.md либо явно непроверена.
- Нет придуманных отзывов и смешения сценария с гарантией.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

**Причина блокировки/переноса:** Deferred by S201 product cleanup: previous automated/manual MVP release scope or future prediction/expansion work is not the current v3 cleanup. Resume only after v3 acceptance criteria and dependencies are reviewed in a separately authorized phase; ML additionally requires verified outcomes/data and predefined metrics. Historical status and evidence remain in Git.

### T084. Ограничить размер и время приёма API-запросов

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T018.

**Результаты/файлы:** `backend/app/http.py`.

**Шаги:**

1. Ограничить Content-Length и реальный поток bytes.
2. Вернуть безопасный отказ oversized/timeout.

**Критерии закрытия:**

- 413 для переполнения с заголовком и без него.
- 408 для stalled body; обычные запросы не меняются.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S038 / B03 2/10: Pure ASGI middleware limits actual request bytes to 8 MiB and total body receive to 10 seconds, handles false/missing length, disconnect and 400/408/413 before endpoint. Matching Nginx limits configured, runtime still unverified. pytest budget+API: 17 passed, final budget subset 3 passed / exit 0. Files http.py/main.py/nginx.conf and tests; public limits documented.

### T085. Проверять Host и Origin запросов записи

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T016, T084.

**Результаты/файлы:** `backend/app/config.py`; `backend/app/main.py`.

**Шаги:**

1. Закрепить доверенные hosts и public origin.
2. Проверить same-origin и чужие/null origin.

**Критерии закрытия:**

- Production требует явный HTTPS origin.
- Чужой host/origin не изменяет данные.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S039 / B03 3/10: Trusted Host allowlist and exact production HTTPS PUBLIC_ORIGIN supplement custom-header CSRF guard; cross-site/null/foreign origins cannot write. Local dev ports work for trusted loopback hosts; readonly calculations unchanged. pytest origin+config+API: 20 passed / exit 0. Production config now fails closed without explicit host/origin. Docs/env updated; no actual domain or deployment claimed.

### T086. Добавить безопасную диагностику HTTP и readiness

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T084, T085.

**Результаты/файлы:** `backend/app/http.py`; `backend/app/main.py`.

**Шаги:**

1. Request ID, route template, status и duration без пользовательского тела.
2. Отделить liveness от DB readiness.

**Критерии закрытия:**

- Ошибка не раскрывает SQL/токен/PII.
- DB outage даёт readiness 503, liveness 200.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S040 / B03 4/10: Generated request IDs and structured route-template/status/duration logs exclude raw URLs, query, cookie and exception text; unexpected JSON errors return safe 500. Liveness is DB independent, readiness/health return safe 503 on DB failure. Initial test found duplicate Cache-Control header; middleware now replaces diagnostic headers consistently. Targeted diagnostics/origin/budget pytest: 8 passed / exit 0. Uvicorn no-access-log configured for Docker/CI/runbook; real remote/container runtime not claimed.

### T087. Очищать неиспользуемые raw-файлы с защитой публикации

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T078, T079.

**Результаты/файлы:** `backend/app/sources/retention.py`.

**Шаги:**

1. Ввести межпроцессную блокировку raw store.
2. Dry-run по возрасту, referenced hashes сохраняются.

**Критерии закрытия:**

- Cleanup не гоняется с put/commit и не идёт по symlink.
- Удаление только явно указанным apply, ошибки БД запрещают удаление.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S041 / B03 5/10: Raw retention is dry-run unless explicit apply; only old unreferenced SHA-256 files are eligible, all historical snapshot refs are retained, symlinks skipped and DB lookup failure precedes deletion. Shared reentrant interprocess lock spans raw put through publication commit and cleanup. pytest retention/store/publication/worker: 18 passed / exit 0, including process lock, GC-vs-commit race, historical refs and DB failure. Transient storage lock failures use bounded retry. No automatic production cleanup enabled.

### T088. Сохранять согласованную SQLite-копию с raw-файлами

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T087.

**Результаты/файлы:** `backend/app/backup.py`.

**Шаги:**

1. Online backup и manifest с хешами.
2. Скопировать raw именно из сохранённой DB.

**Критерии закрытия:**

- При ошибке нет готовой частичной копии.
- Копия содержит ручную историю и все referenced raw.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S042 / B03 6/10: SQLite online backup plus all raw refs from the saved DB are captured under store lock into a private atomically finalized bundle. Manifest hashes DB and references; timeout/missing raw cleans staging and never reports ready. pytest tests/test_backup.py: 3 passed / exit 0, covering manual watch/history, multiple source versions/raw, orphan exclusion and failed copies. Local SQLite only; production PostgreSQL backup/restore remains open.

### T089. Восстанавливать копию в новое SQLite-окружение

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T088.

**Результаты/файлы:** `backend/app/backup.py`.

**Шаги:**

1. Проверить manifest, hash, integrity и FK.
2. Восстановить только в отсутствующее назначение.

**Критерии закрытия:**

- Повреждённая копия и занятый путь отклоняются.
- Восстановленная история и ownership совпадают.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S043 / B03 7/10: SQLite backup verification checks DB/raw hashes, integrity/FK, revision and exact raw references; unexpected views/triggers, symlinks, corruption and existing destination refused. Restore copies to new private environment and verifies again. pytest backup+restore: 6 passed / exit 0; actual restored FastAPI preserves watch IDs/history and cookie ownership, a new owner sees 404; source raw bytes verified. No working DB switched; PostgreSQL/production restore gate stays open.

### T101. Не перезаписывать назначение при конкурентном restore

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T089.

**Результаты/файлы:** `backend/app/backup.py`.

**Шаги:**

1. Зарезервировать новый destination без overwrite.
2. Не считать незавершённый restore готовым.

**Критерии закрытия:**

- Две попытки не перезаписывают чужую папку.
- Ошибка оставляет существующие данные без изменений.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S056 / B04 9/10: Restore reserves destination with exclusive mkdir and installs verified files without overwrite; concurrent attempts yield exactly one success. Failed finalization leaves restore.pending and verify/migration/API reject it. Initial test edit misplaced an existing schema assertion; corrected placement. Final restore/backup/migration pytest: 18 passed, 1 real PostgreSQL skipped. Hard-link filesystem requirement and partial-folder recovery documented.

### T118. Reject readiness when database revision is incompatible

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T086.

**Результаты/файлы:** `backend/app/main.py`; `backend/app/migrations.py`; `backend/tests/test_diagnostics.py`.

**Шаги:**

1. Reject readiness when database revision is incompatible.
2. Verify success, boundary and relevant failure behavior.

**Критерии закрытия:**

- Ready/health require expected Alembic revision; live remains DB-independent; failures sanitized..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S075: Ready/health compare stored Alembic revisions with packaged migration heads; missing/empty/old/future revision503, live stays DB-independent and no automatic repair. Full backend205 passed/7 PG skipped; frontend68/build and44 Chromium passed on explicitly restarted API8004. After minor print-date/dateformatter/grid fixes, build and3 print/history/mobile checks passed again. Screenshots1440/390 refreshed, three history rows visible, no horizontal page overflow, demo sessions deleted204/204. B05 complete15/15; no real-source/PG/CI gate unlocked.

### T120. Reject ambiguous JSON request documents

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T084.

**Результаты/файлы:** `backend/app/http.py`; `backend/tests/test_manual_hardening.py`.

**Шаги:**

1. Reject ambiguous JSON request documents.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Duplicate keys, nonfinite numbers and excessive nesting are rejected before any endpoint writes..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S078: Request JSON rejects duplicate keys, NaN/Infinity/overflow and depth over64 before writes, preserving normal malformed-JSON validation. Brackets inside strings remain valid. Targeted hardening14 passed; existing8MiB receive budget preserved.

### T121. Bound and redact validation error responses

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T086.

**Результаты/файлы:** `backend/app/main.py`; `backend/app/schemas.py`; `backend/tests/test_manual_hardening.py`.

**Шаги:**

1. Bound and redact validation error responses.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Validation responses expose no input/context values and contain a bounded error summary..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S079: Validation422 returns at most20 redacted field paths, no input/context or unknown key values, with matching OpenAPI schema. Targeted hardening/API/body-budget32 passed.

### T122. Fail closed on invalid environment and production settings

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T085.

**Результаты/файлы:** `backend/app/config.py`; `backend/tests/test_config.py`; `backend/tests/test_config_strict.py`.

**Шаги:**

1. Fail closed on invalid environment and production settings.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Unknown environments/boolean values fail startup; direct Settings cannot bypass production invariants..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S080: Settings fail closed for unknown environment/boolean strings; constructor enforces PostgreSQL, secure cookie and explicit production migrations. Updated prior test to reject an explicit unsafe true instead of silently ignoring it. Config/origin10 passed.

### T123. Bound PostgreSQL connection establishment

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T004.

**Результаты/файлы:** `backend/app/database.py`; `backend/tests/test_connection_timeout.py`.

**Шаги:**

1. Bound PostgreSQL connection establishment.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Unresponsive PostgreSQL handshake fails within configured bounds; credentials are not logged..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S081: PostgreSQL connect timeout defaults5s (allowed1..10), pool checkout5s. Real local TCP peer accepted a connection then stalled: handshake timed out;4 tests passed. This is failure-path wire verification, not a successful PG migration/server test.

### T137. Bound JSON response consumption in the browser

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T073.

**Результаты/файлы:** `frontend/src/lib/transport.ts`; `frontend/src/lib/api.ts`; `frontend/tests/response.test.ts`.

**Шаги:**

1. Bound JSON response consumption in the browser.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Oversized/malformed response bodies stop reading; cancellation and timeout remain effective..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S095: Browser JSON reader enforces10MiB success/64KiB error bounds, cancels oversize/stalled streams, validates UTF8 and MIME, bounds displayed error strings. Four body regressions and all77 frontend tests/build passed; session epoch fence still covers body completion.

### T164. Isolate every PostgreSQL migration test

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T004.

**Результаты/файлы:** `backend/tests/pg_support.py`.

**Шаги:**

1. Isolate every PostgreSQL migration test.
2. Verify successful preparation and meaningful refusal cases; record runtime limits.

**Критерии закрытия:**

- All destructive migration checks use a newly created random schema; failure cleanup never targets the shared schema. Native PostgreSQL acceptance remains separate..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S125: pytest test_pg_support.py/test_migrations.py21 passed/7 actual PG skipped. Upgrade/downgrade now uses the same isolated schema fixture as every native case; no destructive test targets public. SQL compiler/controller regressions prove scoped search_path and cleanup on body/engine-creation errors; failed CREATE never triggers DROP. Native PG execution remains unverified.

### T165. Fail mandatory CI checks when PostgreSQL tests are absent or skipped

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T164.

**Результаты/файлы:** `backend/tests/conftest.py`.

**Шаги:**

1. Fail mandatory CI checks when PostgreSQL tests are absent or skipped.
2. Verify successful preparation and meaningful refusal cases; record runtime limits.

**Критерии закрытия:**

- Explicit mandatory mode fails on missing/unsafe configuration, no selected PG cases or any skipped native case; local optional mode remains explicit..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S126: Guard subprocess regressions8 passed; full collection301 tests succeeds. Actual pytest --require-postgres tests/test_migrations.py exits4 with missing disposable PG configuration, rather than green skipped checks. Guard also rejects filtered native cases and teardown skips. CI now requests mandatory PG and JUnit artifact; remote workflow remains unrun/T006 blocked.

### T166. Provide read-only redacted database diagnostics

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T004.

**Результаты/файлы:** `backend/app/diagnostics.py`.

**Шаги:**

1. Provide read-only redacted database diagnostics.
2. Verify successful preparation and meaningful refusal cases; record runtime limits.

**Критерии закрытия:**

- CLI reports dialect/revisions and aggregate manual row counts without migrations, schema creation, data mutation, credentials or row payloads; unavailable database exits nonzero..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S127: Database diagnostic regressions5 passed: actual SQLite counts/read-only rejection, Unicode path, missing file not created, restore marker refusal, legacy/future revision and credential redaction. Real CLI on isolated batch08.db returns revision_current/sqlite/0004 and aggregate counts only. No migrations/repair/session cleanup. PG read-only repeatable-read SQL documented from primary docs, execution unverified.

### T167. Prepare the Compose worker and shared raw volume

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T066.

**Результаты/файлы:** `compose.yaml`.

**Шаги:**

1. Prepare the Compose worker and shared raw volume.
2. Verify successful preparation and meaningful refusal cases; record runtime limits.

**Критерии закрытия:**

- Compose validates a separate optional worker with the same DB/raw volume and no published ports; default stack stays manual. Runtime/real-source gate remains open..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S128: docker compose config --quiet and --profile automation config --quiet exit0 despite Docker config ACL warning. Default services db/backend/frontend; automation adds worker. Shared raw_data path and app-owned image directory, no worker ports or parallel migrations. RUNBOOK includes raw-layer preservation and explicit Engine/image/permissions/runtime limitations; no container started or user volume changed.

### T168. Verify the compiled React application in the browser

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T163.

**Результаты/файлы:** `frontend/playwright.config.ts`; `frontend/tests/e2e/tracker-tools.spec.ts`; `frontend/tests/e2e/keyboard.spec.ts`; `frontend/src/components/UniversityPicker.tsx`; `frontend/src/pages/TrackerPage.tsx`; `.github/workflows/ci.yml`.

**Шаги:**

1. Verify the compiled React application in the browser.
2. Verify successful preparation and meaningful refusal cases; record runtime limits.

**Критерии закрытия:**

- Manual browser suite runs against a fresh production build with current API; lazy error recovery works for emitted chunks; CI requests built-asset checks without claiming an unrun remote result..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b10-runtime.md](../docs/evidence/b10-runtime.md) — B10 first5/5:92 frontend tests/build,12 repeated keyboard checks,70/70 full Chromium passed on actual production assets/PostgreSQL API. Fixed stale catalog options and save focus race; CI preview configured, remote unrun.

### T169. Verify PostgreSQL queue concurrency and worker fencing

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T014, T082.

**Результаты/файлы:** `backend/tests/test_postgres_jobs.py`.

**Шаги:**

1. Verify PostgreSQL queue concurrency and worker fencing.
2. Record successful, boundary and refusal cases on an isolated runtime.

**Критерии закрытия:**

- Concurrent enqueue/claim and SKIP LOCKED work on migrated PostgreSQL; expired owners and disabled jobs cannot publish; independent worker processes cannot claim one source twice..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b10-runtime.md](../docs/evidence/b10-runtime.md) — B10:8 native PostgreSQL queue/fencing cases passed; independent spawn workers claim once and SKIP LOCKED completes while another transaction owns the row.

### T170. Verify atomic PostgreSQL snapshot publication

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T014, T079, T169.

**Результаты/файлы:** `backend/tests/test_postgres_publishing.py`.

**Шаги:**

1. Verify atomic PostgreSQL snapshot publication.
2. Record successful, boundary and refusal cases on an isolated runtime.

**Критерии закрытия:**

- Concurrent imports deduplicate on PostgreSQL; row-write failures and quarantine retain the previous pointer/history; old parser versions and raw hashes remain readable..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b10-runtime.md](../docs/evidence/b10-runtime.md) — B10:7 native PostgreSQL publication cases passed; uncommitted rows remain invisible to another reader, rollback/quarantine preserve last good pointer and crash replay deduplicates.

### T171. Rehearse PostgreSQL and raw backup restoration

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T014, T089.

**Результаты/файлы:** `scripts/rehearse_postgres_restore.py`; `docs/evidence/b10-restore.json`.

**Шаги:**

1. Rehearse PostgreSQL and raw backup restoration.
2. Record successful, boundary and refusal cases on an isolated runtime.

**Критерии закрытия:**

- A disposable PostgreSQL dump and referenced raw data restore into a new database/directory; exact manual history, ownership, idempotency, snapshot rows and raw hashes match; corrupt archives/raw fail; measured timing and quiesced-write limitation are recorded..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b10-runtime.md](../docs/evidence/b10-runtime.md) — B10:actual pg_dump/raw restoration passed;15 tables exact, ownership/history/replay/tombstone and2 raw versions preserved; corrupt archive rolls back, corrupt raw rejected. Timings and quiesced-only RPO recorded.

### T172. Serve production assets without SPA fallback on missing chunks

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T067, T168.

**Результаты/файлы:** `frontend/nginx.conf`; `frontend/tests/e2e/assets.spec.ts`.

**Шаги:**

1. Serve production assets without SPA fallback on missing chunks.
2. Record successful, boundary and refusal cases on an isolated runtime.

**Критерии закрытия:**

- Missing emitted JS/CSS return404 rather than index HTML; hashed resources are immutable while HTML revalidates; deep links and real chunk-error recovery work through nginx..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b10-runtime.md](../docs/evidence/b10-runtime.md) — B10: reproduced missing JS as HTML200, fixed nginx404/nosniff/cache policy;3 actual nginx/chunk-recovery checks passed after fresh image rebuild.

### T173. Verify Compose recreation persistence and worker recovery

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T067, T169, T170, T171, T172.

**Результаты/файлы:** `scripts/rehearse_compose.py`; `docs/evidence/b10-compose-restart.json`.

**Шаги:**

1. Verify Compose recreation persistence and worker recovery.
2. Record successful, boundary and refusal cases on an isolated runtime.

**Критерии закрытия:**

- Recreating all owned Compose services preserves exact guest/history/retry state and raw bytes in volumes; actual worker processes a queued unsupported source after recreation without fetch/publication; ports and permissions remain correct; final checks and handoff are current..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b10-runtime.md](../docs/evidence/b10-runtime.md) — B10 complete10/10:owned4-service Compose recreation preserved history/ownership/retries/raw and actual worker resumed safely. Final332 backend/0skip,92 frontend/build,72 Chromium passed; temporary resources cleaned,preview8089 retained.

### T181. Экспортировать архивные факты отдельно от ручных расчётов

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T179, T180.

**Результаты/файлы:** `backend/app/source_api.py`; `frontend/src/components/ArchiveDirections.tsx`.

**Шаги:**

1. Версионировать owner-only архивный экспорт с provenance.
2. Не включать публичный код,HMAC или cookie в файл.

**Критерии закрытия:**

- Файл воспроизводит сохранённые факты и их снимки.
- Чужие записи и идентификаторы отсутствуют;ручной JSON не меняется.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 22/30:separate owner-only archive-facts-v1 export and actual JSON download verified;1nativePG+1Chromium passed,currentbuild,no identity/access fields.

### T182. Восстановить SGU-архив и подписки из PostgreSQL/raw backup

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T179, T178, T033.

**Результаты/файлы:** `scripts/rehearse_postgres_restore.py`; `docs/evidence/restore.md`.

**Шаги:**

1. Сделать quiesced dump реального формата с обезличенными строками.
2. Сверить все таблицы,историю,ownership,HMAC-key continuity и raw hashes.

**Критерии закрытия:**

- Восстановление проверено чтением и повтором операций.
- Повреждённый backup отвергается;время и границы локального опыта записаны.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 23/30:actual SGU573x2 PostgreSQL/raw restore exact across17tables;ownership,history,key continuity,replay/tombstones and corruption refusal passed,measured localtimings.

### T183. Проверить архивные данные при смене гостя между вкладками

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T025, T021.

**Результаты/файлы:** `frontend/tests/e2e/source-session.spec.ts`.

**Шаги:**

1. Проверить скрытие карточек/истории и поздних ответов.
2. Явная синхронизация показывает только нового владельца.

**Критерии закрытия:**

- Старые факты не появляются после reset в другой вкладке.
- Нет скрытого POSTsession при смене гостя.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 26/30:2nativeAPI/Chromium multi-tab archive privacy cases passed;old facts/history and delayed replies hidden,newowneronly after explicitsync,no automaticbootstrap.

### T184. Проверить текущий архивный контур в локальных контейнерах

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T035, T181, T023.

**Результаты/файлы:** `docs/evidence/b11-container.json`; `docs/RUNBOOK.md`.

**Шаги:**

1. Собрать текущие образы и применить миграции в owned Compose.
2. Проверить API/UI,nginx,перезапуск и сохранность архива без нового HTTPfetch.

**Критерии закрытия:**

- Фактическая схема/снимок сохранены после recreate.
- БД/worker не выставлены наружу;версия и ограничения записаны.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 27/30:current0007 containers preserve actual573-row archive acrossrecreate,noexternalfetch;2nginxchecks andowned4service worker/raw/persistence rehearsal passed.

### T185. Измерить чтение573-строчного архива с20подписками

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T177, T179.

**Результаты/файлы:** `scripts/measure_archive.py`; `docs/evidence/b11-archive-performance.json`.

**Шаги:**

1. Задать локальный профиль до измерения.
2. Замерить p95,ошибки иSQLзапросы при параллельных чтениях.

**Критерии закрытия:**

- Есть реальные размеры/стенд/измерения,не пустаяБД.
- Узкие места измерены;результат не выдан за broadstaging нагрузку.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 28/30:573rows/20subscriptions/4readers measured;p95 202.24→30.90ms,SQL11120→680,80x200;23+1nativePG cases passed;localonly.

### T186. Добавить offline аудит целостности архива и ключа сопоставления

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T029, T033, T179.

**Результаты/файлы:** `backend/app/sources/audit.py`; `backend/tests/test_source_audit.py`.

**Шаги:**

1. Сверить rawSHA256,normalizedhash,строки/места/адаптер безHTTP.
2. Отвергать повреждение или другой identitykey безопасным кодом.

**Критерии закрытия:**

- Аудит не меняет БД,историю илиsourceenabled.
- Коды кандидатов/ключ/raw не попадают в отчёт.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b11-progress.md](../docs/evidence/b11-progress.md) — B11 29/30:readonly raw/normalized/key-continuity audit implemented;3nativePG+3SQLite passed;actual private573-row archive audited cleanly withoutHTTP or identifieroutput.

### T189. Проверить полный локальный путь двух источников до рубежа70%

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T036, T040, T037, T038, T039.

**Результаты/файлы:** `docs/evidence/b12-milestone70.json`; `frontend/tests/e2e/`.

**Шаги:**

1. Собрать текущий контур и пройти source/lookup/confirm/scenario/change/history/seen.
2. Проверить два владельца,отказ/восстановление,архивные даты и честное покрытие.

**Критерии закрытия:**

- Все критерии MILESTONE_70 подтверждены текущими проверками.
- Локальная приёмка не закрывает HTTPSstaging/live/production gates.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b12-milestone70.json](../docs/evidence/b12-milestone70.json) — All six predeclared functional criteria met;current full tests/nativePG/local Docker,two-source browser path,exact restore/private audit verified. Production/live gates remain open.

### T210. Установить причины ошибок и отмен GitHub Actions

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T209.

**Результаты/файлы:** `.github/workflows/ci.yml`; `frontend/`; `docs/evidence/`.

**Шаги:**

1. Логи/annotations реального run сопоставлены с точным commit; ошибки и timeout различимы.

**Критерии закрытия:**

- Логи/annotations реального run сопоставлены с точным commit; ошибки и timeout различимы.
- Общая Definition of Done выполнена; покрытие России не увеличивается от CI исправления..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b18-ci-diagnosis.md](../docs/evidence/b18-ci-diagnosis.md) — Exact remote logs: mobile confirmation focus failure, Firefox2Tab-focus failures, Azure apt mirror22m35s download; checks15m andFirefox25m timeout. Backend666 andcontainers passed.

### T211. Исправить сбой мобильного браузерного сценария

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T210.

**Результаты/файлы:** `.github/workflows/ci.yml`; `frontend/`; `docs/evidence/`.

**Шаги:**

1. Ошибка воспроизведена и затронутые проверки проходят с прежними гарантиями продукта.

**Критерии закрытия:**

- Ошибка воспроизведена и затронутые проверки проходят с прежними гарантиями продукта.
- Общая Definition of Done выполнена; покрытие России не увеличивается от CI исправления..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b18-confirmation-focus.md](../docs/evidence/b18-confirmation-focus.md) — Confirmation focus moved to committed preview layout effect; old8cases reproduce3failures, fixed63source cases passed acrossChromium/Firefox/mobileChromium,0skip;116Vitest/build passed.

### T212. Устранить причины зависаний CI и Firefox

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T211.

**Результаты/файлы:** `.github/workflows/ci.yml`; `frontend/`; `docs/evidence/`.

**Шаги:**

1. Runner/установка/браузерные зависания исправлены на основании логов без скрытия ошибок.

**Критерии закрытия:**

- Runner/установка/браузерные зависания исправлены на основании логов без скрытия ошибок.
- Общая Definition of Done выполнена; покрытие России не увеличивается от CI исправления..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b18-runner-and-firefox.md](../docs/evidence/b18-runner-and-firefox.md) — Firefox scroll-container Tab stop corrected;27keyboard/catalog checks passed across3browser projects,0skip. Ubuntu24.04 pinned; Azure apt mirror replaced with official HTTPS archive; install bounded5min, overalltimeouts unchanged; bash/YAML checks pass. Hosted verification T214.

### T213. Проверить исправленный workflow и диагностику

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T212.

**Результаты/файлы:** `.github/workflows/ci.yml`; `frontend/`; `docs/evidence/`.

**Шаги:**

1. Сохраняются результаты обоих browser stages; локальные затронутые проверки и config checks проходят.

**Критерии закрытия:**

- Сохраняются результаты обоих browser stages; локальные затронутые проверки и config checks проходят.
- Общая Definition of Done выполнена; покрытие России не увеличивается от CI исправления..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b18-ci-reports.md](../docs/evidence/b18-ci-reports.md) — Separate broad/source JUnit outputs preserved;2+2CI-mode browser cases passed with2workers.116Vitest,current build,63source+27keyboard checks passed;YAML/bash validation passed. Backend artifact uploaded before browser install; unique project/attempt artifacts always retained.

### T214. Проверить зелёный удалённый запуск и передать состояние

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T213.

**Результаты/файлы:** `.github/workflows/ci.yml`; `frontend/`; `docs/evidence/`.

**Шаги:**

1. Исправления отправлены, все шесть заданий текущего CI проверены по фактическому результату.

**Критерии закрытия:**

- Исправления отправлены, все шесть заданий текущего CI проверены по фактическому результату.
- Общая Definition of Done выполнена; покрытие России не увеличивается от CI исправления..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/b18-remote-ci.json](../docs/evidence/b18-remote-ci.json) — All6hosted CI jobs passed;666backend nativePG, all4browser projects broad+source stages andcontainer/backup checks verified from10JUnit reports/6artifacts. Original mobile confirmation/FirefoxTab failures fixed; slow Azure apt mirror removed. Local116Vitest/build,63source+27keyboard+4CI-mode+6actualNginx cases passed;demo frontend updated without key/volumes/API changes.
- [docs/evidence/b18-integration.md](../docs/evidence/b18-integration.md) — Exact original/fixed run IDs, local regression, installed browser durations, separate reports, unchanged coverage and cleanup.

### T236. Final UI quality verification at requested viewport widths

**Статус:** `done` · **Приоритет:** P1 · **Размер:** M.

**Зависимости:** T235.

**Результаты/файлы:** `frontend/tests/e2e/final-ui-quality.spec.ts`; `docs/evidence/final-ui-quality.md`.

**Шаги:**

1. Record baseline.
2. Inspect requested widths and both themes.
3. Verify states keyboard and CSS.
4. Fix confirmed defects.
5. Run checks and report limitations and diff.

**Критерии закрытия:**

- Actual production-browser rendering inspected at375/768/1280/1920 in both themes; no page overflow or broken cards/forms; meaningful focus and state checks.
- Only evidence-based fixes; audit conflicting/redundant CSS and shared-component regressions; preserve backend/business/FSD and prior work.
- typecheck/lint/build and relevant tests; report passed/unavailable checks,remaining issues and actual git diff --shortstat; no commits/push or temporary service-directory scripts.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/final-ui-quality.md](../docs/evidence/final-ui-quality.md) — Production Chromium at375/768/1280/1920 light/dark; actual PNGs viewed. Fixed22.39px summary target to44px and redundant control CSS. typecheck/lint/build/format/architecture;150unit;72matrix+50regression Chromium passed/2API-fixture skips. Firefox Target crashed before page;WebKit/live API unavailable. No backend/business/FSD/commits/push.

### T237. Fix cross-browser CI regressions after UI changes

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T236.

**Результаты/файлы:** `frontend/tests/e2e/`; `docs/evidence/ui-ci-regressions.md`.

**Шаги:**

1. Reproduce failures.
2. Identify fixture and focus changes.
3. Correct regression tests or application defects.
4. Verify with isolated API.
5. Record limitations.

**Критерии закрытия:**

- Reproduce the reported Firefox failures where environment permits; separate incomplete mocks and outdated assertions from application defects.
- Preserve session privacy checks and validation; no timeout increases/skips to hide failures.
- Run relevant cross-browser/API regressions and frontend checks;record exact results and unavailable checks.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/ui-ci-regressions.md](../docs/evidence/ui-ci-regressions.md) — Reproduced exact Firefox detached-button timeout: unmocked history401;corrected five E2E fixtures/selectors/cache freshness expectations without production changes/timeouts/skips. Full Firefox254passed/37existing skips;targeted39Chromium+39Firefox;final4reset cases passed each;150unit and typecheck/lint/build/format/architecture. Fresh Ubuntu CI unverified;no push.

### T253. Unify production API DTO errors and route states for React v3

**Статус:** `done` · **Приоритет:** P0 · **Размер:** L.

**Зависимости:** T252.

**Результаты/файлы:** `frontend/src/shared/`; `docs/evidence/v3-production-api.md`.

**Шаги:**

1. Inventory contracts and routes.
2. Unify transport DTO session errors.
3. Connect existing entities.
4. Align live demo and resource states.
5. Verify routes and commit.

**Критерии закрытия:**

- All29 routes smoke without runtime errors; live/demo explicit and no fallback to fake data or success.
- Shared validated DTO transport session errors and retry; retain v3 CSS and catalog; unsupported APIs deferred separately.
- typecheck lint build Playwright smoke; evidence commit and verification instructions.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/v3-production-api.md](../docs/evidence/v3-production-api.md) — Commit69275e6: shared HTTP/validated DTO/session/resource states;live existing catalog/subscriptions/groups/lookup-confirm/changes/coverage;explicit unsupported/demo. typecheck/lint/build exit0;84Chromium passed including29routes and16API tests. CSS/backend/migrations unchanged;PG T250 and hosted CI unverified;no push. Strict204 write acknowledgement regression passed.

### T254. Run complete local Compose PostgreSQL stack with safe startup smoke

**Статус:** `done` · **Приоритет:** P0 · **Размер:** L.

**Зависимости:** T253.

**Результаты/файлы:** `compose.yaml`; `scripts/local_smoke.py`; `README.md`; `docs/evidence/local-postgresql.md`.

**Шаги:**

1. Audit Compose environment and persistent mounts.
2. Start real Docker PostgreSQL safely.
3. Verify migrations and catalog import/API.
4. Provide one reproducible smoke and README.
5. Test persistence and record evidence commit.

**Критерии закрытия:**

- Actual Docker Compose backend frontend PostgreSQL startup; current=head;catalog import and API verified on PostgreSQL only.
- Keep existing project volumes and applied migrations;backup before upgrade and verify stored history across restart;no volume deletion or fabricated product values.
- One documented startup smoke command for new contributor;automated checks,commit and evidence with exact limitations.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/evidence/local-postgresql.md](../docs/evidence/local-postgresql.md) — S203 actual existing-volume Docker Compose full command including build exit0;PG17.11/current=head0011/alembic check/import twice/API/SPA;two-snapshot history and mount identities survive recreate.11native PG tests+5launcher unit tests passed;Chromium390/1440 viewed. Alembic metadata fix881422f,applied migrations intact. No SQLite substitute,push or release-gate claim.

### T260. KAN-238: аудит существующего CI

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** нет.

**Результаты/файлы:** `docs/KAN-238-CI-REPORT.md`.

**Шаги:**

1. Проверены workflow, runner, PostgreSQL guard, миграции, ETL и hosted baseline.
2. До реализации сохранена таблица недостатков и работающих проверок.

**Критерии закрытия:**

- Проверены workflow, runner, PostgreSQL guard, миграции, ETL и hosted baseline.
- До реализации сохранена таблица недостатков и работающих проверок.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-238-CI-REPORT.md](../docs/KAN-238-CI-REPORT.md) — Audit completed before implementation; baseline hosted run 43084056846 success at e4d59b4. Confirmed gaps and preserved checks recorded in report.

### T261. KAN-238: frontend CI и диагностика

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T260.

**Результаты/файлы:** `docs/KAN-238-CI-REPORT.md`.

**Шаги:**

1. npm ci, lint, typecheck, build и npm test проходят на текущем коде.
2. Ошибки runner не скрываются; отчёты доступны; все 29 маршрутов сохранены.

**Критерии закрытия:**

- npm ci, lint, typecheck, build и npm test проходят на текущем коде.
- Ошибки runner не скрываются; отчёты доступны; все 29 маршрутов сохранены.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-238-CI-REPORT.md](../docs/KAN-238-CI-REPORT.md) — npm ci/lint/typecheck/build passed; 94 Chromium tests passed including all 29 routes; 3 child shutdown tests passed. JUnit, screenshot, trace and bounded teardown added. Hosted proof tracked separately in T264.

### T262. KAN-238: PostgreSQL и Alembic

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T260.

**Результаты/файлы:** `docs/KAN-238-CI-REPORT.md`.

**Шаги:**

1. Backend pytest проходит с --require-postgres на изолированном PostgreSQL.
2. Отдельная чистая БД: upgrade head, совпадение heads, alembic check; отказ даёт ненулевой exit code.

**Критерии закрытия:**

- Backend pytest проходит с --require-postgres на изолированном PostgreSQL.
- Отдельная чистая БД: upgrade head, совпадение heads, alembic check; отказ даёт ненулевой exit code.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-238-CI-REPORT.md](../docs/KAN-238-CI-REPORT.md) — Linux Python3.12/PostgreSQL17 full pytest:774 passed,1 explicit missing-dataset skip; required native guard passed.32 migration tests passed; separate clean database upgrade/head0011/check passed;17 repository tests passed; actionlint and pip check passed.

### T263. KAN-238: существующие ML/ETL проверки

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T260.

**Результаты/файлы:** `docs/KAN-238-CI-REPORT.md`.

**Шаги:**

1. Проверены fixture ETL, форматы, воспроизводимость и временная граница.
2. Отсутствующие датасет и обученная модель явно указаны в CI и отчёте.

**Критерии закрытия:**

- Проверены fixture ETL, форматы, воспроизводимость и временная граница.
- Отсутствующие датасет и обученная модель явно указаны в CI и отчёте.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-238-CI-REPORT.md](../docs/KAN-238-CI-REPORT.md) — Existing offline ETL suites:55 passed,1 explicit missing-MICCEDU-dataset skip. Reproducibility, malformed input and temporal-leakage cases preserved. Separate required etl job, artifact availability summary and JUnit/log added; actionlint passed. No trained model or backtest claimed.

### T264. KAN-238: негативные hosted проверки, PR и отчёт

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T260.

**Результаты/файлы:** `docs/KAN-238-CI-REPORT.md`; `docs/evidence/kan-238-ci.json`.

**Шаги:**

1. NEG-01–04 подтверждены hosted run, SHA и артефактами в изолированных ветках.
2. Создан PR в main; последний SHA проверен hosted CI; основной PR без искусственных ошибок.
3. Русский отчёт содержит evidence, ограничения и рекомендации branch protection.

**Критерии закрытия:**

- NEG-01–04 подтверждены hosted run, SHA и артефактами в изолированных ветках.
- Создан PR в main; последний SHA проверен hosted CI; основной PR без искусственных ошибок.
- Русский отчёт содержит evidence, ограничения и рекомендации branch protection.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-238-CI-REPORT.md](../docs/KAN-238-CI-REPORT.md) — PR12 opened without merge. Hosted push43277687053/PR43277802246 success at4f60dad; NEG01frontend43277814063,NEG02backend43277831614,NEG03migrations43277851703 failed as expected; NEG04archives downloaded and XML/log/screenshot/trace verified. Report and compact evidence saved; final documentation push checks must be observed.

### T265. KAN-212: Audit and route matrix

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** нет.

**Результаты/файлы:** `docs/KAN-212-FRONTEND-REPORT.md`.

**Шаги:**

1. Audit current main and merged PRs before implementation.
2. Record all 29 routes with API, DTO, mode, errors, navigation and minimal fixes.
3. Run existing browser baseline.

**Критерии закрытия:**

- Audit current main and merged PRs before implementation.
- Record all 29 routes with API, DTO, mode, errors, navigation and minimal fixes.
- Run existing browser baseline.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-212-FRONTEND-REPORT.md](../docs/KAN-212-FRONTEND-REPORT.md) — Audit completed before code: current main07526c3 and merged PR12/11/9 checked, 29-route API/DTO/mode/navigation matrix and ten minimal fixes recorded. npm ci and baseline94 browser tests passed; SQLite browser stand is not PostgreSQL evidence.

### T266. KAN-212: API and DTO validation

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T265.

**Результаты/файлы:** `docs/KAN-212-FRONTEND-REPORT.md`.

**Шаги:**

1. Reuse one request client and typed runtime decoders.
2. Reject malformed JSON, dates, IDs, numeric and nested DTO fields without defaults.
3. Verify timeout, cancellation, HTTP statuses and session races.

**Критерии закрытия:**

- Reuse one request client and typed runtime decoders.
- Reject malformed JSON, dates, IDs, numeric and nested DTO fields without defaults.
- Verify timeout, cancellation, HTTP statuses and session races.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-212-FRONTEND-REPORT.md](../docs/KAN-212-FRONTEND-REPORT.md) — Reused request and concrete decoders; safe JSON/Headers, strict dates/IDs/ranks/nested fields, provenance and scoped catalog validation. 27 unit tests and full121 passed; lint/typecheck/build pass. First run had transient browser ERR_NO_BUFFER_SPACE before app; unchanged repeat passed.

### T267. KAN-212: Server state and live integration

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T265.

**Результаты/файлы:** `docs/KAN-212-FRONTEND-REPORT.md`.

**Шаги:**

1. Clear private state on session changes and cancel stale mutations.
2. Preserve retry/stale/empty/error semantics and isolate demo.
3. Paginate imported groups and expose metadata errors.

**Критерии закрытия:**

- Clear private state on session changes and cancel stale mutations.
- Preserve retry/stale/empty/error semantics and isolate demo.
- Paginate imported groups and expose metadata errors.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-212-FRONTEND-REPORT.md](../docs/KAN-212-FRONTEND-REPORT.md) — Session-aware resource invalidation and cancelled private mutations implemented; explicit guest recovery, cross-tab expiry without loops, bounded group pagination and metadata errors verified. lint/typecheck and131 tests passed. PostgreSQL local_smoke exit0 with backup and persistence; frontend against PG next.

### T268. KAN-212: Navigation and route boundaries

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T265.

**Результаты/файлы:** `docs/KAN-212-FRONTEND-REPORT.md`.

**Шаги:**

1. Preserve all 29 routes and additional existing aliases.
2. Verify dynamic IDs, unknown auth and malformed URLs, history and query/hash.
3. Fix saved subscription links without changing v3 design.

**Критерии закрытия:**

- Preserve all 29 routes and additional existing aliases.
- Verify dynamic IDs, unknown auth and malformed URLs, history and query/hash.
- Fix saved subscription links without changing v3 design.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-212-FRONTEND-REPORT.md](../docs/KAN-212-FRONTEND-REPORT.md) — All29 direct/reload/internal/Back/Forward checks and dynamic/auth/unknown/query/hash boundaries passed; saved link and URL filters fixed. Full143 tests pass, lint/typecheck pass. Malformed percent encoding tested through SPA because Vite rejects it before React; nginx HTTP check remains T269.

### T269. KAN-212: Regression and review delivery

**Статус:** `review` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T265.

**Результаты/файлы:** `docs/KAN-212-FRONTEND-REPORT.md`.

**Шаги:**

1. Pass npm ci/lint/typecheck/build/test and 29-route browser smoke.
2. Verify existing APIs against PostgreSQL and inspect desktop/mobile screenshots.
3. Publish technical report and reviewable PR with hosted checks; owner review remains required.

**Критерии закрытия:**

- Pass npm ci/lint/typecheck/build/test and 29-route browser smoke.
- Verify existing APIs against PostgreSQL and inspect desktop/mobile screenshots.
- Publish technical report and reviewable PR with hosted checks; owner review remains required.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-212-FRONTEND-REPORT.md](../docs/KAN-212-FRONTEND-REPORT.md) — Final public401 recovery fix verified:147 local tests against PostgreSQL,116 fresh visual pairs equal,58 nginx openings; public401 GET retry creates0 sessions. Initial dc5205c hosted four jobs success, final source SHA/latest checks recorded in PR13. Owner acceptance pending; no merge, user history/volumes retained.
- [docs/evidence/kan-212-stabilization.json](../docs/evidence/kan-212-stabilization.json) — Compact hosted/local/visual/PostgreSQL/nginx/history evidence. Final documentation-only checks are tracked in PR13 description. Owner acceptance pending.

### T270. KAN-214: Baseline and merged PR audit

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** нет.

**Результаты/файлы:** `docs/KAN-214-AUTH.md`.

**Шаги:**

1. Record current main and merged KAN-212/CI PRs; verify clean isolated branch.

**Критерии закрытия:**

- Record current main and merged KAN-212/CI PRs; verify clean isolated branch.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-AUTH.md](../docs/KAN-214-AUTH.md) — Verified main3708d90 and merged PR13/12 via GitHub; isolated clean branch, roadmap check passed. No runtime code changed.

### T271. KAN-214: Guest lifecycle and integration audit

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T270.

**Результаты/файлы:** `docs/KAN-214-AUTH.md`.

**Шаги:**

1. Inspect backend/frontend/infrastructure files requested by KAN-214.
2. Document ownership, destructive guest reset, KAN-212 reuse and external dependencies.

**Критерии закрытия:**

- Inspect backend/frontend/infrastructure files requested by KAN-214.
- Document ownership, destructive guest reset, KAN-212 reuse and external dependencies.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-AUTH.md](../docs/KAN-214-AUTH.md) — Audited requested backend/frontend/infra and guest ownership cascade; recorded KAN-212 reuse, proxy/SMTP constraints. Baseline session/API tests recorded below.

### T272. KAN-214: Security architecture and API contracts

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T271.

**Результаты/файлы:** `docs/KAN-214-AUTH.md`.

**Шаги:**

1. Document threat model, cookies, CSRF, rotation/replay and transaction locking.
2. Specify endpoints, expiry, errors, rate limits and six PR review sequence.

**Критерии закрытия:**

- Document threat model, cookies, CSRF, rotation/replay and transaction locking.
- Specify endpoints, expiry, errors, rate limits and six PR review sequence.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-AUTH.md](../docs/KAN-214-AUTH.md) — Documented threat model, six-table schema, endpoint DTO/status/CSRF/rate contracts, rotation lock ordering, email dependencies and six review boundaries; sources checked against RFC/OWASP/library docs.

### T273. KAN-214: PostgreSQL account foundation

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T272.

**Результаты/файлы:** `docs/KAN-214-AUTH.md`.

**Шаги:**

1. Add independent user/session/refresh/action-token/rate-budget models and additive migration.
2. Prove native PostgreSQL uniqueness races, FK integrity and guest history preservation.

**Критерии закрытия:**

- Add independent user/session/refresh/action-token/rate-budget models and additive migration.
- Prove native PostgreSQL uniqueness races, FK integrity and guest history preservation.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-AUTH.md](../docs/KAN-214-AUTH.md) — Six independent account tables and additive0012 implemented.39 tests pass incl native PG uniqueness race, constraints, cleanup/replay retention, guest preservation and standalone schema agreement; no user DB/volume touched.

### T274. KAN-214: Password security foundation

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T273.

**Результаты/файлы:** `docs/KAN-214-AUTH.md`.

**Шаги:**

1. Pin Argon2id library with RFC9106 low-memory parameters and rehash support.
2. Test email/password policy, unique salts, invalid hashes and guest regression.

**Критерии закрытия:**

- Pin Argon2id library with RFC9106 low-memory parameters and rehash support.
- Test email/password policy, unique salts, invalid hashes and guest regression.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-AUTH.md](../docs/KAN-214-AUTH.md) — Argon2id RFC9106 production parameters, input policy, bounded capacity, dummy verification, rehash and purpose-separated tokens implemented;52 primitive/guest/API tests pass,pip check clean. PR1 awaiting review; PR2-6 not implemented.
- [docs/evidence/kan-214-foundation.json](../docs/evidence/kan-214-foundation.json) — Final local backend763/0skip,frontend147,migrations0012 clean,ETL55+1 dataset skip; PR14 foundation only, owner review pending.

### T275. KAN-214: Registration and login API

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T274.

**Результаты/файлы:** `docs/KAN-214-AUTH.md`.

**Шаги:**

1. Implement PR2 acceptance from KAN-214 specification with PostgreSQL tests and review.

**Критерии закрытия:**

- Implement PR2 acceptance from KAN-214 specification with PostgreSQL tests and review.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR2.md](../docs/KAN-214-PR2.md) — PR15 ready for owner review; source7a90d60 hosted run43413656989 all4 jobs success:backend820/0skip,frontend147,ETL55+1 explicit dataset skip,migrations0012 check. Exact latest documentation SHA/checks in PR15 description. No merge; auth defaults disabled, SMTP/full lifecycle remain later PRs.
- [docs/KAN-214-PR3.md](../docs/KAN-214-PR3.md) — User requested PR3; GitHub confirms PR15 merged into main5cddc54 with all4 hosted jobs green.

### T276. KAN-214: Refresh logout and CSRF

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T275.

**Результаты/файлы:** `docs/KAN-214-AUTH.md`.

**Шаги:**

1. Implement PR3 acceptance from KAN-214 specification with concurrency/security tests and review.

**Критерии закрытия:**

- Implement PR3 acceptance from KAN-214 specification with concurrency/security tests and review.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR3.md](../docs/KAN-214-PR3.md) — PR3 backend refresh/logout/CSRF lifecycle implemented; local native-PG867/0skip,security47,frontend147,migrations0012 check pass. Final SHA/hosted run/results recorded in review PR for feat/kan-214-session-lifecycle. Owner acceptance required; no SMTP/frontend/full KAN-214 claim.
- [docs/KAN-214-PR4.md](../docs/KAN-214-PR4.md) — User requested PR4; GitHub confirms PR16 merged/main d63a208; hosted867/0skip and all4 jobs success.

### T277. KAN-214: Email verification and recovery

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T276.

**Результаты/файлы:** `docs/KAN-214-AUTH.md`.

**Шаги:**

1. Implement PR4 acceptance; test transport is isolated; production delivery remains external gate.

**Критерии закрытия:**

- Implement PR4 acceptance; test transport is isolated; production delivery remains external gate.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR4.md](../docs/KAN-214-PR4.md) — PR4 SMTP/verification/recovery implemented. Local native-PG976/0skip,action/security83,mail/config35,frontend147,migrations0012 passed. Final SHA/PR/verified hosted results in review PR description. Actual SMTP inbox delivery remains an explicit external acceptance gate; no merge/production readiness claim.
- [docs/KAN-214-PR5.md](../docs/KAN-214-PR5.md) — User requested PR5; GitHub confirms PR17 merged/main3035f5e. Backend976/0skip and all4 hosted jobs green; real email delivery gate remains unaccepted.

### T278. KAN-214: React v3 account integration

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T277.

**Результаты/файлы:** `docs/KAN-214-AUTH.md`.

**Шаги:**

1. Implement PR5 acceptance preserving API client guest epoch, 29 routes and v3 visuals.

**Критерии закрытия:**

- Implement PR5 acceptance preserving API client guest epoch, 29 routes and v3 visuals.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR5.md](../docs/KAN-214-PR5.md) — PR5 React account integration implemented; local frontend175, native-PG browser2, backend976/0skip, visual108/108, migrations0012 passed. Final SHA/review PR/hosted results in PR description; owner review/merge and production delivery remain unaccepted.
- [docs/KAN-214-PR6.md](../docs/KAN-214-PR6.md) — PR18 owner-merged into main12c78e4; final source6ae95ad/run43474248315 all4 jobs green, backend976/0skip and frontend175. Delivery/production gate remains unaccepted.

### T279. KAN-214: Final security and acceptance

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T278.

**Результаты/файлы:** `docs/KAN-214-AUTH.md`.

**Шаги:**

1. Implement PR6 acceptance: PostgreSQL E2E/security/browser/visual/hosted CI and owner review.
2. Require real email delivery or explicit documented owner exception.

**Критерии закрытия:**

- Implement PR6 acceptance: PostgreSQL E2E/security/browser/visual/hosted CI and owner review.
- Require real email delivery or explicit documented owner exception.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

### T280. KAN-214 PR2: Merged baseline and PR2 boundaries

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T274.

**Результаты/файлы:** `docs/KAN-214-PR2.md`.

**Шаги:**

1. Verify merged PR14 and clean main branch.
2. Specify implemented API, mail boundary, CSRF prerequisite and verification evidence.

**Критерии закрытия:**

- Verify merged PR14 and clean main branch.
- Specify implemented API, mail boundary, CSRF prerequisite and verification evidence.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR2.md](../docs/KAN-214-PR2.md) — Verified PR14 merged/main494d270; PR2 acceptance and safe mail/CSRF/disabled-rollout boundaries recorded before implementation.

### T281. KAN-214 PR2: Persistent auth rate budgets

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T280.

**Результаты/файлы:** `docs/KAN-214-PR2.md`.

**Шаги:**

1. Atomic committed HMAC-keyed database counters before hashing/mail.
2. Native PG concurrent limits, restart persistence, windows and no forwarded-header trust.

**Критерии закрытия:**

- Atomic committed HMAC-keyed database counters before hashing/mail.
- Native PG concurrent limits, restart persistence, windows and no forwarded-header trust.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR2.md](../docs/KAN-214-PR2.md) — Persistent HMAC-keyed atomic database budgets implemented; native PG concurrency/restart/window/soft-policy tests and existing config tests passed (results recorded in report).

### T282. KAN-214 PR2: Registration and CSRF prerequisite

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T281.

**Результаты/файлы:** `docs/KAN-214-PR2.md`.

**Шаги:**

1. Bounded strict DTOs and synchronizer context; preserve Origin/custom header.
2. Create normalized unverified user and purpose-hashed action transactionally; generic duplicate response.
3. No mail port means503 without false success; injectable isolated test transport only.

**Критерии закрытия:**

- Bounded strict DTOs and synchronizer context; preserve Origin/custom header.
- Create normalized unverified user and purpose-hashed action transactionally; generic duplicate response.
- No mail port means503 without false success; injectable isolated test transport only.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR2.md](../docs/KAN-214-PR2.md) — Registration/CSRF implemented;20 native PG tests pass including real persistence, duplicate race, token hashes, redacted validation, CSRF/Origin and mail failure/suppression. No real SMTP or automatic email verification.

### T283. KAN-214 PR2: Login and current account session

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T282.

**Результаты/файлы:** `docs/KAN-214-PR2.md`.

**Шаги:**

1. Real Argon2id verification, uniform credential denial and user lock recheck.
2. Independent access credential, session CSRF rotation and current-account dependency.
3. Expiry/revocation/status checked server-side; no guest mutation or refresh issuance.

**Критерии закрытия:**

- Real Argon2id verification, uniform credential denial and user lock recheck.
- Independent access credential, session CSRF rotation and current-account dependency.
- Expiry/revocation/status checked server-side; no guest mutation or refresh issuance.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR2.md](../docs/KAN-214-PR2.md) — Real login/current-account sessions implemented;25 native PG login/HTTP security tests pass including race rechecks, CSRF isolation, production cookies, guest preservation, rate persistence and secret redaction. Refresh/logout/SMTP remain later PRs; auth disabled by default.

### T284. KAN-214 PR2: PR2 regression and review delivery

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T283.

**Результаты/файлы:** `docs/KAN-214-PR2.md`.

**Шаги:**

1. Native PG registration/login/CSRF/rate/concurrency/guest tests.
2. Full backend, migration, frontend and hosted checks; reviewable PR, no merge.
3. Document unfinished refresh/logout/email delivery and safe disabled-by-default rollout.

**Критерии закрытия:**

- Native PG registration/login/CSRF/rate/concurrency/guest tests.
- Full backend, migration, frontend and hosted checks; reviewable PR, no merge.
- Document unfinished refresh/logout/email delivery and safe disabled-by-default rollout.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR2.md](../docs/KAN-214-PR2.md) — PR15 ready for owner review; source7a90d60 hosted run43413656989 all4 jobs success:backend820/0skip,frontend147,ETL55+1 explicit dataset skip,migrations0012 check. Exact latest documentation SHA/checks in PR15 description. No merge; auth defaults disabled, SMTP/full lifecycle remain later PRs.
- [docs/KAN-214-PR3.md](../docs/KAN-214-PR3.md) — User requested PR3; GitHub confirms PR15 merged into main5cddc54 with all4 hosted jobs green.

### T285. KAN-214 PR3: Merged baseline and lifecycle acceptance

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T275.

**Результаты/файлы:** `docs/KAN-214-PR3.md`.

**Шаги:**

1. Confirm merged PR15/current main, isolated branch and PR2 acceptance.
2. Specify refresh/logout/CSRF/replay and native PG checks before implementation.

**Критерии закрытия:**

- Confirm merged PR15/current main, isolated branch and PR2 acceptance.
- Specify refresh/logout/CSRF/replay and native PG checks before implementation.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR3.md](../docs/KAN-214-PR3.md) — Confirmed PR15 merged/main5cddc54; PR2 accepted, lifecycle/CSRF/locking/replay/logout and real PostgreSQL acceptance documented before implementation.

### T286. KAN-214 PR3: Refresh rotation and expiry

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T285.

**Результаты/файлы:** `docs/KAN-214-PR3.md`.

**Шаги:**

1. Mint independent refresh at login; server checks user/session/credential deadlines.
2. Atomic user/session/refresh/context locking, one rotation, durable family revocation on replay.
3. Access-expired classification and session-bound CSRF restoration without creating guests.

**Критерии закрытия:**

- Mint independent refresh at login; server checks user/session/credential deadlines.
- Atomic user/session/refresh/context locking, one rotation, durable family revocation on replay.
- Access-expired classification and session-bound CSRF restoration without creating guests.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR3.md](../docs/KAN-214-PR3.md) — Refresh source51975ee verified:39 native PG refresh/login/security tests pass. Rotation, bound CSRF restoration, strict replay family revocation, locks and deadlines implemented. Temporary helper was recreated after session interruption; registry updated to completed refresh and current logout.

### T287. KAN-214 PR3: Server logout and revocation

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T286.

**Результаты/файлы:** `docs/KAN-214-PR3.md`.

**Шаги:**

1. Revoke family server-side before deleting account cookies; preserve guest history.
2. Expired access logout, safe repeat with CSRF, other-session/account isolation.
3. No cookie deletion or false success on DB failure.

**Критерии закрытия:**

- Revoke family server-side before deleting account cookies; preserve guest history.
- Expired access logout, safe repeat with CSRF, other-session/account isolation.
- No cookie deletion or false success on DB failure.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR3.md](../docs/KAN-214-PR3.md) — Server logout implemented;8 native PG tests pass for revocation, exact cookie deletion, safe repeat/expired access, other-family isolation, preserved guest history, refresh/logout race and failed commit without deletion.

### T288. KAN-214 PR3: Concurrency and security regression

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T287.

**Результаты/файлы:** `docs/KAN-214-PR3.md`.

**Шаги:**

1. Native PG simultaneous refresh/replay/logout races and rollback behavior.
2. CSRF/Origin/cookie tampering, expired/revoked credentials, trusted-peer budgets and secret redaction.

**Критерии закрытия:**

- Native PG simultaneous refresh/replay/logout races and rollback behavior.
- CSRF/Origin/cookie tampering, expired/revoked credentials, trusted-peer budgets and secret redaction.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR3.md](../docs/KAN-214-PR3.md) — 47 native PostgreSQL refresh/logout/security tests passed, including CSRF/Origin, mixed credentials, deterministic bootstrap/logout and refresh races, rollback, fresh-engine revocation, durable budgets, production cookies and absolute/idle policy.

### T289. KAN-214 PR3: PR3 verification and review delivery

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T288.

**Результаты/файлы:** `docs/KAN-214-PR3.md`.

**Шаги:**

1. Full native backend, frontend regression, migrations and hosted checks.
2. Document browser coordination reserved for PR5, external SMTP/HTTPS gates and no production readiness claim.
3. Publish small reviewable PR, update STATE/TASKS/LOG, no autonomous merge.

**Критерии закрытия:**

- Full native backend, frontend regression, migrations and hosted checks.
- Document browser coordination reserved for PR5, external SMTP/HTTPS gates and no production readiness claim.
- Publish small reviewable PR, update STATE/TASKS/LOG, no autonomous merge.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR3.md](../docs/KAN-214-PR3.md) — PR3 backend refresh/logout/CSRF lifecycle implemented; local native-PG867/0skip,security47,frontend147,migrations0012 check pass. Final SHA/hosted run/results recorded in review PR for feat/kan-214-session-lifecycle. Owner acceptance required; no SMTP/frontend/full KAN-214 claim.
- [docs/KAN-214-PR4.md](../docs/KAN-214-PR4.md) — User requested PR4; GitHub confirms PR16 merged/main d63a208; hosted867/0skip and all4 jobs success.

### T290. KAN-214 PR4: Merged baseline and email acceptance

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T276.

**Результаты/файлы:** `docs/KAN-214-PR4.md`.

**Шаги:**

1. Verify merged PR16/current main, isolate branch, inspect existing lifecycle and SMTP configuration presence without exposing secrets.
2. Define provider/DB failure, anti-enumeration, token and reset revocation policy before implementation.

**Критерии закрытия:**

- Verify merged PR16/current main, isolate branch, inspect existing lifecycle and SMTP configuration presence without exposing secrets.
- Define provider/DB failure, anti-enumeration, token and reset revocation policy before implementation.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR4.md](../docs/KAN-214-PR4.md) — Verified PR16 merged/main d63a208; audited port/lifecycle and absence of SMTP fields without exposing values. Defined TLS/mail-error/oracle/token/reset-race acceptance before implementation.

### T291. KAN-214 PR4: Secure SMTP transport

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T290.

**Результаты/файлы:** `docs/KAN-214-PR4.md`.

**Шаги:**

1. TLS-only stdlib SMTP adapter, verified certificates, environment configuration without logged credentials.
2. Fixed-origin fragment links, bounded network/capacity/retry policy, explicit unavailable/refused/error behavior.
3. Isolated transport tests, no production delivery claim.

**Критерии закрытия:**

- TLS-only stdlib SMTP adapter, verified certificates, environment configuration without logged credentials.
- Fixed-origin fragment links, bounded network/capacity/retry policy, explicit unavailable/refused/error behavior.
- Isolated transport tests, no production delivery claim.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR4.md](../docs/KAN-214-PR4.md) — TLS-only SMTP transport/config implemented;33 mail/config tests pass. Verified contexts/order, MIME fragment links, bounded attempts/capacity, refusal/errors and unavailable default. No real provider/delivery or infrastructure changes.

### T292. KAN-214 PR4: Email verification and resend

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T291.

**Результаты/файлы:** `docs/KAN-214-PR4.md`.

**Шаги:**

1. Typed request/confirm APIs with existing CSRF/Origin, persistent peer/email/token budgets.
2. 24h purpose-hashed token, one use under user lock, resend invalidates older actions.
3. Generic request responses and actual mail-port invocation on eligible/ineligible addresses; test failures and races.

**Критерии закрытия:**

- Typed request/confirm APIs with existing CSRF/Origin, persistent peer/email/token budgets.
- 24h purpose-hashed token, one use under user lock, resend invalidates older actions.
- Generic request responses and actual mail-port invocation on eligible/ineligible addresses; test failures and races.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR4.md](../docs/KAN-214-PR4.md) — Verification/resend implemented;43 native PG verification+registration tests pass including real register-confirm-login, token purpose/expiry/one-use, races, uniform public responses and provider outage/failure. No automatic login or real delivery claim.

### T293. KAN-214 PR4: Password recovery and revocation

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T292.

**Результаты/файлы:** `docs/KAN-214-PR4.md`.

**Шаги:**

1. Generic request and30min purpose-hashed one-use reset, strict server password policy.
2. Reset atomically updates hash, consumes outstanding actions and revokes all user sessions/refresh; no auto login or guest/other-account mutation.
3. PostgreSQL reset/reset, reset/refresh and failure/expiry/replay tests.

**Критерии закрытия:**

- Generic request and30min purpose-hashed one-use reset, strict server password policy.
- Reset atomically updates hash, consumes outstanding actions and revokes all user sessions/refresh; no auto login or guest/other-account mutation.
- PostgreSQL reset/reset, reset/refresh and failure/expiry/replay tests.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR4.md](../docs/KAN-214-PR4.md) — Recovery/reset implemented;18 native recovery and83 combined action/security tests pass. Atomic hash/action/session/refresh update, one use, no auto-login, reset/refresh orderings, rollback, guest/other-account isolation verified. Mail/config35 passed; real delivery still unverified.

### T294. KAN-214 PR4: PR4 regression and review handoff

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T293.

**Результаты/файлы:** `docs/KAN-214-PR4.md`.

**Шаги:**

1. Full native PG backend, transport/security regression, frontend and migrations, hosted checks.
2. Document real SMTP delivery/HTTPS/egress external gate and isolated test-mail evidence.
3. Publish reviewable PR with actual test counts and no autonomous merge.

**Критерии закрытия:**

- Full native PG backend, transport/security regression, frontend and migrations, hosted checks.
- Document real SMTP delivery/HTTPS/egress external gate and isolated test-mail evidence.
- Publish reviewable PR with actual test counts and no autonomous merge.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR4.md](../docs/KAN-214-PR4.md) — PR4 SMTP/verification/recovery implemented. Local native-PG976/0skip,action/security83,mail/config35,frontend147,migrations0012 passed. Final SHA/PR/verified hosted results in review PR description. Actual SMTP inbox delivery remains an explicit external acceptance gate; no merge/production readiness claim.
- [docs/KAN-214-PR5.md](../docs/KAN-214-PR5.md) — User requested PR5; GitHub confirms PR17 merged/main3035f5e. Backend976/0skip and all4 hosted jobs green; real email delivery gate remains unaccepted.

### T295. KAN-214 PR5: Merged baseline and frontend auth audit

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T277.

**Результаты/файлы:** `docs/KAN-214-PR5.md`.

**Шаги:**

1. Confirm PR17 merge/current main, audit API/guest epoch/router/design/tests.
2. Define account transport/state/lock/secret/Demo boundaries and verification before code.

**Критерии закрытия:**

- Confirm PR17 merge/current main, audit API/guest epoch/router/design/tests.
- Define account transport/state/lock/secret/Demo boundaries and verification before code.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR5.md](../docs/KAN-214-PR5.md) — Confirmed PR17 merged/main3035f5e; audited shared client, guest ownership, UI/router and test runtime. Defined classification, independent account epoch, lock/retry/secret/Demo and real-PG browser acceptance before implementation.

### T296. KAN-214 PR5: Shared client and account state

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T295.

**Результаты/файлы:** `docs/KAN-214-PR5.md`.

**Шаги:**

1. Reuse shared/api.ts with explicit public/guest/auth/account classification and safe errors/decoders.
2. Server-verified reload, one bounded refresh, single-flight/Web Locks and separate account epoch/abort.
3. No secrets/account proof in browser storage; network unavailable is not anonymous.

**Критерии закрытия:**

- Reuse shared/api.ts with explicit public/guest/auth/account classification and safe errors/decoders.
- Server-verified reload, one bounded refresh, single-flight/Web Locks and separate account epoch/abort.
- No secrets/account proof in browser storage; network unavailable is not anonymous.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR5.md](../docs/KAN-214-PR5.md) — Shared transport/account store and whitelist DTO implemented; 32 API/DTO tests, typecheck and lint passed. Guest epoch preserved; independent account invalidation, locked refresh and nonsecret cross-tab coordination.

### T297. KAN-214 PR5: Live forms and email link routes

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T296.

**Результаты/файлы:** `docs/KAN-214-PR5.md`.

**Шаги:**

1. Real register/login/recovery/verification/resend/reset forms with loading/validation/abort and server-confirmed outcomes.
2. Consume fragments before network/render, memory-only single-use link state and no auto confirm/login.
3. Preserve v3 form/CSS and inert explicit Demo.

**Критерии закрытия:**

- Real register/login/recovery/verification/resend/reset forms with loading/validation/abort and server-confirmed outcomes.
- Consume fragments before network/render, memory-only single-use link state and no auto confirm/login.
- Preserve v3 form/CSS and inert explicit Demo.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR5.md](../docs/KAN-214-PR5.md) — Live controlled auth/email-link forms implemented; nine new browser scenarios passed, typecheck/lint passed. Preserved public error contract and lazy auth/app bootstrap; real PostgreSQL lifecycle browser scenario also passed.

### T298. KAN-214 PR5: Logout guards and browser isolation

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T297.

**Результаты/файлы:** `docs/KAN-214-PR5.md`.

**Шаги:**

1. Real server logout, private state clear/abort and cross-tab markers without credentials.
2. Minimal current-account/profile guard, preserve guest-only /app functionality and defer KAN-215/216 business logic.
3. Browser tests for errors, slow/double/cancel, expired sessions, tabs/account switch and real native-PG auth flow with isolated mailbox.

**Критерии закрытия:**

- Real server logout, private state clear/abort and cross-tab markers without credentials.
- Minimal current-account/profile guard, preserve guest-only /app functionality and defer KAN-215/216 business logic.
- Browser tests for errors, slow/double/cancel, expired sessions, tabs/account switch and real native-PG auth flow with isolated mailbox.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR5.md](../docs/KAN-214-PR5.md) — Minimal account guard/logout and cross-tab isolation verified; default172 tests, transport35, native PostgreSQL browser2 and backend976/0skip passed. Test mailbox/clock are private filesystem-only; real SMTP delivery remains unaccepted.

### T299. KAN-214 PR5: Frontend regression visual and PR handoff

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T298.

**Результаты/файлы:** `docs/KAN-214-PR5.md`.

**Шаги:**

1. Keep all29 original routes plus2 technical routes, lint/typecheck/build/tests and relevant backend/native checks.
2. Compare current v3 desktop/mobile with main; explain auth-only differences and do not rewrite baselines.
3. Publish review PR with hosted results and explicit SMTP/production/full-browser gates, no merge.

**Критерии закрытия:**

- Keep all29 original routes plus2 technical routes, lint/typecheck/build/tests and relevant backend/native checks.
- Compare current v3 desktop/mobile with main; explain auth-only differences and do not rewrite baselines.
- Publish review PR with hosted results and explicit SMTP/production/full-browser gates, no merge.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR5.md](../docs/KAN-214-PR5.md) — PR5 React account integration implemented; local frontend175, native-PG browser2, backend976/0skip, visual108/108, migrations0012 passed. Final SHA/review PR/hosted results in PR description; owner review/merge and production delivery remain unaccepted.
- [docs/KAN-214-PR6.md](../docs/KAN-214-PR6.md) — PR18 owner-merged into main12c78e4; final source6ae95ad/run43474248315 all4 jobs green, backend976/0skip and frontend175. Delivery/production gate remains unaccepted.

### T300. KAN-214 PR6: Merged baseline and acceptance audit

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T278.

**Результаты/файлы:** `docs/KAN-214-PR6.md`.

**Шаги:**

1. Confirm PR18 owner merge and audit current auth models/API/browser/security/infrastructure.
2. Define critical-case matrix and distinguish code verification from external production acceptance.

**Критерии закрытия:**

- Confirm PR18 owner merge and audit current auth models/API/browser/security/infrastructure.
- Define critical-case matrix and distinguish code verification from external production acceptance.
- Общая Definition of Done: docs/QUALITY.md..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR6.md](../docs/KAN-214-PR6.md) — Confirmed owner merge PR18/main12c78e4 and audited account/guest lifecycle, tests and infrastructure. Defined T300-T304 acceptance and gaps: native-PG browser hosted coverage, engine isolation, actual SMTP/HTTPS/egress; production compose remains unchanged.

### T301. KAN-214 PR6: Security regression and evidence

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T300.

**Результаты/файлы:** `docs/KAN-214-PR6.md`.

**Шаги:**

1. Map every critical auth threat to reproducible tests; close material gaps without weakening existing checks.
2. Verify isolation, durable limits, CSRF/replay/revocation, credentials/logging and guest data preservation.

**Критерии закрытия:**

- Map every critical auth threat to reproducible tests; close material gaps without weakening existing checks.
- Verify isolation, durable limits, CSRF/replay/revocation, credentials/logging and guest data preservation.
- Общая Definition of Done: docs/QUALITY.md..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/KAN-214-PR6.md](../docs/KAN-214-PR6.md) — Added populated guest graph/migration/privacy native-PG acceptance (3 passed), security selection112 passed and evidence validator3 passed. Published32 critical controls with actual test selectors; validator refuses incomplete results and never accepts external release gates.

### T302. KAN-214 PR6: Native PostgreSQL cross-browser acceptance

**Статус:** `in_progress` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T301.

**Результаты/файлы:** `docs/KAN-214-PR6.md`.

**Шаги:**

1. Run real lifecycle and negative cases in Chromium Firefox WebKit with isolated disposable PostgreSQL and private mail transport.
2. Add native PostgreSQL browser checks to the existing CI job using its existing PostgreSQL service; no CI rewrite/new service.

**Критерии закрытия:**

- Run real lifecycle and negative cases in Chromium Firefox WebKit with isolated disposable PostgreSQL and private mail transport.
- Add native PostgreSQL browser checks to the existing CI job using its existing PostgreSQL service; no CI rewrite/new service.
- Общая Definition of Done: docs/QUALITY.md..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

### T303. KAN-214 PR6: Migration visual and full regression

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T302.

**Результаты/файлы:** `docs/KAN-214-PR6.md`.

**Шаги:**

1. Verify additive migration with guest history preserved, clean head/schema and all existing backend/frontend routes/tests.
2. Compare approved v3 Live/Demo desktop/mobile without rewriting baselines and record actual outcomes.

**Критерии закрытия:**

- Verify additive migration with guest history preserved, clean head/schema and all existing backend/frontend routes/tests.
- Compare approved v3 Live/Demo desktop/mobile without rewriting baselines and record actual outcomes.
- Общая Definition of Done: docs/QUALITY.md..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

### T304. KAN-214 PR6: Final report and review handoff

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T303.

**Результаты/файлы:** `docs/KAN-214-PR6.md`.

**Шаги:**

1. Publish complete architecture/security/API/guest/email/tests/migration/GitHub/handoff report and review PR.
2. Leave real SMTP/HTTPS and owner acceptance open unless supported by actual evidence or explicit owner exception.

**Критерии закрытия:**

- Publish complete architecture/security/API/guest/email/tests/migration/GitHub/handoff report and review PR.
- Leave real SMTP/HTTPS and owner acceptance open unless supported by actual evidence or explicit owner exception.
- Общая Definition of Done: docs/QUALITY.md..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

## E6. Резерв и выпуск

Плановый интервал: D28–D30.

### T053. Собрать релизный кандидат и отчёт gates

**Статус:** `deferred` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T042, T043, T044, T045, T046, T049, T050, T051, T052.

**Результаты/файлы:** `docs/releases/`; `docs/STATE.json`.

**Шаги:**

1. Проверить G0–G5, scope и список дефектов.
2. Зафиксировать commit/images/schema/model/source versions и release notes.

**Критерии закрытия:**

- Все обязательные критерии подтверждены ссылками.
- Наличие P0 или недоступной обязательной интеграции блокирует кандидат.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

**Причина блокировки/переноса:** Deferred by S201 product cleanup: previous automated/manual MVP release scope or future prediction/expansion work is not the current v3 cleanup. Resume only after v3 acceptance criteria and dependencies are reviewed in a separately authorized phase; ML additionally requires verified outcomes/data and predefined metrics. Historical status and evidence remain in Git.

### T054. Использовать резерв на исправления и повторную проверку

**Статус:** `deferred` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T053.

**Результаты/файлы:** `docs/releases/`; `docs/LOG.md`.

**Шаги:**

1. Закрыть дефекты приёмки или зафиксировать отсутствие нужных исправлений.
2. Повторить затронутые тесты и проверить свежесть release evidence.

**Критерии закрытия:**

- Резерв не потрачен на незаявленные функции.
- Release candidate соответствует последним проверенным изменениям.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

**Причина блокировки/переноса:** Deferred by S201 product cleanup: previous automated/manual MVP release scope or future prediction/expansion work is not the current v3 cleanup. Resume only after v3 acceptance criteria and dependencies are reviewed in a separately authorized phase; ML additionally requires verified outcomes/data and predefined metrics. Historical status and evidence remain in Git.

### T055. Выпустить MVP и передать рабочий контекст

**Статус:** `deferred` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T054.

**Результаты/файлы:** `docs/releases/`; `docs/STATE.md`; `docs/RUNBOOK.md`.

**Шаги:**

1. Выполнить выпуск, production smoke и проверить доступность основных путей.
2. Записать URL/версию/ограничения/backup/следующий backlog и обновить G6.

**Критерии закрытия:**

- Выпуск подтверждён фактическим состоянием сервиса.
- Пользователь получил результат, а новая сессия может продолжить по STATE без догадок.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

**Причина блокировки/переноса:** Deferred by S201 product cleanup: previous automated/manual MVP release scope or future prediction/expansion work is not the current v3 cleanup. Resume only after v3 acceptance criteria and dependencies are reviewed in a separately authorized phase; ML additionally requires verified outcomes/data and predefined metrics. Historical status and evidence remain in Git.

## E7. После MVP: аккаунты, уведомления, ИИ и следующий сезон

Плановый интервал: После G6; сроки после оценки данных и нагрузки.

### T058. Добавить аккаунт и перенос гостевых направлений

**Статус:** `todo` · **Приоритет:** P2 · **Размер:** M.

**Зависимости:** T016, T043, T055.

**Результаты/файлы:** `backend/app/auth/`; `frontend/src/pages/account/`; `docs/data-policy.md`.

**Шаги:**

1. Выбрать вход и recovery без самодельной криптографии.
2. Перенести гостевые данные с защитой ownership и протестировать несколько устройств.

**Критерии закрытия:**

- Нельзя присвоить чужую гостевую сессию.
- Восстановление, logout, удаление аккаунта и сессии проверены.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

### T059. Подключить внешние уведомления по подписке

**Статус:** `todo` · **Приоритет:** P2 · **Размер:** M.

**Зависимости:** T040, T058.

**Результаты/файлы:** `backend/app/notifications/`; `frontend/src/pages/settings/`.

**Шаги:**

1. Выбрать один канал, явную подписку, настройки и отписку.
2. Добавить очередь, rate limits, дедупликацию и обработку ошибок провайдера.

**Критерии закрытия:**

- Сообщения получают только подписанные владельцы.
- Сбой доставки не тормозит импорт и не создаёт повторный спам.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

### T060. Проверить реализуемость статистического прогноза

**Статус:** `deferred` · **Приоритет:** P2 · **Размер:** M.

**Зависимости:** T036, T055.

**Результаты/файлы:** `docs/research/forecast-data.md`.

**Шаги:**

1. Провести аудит исторических снимков, меток исхода и допустимого использования.
2. Оценить смещения выборки, утечки и минимальный полезный baseline.

**Критерии закрытия:**

- Принято доказательное go/no-go для вероятностей.
- Недостаток данных приводит к отказу от процентов, а не к их выдумыванию.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

**Причина блокировки/переноса:** Deferred by S201 product cleanup: previous automated/manual MVP release scope or future prediction/expansion work is not the current v3 cleanup. Resume only after v3 acceptance criteria and dependencies are reviewed in a separately authorized phase; ML additionally requires verified outcomes/data and predefined metrics. Historical status and evidence remain in Git.

### T061. Построить baseline на временно разделённых данных

**Статус:** `deferred` · **Приоритет:** P2 · **Размер:** M.

**Зависимости:** T060.

**Результаты/файлы:** `research/forecast/`; `docs/research/`.

**Шаги:**

1. Зафиксировать признаки доступные до момента прогноза и train/validation/test.
2. Обучить простой baseline и обеспечить воспроизводимость данных/seed/version.

**Критерии закрытия:**

- Будущие согласия и приказы не попадают в признаки прошлого.
- Holdout не использован для настройки.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

**Причина блокировки/переноса:** Deferred by S201 product cleanup: previous automated/manual MVP release scope or future prediction/expansion work is not the current v3 cleanup. Resume only after v3 acceptance criteria and dependencies are reviewed in a separately authorized phase; ML additionally requires verified outcomes/data and predefined metrics. Historical status and evidence remain in Git.

### T062. Проверить калибровку и применимость прогноза

**Статус:** `deferred` · **Приоритет:** P2 · **Размер:** L.

**Зависимости:** T061.

**Результаты/файлы:** `research/forecast/`; `docs/model-card.md`.

**Шаги:**

1. Оценить Brier/log loss/calibration и сегменты по времени/вузам.
2. Сравнить с baseline, определить интервалы неопределённости и abstention.

**Критерии закрытия:**

- Порог качества задан до итогового теста и достигнут.
- Модель отказывается на неподдержанном домене и имеет мониторинг drift.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

**Причина блокировки/переноса:** Deferred by S201 product cleanup: previous automated/manual MVP release scope or future prediction/expansion work is not the current v3 cleanup. Resume only after v3 acceptance criteria and dependencies are reviewed in a separately authorized phase; ML additionally requires verified outcomes/data and predefined metrics. Historical status and evidence remain in Git.

### T063. Добавить ИИ-объяснение с контролем фактов

**Статус:** `deferred` · **Приоритет:** P2 · **Размер:** M.

**Зависимости:** T039, T043, T055.

**Результаты/файлы:** `backend/app/assistant/`; `docs/model-card.md`.

**Шаги:**

1. Ограничить вход структурированными facts и отделить недоверенный текст сайтов.
2. Добавить проверку чисел/источников, timeout, бюджет и шаблонный fallback.

**Критерии закрытия:**

- LLM не меняет расчёт и не выдумывает вероятность.
- Prompt injection и отказ провайдера не нарушают основной сценарий.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

**Причина блокировки/переноса:** Deferred by S201 product cleanup: previous automated/manual MVP release scope or future prediction/expansion work is not the current v3 cleanup. Resume only after v3 acceptance criteria and dependencies are reviewed in a separately authorized phase; ML additionally requires verified outcomes/data and predefined metrics. Historical status and evidence remain in Git.

### T064. Пересмотреть инфраструктуру по стоимости и нагрузке

**Статус:** `deferred` · **Приоритет:** P2 · **Размер:** M.

**Зависимости:** T044, T055, T057.

**Результаты/файлы:** `docs/DECISIONS.md`; `docs/evidence/performance.md`.

**Шаги:**

1. Измерить jobs lag, БД/raw объём, стоимость запроса и частоту обращений.
2. Выбрать масштабирование worker/cache/queue только по установленным узким местам.

**Критерии закрытия:**

- Есть сравнение измерений до/после и предел бюджета.
- Усложнение архитектуры обосновано результатом.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

**Причина блокировки/переноса:** Deferred by S201 product cleanup: previous automated/manual MVP release scope or future prediction/expansion work is not the current v3 cleanup. Resume only after v3 acceptance criteria and dependencies are reviewed in a separately authorized phase; ML additionally requires verified outcomes/data and predefined metrics. Historical status and evidence remain in Git.

### T065. Подготовить следующий сезон приёма

**Статус:** `deferred` · **Приоритет:** P2 · **Размер:** M.

**Зависимости:** T010, T057.

**Результаты/файлы:** `docs/sources/`; `backend/app/rules/`; `docs/releases/`.

**Шаги:**

1. Проверить новые официальные правила/сроки и повторно аттестовать источники.
2. Создать campaign/rule versions и регрессию миграции между сезонами.

**Критерии закрытия:**

- Прошлый сезон остаётся воспроизводимым.
- Новые правила не применяются к старым данным молча.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

**Причина блокировки/переноса:** Deferred by S201 product cleanup: previous automated/manual MVP release scope or future prediction/expansion work is not the current v3 cleanup. Resume only after v3 acceptance criteria and dependencies are reviewed in a separately authorized phase; ML additionally requires verified outcomes/data and predefined metrics. Historical status and evidence remain in Git.
