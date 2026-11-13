# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-13. Последняя сессия: S210.

## Продолжение

- Текущая задача: нет.
- Следующая задача: T275.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

KAN-214 PR1/6 in PR14 awaiting owner review/merge. T270-T274 implemented; final local backend763/0skip, frontend147, ETL55+1 explicit dataset skip, native migration0012/head/check pass. Latest hosted status/source SHA in PR14. No auth endpoints or frontend integration yet. After review/merge continue T275 PR2; never merge autonomously.

## Последняя завершённая работа

- T274: Argon2id RFC9106 production parameters, input policy, bounded capacity, dummy verification, rehash and purpose-separated tokens implemented;52 primitive/guest/API tests pass,pip check clean. PR1 awaiting review; PR2-6 not implemented.

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Знаменатель вузов взят из выгрузки реестра аккредитации 2026-11-10; программы, правила ЕГЭ и живые списки по стране не собраны. Живая кампания 2027 и суточное наблюдение не подтверждены.
- KAN-214: real SMTP provider/from/credentials and delivery verification absent; production HTTPS/trusted-proxy contract and SMTP egress require deployment owner agreement.
- PR14 owner review/merge required before PR2; KAN-214 full acceptance remains open.

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
