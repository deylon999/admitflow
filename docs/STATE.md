# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-10. Последняя сессия: S202.

## Продолжение

- Текущая задача: нет.
- Следующая задача: не назначена.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

T253 P0 production API block complete;implementation69275e6 plus final204 acknowledgement regression. Review docs/evidence/v3-production-api.md. Local commits,no push. New feature APIs are separate tasks;T250 native PostgreSQL remains blocked.

## Последняя завершённая работа

- T253: consolidated P0 API/DTO/errors with live route bindings and explicit demo/unsupported;all29originalroutes smoke passed;implementation69275e6.

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Опорный мониторинг не включает все лицензированные вузы. 2026-11-05 islod.obrnadzor.gov.ru/rlic timeout; нужна доступная официальная выгрузка для T056. Живая кампания 2027 и суточное наблюдение не подтверждены.

## Проверенное окружение

- S202: frontend typecheck/lint/build exit0;84Chromium passed/0failed/skipped (17.0s),including29route smoke,16API tests,catalog and demo regressions.
- CSS v3,backend,applied migrations and PostgreSQL data unchanged. Existing owned FastAPI/SQLite runner used;native guest start/empty history verified,positive lookup/confirm/error injection via synthetic HTTP fixtures.
- Native PostgreSQL T250,Firefox/WebKit,fresh hosted CI,full reference pixel comparison and deployment not verified. QA runner stopped owned servers. Local commits only;no push.

## Готовность к выпуску

Принятые gates в STATE.json: не зафиксированы.
Технические результаты и внешние условия — [RELEASE_GATES.md](RELEASE_GATES.md).
Завершение задач не означает автоматическую приёмку gate.

## Чтение по задаче

Карта документов — [README.md](README.md). Полный TASKS, журнал и исследования
источников не входят в стартовый контекст. Старые передачи — [архив](archive/state-before-optimization.md).
