# T254 / T250 — полный локальный Compose + PostgreSQL

2026-11-10, S203. Acceptance T254 записан до реализации: реальный полный старт
backend/frontend/PostgreSQL одной командой, существующие миграции и импорт,
сохранение volumes/истории, тесты и коммит. SQLite не используется как
подтверждение PostgreSQL. Прежний Docker-блокер T250 фактически снят.

## Итог

**PASS**, `python scripts/local_smoke.py`, exit 0; отдельный повтор с
`--no-build` тоже exit 0. Команда запущена ровно в форме из README, с build.
Стек оставлен работающим на **http://localhost:8080**.

| Проверка | Фактический результат |
| --- | --- |
| Docker Engine | 29.9.2; Desktop Linux Engine запущен в фоне |
| Compose | db/backend/frontend healthy; backend/DB не публикуют host-порты |
| PostgreSQL | 17.11, настоящий engine `postgresql` |
| Alembic current / heads | `0011` / `0011` |
| Alembic check | Нет новых upgrade operations |
| Проверенный импорт | Два повторных импорта; количества стабильны, источники не активируются |
| Public catalog | 1257 вузов, 2 проверенных архивных программы |
| API | ready, списки/детали, stable IDs, неизвестный ID 404, неверный фильтр 422 |
| Frontend | root, assets, SPA routes через nginx; реальный каталог в Chromium |
| Recreate | db/backend/frontend пересозданы, named mounts идентичны |
| История | Два реальных снимка собственной синтетической гостевой истории полностью совпали до/после recreate |
| Cleanup | Удалена только созданная smoke сессия; контрольные суммы исходных таблиц совпали |
| Backup | До миграций создан custom pg_dump; pg_restore --list прочитал архив |

Подробный [машинный отчёт](local-postgresql.json) содержит только счётчики,
контрольные суммы и состояние. Приватный dump остаётся в ignored
`test-results/local-start/20261110T204015-c204d96f-before-upgrade.dump`.
Полное восстановление этого backup в этой задаче не выполнялось.

## Найдено и исправлено

Отдельный процесс `alembic check` ошибочно предлагал `remove_table
worker_heartbeats`: `backend/alembic/env.py` не импортировал модель
`app.observability`. Добавлена регистрация модели. Таблица не удалялась,
применённые файлы 0001–0011 не редактировались. Исправление и subprocess
PostgreSQL regression test — коммит **881422f**.

Новый host launcher проверяет Docker/Compose и PostgreSQL, сохраняет backup
до запуска backend, выполняет build/up/migrations/import/API/recreate и
сравнивает историю. На сбое возвращает exit 1 и новый JSON, а не фиктивный
успех или SQLite fallback. Параметры другого Compose-проекта и destructive
cleanup не принимаются. Named project остаётся admitflow. Не вызывает
down, удаление volumes, downgrade или restore текущей БД. Архивы/отчёты
получают уникальные имена; сырые строки истории и cookies в отчёт не попадают.

Первые прогоны завершались с ненулевым кодом: сначала из-за настоящего
Alembic metadata defect, затем из-за попадания дополнительного `compose run`
контейнера в список backend IDs. Исправлены диагностика stdout Alembic и
выбор обычного контейнера по oneoff label; добавлен unit regression test.
Финальные полные прогоны прошли; первоначальные ошибки не выдаются за успех.

## Тесты

- **11 native PostgreSQL passed**, 28 нерелевантных тестов deselected,
  exit 0, Linux Docker container. Выбраны native migration/product catalog
  и standalone metadata tests. `TEST_DATABASE_URL` указывал на новую
  `admitflow_test_s203_*`, каждый destructive test владел отдельной схемой;
  только эта новая тестовая БД удалена после завершения.
- Проверены миграции пустой схемы, принятие legacy-схемы с непустой историей,
  отказ от несовместимой схемы, cascade-переход и нативный путь каталога.
  Тестовые downgrade работают только в принадлежащих тестам схемах.
- **5 launcher unit tests passed**, exit 0: Docker недоступен, backup failed
  блокирует backend/migrations, fingerprint замечает изменение истории,
  ошибки команды не скрываются, oneoff контейнеры не принимаются за backend.
  Эти unit tests не являются доказательством PostgreSQL-совместимости.
- `docker compose config --quiet`, сборка обоих образов, `py_compile` и
  `git diff --check` прошли. Docker frontend build включает TypeScript/build.
- Реальный Chromium: `/programs` → `/programs/sgu-2026-4576` через nginx/API/
  PostgreSQL на 390 и 1440 px; 0 page errors, overflow false. PNG просмотрены:
  [390 px](local-postgresql-390.png), [1440 px](local-postgresql-1440.png).

## Сохранность и границы

Фактически переиспользованы **admitflow_postgres_data** и **admitflow_raw_data**.
Имена и точки монтирования совпали до/после recreate. При старте защищённые
исторические таблицы существующего volume были пусты: не заявляется сохранение
несуществующих пользовательских записей. Непустая история проверена двумя
снимками в настоящем runtime и legacy-данными в нативных migration tests.

CSS/React v3 и применённые migration versions не менялись. Не добавлялись
source-backed значения, ML или вероятности. Raw volume не удалялся; проверена
идентичность mount, а не побайтовый аудит всего raw-хранилища.

Не подтверждаются публичный deployment/HTTPS, все release gates, hosted CI,
сутки работы источников, полная backend test suite или все браузеры. Текущее
использование локальных HTTP/dev credentials — только loopback development.
Production backup/restore и условия владельца остаются отдельными задачами.

## Повтор проверки

Из корня: `python scripts/local_smoke.py`. Нужны только Python 3.10+ и
запущенный Docker с Compose; первая сборка требует сети. Для быстрой повторной
проверки: `python scripts/local_smoke.py --no-build`. Следовать README;
на время fingerprint-проверки не запускать параллельные записи.

CPU-тесты launcher:
`backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_local_start.py`.
Нативные tests запускаются с `TEST_DATABASE_URL` отдельной одноразовой БД
`admitflow_test_*` и `pytest --require-postgres`; не указывать рабочую БД.
Изменения сохраняются локальными коммитами; push не выполняется.
