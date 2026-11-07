# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-08. Последняя сессия: S201.

## Продолжение

- Текущая задача: T249.
- Следующая задача: T249.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

User requested cleanup only. Branch chore/product-foundation-cleanup created from clean catalog state. Audit first; preserve v3 visuals, PostgreSQL data and all applied migrations. No new product features.

## Последняя завершённая работа

- T243: full 29-route functionality/demo/API/dependency/priority audit and backend reuse/model/API plan in docs/product-functional-audit.md.
- T244-T245: additive public catalog API + atomic reviewed metadata import and four React API pages. Existing models/DB reused; source scopes: 1257 reference institutions and two SGU archive-2026 contests, no invented cutoff/exams/ML.
- T246-T247: 47 backend passed/1 native PostgreSQL skipped; 193 Chromium passed including 125 pixel comparisons (100 raw +25 explicit demo labels); standalone default68 passed, 20 catalog screenshots at five widths; lint/TS/build/install passed.

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Опорный мониторинг не включает все лицензированные вузы. 2026-11-05 islod.obrnadzor.gov.ru/rlic timeout; нужна доступная официальная выгрузка для T056. Живая кампания 2027 и суточное наблюдение не подтверждены.

## Проверенное окружение

- Docker API/config permission denied; PostgreSQL unavailable and native test explicitly skipped. Real API E2E used owned temporary SQLite with current migrations; existing legacy user DB read-only inspected, not changed.
- 23 original UI/config files verified with four exact demo label changes/type-only fix; three integration compositions explicit. Original CSS and all 68 source files unchanged. No new runtime dependencies or product database.
- Windows Playwright webServer teardown hang fixed with scripts/test.mjs owning Vite previews and Python stdin shutdown. Standalone68 and visual193 finish and close servers. Early temp DB folders xhiql9eb/_wn5xa4d remain: automatic approval rejected outside-workspace deletion (sandbox_approval=false); no bypass.
- Hosted CI/Docker/Nginx/Firefox/WebKit not verified; full dark theme absent in source. No push/deployment; main, exact-copy and previous redesign branches unchanged.

## Готовность к выпуску

Принятые gates в STATE.json: не зафиксированы.
Технические результаты и внешние условия — [RELEASE_GATES.md](RELEASE_GATES.md).
Завершение задач не означает автоматическую приёмку gate.

## Чтение по задаче

Карта документов — [README.md](README.md). Полный TASKS, журнал и исследования
источников не входят в стартовый контекст. Старые передачи — [архив](archive/state-before-optimization.md).
