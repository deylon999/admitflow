# Контекст для продолжения

Последняя запись: **S046, 2026-11-01**. Подход **B03 завершён 10/10: T083–T092**, отдельный Conventional Commit на каждый шаг. Активной задачи нет. Точка продолжения — снять внешние блокеры T006/T013; STATE.nextTask=null, потому что доступных задач по текущему графу без внешних входов нет. Пользователь последние два раза просил по 10 задач; обычное прежнее предпочтение было 5. Следовать последнему запросу.

## Текущее состояние

- 40 done из 92, 3 review, 3 blocked. Все 7 release gates открыты. Оценка автоматического MVP около 40%, D1/30 (старт 2026-11-01). Новые подзадачи не означают достижение национального охвата или прохождение релизных gates.
- Ручной React-кабинет: CRUD, сессия/expiry/reset, идемпотентность, объяснение формулы, сравнение снимков/до 3 направлений, история до всех 500 записей страницами, экспорт и подтверждённый импорт JSON. Импорт проверяет файл до 8 MiB, переносит значения/даты в новые IDs/ownership, не cookie. Детерминированный ключ безопасен при потере ответа; повтор после удаления не восстанавливает удалённое.
- Проверка максимального pretty-export 20×500 с полными IDs/числами показала, что 6 MiB мало; лимит UI повышен до 8 MiB, перед HTTP данные нормализуются. Отдельный unit покрывает этот случай. Формула manual-v1 не менялась, импорт остаётся ручным.
- API: 8 MiB/10 секунд приёма тела, trusted Host, Origin/Fetch Metadata для записи, точный HTTPS PUBLIC_ORIGIN в production. Указания ALLOWED_HOSTS/PUBLIC_ORIGIN в .env.example/RUNBOOK. X-Request-ID создаётся сервером; журнал только method/route template/status/duration без cookie/query/тела. Uvicorn запускать с --no-access-log.
- /api/live не зависит от БД; /api/ready и /api/health возвращают 503 при DB outage. Покрытие /api/v1/coverage и UI: 2 вуза в справочнике, 0 автоматических источников, 0 published groups; nationalTotal=null. Ошибка не подменяется нулём. Production registry ПУСТ, assessmentAvailable=false.
- Контур импорта из B02 сохранён: строгие DTO/HMAC IDs, fetcher, карантин, raw store, атомарные версии публикации, очередь/lease/fencing, worker и CLI. Реальные адаптеры не аттестованы. Worker не оставлен loop-процессом и не включён в Compose автоматически.
- Raw retention: dry-run по умолчанию, --apply только для старых unreferenced hashes; межпроцессная блокировка держится от raw put до DB commit и во время cleanup. Все исторические refs сохраняются; DB failure запрещает удаление. Cleanup не охватывает capture bundles и .writing remnants, расписание не включено.
- Локальный SQLite backup/verify/restore: online DB copy + referenced raw из сохранённой БД, manifest/hash, integrity/FK, новая отсутствующая папка назначения. Восстановленный API сохраняет историю и изоляцию владельцев. Это не PostgreSQL/production backup и не измеренные RPO/RTO. Рабочие пользовательские БД не переключались.
- Alembic 0001–0004; development upgrade вместо create_all. Новых миграций B03 не потребовалось. Неожиданные unversioned схемы не угадывать/stamp-ить; downgrade нескольких parser versions одного raw может потребовать backup.
- Проверки текущего checkout: **188 backend passed / 1 PostgreSQL skipped; 62 frontend passed; build exit 0; 24 Chromium E2E passed**. После финального изменения размера файла отдельно 4 import/coverage E2E passed. Есть один warning зависимости Starlette/httpx. Подробности — S046 в LOG.
- docs/PROGRESS.md и CHECKLIST.md актуальны. Скриншоты desktop/mobile показывают синтетические карточки, 2/0/0 coverage и preview импорта без POST. Demo session удалена (204). Точная сверка Figma и локальные шрифты ещё не закрыты.

## Внешние блокеры и следующая работа

- **T006 blocked:** git ls-remote origin HEAD вновь не подключился к github.com:443. Нужны доступ GitHub и успешный remote workflow проверяемого SHA. Конфиг CI сохранён; не выдавать локальные тесты за CI.
- **T013 blocked:** оригинальные HTML двух списков не получены. Реальный capture СГУ вернул network_error/captured=false/exit 1; web-tool СГУ 4588 timeout, профиль СГУПС 1348 cache miss. Есть закрытая команда получения original bytes/manifest/hash; инструкции docs/sources/pilot.md. Выполнить её в среде с разрешённой сетью, проверить bytes/сезон/группу/полноту, затем обезличенные fixtures и реальные адаптеры. Извлечённый web-текст индекса не восстанавливать как оригинальный HTML.
- **T007 blocked:** нет локальных Inter/JetBrains Mono/лицензий; получение блокировалось WinError 10013. Снять после файлов и FontFace проверки.
- T014/T017 и широкий T032 требуют реального PostgreSQL, lock/lease/concurrency. Локальный psql/postgres/pg_ctl не найден, Docker Engine/config недоступны по ACL. T067 review: compose config был проверен, build/up по-прежнему нет. PG offline SQL не равен настоящему PG.
- T022 review: реальные группы/сезоны/фильтры требуют данных. После фиксации сезона и аттестации — поиск своей строки, автоматические assessments/diff, UI свежести, replay, наблюдение циклов.
- Широкие T019/T023/T025/T038/T039/T041/T043/T049 не закрыты локальными частями. До выпуска нужны реальные источники, PostgreSQL/Docker/CI, production backup/retention, наблюдаемость/нагрузка, браузеры/доступность и staging/HTTPS.
- Исследование касалось 2026 (архив вне сезона). Релизный сезон, площадка, домен/бюджет пока не выбраны. Вероятности поступления требуют истории и отдельной валидации; текущая модель — условные сценарии.

## Git и процессы

B03: 12b6e86 capture, ca5db61 budgets, 91f802c host/origin, cb28fd5 diagnostics, c280fda retention, 80d209d backup, 1820da9 restore, fcf1386 import API, 984e7bc import UI; заключительный коммит — coverage и checkpoint. Авторство пользователя сохранено; origin https://github.com/deylon999/admitflow.git. Push не подтверждён, force push запрещён без отдельного запроса. Прежний Site ID — ADR-017, новые Site не создавать.

Актуальный preview **http://127.0.0.1:5183/tracker**: frontend session 24508 (API_TARGET=8003), API session 38488 / PID 18244 на 8003, БД backend/.pytest_cache/batch03.db, revision 0004. API явно перезапущен после coverage, без reload и без access-log. Прежняя API session 76557 остановлена. Старые 5173/8000, 5180/8001, 5182/8002 не трогались и не считаются актуальными. Проверять живые процессы/порты перед запуском; запись session не доказывает их жизнь.

CLI smoke backup/verify/restore выполнен только на изолированной batch03.db: schema 0004, rawCount=0, восстановление в backend/.pytest_cache/recovery-smoke-d8506877-4ecb-4125-a0d4-bae1dc6b2a5d, exit 0. Retention dry-run — 0 кандидатов/удалений. Полный набор raw проверяется отдельными тестами с синтетическим источником. Ничего не удалять из рабочего окружения для снятия блокера.

Продолжение: читать ROADMAP/TASKS/DECISIONS/LOG, выполнить roadmap --check и --next, проверить git status. **Приоритет — получить реальные входы и окружение; не заменять это очередной десяткой синтетических адаптеров или переписыванием готового контура.** Сначала снять конкретный blocker и актуализировать граф. Временный backend/.pytest_cache/batch03.py служил обновлению статусов B03, не является частью приложения и не нужен для продолжения.
