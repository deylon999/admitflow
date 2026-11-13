# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-13. Последняя сессия: S212.

## Продолжение

- Текущая задача: T286.
- Следующая задача: T286.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

KAN-214 PR3 lifecycle implementation T285-T289 from main5cddc54. Auth remains disabled; SMTP/frontend later PRs. No merge.

## Последняя завершённая работа

- T285: Confirmed PR15 merged/main5cddc54; PR2 accepted, lifecycle/CSRF/locking/replay/logout and real PostgreSQL acceptance documented before implementation.

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Знаменатель вузов взят из выгрузки реестра аккредитации 2026-11-10; программы, правила ЕГЭ и живые списки по стране не собраны. Живая кампания 2027 и суточное наблюдение не подтверждены.
- KAN-214: real SMTP provider/from/credentials and delivery verification absent; production HTTPS/trusted-proxy contract and SMTP egress require deployment owner agreement.

## Проверенное окружение

- S211: hosted source7a90d60/run43413656989 all4 jobs success:backend820 passed/0skip,frontend147,ETL55+1 explicit dataset skip,migrations0012/head/check; repository tools17/0skip. Local full811/0skip plus16 targeted cases documented separately; final SHA/latest checks in PR15 description.
- Frontend147/lint/typecheck/build,ETL55+1 explicit dataset skip,pip check pass; native clean migration0012/head/schema alignment pass; repository tools17 with1 local missing-PDF-dependency skip.
- Owned PostgreSQL17 test container/databases/random schemas removed; user DBs/volumes/other containers untouched. No frontend/CSS/CI/compose/applied-migration changes. Auth disabled by default; no real email or full auth acceptance.

## Готовность к выпуску

Принятые gates в STATE.json: не зафиксированы.
Технические результаты и внешние условия — [RELEASE_GATES.md](RELEASE_GATES.md).
Завершение задач не означает автоматическую приёмку gate.

## Чтение по задаче

Карта документов — [README.md](README.md). Полный TASKS, журнал и исследования
источников не входят в стартовый контекст. Старые передачи — [архив](archive/state-before-optimization.md).
