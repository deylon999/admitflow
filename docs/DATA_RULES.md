# Данные, расчёты и границы вывода

Формат reviewed-html-table-v2 для нового SGU4576: только явно перечисленные альтернативные названия экзаменов в одной колонке сравниваются как множество с проверкой размера и без повторов; положение колонок не меняется. Неизвестное название или состав альтернатив не нормализуются. Ранги, scores, consent, priority, seats, source/year и правила сценария не меняются. V1 остаётся строгой для прежних профилей; новая версия сохраняется в provenance. Проверки: test_next_scope.py (перестановка допустима, добавление экзамена и применение v2-послабления к v1 запрещены).

B14: опорный каталог MICCEDU 2025 содержит 1257 организаций и филиалов с исключениями мониторинга. registryTotal/registryEdition описывают этот датированный набор; nationalTotal остаётся null. Каталог объединяется с операторскими записями по явно сверенным ID, без объединения филиалов по названию/домену. legalName — полное исходное название, name — ограниченное название ручной записи; officialUrl может быть неизвестен. Дата карточки каталога не подтверждает наличие приёма, свежесть списков или работу автоматического источника. Кандидатные ссылки из инвентаризации сайтов не меняют attestation/coverage/rules_version.

## 1. Три уровня ответа

| Уровень | Что можно утверждать | Что нельзя утверждать |
| --- | --- | --- |
| Факт | Официальный номер, число мест, статус и дата из источника | Неизвестное поле считать отсутствующим/нулевым |
| Сценарий | Результат при явно заданном составе участников и допущениях | Называть его окончательным зачислением |
| Прогноз | Оценка вероятности с проверенной моделью и ограничениями | Выдавать процент без истории, валидации и калибровки |

## 2. Ручная модель manual-v1

Граница оценки: `ready` — можно показать два ручных сценария; `insufficient_data` — нет полного корректного ввода, место не показывается; `unsupported` — неизвестная версия правил, automatic или archive без аттестации, числового вывода нет. Пустая форма не получает отрицательный статус «вне бюджета». POST `/api/v1/assess` и frontend используют общий набор `shared/assessment-cases.json`; `/calculate` остаётся строгим арифметическим контрактом. Статусы внутри ready относятся только к введённым данным и не являются вероятностью поступления.

Эти границы действуют также на лендинге, в диаграмме, title/description и FAQ. Не называть ручной результат «как на самом деле» или универсальным официальным местом. Смысл согласия/его область нельзя привязывать ко всем направлениям одинаково: FAQ направляет к правилам конкретной кампании. Пример интервью остаётся рассказом, не доказательством гарантии. Готовые ручные функции и будущая автоматизация помечаются раздельно.

Параметры: `R` — номер в одном упорядоченном списке; `B` — доступные места выбранного конкурса; `E` — люди выше, не участвующие в этом же конкурсе; `N` — остальные выше, чьё согласие отсутствует в выбранном сценарии.

`E` и `N` не пересекаются. `R >= 1`, `B >= 1`, `E,N >= 0`, `E+N < R`. Дробные, пустые, отрицательные и чрезмерные значения отклоняются. Нулевое число мест в автоматическом источнике — допустимый факт с результатом «мест нет», но текущая ручная форма не поддерживает этот случай: расширение модели требует отдельного теста и версии.

- Текущий упрощённый сценарий: `P = R - E - N`.
- Сценарий всех согласий среди этой же группы: `W = R - E`.
- Если `P > B`: сейчас вне границы по модели.
- Если `P <= B < W`: зависит от дальнейших согласий.
- Если `W <= B`: внутри границы в обоих рассмотренных сценариях при неизменности остальных входов.

Пример: R=120, B=90, E=30, N=16 → P=74, W=90. При B=80 → условный сценарий; при B=73 → за границей. Это не вычисление вероятности.

Люди без согласия не исчезают из конкурса навсегда. Изменение состава списка, приоритетов, мест или этапа может сделать ручную оценку неактуальной. Формулировку «при любом сценарии» нужно заменить на текст, ограниченный рассмотренными допущениями.

Импорт собственной manual-export-v1 истории остаётся ручным вводом: проверяются формула, версия и даты, но данные не аттестуются как официальный список. Даты исходных ручных сохранений сохраняются, неизвестная свежесть источника не становится известной. В новой сессии создаются новые IDs и ownership; файл не содержит токен доступа к старой сессии. Порядок сохраняется даже при равных timestamp. Восстановление старого файла не означает нового обновления вуза.

Ручные снимки упорядочены по UTC-времени и затем ID по убыванию. При равном серверном времени новый внутренний UUID выбирается больше предыдущего, само время не сдвигается и число не теряется из latest. Если часы ушли назад относительно создания направления/последнего снимка (включая импорт из будущего), запись отклоняется409 без изменения истории. Нельзя исправлять это выдуманной датой или переписыванием старого снимка; проверить часы/дождаться допустимого времени. Формула manual-v1 от этого не меняется.

## 3. Автоматическая модель

Проверка источников 2026-11-01: [аудит](evidence/source-audit.md), [паспорт пилота](sources/pilot.md). Кампания исследования — 2026; вне приёмной кампании данные маркируются архивными. В СГУ проверены правила VII–VIII, пункты 82–90: https://www.sgu.ru/sites/default/files/page/files/pravila-priema-2026_0.pdf. Официальное ранжирование, согласие на организацию и приоритеты нельзя заменить сортировкой по сумме баллов.

До аттестации конкретной группы автоматический вывод — unsupported/insufficient-data. Разрешено показывать официальный порядок и источник; нельзя автоматически исключать человека по неизвестному статусу или брать число мест из соседней группы. Подтверждённого универсального правила исключений для двух вузов сейчас нет, поэтому исключения в автоматическую модель не добавлены. Начальный охват — бюджет общего конкурса бакалавриата/специалитета; магистратура, БВИ, квоты и платные группы требуют отдельной версии правил.

До реализации зафиксировать для каждого сезона и поддержанного способа приёма:

1. Что именно является конкурсной группой; какие виды мест включены.
2. Смысл каждой колонки и области согласия/приоритетов.
3. Официальный порядок ранжирования, правила равных баллов и специальные признаки.
4. Какие статусы исключают участие, а какие лишь временные/информационные.
5. Какие этапы и даты меняют правила оценки.
6. Можно ли вычислить эффективное участие из доступных полей; какие внешние сведения отсутствуют.

Сначала сохранять официальный порядок строк. При равных баллах не сортировать по одному числу баллов, игнорируя дополнительные основания. Исключать строку только с проверенной причиной. Каждый исключённый участник должен иметь reason code и ссылку на правило. Пользователю показывать агрегаты, не списки чужих персональных сведений.

Если эффективный приоритет нельзя восстановить, результат получает `insufficient_data` или ограниченный сценарий, а не выдуманное «реальное место». Межвузовые заявления нельзя склеивать по ФИО/сходству ID. Перестановка приоритетов — новый вход, который требует пересчёта.

## 4. Проверка нормативной основы

Это техническая спецификация проверки, а не универсальная правовая инструкция. Для релиза нужен датированный набор официальных правил конкретного сезона и вузов. Страница [СГУ о приёме 2026](https://sgu.ru/abiturient) описывает приоритеты и действия с согласием; она подтверждает, что простой номер не исчерпывает правила. Она не подтверждает универсальность текущей формулы для всех вузов.

На 2026-10-31 URL [конкурсных списков РГУ им. Косыгина](https://rguk.ru/applicant/konkursnye-spiski/?special_version=N) найден поиском, но прямое открытие завершилось ошибкой инструмента. Это кандидат для исследования, не проверенная интеграция. Общедоступный единый API всех конкурсных списков не подтверждён. Доступ к данным Госуслуг/ФИС не предполагается автоматически.

В T010 исполнитель должен найти официальную актуальную редакцию порядка приёма, изменения выбранного года и правила вузов, записать URL, даты действия и пункты в source passports. Пока этого нет, автоматическая модель не считается нормативно проверенной. Каталог организаций и доступ к конкурсным спискам проверяются раздельно.

## 5. Контракт адаптера

Вход: зарегистрированный источник, группа/сезон, ограниченный raw response. Выход: `ParsedList` с entries, capacity, source timestamps, warnings и provenance. У каждой строки original row reference, source candidate id, official rank, поля с типами и явным unknown.

Обязательные образцы для каждого адаптера: обычный список, пустой, пагинация, отсутствующее поле, неизвестное значение, дубль ID, другой сезон, страница ошибки вместо списка, изменение заголовков, неполная загрузка. Список из одной страницы не считается полным, если есть пагинация.

Идентичный hash не создаёт новую содержательную версию, но успешная проверка фиксируется. Изменённый parser на старом raw response имеет новую parser version. Качество и содержимое прошлой версии не переписываются.

Базовый контракт реализован в sources/contracts.py: неизвестные согласие/приоритет/места остаются None, порядок строк задаёт official_rank, score не используется для пересортировки. Ключ участника — HMAC-SHA256 публичного ID с отдельным секретом не короче 32 байт и областью source/group/year. Ключи разных источников/сезонов не склеиваются; секрет нельзя менять без отдельного переноса идентичностей. ФИО и другие дополнительные поля контракт отклоняет. Ошибки адаптеров содержат только ограниченные коды, не ValidationError с исходными значениями.

Production registry пока пуст: ни один реальный адаптер не аттестован. Тестовый Registry разрешает явно переданные синтетические адаптеры только с allow_unattested; этот флаг не должен появляться в пользовательском API или production CLI. Адрес, домен, версия адаптера, группа и сезон берутся из закрытого registry/БД, а не из запроса браузера.

Публикация: блокировка Source, повторная проверка binding/quality, вставка SourceSnapshot и всех CandidateEntry, затем переключение PublishedSnapshot в одной транзакции. Ключ повтора — source/raw SHA-256/adapter version; normalized hash выявляет недетерминированный parser. Новая версия парсера создаёт отдельный снимок на тех же bytes. Возврат исторического payload после более нового и запоздалый fetch требуют проверки; latest не откатывается молча. Provenance хранит fetched URL/MIME/charset, row references, seats и parser version. Старые снимки без этой информации сохраняются как неизвестные и требуют проверки перед продолжением импорта. Ошибка БД не меняет latest/строки; raw может остаться orphan до политики retention.

## 6. Свежесть и доверие

Состояния: `fresh`, `stale`, `source_error`, `quarantined`, `archived`, `unknown`. Freshness рассчитывается по политике конкретного источника и наблюдаемым временам. Отсутствующую дату публикации показывать как неизвестную.

Диагностика также различает `disabled` и `unsupported`. Без опубликованного снимка — unknown; при ошибке прежний снимок остаётся доступен с отдельным dataKind. Архив/прошлый сезон никогда не fresh, даже после успешной проверки сегодня. Для live fresh означает недавнюю успешную проверку того же опубликованного содержимого (начальная политика 1800 секунд), а не известное время изменения источника. Последнее остаётся отдельным nullable sourceUpdatedAt. Нужен зарегистрированный аттестованный адаптер той же версии; без него unsupported. Диагностика не включает автоматически assessment и не повышает coverage группы.

Метрики покрытия также требуют automatic coverage конкретной группы и rules_version; наличие адаптера в коде или вуза в справочнике не увеличивает счёт автоисточников. Опубликованные группы считаются по корректным complete snapshots активной версии; fresh и archive разделены. Эти метрики описывают подключение, а не доступность численного assessment (он пока отключён). Общий национальный знаменатель не подтверждён — nationalTotal=null, процент национального охвата не показывается.

Завершившееся ошибкой задание или истёкшая аренда worker исключают fresh: диагностика возвращает source_error, сохраняя last good snapshot, его даты и dataKind (в том числе archive). Отключение источника и зарегистрированный карантин имеют приоритет. WorkerState показывает только unknown/queued/running/idle/failed/expired, без токена аренды и внутренних ошибок. Отсутствие задания само по себе не подтверждает работу worker. После восстановления очереди свежесть снова определяется адаптером, полнотой и временем последней успешной проверки; она не продлевается чтением диагностики. Это правило проверяется на синтетических live/archive снимках и границе lease, не считается проверкой живого сборщика или PostgreSQL.

HTTP 200 с CAPTCHA, HTML-ошибкой или пустой таблицей не является успехом. Резкое уменьшение числа строк/мест требует проверки; порог — настраиваемый сигнал, не универсальный запрет на реальные изменения. Отключение источника не удаляет последние корректные данные.

Базовый validator проверяет source/group/year/version/kind, complete, заявленное число строк, уникальные ключи/row references и непрерывный официальный порядок от 1. Пустой список требует явно подтверждённого expected_rows=0. Форматы с пропусками официальных номеров потребуют отдельной аттестации; сейчас карантин безопаснее догадки о полноте. Время источника не может опережать загрузку больше чем на 5 минут или регрессировать относительно предыдущего снимка.

Начальная QualityPolicy: падение числа строк более чем на 50% при предыдущем числе не меньше 10 либо мест более чем на 50% вызывает карантин. Рост мест более чем вдвое (и минимум на 10) относительно прошлого снимка вызывает карантин `capacity_growth`, а первая публикация с числом мест вне диапазона 50–200% от проверенного значения группы — `capacity_mismatch`: завышенное число мест иначе превратило бы любую строку в положительный статус. Это настраиваемый сигнал для проверки, а не утверждение об ошибке вуза. Неизвестное число мест сохраняется как None. Validator не сортирует строки по баллам и не вычисляет согласие из приоритета. Карантин не меняет опубликованный latest.

Архивные данные всегда содержат сезон и метку архива. «Проигрывание» истории ускоренно допустимо только в демонстрационном режиме; время события и время воспроизведения разделяются.

## 7. Персональные данные и доступ

На первом этапе не собирать ФИО, СНИЛС, паспорт и учётные данные Госуслуг. Публичный ID тоже может относиться к человеку, поэтому его хранение, вывод и логирование ограничиваются. Для cross-session lookup нужен минимально необходимый ID конкретного источника; в логах — редактированное значение/внутренний reference.

Сырые списки не отдавать публично из volume. Описать сроки хранения и удаление. Перед внешним запуском проверить применимые требования к обработке и размещению данных и назначить ответственную сторону; считать это открытым пунктом приёмки, а не заявлять юридическую готовность автоматически.

## 8. Прогноз и ИИ после MVP

Для вероятности потребуются временные снимки до исхода и достоверная метка самого исхода. Исчезновение строки из списка не равно поступлению. Нельзя использовать финальные согласия или приказы как признаки для прогноза на более раннюю дату.

Сначала baseline, затем более сложная модель. Разделение обучения/проверки по времени и вузам, предотвращение утечки одного человека между выборками, оценка Brier/log loss и калибровки, анализ по сроку до дедлайна и группам. Порог качества фиксируется до итоговой оценки; сравнение с baseline обязательно. Нет улучшения/мало данных → процент не показывается.

LLM получает только разрешённые структурированные facts; текст сайтов считается данными, не инструкциями. Ответ проверяется на соответствие числам и источникам. При таймауте/ошибке/противоречии используется шаблон. Автоматическая подача документов, отзыв согласия или выбор вуза за пользователя не входят в продукт.

Границы календаря UTC (B07/T149): ручная aware ISO-дата должна нормализоваться в UTC в пределах годов0001–9999 включительно. Выход за эти границы после применения timezone — ошибка валидации. Принятые исходные offsets и микросекунды сохраняются. Проверки: backend/tests/test_timestamp_bounds.py и frontend/tests/time.test.ts. Формула, группы согласий и сезон не менялись.

Часы при ручном экспорте (B07/T150): время выгрузки наблюдается после согласованного чтения под блокировкой владельца. Если сохранённая дата опережает эти часы, вернуть409 и сохранить данные; не выдумывать более позднюю дату экспорта и не менять историю. Это также кратковременно касается импортированных дат в допустимом будущем интервале5 минут. Повторить после того, как серверное время достигнет сохранённого.

Устаревшее ручное редактирование (B08/T160): новый клиент передаёт X-Expected-Snapshot с ID снимка, на основе которого открывал форму. Под блокировкой владельца сервер сначала проверяет сохранённый результат ключа операции: успешный replay не добавляет снимок даже после более новых записей. Для новой операции несовпадение latest ID возвращает409 без записи; неверный заголовок —400. Для старых клиентов заголовок необязателен. Формула, даты наблюдения и исходная история не меняются. PostgreSQL-конкуренция остаётся отдельной непроверенной частью T017.

B11 source transport bounds: default5MiB,explicit trusted per-adapter cap<=8MiB after measured SGU original5851174bytes. Raw storage/restore absolute8MiB; selected child-exchange cap is enforced independently. Offline inspection also8MiB. This changes transport capacity only,not season/participation/consent or calculation semantics. Research-only curl was bounded20MiB and never enabled production fetch by itself.

SGU2026/4588-v1: factual archive only,573rows and exact09.03.04 general-budget group,16places(не20includingquotas). Official rank preserved for ties;Да/Нет consent→true/false,---→unknown/null;Зачислен→enrolled,---status→unknown(неactive/withdrawn). First priority component preserved;OVP/VPP не интерпретируютсякак official outcome. No verified source timestamp→null. Version fails closed if group/year/layout/count/capacity changes. Neither fetchedAt nor November page footer makes the archive a current campaign or guarantees admission. Candidate public codes normalize to HMAC(source/group/year/publicCode);stable operator key is required and is not logged/exported.

B11 confirmed archive directions share the existing20-direction guest budget with manual watches. Owner row lock protects manual create,manual import and source confirmation;successful cached replay is checked before capacity/expiry changes and never duplicates. A confirmation is owner/source/group/snapshot bound,valid300s for a new operation. A previously successful operation may replay its saved IDs after token expiry while guest access remains valid;an unconsumed expired token410 and an unconsumed stale snapshot409 make no writes. Source public code is not stored. Creation records one immutable source-confirmation-v1 assessment with stateunsupported and factual fields only—no calculated admission/consent action/probability. Source association follows that immutable confirmed snapshot. Guest reset/expiry removes private subscriptions/assessments/operation payloads,shared source snapshots remain.

Migration0005 aligns the composite assessment→subscription/group FK with its existing simple CASCADE FK. PostgreSQL previously rejected a guest cascade when assessments existed;SQLite had hidden this ordering issue. Only the constraint changes;old IDs/facts/source snapshots are retained through upgrade/downgrade/upgrade tests. Production migration remains explicit,not blind stamp/create_all.

B11 fact history: `source-confirmation-v1` preserves explicitly confirmed initial facts; subsequent `source-facts-v1` assessments are appended in the shared source publication transaction for subscriptions confirmed in that same source. Both have `unsupported` numeric assessment state; consent/priority/participation remain source facts. A missing row is `candidate=null,present=false`, never inferred withdrawal. Page order uses source snapshot fetchedAt then assessment ID; assessedAt and sourceUpdatedAt remain separate. Historical values/seats/fetch URL come from the immutable snapshot. Current source check status does not rewrite historical dates.

Manual history dispatch is fixed by stored modelVersion. `manual-v1` retains its own callable; new versions must be appended explicitly. Reading an unknown version returns409 and preserves inputs/version, never substitutes the current calculator. This also applies to exported history. Source-fact versions remain a separate unsupported numeric assessment.

B11 final audit2026-11-04: newly appended source-facts-v1 assessedAt is actual processing-clock time, separate from historical snapshot fetchedAt. Retrying the same publication retains its original assessment timestamp. Previously stored assessment timestamps are not rewritten. History order/cursors continue to use snapshot fetchedAt+ID, independently of processing time.

B12 reviewedtablefamily: one decoder+closedJSONprofiles for independently auditedSGU573/GUAP581. GUAPcontractlist explicitly has0places and no consentcolumn;contract/payment and highestpriorityflags do not become admissionconsent. All581consent=null,92explicit enrolled suffixes preserved,othersunknown. Unknown source-time remainsnull. Annualcapacity/group-index counts do not replace snapshotcapacity. Second factualsource attestation is not automatic eligibility for a budget/admission model.

B12/listed-consent-v1 (conditional scenario,not officialadmission): server uses exactimmutableordered generalbudget snapshot and assumes applicant's ownconsent,fixedcomposition/capacity,no cross-grouppriorities. Explicitwithdrawn rows above are excluded once;unknownparticipation remains included. Amongotherincludedrows,counttrue/false/nullconsent separately. Currentbound=[1+true,1+true+unknown];all-consentplace=1+allincludedabove. No second quota deduction because sourcealreadyrepresentsonecompetitiongroup. Officialorder resolves ties;never re-sort byscore. Within means all-consentplace<=seats;out means evenlowercurrentbound>seats;conditional means uppercurrentbound<=seats<worst;unknownbounds crossingcapacity givesinsufficient_data. Contract/non-general/unknownrule/zero-or-missingcapacity/missingcandidate refuse decision withreasoncodes. Ownfalse/nullconsent is an explicit assumption,not submitted action. Versioned result/diff is appended,oldresult unchanged. Models do not compute an officialresult/probability;allUIexplanations mustretaintheseconditions.

B12 coverage rule:registration/catalog/proof definitions do not imply a published import or live automation. A counted import requires enabled exact reviewed scope,complete current published snapshot,normalized hash andmatching parser version. Imported rows are a sum across snapshots,not unique people;archive/conditional/automatic counters remain distinct. Operator hold retains lastgood datedarchive,does not refresh fetchedAt. National denominator remains unknown. See catalog-coverage.md and test_coverage.py for reproducible definitions.

B15 sectioned-competition-v1: 11 reviewed archive2026 contract groups on 10 official
MIEPP/UIFR pages. Each section is identified by exact program, index/count and
preceding study-form/funding/capacity metadata. Hierarchical header labels and
rowspan/colspan are validated. The page attestation counts all reviewed sections;
each group publishes only its own rows. A shared URL never merges scoped HMAC
identities. Contract/payment is not admission consent: consent=null throughout.
Priority 0 means unknown/null only in this new version; positive values remain.
Color legends and highest-priority flags do not prove participation or admission:
participation=unknown. Publication text without a timezone leaves sourceUpdatedAt
null; archive never becomes fresh after a new fetch. Contract groups cannot enable
the general-budget scenario. Unknown/empty sections are unsupported until reviewed.
Old V1/V2 decoders and proofs retain their original interpretation.
