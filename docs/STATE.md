# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-21. Последняя сессия: S225.

## Продолжение

- Текущая задача: нет.
- Следующая задача: T316.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

Review PR27 (KAN-218 PR1), check exact head CI in PR description; no automatic merge. After owner merge, new main -> T317 official-source import and concrete KAN-223 DTO agreement. Target2027 >=471/785 remains unmet.

## Последняя завершённая работа

- KAN-218 PR1: audit current main, catalog and source pipeline
- KAN-218 PR1: define identity, campaign and publication architecture
- KAN-218 PR1: implement reproducible scoped identity keys
- KAN-218 PR1: add compatible Program and competition relationships

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Знаменатель вузов взят из выгрузки реестра аккредитации 2026-11-10; программы, правила ЕГЭ и живые списки по стране не собраны. Живая кампания 2027 и суточное наблюдение не подтверждены.
- KAN-214 PR6: no real SMTP provider/inbox delivery verified or owner exception; production HTTPS/Origin/cookies/trusted-proxy rate-limit policy/SMTP egress unverified. AUTH_ENABLED remains false. compose.prod auth/mail env and backend egress need reviewed deployment overlay. PR19/visual variance owner review pending.
- 2026-11-14 real SMTP setup: no provider host/credentials/verified sender/HTTPS staging/controlled inbox supplied; drafts21/22 and frontend stack prepared, live register/resend/recovery receipt pending.

## Проверенное окружение

- S225: PostgreSQL17 identity/storage/migrations/account-foundation100 passed0skip; frontend384/typecheck/lint/build, roadmap-unit10 pass. Initial full CI1075pass/1 stale added-table expectation corrected; final Linux CI/exact SHA tracked in PR27. Windows full backend needs existing Linux resource module. No product DTO/frontend/workflow changes.
- S215 local backend979/0skip,315.55s; security selection112; frontend175/lint/typecheck/build; validator3/lifecycle3; migrations0012/head/no drift. ETL55+1 external dataset skip, tools20+1 optional local PDF skip.
- Hosted milestone79a40fc/run43478500035 all4 success: backend979/0skip, native-PG Chromium5 Firefox5 WebKit5,32 controls, tools20/0skip. Final source rechecked by CI; final head/results maintained in PR19 description.
- Visual124 Live/Demo pairs at390/1440:123 exact;15px maxRGBdelta1 /programs border variance, repeats/raw images preserved. Identical frontend/src tree0b245e8e108d5c1a0b93e9a8290969bd6321c021; no CSS/product code/baseline changes.
- Owned local PG container admitflow-kan214-pr5-db stopped after tests; test-only volume preserved, random schema/private mailbox/runtime processes cleaned. User data and other services untouched.

## Готовность к выпуску

Принятые gates в STATE.json: не зафиксированы.
Технические результаты и внешние условия — [RELEASE_GATES.md](RELEASE_GATES.md).
Завершение задач не означает автоматическую приёмку gate.

## Чтение по задаче

Карта документов — [README.md](README.md). Полный TASKS, журнал и исследования
источников не входят в стартовый контекст. Старые передачи — [архив](archive/state-before-optimization.md).
