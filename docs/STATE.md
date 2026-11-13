# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-13. Последняя сессия: S211.

## Продолжение

- Текущая задача: нет.
- Следующая задача: не назначена.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

KAN-214 PR2 on feat/kan-214-register-login awaiting hosted checks and owner review/merge. T280-T283 done; T275/T284 review. Local811 backend+16 final negatives,frontend147,migrations0012 pass. Final SHA/run/PR in GitHub PR description. After owner merge continue T276 PR3, never merge autonomously. Auth disabled by default; real mail/refresh/logout not implemented.

## Последняя завершённая работа

- T283: Real verified-account login and current-session API, server-state checks, CSRF rotation, safe cookies, password-change/concurrent-login races and guest isolation verified.
- T282: Registration, unique-user/action persistence, CSRF/Origin and explicit mail failures verified.
- T281: Persistent HMAC budgets verified against native PostgreSQL concurrency/restart/windows.
- T280: PR14 merge/main494d270 and PR2 boundaries verified.

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Знаменатель вузов взят из выгрузки реестра аккредитации 2026-11-10; программы, правила ЕГЭ и живые списки по стране не собраны. Живая кампания 2027 и суточное наблюдение не подтверждены.
- KAN-214: real SMTP provider/from/credentials and delivery verification absent; production HTTPS/trusted-proxy contract and SMTP egress require deployment owner agreement.
- KAN-214 PR2 owner review/merge required before PR3. Real SMTP/confirmation/recovery and refresh/logout remain unimplemented; production auth must stay disabled.

## Проверенное окружение

- S211: local required-native-PG backend811 passed/0skip (collection before nine final test cases); current targeted16 passed covers those changes. Hosted expected820; final exact SHA/run/results in PR description.
- Frontend147/lint/typecheck/build,ETL55+1 explicit dataset skip,pip check pass; native clean migration0012/head/schema alignment pass; repository tools17 with1 local missing-PDF-dependency skip.
- Owned PostgreSQL17 test container/databases/random schemas removed; user DBs/volumes/other containers untouched. No frontend/CSS/CI/compose/applied-migration changes. Auth disabled by default; no real email or full auth acceptance.

## Готовность к выпуску

Принятые gates в STATE.json: не зафиксированы.
Технические результаты и внешние условия — [RELEASE_GATES.md](RELEASE_GATES.md).
Завершение задач не означает автоматическую приёмку gate.

## Чтение по задаче

Карта документов — [README.md](README.md). Полный TASKS, журнал и исследования
источников не входят в стартовый контекст. Старые передачи — [архив](archive/state-before-optimization.md).
