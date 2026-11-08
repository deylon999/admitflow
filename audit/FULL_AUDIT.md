# Технический аудит AdmitFlow

Дата: 2026-11-08. Проверяемый baseline `origin/mvp-readiness` = `ad5b938`.
Текущий checkout `review/vadim-audit-fixes`. Это аудит приоритетных рисков и
сквозных сценариев. Он охватывает значимые модули и доступные интеграционные
проверки; построчное ревью каждого файла и production-наблюдение не проводились.

## Границы и воспроизводимость

Изучены `frontend/src/{lib,components,pages}`, React Query/Router, формы,
калькулятор, импорт/экспорт, история, сессии, ошибки и responsive состояния;
`backend/app/{main,database,schemas,migrations,operations,importing,source_api,worker}`,
`backend/app/sources` (fetch, validation, publishing, storage, registry, adapters),
Alembic и тесты; Compose, Dockerfile, nginx/Caddy, CI, backup/monitoring.
Правила сверены с `docs/DATA_RULES.md`, качество и ограничения — с
`docs/QUALITY.md`, `docs/RELEASE_GATES.md`, `docs/RUNBOOK.md`.

Команды и фактический результат:

| Проверка | Результат |
| --- | --- |
| `python scripts/roadmap.py --render --check --self-test` из корня | План валиден, 6 некорректных состояний отклонены |
| `npm ci`, `npm test`, `npm run build` из frontend | Чистая установка; 125 Vitest passed; сборка passed |
| `docker compose config --quiet` | Passed |
| Изолированный Compose project `admitflow-audit-20261108`, порт 18080 | PostgreSQL/backend/frontend healthy; миграции до 0010 |
| `python scripts/backup_production.py` с `COMPOSE=docker compose -p admitflow-audit-20261108`, `RAW_SERVICE=backend` | Восстановлено 20 таблиц, проверен 1 синтетический raw hash; temporary DB удалена; backup private/ignored |
| `backend/.venv/Scripts/python.exe -m pytest -q tests/test_production_backup.py tests/test_ops_check.py tests/test_worker.py` | 27 passed |
| `docker run ... python /workspace/audit/run_backend.py -q --require-postgres --junitxml=/evidence/backend-native.xml` на отдельной БД `admitflow_test_audit` | 565 passed, 0 skipped, 2 warnings; краткая [сводка](evidence/verification.json) |
| `npm run test:e2e -- --workers=2 --reporter=line,json`, `E2E_API=1`, preview/SQLite API | 600 collected; 434 passed, 163 scoped skips, 3 failed: 2 WebKit выбора вуза (исправлены), 1 Firefox/Kaspersky extension; [сводка](evidence/verification.json) |
| 13 targeted Chromium API E2E session/cache/draft после исправлений | 13 passed |
| Все сценарии каталога на пяти browser profiles после исправления | 15 passed, 0 skipped |
| Source fixture API, 4 сценарных файла × 5 браузерных профилей после исправления | 90 passed, 0 skipped; исходный прогон 95 passed/10 failed (9 связанных с фокусом, 1 внешний Firefox POST) |
| Chromium 390/1440 visual capture с API | 2 passed, overflow нет, PNG просмотрены |

Первый полный pytest на Windows прервался на 12 collection errors из-за `resource`.
После исправления Linux с Windows bind mount дал 564 passed/1 timing failure в
2-секундном ожидании запуска дочернего процесса. Тот же тест (3/3) и полный
прогон (565/565) прошли на native Linux filesystem без ослабления кода/таймаута.
Старый dist и предыдущие отчёты не считались доказательством текущей версии.

В полном 600-case browser прогоне 163 случая сознательно пропущены по условиям
тестов: 70 требуют disposable anonymized fixture API, 15 — two-source fixture,
15 — anonymized fixture API, 15 — настоящий nginx image, ещё 45 относятся к
архивным/source DTO и control fixtures, 3 — PDF только headless Chromium.
Отдельный single-source fixture прогон затем проверил доступные source пути:
90/90 после исправления. Two-source сценарии не засчитаны, потому что первый
запуск с такой фикстурой нарушал предпосылку тестов об одной группе;
нужна отдельная конфигурация теста. Ни один skip не записан как passed.
Полный 600-case прогон после последних исправлений не повторялся; исправленные
пути проверены целевыми запусками на всех пяти профилях.

## Frontend

Сильные стороны: строгие контракты JSON, ограничения размеров ответа/импорта,
явное разделение ручного расчёта и архивного сценария, понятные retry/error
состояния, идемпотентные ключи сохранения, проверка непредсказуемого HTTP и
доступности клавиатуры в E2E. Устройство интерфейса компактно и работает на
320–1440 px в проверенных сценариях.

Риски: query-cache прежней гостевой сессии мог пережить reset (AUD-09),
Web Lock race могла завершить новую сессию (AUD-08), черновик не удалялся при
отмене значений (AUD-10). На WebKit выбор вуза мог теряться при blur/click
(AUD-11). После просмотра архивной записи фокус мог попасть мимо заголовка
подтверждения (AUD-12). Локальные исправления и тесты перечислены отдельно.
Page/Source components сейчас содержат много API и UI обязанностей вместе;
последующий `main` уже содержит FSD-миграцию, поэтому крупная перестройка здесь
не проводилась. У старой ветки нет самостоятельного lint/format script;
типизация проверялась `tsc` внутри build.

## Backend и данные

Сильные стороны: ownership на сессионном hash, POST под row lock, строгие
Pydantic DTO и негативные тесты, идемпотентность импорта/снимков, SQLAlchemy
транзакции, явно ограниченный исходящий HTTPS с проверкой домена, IP и TLS,
аттестованный scope адаптеров, карантин роста/падения мест, immutable history.
Прямых подтверждений SQL injection, SSRF или XSS в проверенных путях нет;
абсолютную безопасность такой вывод не доказывает.

Риски: новая production backup/monitoring цепочка содержала AUD-01–06,
в том числе потенциальную утрату чужих каталогов и проверочной БД. Безусловный
Unix import ломал тесты Windows (AUD-07). После исправления restore с raw
проверен в принадлежащем аудиту контейнере. Восстановление всей системы на
реальном staging, RPO/RTO и 24-часовая работа worker не проверены.

Большие `main.py`/`source_api.py` и сочетание API, запуска миграций и источников
повышают цену изменений. Формат семейства адаптеров уже отделяет parser от
конкретного вуза, но подключение живой кампании требует отдельной аттестации;
универсального покрытия всех вузов нет.

## Инфраструктура, безопасность, готовность

Docker Compose в dev использует локальные тестовые реквизиты и привязку
127.0.0.1; prod Compose требует HTTPS, PostgreSQL, secure cookies, хосты и
секрет идентичности. Nginx содержит per-address limits, заголовки и
ограничение тела. Docker сборка и локальный PostgreSQL подтверждены; настоящая
production-конфигурация в публичном домене, TLS, мониторинг и CI после нового
коммита не запускались. `npm ci` сообщил 0 известных npm advisories для
закреплённого frontend lockfile; Python advisory scan не проводился.

`docs/RELEASE_GATES.md` прямо оставляет G4 частичным, G5/G6 открытыми.
Функциональный ручной путь и архивный replay доступны; живой сезон 2027,
национальное покрытие, приёмка людьми и сутки наблюдения не доказаны.
Никакой балл ниже не означает принятие gate.

| Вид готовности | Проверенный результат | Что остаётся |
| --- | --- | --- |
| Функциональная | Ручной расчёт, сравнение, сохранение, история, JSON и архивные сценарии проходят доступные тесты | Живые списки кампании 2027 и требуемое покрытие |
| Техническая | Сборка, native PostgreSQL suite, локальный Compose и восстановление проходят | CI нового review-коммита и staging restore |
| Production | Конфигурация Compose синтаксически валидна; backup исправлен локально | TLS/домен, права на данные, 24 часа monitoring и реальный RPO/RTO |
| UX | Desktop/mobile paths и 390/1440 px без overflow; ошибки фокуса исправлены | Живые тестеры и проверка на чистом Firefox runner |
| Security | Ownership, валидация и отрицательные сценарии проверены в коде/тестах | Внешний security review окружения, секретов, зависимостей Python и production-наблюдение |

Из архитектурных задач для актуального `main` предлагается выделить из
`main.py` и `source_api.py` маршруты, транзакционные сервисы и интеграцию
источников с явными контрактами; во frontend разделить API orchestration и
представление крупных страниц. Это постепенные изменения после приёмки
контрактов, без переписывания работающего расчёта или изменения DATA_RULES.

| Ось | Оценка /10 | Основание и предел |
| --- | ---: | --- |
| Frontend | 7 | Рабочие пути и типизация, но подтверждены ошибки сессий/фокуса в baseline |
| Backend | 7 | Широкие native PG тесты и защитные контракты; backup потребовал исправлений |
| Architecture | 6 | Разделение источников полезно; монолитные API/UI узлы и сложный ops контур |
| Security | 6 | Ownership/CSRF/SSRF проверки есть; prior backup side effects и нет staging audit |
| Testing | 7 | 565 native PG и 600 browser cases; остаётся Firefox extension/CI и живой сезон |
| Maintainability | 5 | Документация подробна, но старые крупные компоненты и 194 карточки усложняют вход |
| MVP readiness | 4 | Ручной и архивный режимы локально работают; production gates G4–G6 открыты |
| Исследованный вклад ветки | 7 | Измеренная производительность/ops/CI; найдены серьёзные backup дефекты |
| Проект в целом | 6 | Сильная тестовая база, локальная функциональность; выпуск требует внешних доказательств |

Оценки — экспертные суждения по проверенному коду и среде, не объективные
метрики качества. История и ограничение атрибуции — VADIM_CODE_REVIEW.md;
каждый подтверждённый дефект — BUG_REPORT.md; точные исправления — FIX_REPORT.md.

## Незавершённое и решения

1. Проверить финальный CI на свежем runner после публикации ветки и отдельно
   повторить Firefox font check без вмешательства расширения Kaspersky.
2. Владелец выбирает staging сервер, домен, бюджет/регион, сроки хранения и
   правовое основание источников; затем T048–T052 и 24 часа наблюдения.
3. Перенести ops исправления в текущий main адресно после ревью. Нельзя считать
   новую review-ветку прямым продолжением main: main уже содержит позднюю FSD
   миграцию и исправления frontend, а mvp-readiness входит в main как предок.
