# Исправления и проверка

Рабочая ветка `review/vadim-audit-fixes`, база `ad5b938`. Ветка опубликована на GitHub; PR и merge не выполнялись.

| Коммит / этап | Изменения | Проверка |
| --- | --- | --- |
| b1e223d | История веток, план T238–T242; генерация STATE.md в старом roadmap | roadmap --render --check --self-test, 6 negative self-tests |
| f587eef | AUD-01–07: backup ownership, restore/raw verification, monitoring, Windows import | 27 targeted pytest; реальный restore 20 таблиц/1 raw; полный Linux PostgreSQL 565 passed / 0 skipped |
| e3ae7dd | AUD-08–10: session epoch/lock, удаление private cache при reset, корректный draft rollback | 125 Vitest; build; 13 Chromium API-регрессий passed |
| 1441d00 | AUD-11: WebKit picker blur; AUD-12: focus превью после commit; запись responsive PNG | До: 2 WebKit catalog failures; source 95 passed/10 failed. После: 15 catalog и 90 source fixture API E2E passed на пяти профилях |

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

Полная browser matrix до последних двух исправлений: 600 collected,
434 passed, 163 scoped skips, 3 failed. Два WebKit catalog failure — AUD-11;
третий — Firefox font test увидел запрос установленного расширения Kaspersky
к стороннему домену. Повтор Firefox дал тот же внешний запрос; app font assertions
прошли. Для source-failure E2E область проверки POST уточнена до своего API,
так как сторонние запросы расширения не означают мутацию приложения.
Финальные целевые прогоны источника — 90/90, каталога — 15/15;
после этих правок Vitest 125/125 и production build прошли. Полный прогон
600 тестов повторно не запускался: целевые тесты покрывают исправленные
сценарии, а исходное Firefox падение зависит от внешнего расширения.
