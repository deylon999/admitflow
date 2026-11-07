# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-07. Последняя сессия: S194.

## Продолжение

- Текущая задача: нет.
- Следующая задача: T057.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

User authorized commits after T236. Frontend committed as 2a9da3b; tests as 16cb145; UI evidence and session state committed separately. No push. Next product candidate T057.

## Последняя завершённая работа

- T233-T236 UI changes committed:2a9da3b frontend,16cb145 tests;verification and screenshots in docs/evidence/final-ui-quality.md.

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Опорный мониторинг не включает все лицензированные вузы. 2026-11-05 islod.obrnadzor.gov.ru/rlic timeout; нужна доступная официальная выгрузка для T056. Живая кампания 2027 и суточное наблюдение не подтверждены.

## Проверенное окружение

- S193: typecheck/lint/build/format/architecture passed;150unit;72matrix+50regression Chromium passed/2reviewed-source API skips;12actual screenshots viewed and saved.
- Chromium production UI checked at375/768/1280/1920 light/dark. Firefox page creation Target crashed;WebKit absent;physical devices/live API/full WCAG not verified. No backend/business/FSD changes. Temporary preview stopped.
- S194: user requested commits; prior verification retained because application files did not change. git diff --cached --check passed before commits. No push.

## Готовность к выпуску

Принятые gates в STATE.json: не зафиксированы.
Технические результаты и внешние условия — [RELEASE_GATES.md](RELEASE_GATES.md).
Завершение задач не означает автоматическую приёмку gate.

## Чтение по задаче

Карта документов — [README.md](README.md). Полный TASKS, журнал и исследования
источников не входят в стартовый контекст. Старые передачи — [архив](archive/state-before-optimization.md).
