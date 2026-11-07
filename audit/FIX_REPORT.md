# Исправления и проверка

Рабочая ветка `review/vadim-audit-fixes`, база `ad5b938`. Push и merge не выполнялись.

| Коммит / этап | Изменения | Проверка |
| --- | --- | --- |
| b1e223d | История веток, план T238–T242; генерация STATE.md в старом roadmap | roadmap --render --check --self-test, 6 negative self-tests |
| f587eef | AUD-01–07: backup ownership, restore/raw verification, monitoring, Windows import | 27 targeted pytest; реальный restore 20 таблиц/1 raw; полный Linux PostgreSQL 565 passed / 0 skipped |
| T240 | AUD-08–10: session epoch/lock, удаление private cache при reset, корректный draft rollback | 125 Vitest; build; 13 Chromium API-регрессий passed |

Основные файлы backend: scripts/backup_production.py, backup_production.sh,
ops_check.py, backend/app/worker.py. Новые негативные проверки:
backend/tests/test_production_backup.py; расширены test_ops_check.py/test_worker.py.
Формат backup изменён явно в RUNBOOK. Существующие копии не удалены; для нового
monitoring нужна первая копия с verified.json. Неудачные `.writing-*` оставляются
для диагностики и не считаются проверенными.

Frontend: src/lib/api.ts, query-client.ts, pages/TrackerPage.tsx,
components/DirectionForm.tsx. Логика перенесена адресно из последующих коммитов main
`1c38475`, `3494ed6`, `b2cd2c4`; это не новый оригинальный вклад аудита.
Регрессионные тесты взяты из тех же коммитов с дополнением записи screenshot.
Полная FSD-реорганизация и поздний редизайн main не переносились.

До исправления: session unit 5 failed / 10 passed; draft E2E 3 failed / 1 passed
(9 остановлены лимитом ошибок); cache E2E 2 failed (4 не запускались).
После: все 13 regression E2E passed. Файлы before/after — screenshots/.

База проверки не объявлена production: SQLite для браузерных ручных сценариев,
PostgreSQL для всех native backend cases и отдельного source fixture API.
Первый полный backend запуск с Windows bind mount дал 564 passed / 1 failure:
spawn не успел создать marker за 2 секунды. Тот же тест, затем вся suite прошли
на native Linux filesystem без изменения таймаута или production-кода:
565 passed, 2 warnings, 0 skipped. Команды — FULL_AUDIT.md; XML — evidence/backend-native.xml.

Дополнительные браузерные, контейнерные и визуальные результаты дополняются после T241.
