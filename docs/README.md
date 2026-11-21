# Документация AdmitFlow

Начните с [README](../README.md) для локального запуска. Чтобы продолжить
работу по задаче, прочитайте [AGENTS.md](../AGENTS.md), [текущий контекст](STATE.md)
и запустите из корня `python scripts/roadmap.py --context` или
`python scripts/roadmap.py --task Tnnn`. Остальные материалы выбирайте по вопросу.

## Актуальные справочники

| Вопрос | Куда идти |
| --- | --- |
| Какие модули и миграции работают в текущем стеке? | [Архитектура](ARCHITECTURE.md) |
| Как устроены Python-пакеты backend и проверена совместимость? | [Инвентаризация](BACKEND_ORGANIZATION_MASTER_PLAN.md), [результат](BACKEND_ORGANIZATION_FINAL_REPORT.md) |
| Какие API и DTO поддерживаются? | [API](API.md). Актуальный набор HTTP-маршрутов также есть в локальном OpenAPI. |
| Какие сценарии доступны и что пока планируется? | [Продукт](PRODUCT.md), [готовность к выпуску](RELEASE_GATES.md) |
| Как понимать кампании, неизвестные данные, свежесть и расчёты? | [Правила данных](DATA_RULES.md) |
| Что можно хранить и публиковать? | [Политика данных](data-policy.md) |
| Какие требования к UX и тестированию? | [Дизайн-система](DESIGN_SYSTEM.md), [критерии качества](QUALITY.md), [риски](RISKS.md) |
| Почему принято архитектурное решение? | [ADR](DECISIONS.md). Смотрите дату решения и последующие уточнения. |

## Эксплуатация

| Операция | Инструкция |
| --- | --- |
| Локальный стек, тестовый API и импорт | [Запуск каталога](catalog-runbook.md) |
| Миграции, PostgreSQL/raw backup, диагностика и HTTPS | [Runbook](RUNBOOK.md) |
| Включение аккаунтов с SMTP на согласованном стенде | [SMTP и проверка доставки](operations/smtp.md) |
| Проверки, платформы, поиск логов | [CI](operations/ci.md) |

## План и состояние

- [TASKS.json](TASKS.json) хранит статусы, зависимости, критерии и доказательства.
  [STATE.json](STATE.json) хранит точку продолжения. [LOG.md](LOG.md) хранит историю.
  `python scripts/roadmap.py --log Tnnn` или `--log Snnn` показывает выборку.
- [TASKS.md](TASKS.md), [STATE.md](STATE.md) и [CHECKLIST.md](../CHECKLIST.md)
  генерируются через `python scripts/roadmap.py --render`. Редактируйте JSON-входы,
  затем запускайте `--render --check`. Отдельно `python scripts/check_doc_links.py`
  проверяет внутренние ссылки и якоря. [ROADMAP.md](ROADMAP.md) описывает этапы.
- [WEEKLY_REPORT.md](WEEKLY_REPORT.md) фиксирует прошлый отчётный период.
  Успешный тест, завершённая задача и приёмка релиза имеют разные критерии.

## Источники и датированные доказательства

- [Покрытие каталога](catalog-coverage.md), [цели национального охвата](NATIONAL_COVERAGE.md),
  [инвентаризация](sources/national-inventory.md), [политика загрузки](sources/fetching.md)
  и [паспорта программ](sources/program-catalog/README.md). При работе с конкретным
  источником откройте его паспорт и исходный контекст кампании.
- [evidence/](evidence/README.md) содержит отчёты, JSON, скриншоты и эталоны.
  Подбирайте доказательства по карточке задачи. Прогон относится к указанному SHA,
  схеме и окружению. [Публичный каталог](evidence/kan-218-pr2-public-api.json),
  [пакетный импорт](evidence/kan-218-pr3-batch.json),
  [авторизация](KAN-214-PR6.md) и [аудит CI](KAN-238-CI-REPORT.md) дают примеры.
- Пути паспортов, JSON, PNG, [карты регрессий](evidence/regression.md) и
  [CI images](ci-images.yaml) могут использоваться автоматически. Перед переносом
  проверьте скрипты, тесты, конфигурацию и `TASKS.json`.

## Архив

[archive/](archive/) хранит прежние контракты и процедуры, включая
[старый runbook](archive/runbook-before-documentation-cleanup.md),
[архитектуру до React v3](archive/architecture-before-foundation.md)
и [историю до B21](archive/progress-through-b21.md).
[design/](design/) хранит исторические макеты. Датированные отчёты PR могут
оставаться в корне `docs/`, если их пути используются в реестре и старых ссылках.
Классификация и карта изменений описаны в [аудите документации](documentation-audit.md).
