# Разработка и тесты

CI использует Python 3.12, Node.js 24 и PostgreSQL 17 на Linux. Из корня репозитория создайте и активируйте venv, затем установите зависимости:

```bash
python -m venv backend/.venv
python -m pip install -r backend/requirements-dev.txt -c backend/constraints.txt
python -m pip install -r scripts/requirements-dev.txt
```

Для полного локального стека используйте [быстрый запуск](../README.md#локальный-запуск). Для изменений интерфейса можно поднять временный FastAPI командой `node scripts/test-api.mjs` из `frontend/`. В другом терминале задайте `API_PROXY_TARGET=http://127.0.0.1:5303` и выполните `npm ci`, затем `npm run dev`. Без этой переменной proxy использует порт 8000.

Из `frontend/`:

```bash
npm ci
npm run lint
npm run typecheck
npm run build
npx playwright install chromium
npm test
```

Launcher Playwright сам запускает временный FastAPI с SQLite и production preview. Для отдельной визуальной проверки, live API и матрицы браузеров смотрите [frontend README](../frontend/README.md).

Из корня с работающим Docker:

```bash
python scripts/test_postgres.py
python -m pytest -q scripts/tests
python scripts/check_doc_links.py
python scripts/roadmap.py --check
python scripts/audit_evidence.py
```

`test_postgres.py` поднимает выделенную PostgreSQL. Полный backend-набор рассчитан на Linux, поскольку worker использует POSIX `resource`. [Workflow](../.github/workflows/ci.yml) отдельно проверяет frontend, backend и auth в трёх браузерах, миграции и ETL. При сбое используйте лог шага и артефакты соответствующего job.

Реестр задач и состояние редактируются в `TASKS.json` и `STATE.json`. `python scripts/roadmap.py --task Tnnn` выводит конкретную карточку и её прямые зависимости. `--render` обновляет корневой `CHECKLIST.md`. Для проверки исторических доказательств в shallow clone выполните `git fetch origin 6fdafc999606b486b200a8eac68d732dfd0a956e`.


Исследовательские CLI по умолчанию читают свежие локальные инвентари из
sources, если они сгенерированы. При их отсутствии берутся те же данные из
закреплённого коммита. Запуск с явным входным файлом по-прежнему читает этот файл.
Для воспроизведения этапов, использующих закрытые raw, дополнительно нужна
приватная копия оригиналов.

## Критерии проверки

- Проверяйте изменённый сценарий через его обычную точку входа, включая ошибки и ранее сохранённые данные. Для изменений схемы проверьте upgrade отдельно на PostgreSQL. Перед работой с существующей БД используйте [порядок резервирования](RUNBOOK.md#копии-и-восстановление).
- Для UI проверяйте ожидаемые состояния загрузки, ошибки, отсутствия данных и истечения сессии. Проверьте затронутые узкие экраны и управление с клавиатуры.
- Привязывайте результаты к SHA, команде и окружению в задаче или PR. Новые логи, скриншоты и JUnit храните в игнорируемом `test-results/` или в артефактах CI. Сохраняйте долгосрочное доказательство по неизменяемой ссылке.
