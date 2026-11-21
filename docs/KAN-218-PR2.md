# KAN-218 PR2: проверенный импорт программ

## Продолжение после согласования T327

Backend импорта из [PR #28](https://github.com/deylon999/admitflow/pull/28)
вошёл в main (`0449e66`) до согласования DTO. Владелец явно одобрил
[расширение API для KAN-223](sources/program-catalog/contract.md) 21 ноября.
Публичный API и frontend доработаны в той же ветке. GitHub сохраняет исходный
diff слитого PR. Продолжение публикуется отдельными коммитами ветки и
ссылкой на их сравнение в описании существующего PR.

Четыре существующих endpoints используют текущие verified-ревизии.
SQL считает `total`, фильтрует и выбирает ключи страницы перед загрузкой фактов
и групп. PostgreSQL использует один снимок транзакции на HTTP-запрос.
Дубли идентичности из нескольких текущих ревизий исключаются до фильтрации.
Архивные записи `sgu-2026-4588` и `sgu-2026-4576` сохраняют старые поля,
ID, URL и условия. Отдельный `programId` для старого конкурса отсутствует
без одной явной связи в БД. Новые записи используют сохранённый `public_id`,
отдельный `programId`, `competitionGroups` и provenance официального документа.

Frontend отображает `null` как «Нет данных» и принимает отсутствие новых полей
у старого сервера. Поиск, фильтры, пагинация и переходы остаются на прежних
страницах. Для ВШЭ 2027 карточка показывает год и источник, не приписывая
ей бюджет, контракт, форму обучения или ноль мест.

Воспроизведение на собственном PostgreSQL с сохранёнными официальными
оригиналами из предыдущего захвата:

```text
backend/.venv/Scripts/python.exe scripts/verify_program_catalog.py --browser --output test-results/kan218/public-proof.json
```

Ответы API СГУ и ВШЭ, равенство прежних ответов до и после импорта и результат
проверки браузером сохранены в [отчёте API](evidence/kan-218-pr2-public-api.json).
Репетиция использовала отдельный временный контейнер и схему.

Изолированная репетиция даёт 2 программы ВШЭ за 2027, 2 программы СГУ за
2026 из новых документов и прежние 2 архивные записи СГУ. ВШЭ и СГУ покрыты
частично. Знаменатель реестра от 10.11.2026 — 785 головных вузов, порог — 471.

| Кампания | Головных вузов с программами | Записей API | Подтверждённых конкурсов | Покрытие |
| --- | ---: | ---: | ---: | ---: |
| 2027 | 1 | 2 | 0 | 0,13% |
| 2026 | 1 | 4 | 2 | 0,13% |

Здесь измерена тестовая публикация в PostgreSQL 17.11, 21 ноября 2026 по
Москве. Рабочее покрытие не измерялось. Национальный сбор, полноценная
проверка внутри вузов, PDF и новые реальные связи с конкурсами остаются открыты.
Этапы поиска/производительности на национальном объёме и приёмка KAN-218
продолжаются отдельно. Полный CI и SHA продолжения фиксируются в описании PR.

Проверено в этой ветке:

- PostgreSQL: `scripts/test_postgres.py` с `test_program_publication_api.py`,
  `test_product_catalog.py`, `test_program_catalog_storage.py`,
  `test_program_catalog_import.py`, `test_program_identity_storage.py`,
  `test_migrations.py` и `test_migration_metadata.py`. 113 тестов без пропусков,
  85,33 с, exit 0. Обновление 0012 → 0014 сохраняет архивные ID, источники и
  снимки. Обновление заполненной 0013 → 0014 сохраняет также M:N связи,
  гостевую сессию и подписку. `alembic check` выполнен в сценариях миграции.
- Существующие `npm run typecheck`, `npm run lint`, `npm run build`, `npm test`
  прошли локально. Playwright — 387 passed, exit 0. Отдельный прогон через
  реальный FastAPI и PostgreSQL с официальными HTML — 1 passed, exit 0.
- Полные backend и ETL, включая тесты с Linux `resource`, проверяются через
  существующий GitHub Actions workflow. Первый локальный прогон нашёл ошибку
  чтения до миграции 0013. После исправления сценарий входит в 113 зелёных тестов.

## История первого backend-этапа до согласования DTO

Работа начата2026-11-21 от `main@46adc5b` после owner merge
[PR27](https://github.com/deylon999/admitflow/pull/27). PR1 принят; вся KAN-218
остаётся открытой. Ветка `feat/kan-218-verified-program-import`.

Пятёрка T322–T326: официальные документы → независимая сверка и конкретный
DTO proposal → provenance/revisions → атомарный импорт и API → nativePG/CI/PR.
Acceptance записаны до реализации в реестре задач. Общая карточка T317
остаётся незавершённой до выполнения её критериев.

Цель2027 сохраняется; архив2026 не переносится. Первое исследование источников
начато, доступность/достоверность и результат сбора ещё не приняты. Существующие
две reviewed программы СГУ/API и все идентификаторы сохраняются.

## T322: источники захвачены

Оба оригинала получены через существующий pinned HTTPS fetcher после robots:
ВШЭ396192байта, SHA256`8518a05c7a817ae2a69f2f3a8f32810a97ffca8fa59b618a7e3a9cd935fc6609`;
СГУ286243байта, SHA256`61f7c938d2d11cc815cf591482e82a2ecd79557e62db32796af82fdb47c3821d`.
Точные URL, даты UTC, robots hashes и политика ограниченного чтения:
[паспорта](sources/program-catalog/README.md),
[метаданные](sources/program-catalog/captures.json).

Добавлен воспроизводимый CLI `scripts/capture_program_catalog.py`; default
cache вне Git, явный source key, один документ после robots, finite delay,
нет retries/обхода запретов. Прежний документ сохраняется при ошибке.
`cd backend; .venv/Scripts/python.exe -m pytest -q tests/test_program_catalog_capture.py`:
**5 passed,0skip,exit0**; проверены serial capture, повтор без дублей raw,
disallow, HTML вместо robots, большой crawl-delay, отказ источника и сохранность.
Это ещё не публикация программ. T323 проверяет факты и конкретный DTO proposal.

## T323: сверка и контракт для согласования

Два независимых чтения: официальный web-текст и выбранные узлы оригинального
HTML с проверкой полного SHA256. В reviewed package —4 программы:
Мода/Современное искусство (ВШЭ, Москва,2027) и Биология/География
(СГУ, головной вуз, очная форма,2026). Выборка частичная; принадлежность к
филиалу/головному вузу проверяется до извлечения, совпадение названий не ключ.

Для ВШЭ утверждён только объявленный набор2027: code/форма/финансирование/
категория/места неизвестны. У СГУ сохранены отдельные budget/paid totals и
квоты; общий конкурс из них не вычисляется, пустая целевая квота —null.
Четыре программы имеют0 новых подтверждённых конкурсных групп. Существующие
две группы СГУ не пересвязываются по совпадению названия/кода.

`program_catalog_review.py` проверяет scope/структуру/точные reviewed факты и
отказывает изменённому оригиналу. Выборка задаётся review package, общего
лимита числа программ нет. Synthetic fixtures проверяют успешный разбор,
разные годы, одинаковые имена в разных кампусах, перестроенную таблицу,
неизвестные значения и попытку заменить null нулём. Capture+review:
**15 passed,0skip,exit0**. Четыре реальные записи дополнительно извлечены
из совпавших по SHA оригиналов; это отдельное evidence от synthetic unit tests.
Это техническая сверка, не заявление о независимом review человеком.

[Конкретный образец ответа](sources/program-catalog/response-proposal.json)
содержит реальные проверенные факты и предлагаемые стабильные ID. Он ещё
не опубликован и не является согласованным контрактом. Предложение:
nullable неизвестные условия, additive programId/competitionGroups,
provenance.kind=admissions для приёмного документа; существующие ID СГУ
и старые поля сохраняются. Вопрос владельцу отправлен2026-11-21.
**T327 остаётся открытой до явного ответа.** Без согласования можно продолжать
provenance/storage/import, но нельзя реализовывать изменённую публичную выдачу
и frontend decoder. Разделение шага не ослабляет acceptance T317/T325.

## T324: обоснование схемы до реализации

0013 хранит только идентичность, поэтому новая аддитивная0014 добавит шесть
таблиц на той же Base и существующих Campaign/Program/CompetitionGroup:
документ заданной кампании; неизменяемую ревизию оригинала/проверки;
версионированные факты программы; подтверждённые связи с конкурсами и снимок
их опубликованных условий; атомарный указатель опубликованной ревизии;
журнал попыток импорта. SourceSnapshot/CandidateEntry относятся к спискам
поступающих и для программы без конкурса неприменимы; они не заменяются.

Ревизия хранит original/final URL, MIME, публикацию или null, fetched/checked UTC,
SHA256 оригинала, extractor/review/normalized hashes, partial/complete и counts.
Факт хранит Program/Campaign scope, стабильный ID проекции, известные поля и
отдельные totals; группа добавляется только по явной сверенной связи.
Composite FK защищают кампанию и существующие identity links. PostgreSQL
запрещает UPDATE/DELETE опубликованных исторических фактов и ревизий; публикация
создаёт новые версии и переключает только source-scoped pointer. Прямые
ручные группы не становятся source-backed программами.

Импорт из closed reviewed package проверяет оригинал и извлечение до публикации.
На документ — одна транзакция под существующим catalog lock; успехи разных
источников изолированы. Повтор raw/extractor/review не дублирует ревизию;
изменение approved факта даёт новую версию, конфликт ключа/кампании — отказ.
Неполный/пустой/непроверенный пакет не переключает pointer. Ошибка журналируется
отдельно после rollback, не удаляя прежнюю ревизию. RawStore сохраняет оригинал
без его публикации в Git. Новая схема сама не меняет публичный API.

Проверка: nativePG upgrade заполненной0013→0014, metadata alignment, старые
identity/source/snapshot связи; immutable история, wrong-scope FK, repeat import,
approved revision update, конфликт, rollback, изоляция источников. Старые
assertions текущего head/table set обновляются точно; auth/runtime/workflows
не меняются. Массовая performance приёмка остаётся отдельным этапом.

Реализованы шесть таблиц и новая0014; applied0001–0013 не менялись.
Publication trigger сверяет counts программ и distinct конкурсов перед
переключением указателя. После публикации нельзя дописать факты в текущую
или прежнюю ревизию; PostgreSQL сериализует проверку через row lock ревизии.
Программа/кампания/конкурс/документ с историческими фактами защищены от
переназначения идентичности; изменяемые журнальные summary поля документа
не затрагивают исходные версии.

NativePG команда из корня:

```text
python scripts/test_postgres.py --python backend/.venv/Scripts/python.exe tests/test_program_catalog_storage.py tests/test_migration_metadata.py tests/test_migrations.py tests/test_account_foundation.py tests/test_program_identity_storage.py tests/test_database_diagnostics.py
```

**81 passed,0skip,45.45s,exit0.** Изолированный PostgreSQL17, upgrade заполненной
0013 с Program/M:N, repeated head0014 и metadata check; существующая проверка
заполненной0012 сохраняет также source snapshots/pointers. Проверены immutable
UPDATE/DELETE, FK явной связи с конкурсом, запрет неполной публикации, новая
согласованная версия и защита прошлой после переключения. SQLite — только
дополнительная compatibility часть существующего migration набора. Рабочая БД
и volumes не использовались. T324 завершена; API/DTO ещё прежние.

## T325: импорт — проверенная независимая часть

CLI `python -m app.program_catalog_import --raw-directory <cache> --raw-store <private-store>`
выбирает только shipped reviewed source keys. Он не принимает URL/JSON из
публичного API, не регистрирует источники поступающих и не активирует workers.
RawStore, catalog lock, University/Campaign/Program и существующие scoped M:N
переиспользованы. Согласованная ревизия источника публикуется одной транзакцией;
журнал отказа фиксируется отдельно после rollback. CLI возвращает exit1 при
любом ошибочном источнике, сохраняя успешные источники и прежние pointers.

Повтор raw/extractor/review сохраняет те же IDs и revision. Новая проверенная
версия названия/фактов сохраняет Program/public scope ID и прошлую ревизию.
Уменьшение выбранного набора или replay старой версии не удаляют ранее
проверенные данные — пакет отклоняется. Unknown places не становятся0.
Существующие подтверждённые группы связываются только при точной проверке
их полей и кампании; автоматического создания конкурса из строки плана нет.

NativePG capture/review/storage/import selection: **44 passed,0skip,17.33s**.
Проверены также combined competition(M:N) на synthetic явной связи и разные
годы с одинаковыми внешними ключами. Проверка обоих порядков импорта СГУ
выявила отличающиеся явно проверенные пары name/URL и старый campaign ID;
импортёр переиспользует их по точному university/year/level scope из reviewed
source profiles, без fuzzy/URL merge и без изменения старых rows. Два первых
прогона дали42/1 и43/1; оба конфликта исправлены, все assertions сохранены.

Публичная часть T325 пока не выполнена: требуется T327. Реальный rehearsal
подготовлен в `scripts/verify_program_catalog.py`; он использует только
собственный disposable PostgreSQL и не подключается к рабочему DATABASE_URL.

### Проверка настоящих оригиналов и удержание provenance

`backend/.venv/Scripts/python.exe scripts/verify_program_catalog.py --output docs/evidence/kan-218-pr2-real-import.json`
проверяет оба оригинала закрытого review package в собственном PostgreSQL17.11.
Получены2 внутренние document publications/4 канонические программы/4 facts;
повтор обеих публикаций unchanged. Старые2 публичные программы/2 конкурса СГУ
сохранены. Это **backend rehearsal, не расширение публичного каталога**:
2027 Public API по-прежнему0, T327 не согласована.

Обнаруженная при проверке reuse-компонентов опасность устранена: raw retention
и SQLite backup reference enumeration теперь учитывают все ProgrammeRevision
оригиналы, включая прошлые версии. Новая публикация держит тот же RawStore
lock, что GC/backup, до commit, поэтому старый cached raw не может быть удалён
между проверкой и сохранением ссылки в БД. NativePG тест проверяет эту гонку
и сохранность обеих исторических версий. Production PostgreSQL backup уже
архивирует целиком raw store; его существующее требование остановить **всех**
writers распространяется и на новый operator CLI. Production настройки,
backup shell и release gates этим шагом не менялись/не принимались.

Финальная расширенная локальная проверка storage/import/retention/backup и
существующих миграций/identity/account-foundation: **125 passed,0skip,61.75s**
до последнего теста недоступного файла. Модель ревизии явно хранит тип документа
и verification_status; unverified/conflict запрещено публиковать даже при
совпавших counts. Operator CLI требует PostgreSQL и уже применённый текущий
head; он не создаёт SQLite и не обновляет схему пользовательской БД сам.
Ошибки чтения одного raw не прерывают обработку остальных источников.
После последнего изменения чтения raw весь importer-набор: **20 passed,0skip,
11.74s**. Расширение публичного API, DTO/frontend, национального отчёта и массовое
подключение источников не заявляются выполненными этим backend шагом.

## Текущая передача

Финальный real-original rehearsal выполнен на `eecba42`:
[JSON evidence](evidence/kan-218-pr2-real-import.json). Оба оригинала совпали с
заданными SHA; PostgreSQL17.11/schema0014,4canonical programmes,4facts,2внутренние
source publications; оба повторных импорта unchanged. Verification=verified,
источники типизированы announcement/plan и помечены partial. Две прежние
публичные программы/конкурса СГУ сохранены. Никаких записей в рабочую БД.

Чек-лист пятёрки:

- [x] T322 — оригиналы/robots/URL/даты/SHA и bounded capture.
- [x] T323 —4сверенных факта, synthetic negative cases и конкретный proposal.
- [x] T324 — provenance/immutable versions/atomic pointer/0014/nativePG.
- [ ] T325 — backend importer готов; публичная выдача ждёт T327.
- [ ] T326 — полная приёмка PR2, включая новые API/UI состояния, ещё не выполнена.

T327 — явное согласование владельцем, вопрос отправлен; ответа ещё нет.
Слияние PR1 не использовано как согласие на новый DTO. Backend изменение можно
рассмотреть отдельно, но весь T317/PR2 и KAN-218 не считаются завершёнными.
После согласования: SQL projection в существующие endpoints, совместимый
decoder/«Нет данных» без редизайна, nativePG API/browser regression и новый
проверенный head. После review/merge следующий этап от актуального main.

Ограничения: два HTML-семейства, только выбранные головные вузы/бакалавриат;
PDF/филиалы/специалитет и массовое подключение ещё не реализованы. Новых
подтверждённых групп в реальном наборе0; synthetic M:N проверяет механизм,
не подтверждает реальные конкурсы. Нет переноса ЕГЭ, snapshots или прогнозов.
Новый public API coverage2027 —0/785, цель471/785 не достигнута. Знаменатель
остаётся датированным реестром2026-11-10; текущий отчёт не утверждает, что
непубликация2027 объективно блокирует всю страну.

Обязательный Linux CI и exact final head фиксируются в draft PR, чтобы
добавление результата в отчёт не создавало ещё один непроверенный SHA.
Backend draft: [PR28](https://github.com/deylon999/admitflow/pull/28).

### Исправление регрессии backup/restore в CI

На `3b7bc1d` оба backend job упали на пяти существующих тестах restore/source-size:
1126 passed, 5 failed. [PR run](https://github.com/deylon999/admitflow/actions/runs/44828963792)
и [push run](https://github.com/deylon999/admitflow/actions/runs/44828955034).
Причина: verifier SQLite backup запрещал любые triggers/views, а новая0014
добавляет защитные триггеры неизменяемости и согласованности публикации.

Verifier теперь сверяет полный набор type/name/table/SQL с доверенным DDL
соответствующей миграции. Неизвестные, изменённые и отсутствующие триггеры,
а также дополнительные views отклоняются. Проверки checksum, revision, raw
references, integrity, foreign keys и `trusted_schema=OFF` сохранены.
В ещё не объединённой0014 выделен экспорт точного SQLite DDL без изменения
создаваемых объектов; применённые0001–0013 и PostgreSQL DDL не менялись.
Добавлены четыре проверки подмены схемы и проверка допустимых объектов0013/0014.
Локальные backup/restore: **14 passed, 0 skipped, 7.74s**.
`backend/.venv/Scripts/python.exe scripts/test_postgres.py tests/test_program_catalog_storage.py tests/test_program_catalog_import.py tests/test_migrations.py tests/test_migration_metadata.py tests/test_program_identity_storage.py tests/test_backup.py tests/test_restore.py`:
**101 passed, 0 skipped, 59.42s**, собственный disposable PostgreSQL17.
Финальный Linux CI и точный SHA после исправления фиксируются в PR,
без объявления успеха заранее.
