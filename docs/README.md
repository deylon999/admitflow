# Документация AdmitFlow

Старт: [AGENTS.md](../AGENTS.md) → [STATE.md](STATE.md) →
`python scripts/roadmap.py --context` из корня. Проверка: `--check`.
Для другой выбранной задачи — `--task Tnnn`.
Полные TASKS, LOG, архив и исследования источников для старта не нужны.

| Информация | Авторитетный источник | Когда читать |
| --- | --- | --- |
| Задачи, статусы, зависимости, acceptance, evidence | [TASKS.json](TASKS.json) | Через `--task Tnnn` или `--context` |
| Продолжение и техническое состояние сессии | [STATE.json](STATE.json) | Обычно достаточно генерируемого [STATE.md](STATE.md) |
| Этапы и приоритеты | [ROADMAP.md](ROADMAP.md) | При выборе или изменении направления работ |
| Требования и границы продукта | [PRODUCT.md](PRODUCT.md) | При изменении сценариев и обещаний |
| Фактическая архитектура | [ARCHITECTURE.md](ARCHITECTURE.md) | При изменении модулей и зависимостей |
| Контракты API | [API.md](API.md) | HTTP/DTO; [api-contract.md](api-contract.md) — указатель совместимости |
| Формулы и ограничения данных | [DATA_RULES.md](DATA_RULES.md) | Расчёты, импорт, свежесть |
| Приватность и хранение | [data-policy.md](data-policy.md) | Пользовательские и исходные данные |
| Визуальная система | [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) | UI; для backend автоматически не читать |
| Решения и обоснования | [DECISIONS.md](DECISIONS.md) | Только релевантные ADR с учётом последующих решений |
| DoD и критерии приёмки | [QUALITY.md](QUALITY.md) | Перед реализацией и закрытием задачи |
| Фактическая готовность выпуска | [RELEASE_GATES.md](RELEASE_GATES.md) | Приёмка/выпуск; done не равен принятому gate |
| Запуск, проверка, выпуск, восстановление | [RUNBOOK.md](RUNBOOK.md) | Нужный раздел по операции |
| Риски | [RISKS.md](RISKS.md) | При затрагивании соответствующего риска |
| История действий и результатов | [LOG.md](LOG.md) | `--log Tnnn`, `--log Snnn`, `--log --entries 3` |

`--task` показывает полную карточку и evidence прямых зависимостей без
рекурсивной выгрузки истории. Для более глубокой зависимости запросить её ID.
`--log ID --entries N` выбирает последние N записей с точным ID задачи/сессии.
Команды чтения не записывают файлы. `--render` обновляет [TASKS.md](TASKS.md),
[STATE.md](STATE.md), [CHECKLIST.md](../CHECKLIST.md); актуальность проверяет `--check`.
Эти три файла вручную не редактировать. STATE.json хранит только актуальный
снимок: lastCompleted/environment заменять при изменении, историю добавлять в LOG.
Не накапливать прошлые сессии в STATE.

Источники — только по задаче: [покрытие каталога](catalog-coverage.md),
[цель охвата](NATIONAL_COVERAGE.md), [инвентаризация](sources/national-inventory.md),
[fetcher](sources/fetching.md) и конкретный паспорт в `sources/`.
Большие JSON — данные исследований, некоторые связаны хешами; их не
переформатировать ради документации. Паспорта, `evidence/regression.md`, fixtures,
JSON/PNG evidence и [ci-images.yaml](ci-images.yaml) имеют автоматических потребителей.

История: [PROGRESS до B21](archive/progress-through-b21.md),
[старые STATE](archive/state-before-optimization.md),
[план до FSD](archive/architecture-before-fsd.md),
[gates на 5 ноября](archive/release-gates-2026-11-05.md),
[рубеж 70%](MILESTONE_70.md). Это не текущие инструкции или приёмка.
Исходные макеты `design/` не заменяют актуальную дизайн-систему.
Датированные проверки — `evidence/`; не читать каталог целиком.
