# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-13. Последняя сессия: S213.

## Продолжение

- Текущая задача: нет.
- Следующая задача: не назначена.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

KAN-214 PR4 review for feat/kan-214-email-recovery. T290-T293 done; T277/T294 review. TLS SMTP,verification/resend,recovery/reset with all-session revocation implemented; local native-PG976/0skip,action/security83,mail/config35,frontend147,migrations0012. Exact final SHA/PR/verified hosted results in PR description. Owner review/merge required before T278 PR5. Real provider/inbox delivery,HTTPS/egress and frontend integration remain external/later gates; auth disabled, no autonomous merge.

## Последняя завершённая работа

- T293:Recovery/reset atomically changes hash, consumes actions and revokes target sessions;18 recovery and83 combined action/security tests pass.
- T292:Verification/resend and one-use confirm;43 native verification/registration tests pass.
- T291:TLS SMTP transport and fail-closed config; current35 mail/config tests pass, no real delivery verified.
- T290:PR16 merge/main d63a208, SMTP-field absence and acceptance verified.

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Знаменатель вузов взят из выгрузки реестра аккредитации 2026-11-10; программы, правила ЕГЭ и живые списки по стране не собраны. Живая кампания 2027 и суточное наблюдение не подтверждены.
- KAN-214 PR4 owner review/merge required before PR5. Real SMTP credentials/from/recipient and actual inbox delivery not supplied/verified; production HTTPS/client-address/SMTP-egress and frontend acceptance remain open. See RELEASE_GATES/KAN-214-PR4; code/mock delivery does not close full email acceptance.

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
