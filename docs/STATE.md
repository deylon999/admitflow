# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-13. Последняя сессия: S215.

## Продолжение

- Текущая задача: T303.
- Следующая задача: T303.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

KAN-214 PR6 final acceptance from owner-merged main12c78e4. Five tasks T300-T304: audit, security matrix, native-PG cross-browser/CI, regression/migration/visual, report/review. Do not merge autonomously or mark full acceptance without real delivery/owner decision.

## Последняя завершённая работа

- T302: Hosted source79a40fc/run43478500035 all4 jobs success: native-PG Chromium5 Firefox5 WebKit5, backend979/0skip, validator32 controls. Added engine identity proof and stale-report protection; local Chromium/Firefox5 each repeated after guest-cookie wait fix. Final head CI recorded in PR19.

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Знаменатель вузов взят из выгрузки реестра аккредитации 2026-11-10; программы, правила ЕГЭ и живые списки по стране не собраны. Живая кампания 2027 и суточное наблюдение не подтверждены.
- KAN-214 real SMTP/provider inbox delivery and production HTTPS/proxy/egress gate remain unaccepted after code-only PR4 merge. Backend auth defaults disabled; frontend must show actual503 without fake success.

## Проверенное окружение

- S214: frontend175 default tests/lint/typecheck/build, server lifecycle3; native PostgreSQL browser2 (private file mailer, no production delivery).
- Full native-PG backend976/0skip; ETL55+1 explicit dataset skip; repository tools17+1 optional local PDF skip; clean migrations0012/head/no schema drift. Hosted results/final SHA recorded in review PR description.
- Visual108/108 identical retained Live/Demo comparisons at390/1440, plus12 changed/technical screen captures; baseline/source comparison evidence committed. No CSS, backend product/migration/dependency/CI/Compose changes.
- Owned PostgreSQL17 test container admitflow-kan214-pr5-db stopped; its test-only volume preserved. Random test schemas cleaned. User DBs/volumes and running services untouched. Mailbox/clock/preview processes cleaned.

## Готовность к выпуску

Принятые gates в STATE.json: не зафиксированы.
Технические результаты и внешние условия — [RELEASE_GATES.md](RELEASE_GATES.md).
Завершение задач не означает автоматическую приёмку gate.

## Чтение по задаче

Карта документов — [README.md](README.md). Полный TASKS, журнал и исследования
источников не входят в стартовый контекст. Старые передачи — [архив](archive/state-before-optimization.md).
