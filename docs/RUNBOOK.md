# Эксплуатация AdmitFlow

[Оглавление](README.md) · [Архитектура](ARCHITECTURE.md) · [Готовность выпуска](RELEASE_GATES.md)

## Команды приложения

- **Локальный PostgreSQL и каталог.** [Запуск, проверки и импорт](catalog-runbook.md). `python scripts/local_smoke.py` из корня создаёт резервную копию, запускает стек, применяет миграции через контейнер backend и проверяет сохранность истории после пересоздания. Обычная остановка — `docker compose stop`. Перед запуском на существующих данных согласуйте окно и приостановите остальные записи.
- **Работа над интерфейсом.** [Запуск frontend](../frontend/README.md) и [временный API](catalog-runbook.md#локальная-проверка-без-изменения-пользовательской-бд). Запускайте npm-команды из `frontend/`.
- **Тесты и диагностика CI.** [Локальные команды и артефакты Actions](operations/ci.md). Назначение и параметры утилит собраны в [карте scripts](../scripts/README.md).
- **HTTPS-стенд, аккаунты и почта.** [Базовый стек](#стенд-с-https) и [опциональный SMTP](operations/smtp.md).

## Миграции

Текущий Alembic head — `0014`. Контейнер [backend](../backend/Dockerfile)
выполняет `python -m alembic upgrade head` до запуска Uvicorn. В production
`AUTO_CREATE_SCHEMA=false` предотвращает миграцию из lifespan приложения.
Для ручной диагностики из `backend/` с явно заданным `DATABASE_URL`:

```bash
python -m alembic current
python -m alembic heads
python -m alembic check
```

Перед обновлением сделайте проверенную копию. Для репетиции upgrade используйте
одноразовую PostgreSQL, а не работающую базу. Сверьте `current` с `heads`.
При ошибке снимите диагностику схемы и Alembic. Существующие volumes и
применённые ревизии сохраняются. Stamp не исправляет несовместимую схему.

## Стенд с HTTPS

[compose.prod.yaml](../compose.prod.yaml) определяет PostgreSQL 17, backend,
worker, nginx и Caddy. Перед запуском на согласованном хосте заполните приватное
окружение по [.env.production.example](../.env.production.example), проверьте
DNS, доступность портов 80/443, `PUBLIC_ORIGIN`, точные `ALLOWED_HOSTS` и
Secure cookies. Сохраните имя проекта и секреты, включая `SOURCE_IDENTITY_KEY`.
Последний определяет ключи записей абитуриентов и требует отдельной миграции
при ротации.

```bash
docker compose -f compose.prod.yaml config --quiet
docker compose -f compose.prod.yaml up -d --build --wait
docker compose -f compose.prod.yaml exec backend python -m app.observability status
```

Первая команда проверяет конфигурацию без печати развёрнутых секретов.
В базовом стеке backend находится во внутренней сети, worker имеет egress
для загрузки источников. [SMTP overlay](operations/smtp.md) отдельно включает
аккаунты и egress backend. Сведения о текущей проверке релиза и внешних
условиях находятся в [RELEASE_GATES.md](RELEASE_GATES.md).

## Резервное копирование и восстановление

- **PostgreSQL и raw.** [backup_production.sh](../scripts/ops/backup_production.sh)
  делает PostgreSQL dump и архив raw, восстанавливает dump в служебную
  `admitflow_restore_check` и сравнивает число строк. Не запускайте параллельные
  копии и не используйте зарезервированное имя для других баз. Согласуйте окно,
  остановите все записи в PostgreSQL и raw, включая операторский импорт и worker.
  Закройте доступ к незашифрованным копиям и заранее согласуйте срок хранения:
  скрипт удаляет устаревшие директории в указанном каталоге копий.
- **Пробное восстановление.** [rehearse_postgres_restore.py](../scripts/qa/rehearse_postgres_restore.py)
  использует временный PostgreSQL. Для восстановления рабочей системы
  сначала восстановите копию в отдельной среде и проверьте schema head, raw,
  историю и smoke. Результат сравнения числа строк сам по себе не проверяет
  соответствие всех исторических связей.
- **SQLite для локальной разработки.** Из `backend/`: `python -m app.backup create`,
  `verify <папка>` и `restore <папка> --destination <новая папка>` через тот же
  модуль. Существующее назначение не перезаписывается. Состояние `restore.pending`
  означает, что восстановление нужно повторить в новом назначении.

## Worker и диагностика

`/api/live` проверяет процесс. `/api/ready` и `/api/health` проверяют доступ к БД.
У агрегированной диагностики [наблюдаемости](../backend/app/observability.py)
есть CLI `python -m app.observability status` и `trace <runId>` внутри backend.
Внешний nginx закрывает служебные маршруты, включая `/api/status` и OpenAPI.

Управление аттестованными источниками списков — `python -m app.sources.cli`;
очередь обслуживает отдельный Linux-процесс `python -m app.worker loop`.
В продакшен-стеке worker запущен отдельным сервисом. Перед повторной загрузкой
проверьте паспорт и состояние источника. Сырые документы хранятся вне web root.
`python -m app.sources.retention --days 7` из backend показывает план, применение
требует `--apply`. При очистке учитываются ссылки из snapshots и ревизий программ.

Импорт образовательных программ выполняется отдельно от worker списков.
[Проверенные оригиналы и пакетный запуск](catalog-runbook.md#операторский-импорт-программ)
различают захват, сверку и опубликованную ревизию.

Прежние инструкции со старыми путями, версиями и датами хранятся в
[архиве runbook](archive/runbook-before-documentation-cleanup.md).
