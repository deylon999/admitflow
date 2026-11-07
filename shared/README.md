# Исторические fixtures

`calculations.json` проверяет версионированную арифметику сохранённых manual
snapshot в backend. `manual-watch.json` — сохранённый manual data contract
для истории/импорта/экспорта и тестов сохранности. Новый frontend их не
использует и не получает из них прогнозы.

Файлы оставлены из-за зависимостей persisted-data механизма. Assessment-cases
для удалённой HTTP-обёртки `/assess` удалены. Данные PostgreSQL и миграции
не удаляются вместе с устаревшими UI/API тестами.
