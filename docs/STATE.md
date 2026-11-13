# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-13. Последняя сессия: S215.

## Продолжение

- Текущая задача: нет.
- Следующая задача: T304.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

KAN-214 PR6 PR19 awaits owner review/merge. Read docs/KAN-214-PR6.md and PR19 description for final head/hosted results. Do not merge or mark full KAN-214 done; actual SMTP delivery (or explicit owner exception), production HTTPS/trusted proxy/egress and visual variance review remain unaccepted.

## Последняя завершённая работа

- T300-T303: main/guest audit,32 security controls, populated graph migration/isolation, native-PG3 engines x5 hosted, full979/175 regression and visual diagnostics complete. T279/T304 remain review.

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Знаменатель вузов взят из выгрузки реестра аккредитации 2026-11-10; программы, правила ЕГЭ и живые списки по стране не собраны. Живая кампания 2027 и суточное наблюдение не подтверждены.
- KAN-214 PR6: no real SMTP provider/inbox delivery verified or owner exception; production HTTPS/Origin/cookies/trusted-proxy rate-limit policy/SMTP egress unverified. AUTH_ENABLED remains false. compose.prod auth/mail env and backend egress need reviewed deployment overlay. PR19/visual variance owner review pending.

## Проверенное окружение

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
