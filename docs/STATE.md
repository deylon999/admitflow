# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-21. Последняя сессия: S228.

## Продолжение

- Текущая задача: нет.
- Следующая задача: T326.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

T327 approved. API/frontend continuation of already-merged PR28 is implemented in its existing branch based on main@06fc988. T325/T328 done; T326/T317 review, exact branch CI and comparison in PR28 description. New review merge requires owner decision as merged PR28 cannot accept more commits. No new PR requested. Isolated2027 rehearsal1/785, national target471 remains open.

## Последняя завершённая работа

- T327 approved contract; T325 verified current-publication API; T328 compatible frontend. API/browser proof with two verified HSE2027 programmes and preserved legacy SGU IDs.

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Знаменатель вузов взят из выгрузки реестра аккредитации 2026-11-10; программы, правила ЕГЭ и живые списки по стране не собраны. Живая кампания 2027 и суточное наблюдение не подтверждены.
- KAN-214 PR6: no real SMTP provider/inbox delivery verified or owner exception; production HTTPS/Origin/cookies/trusted-proxy rate-limit policy/SMTP egress unverified. AUTH_ENABLED remains false. compose.prod auth/mail env and backend egress need reviewed deployment overlay. PR19/visual variance owner review pending.
- 2026-11-14 real SMTP setup: no provider host/credentials/verified sender/HTTPS staging/controlled inbox supplied; drafts21/22 and frontend stack prepared, live register/resend/recovery receipt pending.

## Проверенное окружение

- S228: disposable PG17.11/0014, 113 tests without skips (85.33s), schema alignment and preserved subscriptions/snapshots. Typecheck/lint/build and Playwright387 pass; actual-original HSE journey pass in Chromium. Full Linux results linked in PR28.
- S227 на main@0449e66: backend 118 успешных проверок с PostgreSQL 17.11 и --require-postgres. Сборка, проверка типов и линтер прошли. Chromium: 380 успешных и 4 неуспешных проверки из-за горизонтальной прокрутки страниц вузов при 390 px. Полный Compose-прогон остановился на docker info.
- S226 CI correction: backup/restore14pass; disposable PostgreSQL17 migration/storage/import/identity/backup/restore101passed0skip59.42s. Only exact reviewed migration trigger definitions accepted; modified/missing/extra objects rejected. Final Linux CI tracked in PR28.
- S226: nativePG extended125/0skip + final importer20/0skip; actual originals rehearsal eecba42 on PG17.11/0014 creates4canonical facts and repeat unchanged. Old public SGU2 preserved; public2027 coverage0 pending DTO agreement. Own containers/schemas only.
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
