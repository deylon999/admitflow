# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-13. Последняя сессия: S211.

## Продолжение

- Текущая задача: T281.
- Следующая задача: T281.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

KAN-214 PR2 implementation from main494d270. T280-T284; no merge. Real SMTP and full lifecycle remain PR3-6; auth disabled by default.

## Последняя завершённая работа

- T280: Verified PR14 merged/main494d270; PR2 acceptance and safe mail/CSRF/disabled-rollout boundaries recorded before implementation.

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Знаменатель вузов взят из выгрузки реестра аккредитации 2026-11-10; программы, правила ЕГЭ и живые списки по стране не собраны. Живая кампания 2027 и суточное наблюдение не подтверждены.
- KAN-214: real SMTP provider/from/credentials and delivery verification absent; production HTTPS/trusted-proxy contract and SMTP egress require deployment owner agreement.

## Проверенное окружение

- S210: final local required-native-PostgreSQL backend763 passed/0skip; frontend npm ci/lint/typecheck/build/test147 passed; ETL55 passed+1 explicit missing-dataset skip; migrations0012/head/schema check passed.
- Focused foundation/password/catalog48 passed. Real PostgreSQL17 random schemas prove uniqueness races, constraints, guest preservation and account cleanup. Owned test DB container/anonymous volume removed after tests; no AdmitFlow user DB/volume modified.
- PR14 first workflow43409888388; final SHA/latest hosted status maintained in PR14 description. No frontend/CSS/baseline/workflow/compose changes. No production email or HTTPS claim.

## Готовность к выпуску

Принятые gates в STATE.json: не зафиксированы.
Технические результаты и внешние условия — [RELEASE_GATES.md](RELEASE_GATES.md).
Завершение задач не означает автоматическую приёмку gate.

## Чтение по задаче

Карта документов — [README.md](README.md). Полный TASKS, журнал и исследования
источников не входят в стартовый контекст. Старые передачи — [архив](archive/state-before-optimization.md).
