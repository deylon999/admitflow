# Контекст для продолжения

2026-11-03, B10: пользователь запросил10 задач, затем подтвердил «доделай». Основа33a962b; первая пятёрка завершена отдельными Conventional Commits: T103, T014, T017, T067, T168. Финальные70/70 Chromium прошли на actual nginx build и PostgreSQL API. Далее T169. Точная точка продолжения — STATE.json; статусы — TASKS.json.

## Новые факты окружения

Docker Engine29.9.2 теперь доступен. Linux/Python3.14.8/Node22.23.1, зависимости установлены. Свой PostgreSQL17.11 контейнер `admitflow-b10-pg`, localhost55439, disposable database `admitflow_test_b10`; native tests создают отдельную schema. Старые Windows session/PID из S123 здесь не действуют.

Compose project `admitflow-b10`: db/backend/frontend healthy, frontend **http://127.0.0.1:8089/tracker**; PostgreSQL17.11/revision0004, raw_data и postgres_data — новые volumes. Существующий проект radar не менялся. Runtime без host network, опубликован только frontend localhost8089. Build network Docker на этом хосте не имеет egress: образы успешно собраны с `docker build --network host --allow network.host`, см. RUNBOOK. API image соответствует текущему backend; frontend пересобирается после исправлений T168.

GitHub доступен через `git ls-remote`, remote HEAD33a962b. `gh auth status`: ни один host не авторизован. Push и remote CI не проверены; прежний сетевой блокер больше не актуален. Авторство Git не менялось; все новые коммиты локальные.

## Проверено B10

- T103:6 native legacy adoption/refusal cases passed; ID/история сохранены, неподходящие CHECK отвергнуты.
- T014:21 migration cases passed, включая7 native PG; disposable runner ждёт TCP readiness, набор без native cases возвращает exit1.
- T017:21 write tests passed, включая11 PG;20/500 limits, replay/tombstone и два независимых app pools с ожидаемым снимком дают201/409.
- T067:actual Compose build/start,15 HTTP smoke checks passed,204/204 cleanup; PG diagnostics readOnly/revision_current и прямой SELECT0004. Отчёт b10-compose-smoke.json.
- T168:92 frontend tests passed. Первый полный Chromium68/69 обнаружил потерю фокуса из-за deferred catalog options; stale options скрыты. Повторы9/9 прошли, следующий полный68/69 выявил другую гонку возврата фокуса на disabled кнопку после сохранения. Теперь возврат ждёт busy=false; при20 направлениях используется заголовок. Финальные12/12 повторных keyboard cases,92 unit tests/build и полный70/70 Chromium passed; новый boundary20-го направления проверен. Emitted chunk failure/reload проверен также через свежий vite preview; CI выбирает preview. Неизвестный E2E_SERVER даёт exit1.

## Следующая пятёрка

T169 — native queue/SKIP LOCKED и независимые worker-процессы; T170 — native atomic publish/rollback; T171 — отдельная репетиция pg_dump/raw restore; T172 —404 отсутствующих production assets/cache policy; T173 — пересоздание собственного Compose и worker recovery. Карточки добавлены, ещё todo. Все проверки на синтетических данных явно ограничены этим scope.

Автоматических аттестованных источников0, published groups0, nationalTotal=null; сезон/формула/согласия не менялись. Реальные HTML/font inputs и staging HTTPS отсутствуют; source gates открыты. T022 review. Проверки PostgreSQL/Compose теперь нельзя называть полностью отсутствующими, но production restore/live import/remote CI этим не подтверждены. Подробные команды, ошибки и evidence: docs/evidence/b10-runtime.md, docs/LOG.md. Никакие старые volumes не удалять и не stamp вслепую.
