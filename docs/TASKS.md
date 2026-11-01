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

**Статус:** `blocked` · **Приоритет:** P0 · **Размер:** M.

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

**Причина блокировки/переноса:** GitHub:443 remains unreachable in B03 (git ls-remote failed). Resume after repository access and a successful remote workflow for the tested SHA.

### T007. Закрепить шрифты и дизайн-токены

**Статус:** `blocked` · **Приоритет:** P0 · **Размер:** M.

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

Пока нет.

**Причина блокировки/переноса:** Получение файлов шрифтов блокируется WinError 10013; локальные Inter/JetBrains Mono не найдены. Для снятия нужны лицензированные файлы и проверка FontFace.

### T008. Сверить React-лендинг с исходными макетами

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

Пока нет.

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

**Статус:** `review` · **Приоритет:** P0 · **Размер:** M.

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

### T103. Fix PostgreSQL legacy CHECK reflection during migration adoption

**Статус:** `review` · **Приоритет:** P0 · **Размер:** M.

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

**Статус:** `blocked` · **Приоритет:** P0 · **Размер:** M.

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

**Причина блокировки/переноса:** Original pilot list bytes unavailable: real capture returned network_error, SGU page timed out and SGUPS profile cache missed. Resume after verified original capture bundles and anonymized real fixtures; capture CLI alone is not a fixture.

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

## E2. Ядро продукта

Плановый интервал: D4–D10.

### T014. Ввести Alembic и PostgreSQL-проверки

**Статус:** `review` · **Приоритет:** P0 · **Размер:** L.

**Зависимости:** T004, T015.

**Результаты/файлы:** `backend/alembic/`; `backend/alembic.ini`; `backend/tests/integration/`.

**Шаги:**

1. Создать миграции текущих и целевых сущностей без потери ручных данных.
2. Проверить upgrade на пустой БД и на предыдущей схеме, описать восстановление.

**Критерии закрытия:**

- Схема PostgreSQL создаётся миграциями.
- Ошибка миграции не скрывается автоматическим create_all в production.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S012: SQLite migration suite и PG offline SQL проходят, реальный PG skipped; CI подготовлен.

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

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T014, T016, T068.

**Результаты/файлы:** `backend/app/services/`; `backend/tests/integration/`.

**Шаги:**

1. Добавить транзакционные гарантии и идемпотентность создающих операций.
2. Протестировать конкурентные запросы, лимиты и потерянный ответ.

**Критерии закрытия:**

- Повтор запроса не дублирует запись в предусмотренном контракте.
- Параллельные операции не обходят установленные лимиты.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

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

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T016, T017, T018, T091.

**Результаты/файлы:** `frontend/src/pages/TrackerPage.tsx`; `frontend/tests/e2e/tracker.spec.ts`.

**Шаги:**

1. Проверить создание/обновление/историю/удаление и pending/error/empty.
2. Сохранить введённые поля при ошибке, исключить двойное нажатие и XSS.

**Критерии закрытия:**

- Сквозной путь работает после reload и перезапуска API.
- Ручные данные не помечены автоматическими.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

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

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

Пока нет.

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

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T018.

**Результаты/файлы:** `backend/app/schemas.py`.

**Шаги:**

1. Reject control characters in manual metadata.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- API names and URLs reject raw controls before normalization; client/import contracts agree..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S077: Reject C0/DEL controls before Pydantic URL normalization; client form/import contracts reject them consistently. Targeted backend9 passed; frontend69 passed. No metadata write on invalid input.

### T124. Batch manual direction and export reads

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T018.

**Результаты/файлы:** `backend/app/main.py`.

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

**Результаты/файлы:** `backend/app/main.py`.

**Шаги:**

1. Order same-time snapshots and refuse clock regression.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Equal-time updates become latest without changing observed time; backward-clock writes refuse atomically..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S083: Equal-time updates retain exact observed time and use increasing UUID tie-breaks, becoming latest deterministically. Backward clock refuses409 atomically; DATA_RULES updated, formula unchanged. Clock/API15 passed after correcting a nonexistent test filename.

### T126. Enforce ISO aware timestamps on manual DTOs

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T090.

**Результаты/файлы:** `backend/app/schemas.py`.

**Шаги:**

1. Enforce ISO aware timestamps on manual DTOs.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Numeric/coercible timestamps and unsupported precision rejected; actual aware datetimes remain valid internally..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S084: Manual DTO timestamps accept only explicit ISO timezone strings up to6fraction digits or aware internal datetimes; numeric/naive/coercible timestamps rejected422. Hardening/import/export32 passed; original timestamps remain unchanged.

### T128. Compare opaque IDs by Unicode code point

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T095.

**Результаты/файлы:** `frontend/src/lib/time.ts`.

**Шаги:**

1. Compare opaque IDs by Unicode code point.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Same-time ordering agrees with Python for BMP and supplementary Unicode IDs..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S086: Same-time opaque IDs compare Unicode code points like Python, not UTF16 code units. Text length counts code points, accepting valid100-character supplementary IDs from the server. Unicode ordering/export regression and all71 frontend tests passed.

### T135. Serialize guest bootstrap between browser tabs

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T098.

**Результаты/файлы:** `frontend/src/lib/api.ts`.

**Шаги:**

1. Serialize guest bootstrap between browser tabs.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Concurrent initial tabs share one guest bootstrap when Web Locks is available; no reset deadlock..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

### T136. Fence stale session results after access changes

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T135.

**Результаты/файлы:** `frontend/src/lib/api.ts`.

**Шаги:**

1. Fence stale session results after access changes.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Late promises from earlier access cannot clear/replace newer session state or trigger hidden writes..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

## E3. Автоматический сбор

Плановый интервал: D8–D17.

### T021. Найти абитуриента в конкретном источнике

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T018, T029.

**Результаты/файлы:** `backend/app/candidates/`; `frontend/src/components/`.

**Шаги:**

1. Определить допустимый публичный ID и область уникальности.
2. Сделать поиск, подтверждение строки, not-found/ambiguous и rate limit.

**Критерии закрытия:**

- Нет склейки людей по ФИО или чужому ID другого источника.
- Пользователь подтверждает правильную группу и запись до сохранения.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

### T027. Определить интерфейс адаптера и registry

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

Пока нет.

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

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** L.

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

Пока нет.

### T030. Ввести нормализацию и карантин

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

Пока нет.

### T031. Подключить второй независимый источник

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** L.

**Зависимости:** T029, T030.

**Результаты/файлы:** `backend/app/sources/adapters/`; `docs/sources/`.

**Шаги:**

1. Проверить второй вуз/формат отдельно, даже если платформа похожа.
2. Добавить собственные реальные и негативные fixtures.

**Критерии закрытия:**

- Второй источник проходит те же критерии, что первый.
- Доказательство не основано только на совпадении названий колонок.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

### T032. Реализовать планировщик и отдельный worker

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** L.

**Зависимости:** T014, T027, T028, T081.

**Результаты/файлы:** `backend/app/worker/`; `backend/tests/integration/`.

**Шаги:**

1. Сделать PostgreSQL jobs, атомарный lease, heartbeat, max retries и лимиты домена.
2. Проверить два worker и восстановление задания после смерти процесса.

**Критерии закрытия:**

- Одно задание не публикуется дважды.
- Worker не блокирует API и не создаёт шторм запросов.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

### T033. Сохранять и публиковать снимки атомарно

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T014, T030, T032, T079.

**Результаты/файлы:** `backend/app/snapshots/`; `backend/tests/integration/`.

**Шаги:**

1. Сохранить raw hash/provenance и normalised snapshot.
2. Переключать latest только после полной проверки, ограничить retention.

**Критерии закрытия:**

- Повтор импорта идемпотентен.
- Падение до commit сохраняет предыдущий latest и не показывает полуготовые данные.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

### T034. Считать автоматические assessments и diff

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** L.

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

Пока нет.

### T035. Обработать отказ и восстановление источника

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

Пока нет.

### T036. Сделать детерминированный replay архивов

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

Пока нет.

### T037. Добавить эксплуатационное управление источниками

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

Пока нет.

### T038. Посчитать честные метрики покрытия

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

**Результаты/файлы:** `backend/app/sources/fetcher.py`.

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

**Результаты/файлы:** `backend/app/sources/fetcher.py`.

**Шаги:**

1. Reject ambiguous HTTP headers and malformed redirects.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Critical duplicate headers fail safely; invalid redirect syntax becomes a bounded FetchError..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S088: Fetch reader rejects duplicate critical headers and conflicting transfer framing; malformed/control-character redirects become safe bounded errors. Fetcher42 passed, including no body read on ambiguity. Conservative framing policy follows RFC9112 section6.3.

### T131. Validate immutable fetch policies strictly

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T028.

**Результаты/файлы:** `backend/app/sources/fetcher.py`.

**Шаги:**

1. Validate immutable fetch policies strictly.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Nonfinite or wrong-type limits and mutable/unapproved domain policy are rejected before network..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S089: Immutable fetch policy validates finite timeout up to30s, strict size up to5MiB, redirects0..5, exact lowercase DNS domains and supported content types before network. Fetcher/capture56 passed, including mutable sets, NaN, bool-as-int and wildcard/IP refusals.

### T132. Preserve fetch outcome when spool cleanup fails

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T100.

**Результаты/файлы:** `backend/app/worker.py`.

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

**Результаты/файлы:** `backend/app/sources/registry.py`.

**Шаги:**

1. Validate adapter declarations before registry use.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Attestation is an actual bool; version/domain/callable contract cannot silently admit malformed adapters..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S091: Adapter declarations require an actual boolean attestation, bounded version token, immutable exact domains and callable parser before registry use. Registry/status/worker21 passed; production registry remains empty.

### T134. Apply queue policies on explicit eligible reenqueue

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T081.

**Результаты/файлы:** `backend/app/jobs.py`.

**Шаги:**

1. Apply queue policies on explicit eligible reenqueue.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Changed interval/max attempts apply to eligible jobs; running/backoff jobs remain untouched..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

## E4. Объяснения и UX

Плановый интервал: D15–D22.

### T022. Добавить поиск вузов и групп с coverage

**Статус:** `review` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T012, T018.

**Результаты/файлы:** `frontend/src/pages/`; `backend/app/catalog/`.

**Шаги:**

1. Сделать поиск/фильтры/пагинацию по вузу, филиалу, сезону и группе.
2. Показать automatic/manual/archive/unsupported и путь заявки на подключение.

**Критерии закрытия:**

- Неподключённый вуз не выглядит рабочей интеграцией.
- Можно добавить ручное направление без ложного promise автоматического сбора.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S015: выбор вузов и manual fallback проходят E2E; группы/фильтры пока не готовы.

### T024. Показывать provenance и отдельные времена

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

Пока нет.

### T025. Закрыть ошибки загрузки и повторных действий

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

Пока нет.

### T026. Проверить доступность кабинета и мобильный UX

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

Пока нет.

### T039. Объяснять оценку и изменение проверенными фактами

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

Пока нет.

### T040. Показать изменения внутри приложения

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

Пока нет.

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

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T091.

**Результаты/файлы:** `frontend/src/lib/import.ts`.

**Шаги:**

1. Align import preview date rules with server validation.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Files too old or beyond server future tolerance rejected before POST; boundary is deterministic in tests..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S085: Import preview enforces the server UTC year2000 floor and inclusive5minute future tolerance before POST. Boundary tested to1microsecond. Frontend70/build passed, maximum20x500 export still accepted.

### T138. Recover from lazy page loading failures

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T018.

**Результаты/файлы:** `frontend/src/main.tsx`.

**Шаги:**

1. Recover from lazy page loading failures.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Friendly fallback and explicit reload replace blank screen; no automatic retry/session creation..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

## E5. Качество и эксплуатация

Плановый интервал: D20–D27.

### T041. Добавить наблюдаемость API/worker/источников

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

Пока нет.

### T042. Собрать регрессию правил и качества данных

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

Пока нет.

### T043. Проверить безопасность и пользовательские данные

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

Пока нет.

### T044. Измерить нагрузку и устранить узкие места

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

Пока нет.

### T045. Проверить браузеры и визуальные состояния

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

Пока нет.

### T046. Наблюдать циклы импорта и свежесть

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

### T047. Подготовить контейнерный контур

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

Пока нет.

### T048. Развернуть staging с HTTPS

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** L.

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

### T049. Проверить backup, restore и retention

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

### T050. Настроить эксплуатационные сигналы и откат

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

### T051. Пройти полный путь автоматизированного MVP

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

### T052. Провести продуктовую приёмку

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

**Результаты/файлы:** `backend/app/http.py`.

**Шаги:**

1. Reject ambiguous JSON request documents.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Duplicate keys, nonfinite numbers and excessive nesting are rejected before any endpoint writes..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S078: Request JSON rejects duplicate keys, NaN/Infinity/overflow and depth over64 before writes, preserving normal malformed-JSON validation. Brackets inside strings remain valid. Targeted hardening14 passed; existing8MiB receive budget preserved.

### T121. Bound and redact validation error responses

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T086.

**Результаты/файлы:** `backend/app/main.py`.

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

**Результаты/файлы:** `backend/app/config.py`.

**Шаги:**

1. Fail closed on invalid environment and production settings.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Unknown environments/boolean values fail startup; direct Settings cannot bypass production invariants..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S080: Settings fail closed for unknown environment/boolean strings; constructor enforces PostgreSQL, secure cookie and explicit production migrations. Updated prior test to reject an explicit unsafe true instead of silently ignoring it. Config/origin10 passed.

### T123. Bound PostgreSQL connection establishment

**Статус:** `done` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T004.

**Результаты/файлы:** `backend/app/database.py`.

**Шаги:**

1. Bound PostgreSQL connection establishment.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Unresponsive PostgreSQL handshake fails within configured bounds; credentials are not logged..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

- [docs/LOG.md](../docs/LOG.md) — S081: PostgreSQL connect timeout defaults5s (allowed1..10), pool checkout5s. Real local TCP peer accepted a connection then stalled: handshake timed out;4 tests passed. This is failure-path wire verification, not a successful PG migration/server test.

### T137. Bound JSON response consumption in the browser

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

**Зависимости:** T073.

**Результаты/файлы:** `frontend/src/lib/transport.ts`.

**Шаги:**

1. Bound JSON response consumption in the browser.
2. Verify success and meaningful refusal/boundary cases.

**Критерии закрытия:**

- Oversized/malformed response bodies stop reading; cancellation and timeout remain effective..
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

## E6. Резерв и выпуск

Плановый интервал: D28–D30.

### T053. Собрать релизный кандидат и отчёт gates

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

### T054. Использовать резерв на исправления и повторную проверку

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

### T055. Выпустить MVP и передать рабочий контекст

**Статус:** `todo` · **Приоритет:** P0 · **Размер:** M.

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

## E7. После MVP: вся Россия, аккаунты, ИИ

Плановый интервал: После G6; сроки после оценки данных и нагрузки.

### T056. Расширить проверенный каталог до национального охвата

**Статус:** `todo` · **Приоритет:** P2 · **Размер:** M.

**Зависимости:** T012, T038, T055.

**Результаты/файлы:** `backend/app/catalog/`; `docs/catalog-coverage.md`.

**Шаги:**

1. Сверить организации/филиалы/уровни с датированным опорным реестром.
2. Обновлять каталог воспроизводимым импортом и фиксировать исключения.

**Критерии закрытия:**

- Есть понятный знаменатель полноты и дата.
- Полный каталог не называется полным автоматическим сбором.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

### T057. Масштабировать адаптеры по платформам вузов

**Статус:** `todo` · **Приоритет:** P2 · **Размер:** L.

**Зависимости:** T031, T037, T046, T055.

**Результаты/файлы:** `backend/app/sources/adapters/`; `docs/sources/`.

**Шаги:**

1. Сгруппировать новые сайты по реальным шаблонам и приоритету.
2. Для каждой интеграции пройти passport/fixtures/сверку/наблюдение до включения.

**Критерии закрытия:**

- Каждая добавленная группа имеет доказательство совместимости.
- Рост покрытия не ухудшает freshness и лимиты источников.
- Общая Definition of Done выполнена; в LOG записаны результат проверки и её ограничения.

**Доказательства:**

Пока нет.

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

**Статус:** `todo` · **Приоритет:** P2 · **Размер:** M.

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

### T061. Построить baseline на временно разделённых данных

**Статус:** `todo` · **Приоритет:** P2 · **Размер:** M.

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

### T062. Проверить калибровку и применимость прогноза

**Статус:** `todo` · **Приоритет:** P2 · **Размер:** L.

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

### T063. Добавить ИИ-объяснение с контролем фактов

**Статус:** `todo` · **Приоритет:** P2 · **Размер:** M.

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

### T064. Пересмотреть инфраструктуру по стоимости и нагрузке

**Статус:** `todo` · **Приоритет:** P2 · **Размер:** M.

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

### T065. Подготовить следующий сезон приёма

**Статус:** `todo` · **Приоритет:** P2 · **Размер:** M.

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
