# Запуск каталога v3

Данные текущего среза: датированный справочник MICCEDU и два проверенных
архивных конкурса СГУ 2026. Неподключённые feature API явно обозначены;
демонстрационные экраны открываются отдельно.

## Существующий PostgreSQL-контур

Полный проверяемый старт из корня: `python scripts/local_smoke.py` — backup,
сборка, PostgreSQL, миграции, явный импорт и проверка сохранности при recreate.
См. [README](../README.md) и [результаты](evidence/local-postgresql.md).

Используются текущие Compose, backend и volume БД. Отдельного сервиса или
нового production-хранилища нет. После резервной копии данных выполнить
обычный запуск с миграциями и явный импорт публичных metadata:

```powershell
docker compose up --build -d
docker compose exec backend python -m app.catalog_import
```

Frontend: `http://localhost:8080`. Backend Dockerfile применяет существующий
Alembic upgrade перед Uvicorn. Импорт повторяемый и атомарный, не меняет
несовпадающие записи, не загружает кандидатов и не включает Sources/worker.
Ошибка `catalog_identity_conflict` требует сверки записи; не удалять её и
не исправлять seats вручную ради успешного импорта.

В S200 Docker был недоступен. Новая фактическая проверка S203 выполняется на
PostgreSQL; прежнее ограничение не считается её результатом.

## Локальная проверка без изменения пользовательской БД

Зависимости Python устанавливаются в существующий backend venv:

```powershell
cd backend
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
```

Из frontend запустить проверочный API на 5303:

```powershell
cd frontend
node scripts/test-api.mjs
```

Он использует настоящий FastAPI и миграции во **временной SQLite**,
импортирует только проверенные публичные metadata. Временная БД нужна для
изолированной проверки при недоступном PostgreSQL, не является новой БД
продукта и не меняет `backend/abiturient.db`. Она удаляется при штатном
завершении процесса. Это тот же контур, который проверяет Playwright.

В другом терминале, из frontend:

```powershell
npm ci
$env:API_PROXY_TARGET='http://127.0.0.1:5303'
npm run dev
```

Открыть `http://localhost:5173/universities?q=СГУ+Чернышевского`.
Обычный dev/preview proxy по умолчанию использует localhost:8000 для уже
настроенного backend с собственным DATABASE_URL и миграциями. Переменные
`.env.example` не загружаются Python автоматически: задавать их в окружении
или через существующий Compose. Без program import программы пусты.

Прямой metadata import из backend с настроенным DATABASE_URL и уже применённой
схемой: `.venv/Scripts/python.exe -m app.catalog_import`.

## Проверки

```powershell
cd frontend
npm run typecheck
npm run lint
npm run build
npm test
```

`npm test` сам запускает API на 5303 и production preview на 5301. Нужны
свободные порты, установленные backend requirements-dev и Chromium
(`npx playwright install chromium`). Launcher выбирает PYTHON из окружения,
backend/.venv/Scripts/python.exe, backend/.venv/bin/python либо системный python.

Полное сравнение с соседним оригинальным React (источник только читается):

```powershell
npm run test:visual
node scripts/summarize-visual.mjs
npm run verify:source
```

Обычный QA пишет в ignored test-results/evidence. Для нового сохраняемого
отчёта заранее задать QA_EVIDENCE_DIR (путь относительно frontend).
Предыдущие committed отчёты автоматически не перезаписываются.
QA_BASELINE_REF позволяет сравнить четыре catalog-страницы с сохранёнными
PNG выбранного commit; в S201 использован 2a7835f.

Сравниваются 25 страниц вне каталога. Для четырёх demo-подписей разрешены
точные текстовые замены в эталоне. Каталог проверяется реальными API-сценариями
и скриншотами пяти ширин, без подстановки demo-МТУСИ.

Из backend:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_product_catalog.py tests/test_catalog.py tests/test_national_catalog.py tests/test_group_catalog.py tests/test_api.py tests/test_contracts.py
```

Нативный тест использует только выделенную схему disposable-БД
`admitflow_test*`, не рабочую базу:

```powershell
$env:TEST_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:PORT/admitflow_test_catalog'
.venv/Scripts/python.exe -m pytest -q tests/test_product_catalog.py --require-postgres
```

Без TEST_DATABASE_URL PostgreSQL case пропускается, что не означает успех.
Deployment, свежесть кампании 2027 и ML эти проверки не подтверждают.
