# Контекст для продолжения

Последняя запись: **S057, 2026-11-01**. **B04 завершён 10/10: T093–T102**, отдельный английский Conventional Commit на каждый шаг. Активной задачи нет, STATE.nextTask=null. Последнее предпочтение пользователя — по 10 задач.

## Текущее состояние

- **50 done из 102**, 3 review, 3 blocked, 46 todo. Все 7 release gates открыты. Оценка автоматического MVP остаётся **около 40%, D1/30**, старт 2026-11-01. Исправленные дефекты не сняли блокеры автоматизации; число карточек не равно готовности.
- React-кабинет: ручной CRUD, история всех 500 записей страницами, сравнение снимков/до 3 направлений, формула, экспорт/подтверждённый импорт JSON, ownership, сессия 30 дней, expiry/reset, идемпотентность и лимиты. Replay импорта работает и при 20 направлениях; новый файл получает 409. Лимит файла/тела 8 MiB, максимальный pretty export 20×500 покрыт тестом.
- B04 frontend: точный календарь/timezone/микросекунды и порядок всей истории; field errors/aria/focus; подтверждение потери изменённой формы при cancel/switch/обычной ссылке и beforeunload. SPA back/forward/crash recovery и сохранение черновика на диск не заявляются. Любой query/mutation 401 скрывает старый кабинет без автоматического POST session; новый доступ только явно.
- Лендинг/карточки ограничены условным ручным сценарием, без официального места и универсального правила согласий. Формула manual-v1 не менялась. Импорт остаётся ручным, старые даты не означают новое обновление вуза. Вероятность не реализована.
- API: trusted Host, production HTTPS PUBLIC_ORIGIN, 8 MiB/10 секунд тела, серверный request ID и безопасный JSON-журнал, отдельные live/ready. Uvicorn --no-access-log. Alembic0001–0004, development upgrade вместо create_all, B04 без новой миграции. Неожиданные unversioned схемы не stamp-ить.
- Каталог/coverage: **2 вуза, 0 автоисточников, 0 published groups**, nationalTotal=null, production registry пуст, assessmentAvailable=false. Контур HMAC DTO/fetcher/validator/quarantine/raw/атомарных публикаций/очереди/worker проверен синтетически; реальных аттестованных адаптеров нет.
- B04 backend: общий deadline RLock+OS lock; bounded private spool вместо потенциально блокирующего Pipe.recv; child deadline включает обмен результатом, size/hash/schema проверяются до публикации. Failed/expired jobs дают source_error даже после недавнего успеха; snapshot/даты/archive сохраняются. WorkerState без token/внутренних ошибок. Порядок write-locks не менялся.
- Retention dry-run по умолчанию, apply только старых unreferenced hashes. Все исторические refs сохраняются; DB failure запрещает удаление; lock от raw put до DB commit и на cleanup. Capture bundles/.writing и расписание не включены.
- SQLite backup/verify/restore локальны. Restore резервирует новую папку exclusive mkdir и передаёт проверенные файлы hard links без overwrite (нужна поддержка в одном томе). При частичном сбое restore.pending запрещает verify, миграции и startup API, включая AUTO_CREATE_SCHEMA=false. Повторять в новую папку, маркер не обходить. Конкурентный restore даёт один успех. PostgreSQL/production recovery и RPO/RTO не подтверждены.
- Финальный прогон: **196 backend passed / 1 PostgreSQL skipped, 67 frontend passed, build exit0, 32 Chromium E2E passed** на явно перезапущенном текущем API. Один warning Starlette/httpx. Roadmap render/check/self-test — S057.
- CHECKLIST.md/TASKS.md генерируются; PROGRESS.md — визуальный прогресс B01–B04. Desktop/mobile screenshots B04: синтетические карточки, coverage2/0/0, ошибка формы и фокус; horizontal overflow нет. Это не приёмка Figma/шрифтов. Demo sessions удалены, пользовательские БД не переключались.

## Критический путь и блокеры

- **T006 blocked:** GitHub:443 недоступен; push/remote CI не подтверждены. Нужен успешный remote workflow конкретного SHA; локальные тесты не заменяют CI.
- **T013 blocked:** нет оригинальных HTML двух списков. Capture СГУ network_error, web detail СГУ timeout, СГУПС cache miss. Готова закрытая capture-команда original bytes/manifest/hash: docs/sources/pilot.md. Получить реальные ответы, проверить сезон/группу/полноту, обезличить fixtures. Извлечённый web-текст не подделывать под оригинальный HTML.
- **T007 blocked:** локальные Inter/JetBrains Mono и лицензии не получены, remote probe также не прошёл. После файлов проверить FontFace/макеты; fallback не закрывает задачу.
- T014/T017/T032 требуют настоящего PostgreSQL и concurrency. psql/postgres/pg_ctl локально не найдены; Docker Engine/config недоступны по ACL. T067 review: compose config проверялся, build/up — нет. Не обходить ACL, offline SQL не равен PG.
- T022 review: реальные группы/сезоны/фильтры требуют источников. После выбора релизного сезона и аттестации — lookup своей строки, автоматические assessments/diff, UI и реальные циклы. Исследование 2026 вне сезона требует архивной метки. Вероятности — отдельная работа с историей/backtest.
- Широкие T019/T023/T025/T026/T035/T038/T039/T041/T043/T049 не закрыты локальными частями. Нужны реальный автоматический путь, браузерная/визуальная приёмка, нагрузка, production backup, staging/HTTPS. Площадка/домен/бюджет не выбраны.
- Отправлен асинхронный вопрос о путях original HTML/шрифтов и адресе уже работающего PG без пароля. К checkpoint ответа нет; проверить новые сообщения/входы перед продолжением.

## Git и процессы

B04: c1efb3e (формулировки), 27e43a2 (replay), e56b820 (timestamps/history), a3f1ede (field errors), f83f07d (черновик), 763e4de (expiry), 973ad47 (lock deadline), 3cd2fbb (fetch exchange), b1c002c (restore); десятый коммит — worker diagnostics/checkpoint S057. История B01–B03 сохранена в LOG/Git. Автор deylon999; origin https://github.com/deylon999/admitflow.git. Коммиты локальные, push не подтверждён, force push без отдельного запроса запрещён. Прежний Site ID — ADR-017, новый Site не создавать.

Preview **http://127.0.0.1:5183/tracker**. Frontend session24508, API_TARGET=8003. Актуальный API **session98287 / PID19396**, порт8003, изолированная backend/.pytest_cache/batch04.db, revision0004, без reload/access-log. Прежняя API session38488/PID18244 остановлена перед финальным прогоном. Старые 5173/8000, 5180/8001, 5182/8002 не трогались и не считаются актуальными. Перед повторным запуском проверить жизнь процессов.

Продолжение: STATE → ROADMAP → roadmap --check/--next → карточка/DECISIONS/LOG → реальные файлы/git status. **Приоритет — реальные HTML, PG/Docker, CI, шрифты. Не заменять критический путь десяткой синтетических адаптеров или переписыванием готового контура.** Новые воспроизводимые дефекты фиксировать карточками/доказательствами, не повышая готовность от их числа. Временный backend/.pytest_cache/batch04.py — только помощник статусов; init повторно не запускать.
