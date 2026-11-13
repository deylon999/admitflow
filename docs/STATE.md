# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-13. Последняя сессия: S214.

## Продолжение

- Текущая задача: T298.
- Следующая задача: T298.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

KAN-214 PR5 React auth T295-T299 from main3035f5e. Separate account/guest lifecycle; no secrets in storage; SMTP/full production delivery remains external. No autonomous merge.

## Последняя завершённая работа

- T297: Live controlled auth/email-link forms implemented; nine new browser scenarios passed, typecheck/lint passed. Preserved public error contract and lazy auth/app bootstrap; real PostgreSQL lifecycle browser scenario also passed.

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Знаменатель вузов взят из выгрузки реестра аккредитации 2026-11-10; программы, правила ЕГЭ и живые списки по стране не собраны. Живая кампания 2027 и суточное наблюдение не подтверждены.
- KAN-214 real SMTP/provider inbox delivery and production HTTPS/proxy/egress gate remain unaccepted after code-only PR4 merge. Backend auth defaults disabled; frontend must show actual503 without fake success.

## Проверенное окружение

- S213: all-current local --require-postgres backend976/0skip; combined action/security83; mail/config35; frontend147/lint/typecheck/build. ETL55+1 explicit dataset skip; pip check clean; native clean migration0012/head/schema check passed.
- Repository tools17 with1 local PDF-dependency skip; hosted installs it. Exact final SHA/PR/verified hosted results in review PR description. All new tests collected before full run.
- Owned PG17 test schemas/container/anonymous volume cleaned. User DBs/volumes untouched; no frontend/CSS/CI/compose/dependency/applied-migration changes. SMTP config absent, no external mail sent or inbox verified; auth defaults disabled.

## Готовность к выпуску

Принятые gates в STATE.json: не зафиксированы.
Технические результаты и внешние условия — [RELEASE_GATES.md](RELEASE_GATES.md).
Завершение задач не означает автоматическую приёмку gate.

## Чтение по задаче

Карта документов — [README.md](README.md). Полный TASKS, журнал и исследования
источников не входят в стартовый контекст. Старые передачи — [архив](archive/state-before-optimization.md).
