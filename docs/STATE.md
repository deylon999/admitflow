# Актуальная передача контекста

Генерируется из [STATE.json](STATE.json): `python scripts/roadmap.py --render`.
Не редактировать вручную. История — [LOG.md](LOG.md); выборка — `--log --entries 1`.

Дата: 2026-11-13. Последняя сессия: S209.

## Продолжение

- Текущая задача: T269.
- Следующая задача: не назначена.
- Статусы, зависимости и acceptance: только [TASKS.json](TASKS.json).
- Карточка и прямые зависимости: `python scripts/roadmap.py --context`.

All29 direct/reload/internal/Back/Forward checks and dynamic/auth/unknown/query/hash boundaries passed; saved link and URL filters fixed. Full143 tests pass, lint/typecheck pass. Malformed percent encoding tested through SPA because Vite rejects it before React; nginx HTTP check remains T269. Next: T269

## Последняя завершённая работа

- T268: All29 direct/reload/internal/Back/Forward checks and dynamic/auth/unknown/query/hash boundaries passed; saved link and URL filters fixed. Full143 tests pass, lint/typecheck pass. Malformed percent encoding tested through SPA because Vite rejects it before React; nginx HTTP check remains T269.
- T267: Session-aware resource invalidation and cancelled private mutations implemented; explicit guest recovery, cross-tab expiry without loops, bounded group pagination and metadata errors verified. lint/typecheck and131 tests passed. PostgreSQL local_smoke exit0 with backup and persistence; frontend against PG next.
- T266: Reused request and concrete decoders; safe JSON/Headers, strict dates/IDs/ranks/nested fields, provenance and scoped catalog validation. 27 unit tests and full121 passed; lint/typecheck/build pass. First run had transient browser ERR_NO_BUFFER_SPACE before app; unchanged repeat passed.
- T265: Audit completed before code: current main07526c3 and merged PR12/11/9 checked, 29-route API/DTO/mode/navigation matrix and ten minimal fixes recorded. npm ci and baseline94 browser tests passed; SQLite browser stand is not PostgreSQL evidence.
- T260: аудит до реализации, подтверждённые пробелы и сохранённый зелёный baseline.

## Ограничения

- HTTPS staging/production: сервер, домен, бюджет и регион не выбраны.
- Оператор данных, сроки хранения, основание использования источников и настоящие данные в fixtures требуют решения владельца.
- Нужны живые тестеры для T052.
- Знаменатель вузов взят из выгрузки реестра аккредитации 2026-11-10; программы, правила ЕГЭ и живые списки по стране не собраны. Живая кампания 2027 и суточное наблюдение не подтверждены.

## Проверенное окружение

- S208: Node24.21.0 локально; Linux Python3.12.16/PostgreSQL17 в owned disposable runtime; frontend94, backend774+1dataset skip, migration32, tools17 passed.
- Hosted после разделения: backend719/0skip, ETL55+1explicit missing dataset skip, frontend94; four jobs success. NEG workflow failures и upload artifacts проверены скачиванием.
- Локальные admitflow-kan238-tests/pg и сеть admitflow-kan238 остановлены и удалены; пользовательские volumes не менялись. Test API завершён; production deploy не выполнялся.
- Старые private audit/evidence сохранены и исключены локально; новые raw logs/XML/trace в ignored .qa-tools и GitHub artifacts (7 дней), только компактный безопасный JSON добавлен в git.

## Готовность к выпуску

Принятые gates в STATE.json: не зафиксированы.
Технические результаты и внешние условия — [RELEASE_GATES.md](RELEASE_GATES.md).
Завершение задач не означает автоматическую приёмку gate.

## Чтение по задаче

Карта документов — [README.md](README.md). Полный TASKS, журнал и исследования
источников не входят в стартовый контекст. Старые передачи — [архив](archive/state-before-optimization.md).
