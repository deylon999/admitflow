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
- Workflow `etl`: существующие `test_admission_history.py`, `test_accreditation_registry.py`, `test_exam_requirements.py` перенесены из backend job без удаления проверок и повторного запуска тех же suites. Отдельные JUnit/log и summary явно показывают отсутствие MICCEDU dataset и model/backtest stage; неполная пара CSV/passport вызывает failure. Массового HTTP fetch нет.
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
- T263: offline ETL **55 passed, 1 skipped** (только отсутствующий full dataset, причина видна через `-ra`). Проверены malformed values, duplicate records, provenance, edition/year, byte reproducibility, ограничение `admission_year <= campaign_year - 2`, registry и exam document fixtures. Точный status step workflow исполнен в Linux: отсутствие dataset/model отображается явно. Actionlint exit 0.

- Hosted pull_request: [43277802246](https://github.com/deylon999/admitflow/actions/runs/43277802246), SHA `4f60dad3a6bb01862b4eec43e46ae07139cf6a5d`, все четыре jobs success.
- Hosted push: [43277687053](https://github.com/deylon999/admitflow/actions/runs/43277687053), SHA `4f60dad3a6bb01862b4eec43e46ae07139cf6a5d`, все четыре jobs success.
- Hosted после разделения suites: backend **719 passed, 0 skipped**, ETL **55 passed, 1 explicit dataset skip**, frontend **94 passed**. Отдельный migration job: head `0011`, schema check pass. Shutdown tests и repository tools также success.
- Компактные API-статусы и проверенные manifests: [evidence/kan-238-ci.json](evidence/kan-238-ci.json).

## 5. Проверка обнаружения ошибок

| ID | Изменение / ожидание | Фактический результат | SHA / hosted run | Артефакт |
| --- | --- | --- | --- | --- |
| NEG-01 | Отдельный Playwright assertion `expect(1).toBe(2)`; ожидается failed frontend | PASS: ожидаемый job и workflow failure; upload success | `d64d5018a0f64053b4ebb224eb552064cfb2a8a8`; [run 43277814063](https://github.com/deylon999/admitflow/actions/runs/43277814063) | [frontend-tests](https://github.com/deylon999/admitflow/actions/runs/43277814063/artifacts/13970992560) |
| NEG-02 | Отдельный pytest `assert False`; ожидается failed backend | PASS: ожидаемый job и workflow failure; upload success | `f6ac42ff07b54ab74dc98b0949ee5063a3fc7073`; [run 43277831614](https://github.com/deylon999/admitflow/actions/runs/43277831614) | [backend-tests](https://github.com/deylon999/admitflow/actions/runs/43277831614/artifacts/13970668519) |
| NEG-03 | Колонка `ci_negative_drift` после upgrade в disposable DB; ожидается failed migrations при актуальном head | PASS: ожидаемый job и workflow failure; upload success | `18970ff5630a8be3cddf86ebd1810cc2d09218f4`; [run 43277851703](https://github.com/deylon999/admitflow/actions/runs/43277851703) | [migration-tests](https://github.com/deylon999/admitflow/actions/runs/43277851703/artifacts/13971796615) |
| NEG-04 | Диагностика после падения | PASS: архивы скачаны и XML/log/PNG/trace проверены | Те же SHA и runs NEG-01–03 | [frontend](https://github.com/deylon999/admitflow/actions/runs/43277814063/artifacts/13970992560), [backend](https://github.com/deylon999/admitflow/actions/runs/43277831614/artifacts/13970668519), [migration](https://github.com/deylon999/admitflow/actions/runs/43277851703/artifacts/13971796615) |

NEG-01: 94 обычных теста passed, один искусственный failed; JUnit содержит имя нужного теста.
NEG-02: обычные backend тесты passed, один искусственный failed; XML, pytest output и PostgreSQL log сохранены.
NEG-03: head совпадает (`0011`), затем настоящий Alembic `AutogenerateDiffsDetected` показывает удаление неожиданной колонки.
В этой ветке также ожидаемо падают тесты самого gate в backend; это следствие подмены verifier только в probe-ветке.
NEG-04: frontend archive содержит `frontend.xml`, `frontend.log`, `results.json`, failure PNG, `error-context.md`, `trace.zip`;
backend — `backend.xml`, `backend.log`, `postgres.log`; migration — `migrations.log`, `postgres.log`.
Артефакты хранятся 7 дней; ссылки могут требовать входа в GitHub. Компактное JSON evidence остаётся в репозитории.
Ветки `ci/kan-238-neg-*` изолированы от PR #12 и сохранены для ревью; merge этих веток не требуется.
Applied migrations не менялись. Основная ветка проверена на отсутствие искусственных ошибок.


## 6. Что осталось нерешённым

Полный MICCEDU dataset/passport не собран; `ml/` содержит README, ETL реализован в scripts и tests.
Нет обученной модели, backtest и метрик модели. Fixture checks не доказывают качество модели или национальное покрытие.
Доступность capture из российской сети — отдельное внешнее условие; массовый fetch в CI не запускается.
Старые приватные `audit/evidence/` от ветки предыдущего аудита сохранены на диске и исключены только локальным `.git/info/exclude`; в PR и artifacts они не включаются.

## 7. Pull Request и рекомендации

[PR #12](https://github.com/deylon999/admitflow/pull/12) → `main`, без merge.
Последняя публикация отчёта запускает Checks снова; окончательный SHA/run фиксируются в описании PR и передаче пользователю после завершения прогона.
Production release, trained model, live capture и внешние gates этим PR не принимаются.

Рекомендации владельцу для main (настройки самостоятельно **не менялись**):

- Require pull request и review перед merge; обязательные checks от GitHub Actions: **frontend, backend, migrations, etl**.
- Включить Require branches to be up to date before merging; оценивать checks последнего push/PR merge SHA, после нового push дождаться нового результата.
- Запретить bypass, force push и удаление main; не разрешать merge при failure/cancelled/pending. Настройки должен применить владелец с admin/edit-rules правами.
- Все четыре jobs остаются без условий пропуска/path filters. Не добавлять continue-on-error, pass-with-no-tests или искусственный exit 0.
- GitHub может считать skipped/neutral checks приемлемыми; если в будущем появятся условные jobs, потребуется отдельный required aggregate gate с always() и проверкой каждого needs.result == success. Текущие обязательные jobs не условные; единственный известный dataset skip явно вынесен в ETL summary.

Обоснование: [GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches),
[workflow artifacts](https://docs.github.com/en/actions/tutorials/store-and-share-data),
[Alembic commands](https://alembic.sqlalchemy.org/en/latest/api/commands.html).

Воспроизведение из чистого checkout: npm-команды только в `frontend` (`npm ci`, lint/typecheck/build,
`npx playwright install --with-deps chromium`, `node --test scripts/stop-child.test.mjs`, `npm test`).
В `backend`: `python -m pip install -r requirements-dev.txt -c constraints.txt`; для native tests создать
отдельную `admitflow_test*` PG БД и задать TEST_DATABASE_URL, запустить pytest с `--require-postgres`.
Для standalone migration gate создать **другую пустую** `admitflow_test_migrations`, задать MIGRATION_DATABASE_URL,
PYTHONPATH=., выполнить `python tests/check_migrations.py`; не использовать рабочую/production БД.
Точные команды разбиения backend/ETL — в workflow. Повтор NEG: взять соответствующую probe-ветку,
создать новую ветку от неё и обычным push запустить Checks; не переносить probe-коммиты в PR #12/main.

Тимлиду: проверить diff и NEG evidence, выполнить review PR #12, применить required checks, отдельно подтвердить приёмку.
Готовое сообщение: «KAN-238 подготовлена в PR #12. Frontend, native PostgreSQL, clean Alembic и существующий ETL
проверены hosted CI; NEG-01–04 подтвердили падения и сохранение диагностики. Продукт и applied migrations не изменены.
Полного MICCEDU dataset/model нет; это явно указано. Прошу review и настройку required checks; merge не выполнялся.»

## Чек-лист пятёрки

- [x] T260 — аудит и таблица
- [x] T261 — frontend
- [x] T262 — PostgreSQL / Alembic
- [x] T263 — ETL
- [x] T264 — hosted NEG, PR, отчёт

## Definition of Done и передача

- [x] Аудит и подтверждённые недостатки; существующие проверки сохранены.
- [x] Frontend lint/typecheck/build/tests, все 29 маршрутов.
- [x] Native PostgreSQL pytest без PG skips; отдельная чистая migration DB, heads equality и schema check.
- [x] Реальный offline ETL, честное отсутствие dataset/model, диагностические artifacts.
- [x] Hosted NEG-01–04, отдельный PR, проверенный implementation SHA.
- [x] Scope: workflow/tests/scripts/docs; нет product source/API/DTO/CSS/applied migration changes.
- [x] Секреты/реальные идентификаторы не добавлены; старые private artifacts не опубликованы.
- [x] Локальные owned контейнеры/сеть остановлены и удалены; пользовательские Docker volumes сохранены.
- [x] Русский отчёт, TASKS/STATE/LOG и генерируемый checklist согласованы.

После финального push обязательно проверить latest PR checks; точная ссылка и SHA передаются в PR.
Приёмка тимлидом/merge: **ожидает владельца**, это не автоматическое действие KAN-238.
