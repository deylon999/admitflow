# Эксплуатация AdmitFlow

## Локальный каталог и импорт

После резервирования и остановки параллельных записей можно поднять существующий стек и добавить публичные metadata:

```bash
docker compose up --build -d --wait
docker compose exec backend python -m app.catalog_import
```

Импорт справочника и архивных программ СГУ повторяемый. При `catalog_identity_conflict` сверяйте идентичность, сохраняя существующие записи. Сам импорт metadata не загружает кандидатов.

Для официальных документов используйте `python -m app.program_catalog_import --help` из `backend/`. Нужны применённая схема PostgreSQL, явный `DATABASE_URL`, сверенные оригиналы и приватный `--raw-store`. Возобновляемый `app.program_catalog_batch` делит `capture --year YEAR --work-dir DIR` и `publish --year YEAR --captured DIR --raw-store DIR`. Перед публикацией сверяйте источники, кампанию и результат. Захват сам по себе не меняет публичную выдачу.

Для отчёта о программах используйте `python -m app.national_coverage --target-year 2027 --output coverage-2027.json`. Секция `programCoverage` показывает покрытие целевой кампании, архивные годы, частичные наборы, филиалы и версии опубликованных оригиналов. Статусы наблюдений относятся к конкретным страницам и датам проверки. Для воспроизведения импорта храните сверенные HTML и PDF под именами `<sha256>.html` и `<sha256>.pdf`.

## Миграции и диагностика

[Backend-контейнер](../backend/Dockerfile) выполняет `python -m alembic upgrade head` перед Uvicorn. В production `AUTO_CREATE_SCHEMA=false`. Для ручной диагностики из `backend/` с заданным `DATABASE_URL`:

```bash
python -m alembic current
python -m alembic heads
python -m alembic check
```

Сделайте проверенную копию перед upgrade. Репетируйте на отдельной PostgreSQL, сверяйте текущую ревизию, head и отсутствие drift. При ошибке сохраните диагностику и проверьте совместимость схемы перед повтором. Существующие тома и применённые миграции сохраняются.

Для списков используйте `python -m app.sources.cli --help`. Worker запускается отдельным Linux-процессом `python -m app.worker loop`. `python -m app.observability status` и `trace <runId>` показывают диагностику, а `python -m app.sources.retention --days 7` — план очистки raw. Применение очистки требует `--apply`.

После изменения справочника вузов проверьте политику проекции каталога. В PostgreSQL её можно обновить из `backend/` командой `python -m app.catalog.read_projection refresh-policy` с явно заданным `DATABASE_URL`.

## HTTPS и аккаунты

Используйте [production Compose](../compose.prod.yaml) и приватные переменные из [.env.production.example](../.env.production.example). Проверьте DNS, порты 80/443, `PUBLIC_ORIGIN`, `ALLOWED_HOSTS` и Secure cookies. Сохраните имя Compose-проекта, `POSTGRES_PASSWORD` и `SOURCE_IDENTITY_KEY`. Ротация ключа идентичности требует переноса ключей кандидатов.

```bash
docker compose -f compose.prod.yaml config --quiet
docker compose -f compose.prod.yaml up -d --build --wait
docker compose -f compose.prod.yaml exec backend python -m app.observability status
```

[Auth overlay](../compose.auth.yaml) явно включает аккаунты и сетевой выход backend. Нужны стабильный независимый `AUTH_RATE_KEY`, проверенный отправитель, SPF/DKIM/DMARC, SMTP STARTTLS или implicit TLS и контролируемый ящик. Проверяйте объединённый Compose через `config --quiet`, затем запускайте `python -m app.smtp_check` в backend. Для одиночного письма используйте `--send` с `AUTH_TEST_EMAIL`, переданным через `docker compose exec -e AUTH_TEST_EMAIL`.

Приёмка требует фактического получения писем в HTTPS-окружении: регистрация, повторное подтверждение, вход и восстановление с отзывом старых сессий. Проверяйте ошибку доставки и ограничения частоты. Записывайте только среду и результат. Автоматические сценарии с тестовым SMTP подтверждают логику приложения, внешние HTTPS и доставка проверяются отдельно.

## Копии и восстановление

- [backup_production.sh](../scripts/ops/backup_production.sh) копирует PostgreSQL и raw, проверяет dump в зарезервированной БД `admitflow_restore_check` и применяет ротацию копий. Согласуйте окно без записей, включая worker, и ограничьте доступ к каталогу резервирования.
- [Репетиция PostgreSQL восстановления](../scripts/qa/rehearse_postgres_restore.py) использует временный PostgreSQL. Перед восстановлением рабочей системы проверьте на отдельном стенде ревизию схемы, связи с raw, историю и smoke-сценарии.
- Для локальной SQLite используйте `python -m app.backup create`, `verify <папка>` и `restore <папка> --destination <новая папка>` из `backend/`. При `restore.pending` повторите восстановление в новом назначении.
