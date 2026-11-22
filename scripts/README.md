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


## Команды, которые используют разработчики и CI

| Команда из корня | Основные аргументы | Зависимости и эффект |
| --- | --- | --- |
| `python scripts/local_smoke.py` | `--output DIR`, `--no-build` | Docker Compose, PostgreSQL и собранный frontend. Делает backup, применяет миграции, проверяет синтетическую историю, пересоздаёт контейнеры. Выделенный проект для тестирования описан в runbook и аудите |
| `python scripts/test_postgres.py` | `--python PYTHON`, список путей тестов относительно `backend/` | Docker, backend dev. Поднимает выделенный PostgreSQL и запускает pytest, затем останавливает свой контейнер |
| `python scripts/roadmap.py --check` | `--context`, `--task ID`, `--log` и `--render` | Python stdlib и реестры docs. `--check` сверяет локальные и архивные доказательства, `--render` обновляет CHECKLIST.md |
| `python scripts/check_auth_acceptance.py --help` | `--matrix`, `--backend-junit`, `--browser-results`, `--output` | Python stdlib, матрица auth и результаты реальных тестов. Пишет сводку в указанный файл |
| `python scripts/check_doc_links.py` | `--help` | Python stdlib и Git. Проверяет локальные ссылки и якоря, выводит результат в stdout |
| `python -m scripts.ops.ops_check` | `--compose`, `--backups`, `--disk` | Docker Compose. Читает состояние приложения и копий. `ALERT_WEBHOOK_URL` включает уведомления |
| `scripts/ops/backup_production.sh OUTPUT_DIR` | `COMPOSE`, `RAW_SERVICE`, `KEEP_DAYS` | Bash, Compose и PostgreSQL. Создаёт dump/raw, использует зарезервированную служебную БД, удаляет старые каталоги копий. Перед запуском прочитайте runbook |
| `python -m scripts.qa.rehearse_postgres_restore --help` | `--output FILE`, `--archive-sgu` | Docker и backend dev. Репетиция на выделенной БД, запись отчёта |
| `python -m scripts.reports.weekly_report --week YYYY-WNN` | `--format {pdf,md}`, `--extra`, `--output`, `--main`, `--font` | Git и реестр задач, для PDF — ReportLab и шрифт. Пишет файл или выводит Markdown |

[Все параметры и побочные эффекты](AUDIT.md#аргументы-host-утилит) описаны
в аудите. Там же приведены [операторские CLI backend](AUDIT.md#backend-cli-и-запускаемые-тестовые-стенды)
и [frontend-инструменты](AUDIT.md#аргументы-frontend-инструментов).
python scripts/audit_evidence.py проверяет входы тестов и исторический SHA‑256 манифест визуальных эталонов.
