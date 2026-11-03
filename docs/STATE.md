# Контекст для продолжения

2026-11-03, S154: **B11 — 15/30 завершено**. Пользователь запросил следующие 30 задач; осталось 15. Работать шестью пятёрками, каждую задачу проверять и коммитить. TASKS.json — реестр, STATE.json — точка продолжения.

Завершены T019, T007, T008, T013, T027, T174, T029, T030, T032, T033, T175, T022, T176, T177, T021. Проверки и ограничения: docs/evidence/b11-progress.md. Следующая пятёрка: T178 удаление архивной записи; T179 immutable factual history; T180 UI сравнения фактов; T024 provenance; T023 история ручного режима. Затем продолжить ещё две пятёрки до 30.

SGU4588: один аттестованный архив 2026, 573 строки, общий бюджет16. Вероятности/официальный результат не рассчитываются. STU1348 — неподдержанный headers-only оригинал; второй адаптер T031 и автоматические gates остаются открыты. Не отмечать частичные broad-задачи done. Синтетические изменения для тестов явно отделять от настоящего архива.

Реальные публичные коды только в игнорируемом backend/var/research/sgu4588.original.html; не выводить в логи или browser traces. Derived fixture содержит только FIXTURE-коды и документирован как обезличенная производная DOM. Identity key backend/var/b11-identity.env600 — не печатать/не коммитить/не менять. .dockerignore исключает backend/var.

Own Compose admitflow-b11 на localhost8090 с настоящим архивом573 rows; backend пока образ T022/schema0004, требуется rebuild к текущему0006. Override /tmp/admitflow-b11/images.yaml. Только свои containers/volumes, соседний radar не трогать. Последний настоящий SGU HTTP17:45:52Z, не повторять чаще900сек; для тестов private replay или derived fixture. Worker loop не запущен.

`scripts/serve_source_e2e.py` держит disposable PG+Uvicorn8013, исключительно обезличенный fixture без HTTP-fetch. Лог /tmp/admitflow-b11/source-e2e.log, процесс родителя проверить перед остановкой; после изменений API перезапустить. E2E API_TARGET=http://127.0.0.1:8013 E2E_API=1 E2E_SOURCE=1 E2E_SOURCE_FIXTURE=1 E2E_SERVER=preview E2E_BASE_URL=http://127.0.0.1:4192. Не направлять FIXTURE-тесты на настоящий архив.

На15/30:100 frontend unit + отдельный новый контракт101;5 source flow+5 catalog Chromium;4 lookup/API;37 native passed, один старый table-count assertion исправлен и повторно проверен. Full396backend до новых API — исторический baseline. После всех30 нужны полный current backend/native/frontend/browser и runtime rebuild. Последний full B10 332/92/72 — исторический.

Коммиты локальные; gh не авторизован, remoteCI T006 заблокирован. HTTPS staging/live-soak/второй источник не проверены. Продолжать самостоятельные задачи, не выдавая локальный архив за production MVP. Helper /tmp/admitflow_b11.py start/done обновляет карточки/STATE/LOG/render/check.
