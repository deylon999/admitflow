# Аудит документации AdmitFlow

Срез на 21 ноября 2026 года, `main@a3f5078` после [PR #31](https://github.com/deylon999/admitflow/pull/31). До правок `docs/` содержит 665 файлов. Из них 580 в `evidence/`, 21 в `sources/`, 13 в `archive/`, 4 в `design/` и 47 непосредственно в `docs/`.

Проверка выполнена по [файлам приложения](../backend/app), [маршрутам React](../frontend/src), [миграциям](../backend/alembic/versions), [CI](../.github/workflows/ci.yml), [Compose](../compose.prod.yaml) и [генератору плана](../scripts/roadmap.py). Команды и статусы в датированных отчётах относятся к указанным там версиям.

| Класс | Документы | Решение и основание |
| --- | --- | --- |
| Актуальные | `README.md`, `ARCHITECTURE.md`, `API.md`, `PRODUCT.md`, `DATA_RULES.md`, `data-policy.md`, `DESIGN_SYSTEM.md`, `QUALITY.md`, `RISKS.md`, `RELEASE_GATES.md`, `ROADMAP.md`, `NATIONAL_COVERAGE.md`, `api-contract.md` | **UPDATE** оглавление, архитектуру, API, продуктовый срез и состояние выпуска. **KEEP** остальные пути: единые правила, уже известные навигационные и ссылочные точки. |
| Операционные | `RUNBOOK.md`, `catalog-runbook.md`, `AUTH-SMTP-DEPLOYMENT.md`, `ci-images.yaml` | **UPDATE** runbook и вводные о запуске каталога. **MOVE** действующую инструкцию SMTP в `operations/` с указателем со старого пути. **KEEP** YAML как конфигурационный артефакт. |
| Решения и спецификации | `DECISIONS.md`, `KAN-214-AUTH.md`, `KAN-214-SECURITY-MATRIX.md`, `AUTH-FORM-UX.md`, `AUTH-MAIL-CONTRACT.md`, `AUTH-MAIL-UX.md`, `AUTH-UI-POLISH.md`, `UNIVERSITY-CARDS-UI.md`, `UNIVERSITY-DISPLAY-NAMES.md`, `KAN-218-ARCHITECTURE.md` | **KEEP** существующие пути. Разделить ADR и датированные спецификации в оглавлении. Часть путей записана в реестре задач. |
| Исторические | `archive/`, `design/`, `LOG.md`, `MILESTONE_70.md`, `KAN-212-FRONTEND-REPORT.md`, `KAN-214-PR2.md`–`KAN-214-PR6.md`, `KAN-214-DELIVERY-SMOKE.md`, `KAN-218-PR2.md`, `KAN-218-PR3.md`, `KAN-238-CI-REPORT.md`, `foundation-cleanup-audit.md`, `product-functional-audit.md` | **ARCHIVE** прежний runbook целиком под `archive/runbook-before-documentation-cleanup.md`. **KEEP** остальную историю на прежних путях и обозначить, где смотреть актуальные инструкции. |
| Исследования и источники | `sources/`, `catalog-coverage.md` | **KEEP** паспорта, датированные сведения, оригинальные хеши и расположение файлов. JSON используется сборщиками, скриптом проверки и Playwright. |
| Генерируемые и их входы | `TASKS.md`, `STATE.md`, `WEEKLY_REPORT.md`, `TASKS.json`, `STATE.json`; в корне `CHECKLIST.md` | **KEEP** пути. **UPDATE** статусы только в JSON, затем `scripts/roadmap.py --render`. Недельный отчёт сохраняет свой период. |
| Доказательства | `evidence/` | **KEEP** все 580 исходных файлов, включая PNG/JSON/YAML. Скрипты и тесты обращаются к этим путям и ожидают конкретные данные. |

**DELETE — нет.** Для сведений, которые стали историческими, достаточно архива, ссылки либо явной датировки.

До правок корневой уровень смешивал справочники, текущую эксплуатацию, отчёты PR и старые инструкции. После правок [единое оглавление](README.md) ведёт к действующим документам по вопросу. `operations/` группирует инструкции CI и SMTP. `archive/`, `sources/` и `evidence/` сохраняют назначение. Архитектура, продукт и ADR остаются по привычным стабильным путям.

## Расхождения и проверки

| Что устарело | С чем сверено | Что исправлено |
| --- | --- | --- |
| Описание `0001–0011` как текущей схемы | Ревизии `0012`, `0013`, `0014` и проверка heads в CI | Архитектура называет `0014`, объясняет назначение `0012–0014` и отделяет старую проверку от текущего head. |
| Ожидание T327 и выдачи программ после PR #28 | PR #30, `product_catalog.py`, импортеры и `scripts/local_smoke.py` | Уточнено, что API уже читает утверждённые ревизии после импорта. Штатный старт добавляет архивные конкурсы. Покрытие `1/785` относится к репетиции. |
| Прежний installer Playwright и режим `E2E_API` | `ci.yml`, `frontend/scripts/test.mjs`, `playwright.config.ts` | Текущий workflow, команды и артефакты описаны в operations. Старые команды доступны в архиве. |
| Промежуточные статусы auth PR2–PR4 как действующий контракт | `account_api.py`, `account_mail.py`, `config.py`, `compose.auth.yaml` | Список действующих операций и флаг разделены с доказательствами реальной доставки и HTTPS. |
| Неправильная точка продолжения после слияния PR #31 | `main` и CI PR #31 | Завершение T318 зафиксировано в реестре. Задача очистки оформлена отдельно от следующего этапа каталога. |

Ссылочные потребители проверяются отдельно от Markdown: `roadmap.py` и недельный отчёт используют JSON и записи evidence. ETL и аудит источников используют паспорта и JSON в `sources/`. `verify-source.mjs`, `catalog.spec.ts`, `api-unit.spec.ts`, тесты регрессий и CI используют артефакты, fixtures или manifest. Эти входы и workflow остаются на прежних путях. Операционная инструкция SMTP получает совместимый указатель, поскольку её прежний путь встречается в журнале и реестре задач.
