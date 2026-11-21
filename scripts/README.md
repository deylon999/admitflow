# Служебные инструменты AdmitFlow

Команды Python ниже выполняются из корня репозитория. Для утилит, которые
импортируют backend, используйте его виртуальное окружение с
[requirements-dev.txt](../backend/requirements-dev.txt) и [constraints.txt](../backend/constraints.txt).
Доступ к приватным оригиналам, подготовка тестовой БД и параметры Compose
описаны в [runbook](../docs/RUNBOOK.md). Состав утилит и их потребители
приведены в [аудите](AUDIT.md).

| Путь | Назначение | Пример |
| --- | --- | --- |
| `scripts/` | Публичные команды разработки и тонкие точки совместимости | `python scripts/roadmap.py --check` |
| `scripts/data/` | Сбор, исследование, подготовка и сверка данных | `python -m scripts.data.build_exam_requirements --help` |
| `scripts/qa/` | Репетиции миграций, нагрузка и проверки evidence | `python -m scripts.qa.rehearse_postgres_restore --help` |
| `scripts/ops/` | Бэкап, проверка состояния и временный PostgreSQL для QA | `python -m scripts.ops.ops_check --help` |
| `scripts/reports/` | Отчёты по задачам и истории Git | `python -m scripts.reports.weekly_report --week 2026-W46 --format md` |
| `scripts/tests/` | Unit-тесты служебных утилит | `python -m unittest discover -s scripts/tests` |

Стабильные команды запуска остались в корне `scripts/`. У перемещённых
инструментов старые файловые пути перенаправляют к единственной реализации.
Модульная форма `python -m scripts.<раздел>.<имя>` запускается из корня.

~~~text
python scripts/local_smoke.py
python scripts/test_postgres.py
python scripts/check_auth_acceptance.py --help
python scripts/roadmap.py --check
~~~

Для отчётов PDF используется `scripts/requirements-report.txt`.
Для тестов отчёта установите `scripts/requirements-dev.txt`.
Инструкции для frontend-утилит и npm находятся в [frontend/README.md](../frontend/README.md).
Эксплуатационный `python -m app.sources.cli --help` выполняется из `backend/`.
