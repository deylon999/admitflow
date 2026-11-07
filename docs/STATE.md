# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-08. Последняя сессия: S200.

## Продолжение

- Текущая задача: T244.
- Следующая задача: T244.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

New functional phase on feat/catalog-vertical-slice. Audit first, then verified catalog APIs and four v3 pages. Preserve exact visual foundation; no ML development.

## Последняя завершённая работа

- T242: all 29 v3 routes copied on feat/frontend-v3-exact-copy from main; implementation 3e50540. Original source remains unchanged.
- 187 Chromium tests passed; 145 original/copy comparisons at five widths: zero different pixels, no overflow. Evidence: docs/evidence/frontend-v3-exact.md.

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Опорный мониторинг не включает все лицензированные вузы. 2026-11-05 islod.obrnadzor.gov.ru/rlic timeout; нужна доступная официальная выгрузка для T056. Живая кампания 2027 и суточное наблюдение не подтверждены.

## Проверенное окружение

- S199: npm ci offline, typecheck, build and source verification passed. Source/copy production JS and CSS identical. Dev launch smoke passed for landing, forecast, login.
- Managed Windows Vite optimizer access restrictions bypassed by Vite watch-build/preview launcher (refresh after edits, no HMR). All temporary servers stopped; tools backup removed.
- Backend, shared fixtures and Compose unchanged; API/PostgreSQL integration deliberately excluded. Docker/Nginx and hosted CI not run. Original has no implemented dark theme. No push/deployment.

## Готовность к выпуску

Принятые gates в STATE.json: не зафиксированы.
Технические результаты и внешние условия — [RELEASE_GATES.md](RELEASE_GATES.md).
Завершение задач не означает автоматическую приёмку gate.

## Чтение по задаче

Карта документов — [README.md](README.md). Полный TASKS, журнал и исследования
источников не входят в стартовый контекст. Старые передачи — [архив](archive/state-before-optimization.md).
