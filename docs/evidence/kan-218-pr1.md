# KAN-218 PR1: проверка архитектуры и идентичности

Работа начата 2026-11-20, проверка продолжена 2026-11-21.
База `main@e121d5d`. Архитектура и конкретные границы:
[KAN-218-ARCHITECTURE.md](../KAN-218-ARCHITECTURE.md).

Первый этап: отдельные identity helpers и Program/M:N хранение. Новых
подключённых официальных источников и публичных программ — **0**. Публикация
каталога по-прежнему ограничена двумя reviewed scopes СГУ 2026. Это не
достижение цели 2027, не финальный отчёт KAN-218 и не приёмка release gate.

## Проверки хранения

Команда из корня:

```text
python scripts/test_postgres.py --python backend/.venv/Scripts/python.exe tests/test_catalog_identity.py tests/test_program_identity_storage.py tests/test_migrations.py tests/test_migration_metadata.py tests/test_database_diagnostics.py
```

**88 passed, 0 skipped, 26.16s, exit0**. Native PostgreSQL17-alpine, собственный
disposable контейнер, случайные schemas; штатный runner останавливает свой
контейнер. Рабочая БД/volumes не использовались.

Проверены заполненная0012→0013, metadata alignment, повтор upgrade/import,
сохранение строк источников/персональных snapshots и pointers (всё synthetic),
M:N и standalone, cross-year continuity только явной связью, отказ чужого
вуза/филиала/уровня/кампании, duplicate natural identity, rollback, RESTRICT.
API проверен настоящим FastAPI TestClient с nativePG и теми же двумя СГУ.

Дополнительно: frontend `npm run typecheck`, `npm run lint`, `npm run build`
из `frontend/` — exit0. Публичный DTO, дизайн, авторизация и workflows сохранены.

Два промежуточных88-case прогона:87 passed/1 failed из-за предпосылок нового
теста; история и исправления приведены в архитектурном документе.
Frontend `npm test`: **384 passed, 1.3min, exit0**, включая четыре каталожных
страницы, loading/error/empty/retry, неизвестные значения и прежние контракты.
Это browser-регрессия старого набора; новые реальные программы не проверялись,
так как PR1 ещё не реализует их публикацию.

## Источники и границы покрытия

Никакой сетевой сбор вузов PR1 не выполняет. Переиспользованные проверенные
артефакты: MICCEDU2025, реестр аккредитации2026-11-10, reviewed manifest СГУ2026
(`https://www.sgu.ru/svodka/4588`, `/4576`) и точные правила ЕГЭ KAN-219.
Их URL/даты/SHA256 сохраняются без изменений. Новые ключи и synthetic строки
интеграционных тестов не попадают в публичную выдачу. Независимая сверка новых
семейств, массовый сбор, performance measurement и live-source доступность
ещё не выполнялись. Отсутствие опубликованных условий2027 не доказано.

По встроенному reviewed набору (не снимок production БД):

| Кампания | Знаменатель головных вузов | Головные вузы с программами | Публичные scopes | Подтверждённые группы | Доля вузов |
| --- | ---: | ---: | ---: | ---: | ---: |
| Целевая2027 | 785 | 0 | 0 | 0 | 0% |
| Архив2026 | 785 | 1 | 2 | 2 | 0,1274% |
| Совокупная история reviewed набора | 785 | 1 | 2 | 2 | 0,1274% |

Публичные scopes здесь — прежняя проекция конкурсных групп. Число уникальных
канонических Program в этом наборе **ещё не установлено**: миграция специально
не создаёт их из групп. Цель —471 головной вуз для2027 при этом знаменателе.
СГУ имеет частичный набор; полный перечень его программ не подтверждён.
Филиалов с новым опубликованным набором, новых источников с ошибками и
поступивших staging конфликтов в PR1 —0, поскольку сбор не запускался.
Это не нулевая оценка ошибок всей страны. Измерение по регионам/уровням и
полноте каждого вуза будет частью расширения KAN-221, а не этой таблицы.

## Изменения и воспроизведение

- `backend/app/admissions.py`: Program и две таблицы связей; дополнительные
  unique scopes для composite FK на Campaign и CompetitionGroup.
- `backend/app/catalog_identity.py`: версия1 UUIDv5, literal official keys,
  проверка входа и составной fallback без названий.
- `backend/alembic/versions/0013_program_identity.py`: только новая миграция;
  старые0001–0012 не менялись. Три пустые таблицы без неподтверждённого backfill.
- `backend/tests/test_catalog_identity.py`, `test_program_identity_storage.py`:
  новые существенные проверки. В `test_migrations.py` и
  `test_database_diagnostics.py` обновлены assertions текущей схемы0013/29.
- PRODUCT/DATA_RULES/DECISIONS содержат актуальные указания владельца;
  TASKS/STATE/LOG и их generated views согласуются с ограниченным объёмом PR1.

Публичные API-контракты не изменялись. Существующие product_catalog.py,
product_catalog_schemas.py, frontend/src и GitHub workflows имеют нулевой diff
к `e121d5d`. `python -m unittest scripts.tests.test_roadmap`:10 passed, exit0.
`python scripts/roadmap.py --render --check` и `git diff --check` проверяются
перед каждым завершающим коммитом.

Полный обязательный backend-набор был запущен локально теми же исключениями
ETL, что в текущем CI. Он остановился с exit2 и13 collection errors из-за
существующего `app.worker: import resource`: этот модуль отсутствует на Windows.
Ошибки сохранены в локальном `test-results/kan218/backend.log`; тесты/worker/
CI не ослаблялись. Полный Linux-набор требуется в штатном Actions на SHA PR.

## Проверка и следующий этап

Первые четыре ограниченных шага T312–T315 выполнены; T316 остаётся review
до проверки PR. Полная KAN-218 не переводится в In Review и не закрывается.
Результаты GitHub Actions и точный проверенный head фиксируются в описании PR,
чтобы обновление отчёта не создавало новый ещё не проверенный SHA.

После review/merge PR1: свежий main → T317/PR2. Первый набор должен включать
реальные официальные документы нескольких вузов с независимой сверкой,
provenance/revisions, atomic publication и точную связь программы с конкурсом.
До требуемого изменения DTO предоставить deylon999 реальный образец ответа
и согласовать контракт KAN-223. Массовое подключение не ждать для выдачи первого
согласованного проверенного набора.

Для KAN-227 подготовлена совместимая основа Program↔Campaign↔Group; существующие
group/campaign IDs и snapshots сохранились. Полная готовность к подключению
национальных списков ещё не подтверждена: новых реальных связей и публичных
program IDs нет. Финальный отчёт KAN-218 должен отдельно подтвердить их на
реальных источниках после достижения целевой кампании и review владельца.
