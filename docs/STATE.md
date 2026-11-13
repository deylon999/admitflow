# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-13. Последняя сессия: S213.

## Продолжение

- Текущая задача: T293.
- Следующая задача: T293.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

KAN-214 PR4 SMTP/verification/recovery T290-T294 from main d63a208. Real delivery remains externally unverified; auth disabled, frontend PR5 and no autonomous merge.

## Последняя завершённая работа

- T292: Verification/resend implemented;43 native PG verification+registration tests pass including real register-confirm-login, token purpose/expiry/one-use, races, uniform public responses and provider outage/failure. No automatic login or real delivery claim.

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Знаменатель вузов взят из выгрузки реестра аккредитации 2026-11-10; программы, правила ЕГЭ и живые списки по стране не собраны. Живая кампания 2027 и суточное наблюдение не подтверждены.
- KAN-214: real SMTP provider/from/credentials and delivery verification absent; production HTTPS/trusted-proxy contract and SMTP egress require deployment owner agreement.

## Проверенное окружение

- S212: full local --require-postgres backend867 passed/0skip (all new cases collected before run); lifecycle security47 passed; frontend147/lint/typecheck/build; ETL55+1 explicit dataset skip; pip check clean.
- Fresh native PostgreSQL migration0012/head/schema check passed; repository tools17 with1 local missing-PDF-dependency skip (hosted installs dependencies). Exact final SHA/hosted run/results in review PR description.
- Owned PostgreSQL17 test DB container/anonymous volume and all random schemas removed after tests. User DBs/volumes/other containers untouched; no frontend/CSS/CI/compose/dependency/applied-migration changes.

## Готовность к выпуску

Принятые gates в STATE.json: не зафиксированы.
Технические результаты и внешние условия — [RELEASE_GATES.md](RELEASE_GATES.md).
Завершение задач не означает автоматическую приёмку gate.

## Чтение по задаче

Карта документов — [README.md](README.md). Полный TASKS, журнал и исследования
источников не входят в стартовый контекст. Старые передачи — [архив](archive/state-before-optimization.md).
