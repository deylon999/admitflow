# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-07. Последняя сессия: S195.

## Продолжение

- Текущая задача: нет.
- Следующая задача: T057.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

T237 Firefox CI regressions corrected locally;review docs/evidence/ui-ci-regressions.md. Local commit only;no push or fresh GitHub Actions result. Next product candidate T057.

## Последняя завершённая работа

- T237: five E2E files corrected after UI updates;full Firefox254passed/37existing skips,all14reported scenarios passed;production code unchanged.
- T233-T236 UI changes committed:2a9da3b frontend,16cb145 tests;verification and screenshots in docs/evidence/final-ui-quality.md.

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Опорный мониторинг не включает все лицензированные вузы. 2026-11-05 islod.obrnadzor.gov.ru/rlic timeout; нужна доступная официальная выгрузка для T056. Живая кампания 2027 и суточное наблюдение не подтверждены.

## Проверенное окружение

- S195: typecheck/lint/build/format/architecture passed;150unit;full Firefox254passed/37existing skips;39targetedChromium+39targetedFirefox passed;final4reset cases passed each browser.
- Actual isolated SQLite/FastAPI+production preview;Firefox works outside sandbox. Two Firefox PNGs viewed. Fresh Ubuntu/GitHub CI,source-fixture suites and reverse-proxy tests not verified this turn. Temporary servers stopped and test DB removed. No push.

## Готовность к выпуску

Принятые gates в STATE.json: не зафиксированы.
Технические результаты и внешние условия — [RELEASE_GATES.md](RELEASE_GATES.md).
Завершение задач не означает автоматическую приёмку gate.

## Чтение по задаче

Карта документов — [README.md](README.md). Полный TASKS, журнал и исследования
источников не входят в стартовый контекст. Старые передачи — [архив](archive/state-before-optimization.md).
