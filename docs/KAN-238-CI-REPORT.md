# KAN-238 — аудит и укрепление CI

Дата: 2026-11-12. Ветка: `ci/kan-238-hardening`, база `origin/main` = `e4d59b46f21f3b6e2d1953955d0631bc09c4ff1b`.
Приёмка владельцем и merge не выполняются автоматически.

## 1. Что существовало до изменений

Единственный workflow `.github/workflows/ci.yml` (`Checks`) запускается на push и pull_request.
Независимые frontend/backend jobs, Ubuntu 24.04, Python 3.12, Node 24, таймауты 15 минут,
permissions `contents: read`, npm lockfile/cache, Playwright Chromium с OS dependencies,
собственные API/preview процессы runner, JSON/trace и backend JUnit с `if: always()` уже реализованы.
PostgreSQL 17 service имеет healthcheck. `--require-postgres` отвергает SQLite, отсутствие/skip/фильтрацию native tests.
Тесты используют собственные схемы, удаляют только их; отдельные SQLite unit tests сохраняются.
Alembic upgrade/downgrade/check уже тестируются в pytest, в том числе PostgreSQL legacy paths.
ML/ETL fixtures проверяются общим pytest; обученной модели в `ml/` нет.

Подтверждённый исходный hosted run: [43084056846](https://github.com/deylon999/admitflow/actions/runs/43084056846), SHA базы, success.

## 2. Обнаруженные недостатки

Таблица составлена **до изменения реализации**.

| Существующая проверка | Подтверждённый недостаток | Минимальное изменение | Проверка результата |
| --- | --- | --- | --- |
| npm test / JSON и trace | Нет JUnit; screenshot не включён; Playwright допускает test.only | Добавить JUnit, screenshot on failure, forbidOnly в CI | npm test; NEG-01/04 и содержимое артефакта |
| API process runner | После SIGTERM нет предела ожидания stubborn child | Ограниченный graceful stop с последующим SIGKILL | Тест runner shutdown и полный npm test |
| pip install requirements-dev | Уже существующий runtime constraints.txt не используется; cache frontend зависит только от dev файла | Применить constraints и cache по requirements + constraints | Чистые installs и pip check |
| Backend pytest / PG | Диагностика ограничена XML; нет service log в артефакте | Сохранить pytest output и PG logs с сохранением exit code | NEG-02/04 |
| Миграции внутри backend pytest | Нет отдельного обязательного статуса и отдельной чистой БД; нет явной сверки current heads | Job migrations с собственной PG БД, upgrade, heads equality, check и логом | Чистая БД; NEG-03 schema drift |
| ETL внутри общего backend pytest | Нет отдельного видимого статуса; отсутствие dataset видно только как skip | Выделить существующий ETL suite и явно сообщить границы доступных артефактов | Fixture, reproducibility, leakage tests; XML/summary |

Уже выполненные требования сохраняются: пять frontend команд, 29 маршрутов, реальные PostgreSQL native tests,
healthcheck, job timeouts, независимость frontend/backend, ненулевой exit code тестов,
upload при ошибке, push/PR triggers и минимальные permissions. Не требуется переписывать CI или продукт.

## 3. Что изменено

- `frontend/playwright.config.ts`: CI forbidOnly, JUnit, screenshot on failure; отдельный outputDir для browser artifacts, чтобы Playwright не удалял открытый runner log.
- `frontend/scripts/stop-child.mjs`, `stop-child.test.mjs`, `test.mjs`: ограниченный stdin → TERM → KILL teardown; три проверки реальных дочерних процессов, включая игнорирование сигналов в Linux.
- `.github/workflows/ci.yml`: shutdown tests, сохранение frontend console log через Bash pipefail/tee, явные retention 7 дней и ошибка при отсутствии artifacts.
- Backend/frontend pip используют существующий runtime `constraints.txt`, cache учитывает его, выполняется `pip check`; версии основных зависимостей не обновлены.
- `backend/tests/check_migrations.py`: gate требует явный disposable PostgreSQL URL, пустую БД, upgrade head, равенство heads и `alembic check`. `backend/tests/test_ci_migrations.py` проверяет успешный путь, отказ от непустой БД, schema drift, потерю revision и небезопасные URL.
- Workflow: отдельный независимый `migrations` service/job с собственной чистой БД; backend console/JUnit и PostgreSQL logs сохраняются с исходным кодом ошибки pipeline.
- TASKS/STATE/LOG и генерируемые документы фиксируют пятёрку; PRODUCT/ADR-051 фиксируют критерий hosted приёмки без изменения продуктовых правил.

## 4. Выполненные проверки

- `git status --porcelain`: исходное дерево чистое; `git fetch origin` выполнен.
- `python scripts/roadmap.py --check`: исходный план валиден (255 задач).
- GitHub API: доступ push есть, admin/maintain нет; baseline run действительно success.
- Локально доступны Node 24.21.0, Python 3.14.7, Docker 29.5.3. CI Python 3.12 проверяется отдельно в Linux.
- T261: `npm ci` exit 0 (0 vulnerabilities); lint/typecheck/build exit 0; `npm test` **94 passed**, включая 29 маршрутов; JUnit/JSON записаны. Shutdown tests **3 passed**. UI, API и CSS не менялись.
- T262 targeted Linux/Python 3.12/PostgreSQL 17: **32 passed** (старые и новые migration tests), `pip check` exit 0. Отдельная свежесозданная `admitflow_test_migrations`: head `0011`, schema check pass. `actionlint 1.7.7` exit 0.
- Полный backend до выделения ETL: `python -m pytest -q --require-postgres --junitxml=test-results/backend.xml` — **774 passed, 1 skipped**, 260.97 s. Единственный skip — отсутствующий MICCEDU dataset, не PostgreSQL. Native guard прошёл; SQLite unit tests не выдаются за PG.
- Repository tools: `python -m unittest scripts.tests.test_roadmap scripts.tests.test_weekly_report` — **17 passed**, включая PDF после установки Cyrillic TTF в одноразовом Linux-контейнере. Первоначальный optional font skip устранён установкой окружения, тест не менялся.

## 5. Проверка обнаружения ошибок

NEG-01–04: NOT VERIFIED до фактических hosted runs. Искусственные ошибки допускаются только в отдельных временных ветках.

## 6. Что осталось нерешённым

Полный MICCEDU dataset/passport не собран; `ml/` содержит README, ETL реализован в scripts и tests.
Нет обученной модели, backtest и метрик модели. Fixture checks не доказывают качество модели или национальное покрытие.
Доступность capture из российской сети — отдельное внешнее условие; массовый fetch в CI не запускается.
Старые приватные `audit/evidence/` от ветки предыдущего аудита сохранены на диске и исключены только локальным `.git/info/exclude`; в PR и artifacts они не включаются.

## 7. Pull Request и рекомендации

PR ещё не создан. Итоговый отчёт дополнится ссылкой, SHA и hosted результатом.
Настройки branch protection/rulesets не меняются; рекомендации будут привязаны к фактическим названиям jobs.

## Чек-лист пятёрки

- [x] T260 — аудит и таблица
- [x] T261 — frontend
- [x] T262 — PostgreSQL / Alembic
- [ ] T263 — ETL
- [ ] T264 — hosted NEG, PR, отчёт
