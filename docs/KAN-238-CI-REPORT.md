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

Работа продолжается; итоговый список будет дополнен проверенными изменениями.

## 4. Выполненные проверки

- `git status --porcelain`: исходное дерево чистое; `git fetch origin` выполнен.
- `python scripts/roadmap.py --check`: исходный план валиден (255 задач).
- GitHub API: доступ push есть, admin/maintain нет; baseline run действительно success.
- Локально доступны Node 24.21.0, Python 3.14.7, Docker 29.5.3. CI Python 3.12 проверяется отдельно в Linux.

## 5. Проверка обнаружения ошибок

NEG-01–04: NOT VERIFIED до фактических hosted runs. Искусственные ошибки допускаются только в отдельных временных ветках.

## 6. Что осталось нерешённым

Полный MICCEDU dataset/passport не собран; `ml/` содержит README, ETL реализован в scripts и tests.
Нет обученной модели, backtest и метрик модели. Fixture checks не доказывают качество модели или национальное покрытие.
Доступность capture из российской сети — отдельное внешнее условие; массовый fetch в CI не запускается.

## 7. Pull Request и рекомендации

PR ещё не создан. Итоговый отчёт дополнится ссылкой, SHA и hosted результатом.
Настройки branch protection/rulesets не меняются; рекомендации будут привязаны к фактическим названиям jobs.

## Чек-лист пятёрки

- [x] T260 — аудит и таблица
- [ ] T261 — frontend
- [ ] T262 — PostgreSQL / Alembic
- [ ] T263 — ETL
- [ ] T264 — hosted NEG, PR, отчёт
