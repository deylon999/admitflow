# Контракты API v1

Единый справочник контрактов. Прежний api-contract.md оставлен как указатель.
Маршруты и схемы реализованы в backend/app/main.py, source_api.py, scenario_api.py,
changes.py и schemas.py; клиент проверяет ответы на границах entities.
Исторические результаты ниже не являются новым прогоном тестов.
Политика хранения — [data-policy.md](../data-policy.md), правила — [DATA_RULES.md](../DATA_RULES.md).

Same-origin `/api/v1`, JSON camelCase, даты ISO 8601 с явной timezone. GET не изменяет пользовательские данные. Все записи требуют X-Requested-With: abiturient. 204 не содержит JSON. 400 — неверный ключ операции, 401 — утрата гостевого доступа, 404 — отсутствующее или чужое направление, 409 — лимит/конфликт ключа, 410 — повтор операции уже удалённого направления, 422 — невалидный ввод. Ошибки имеют detail; массив валидации преобразуется в безопасное сообщение интерфейса.

B06: validation422 возвращает строку detail, не более20 безопасных путей fields и флаг truncated. Исходные значения, context/message исключения и неизвестные имена ключей не возвращаются; OpenAPI описывает ValidationProblem. Названия и ссылки отвергают C0/DEL до URL-нормализации. JSON с повторными ключами, NaN/Infinity/переполнением либо вложенностью свыше64 отвергается400 до endpoint. Проверка действует для application/json, application/*+json и отсутствующего Content-Type — всех JSON-вариантов, которые разбирает FastAPI.

Ручные даты принимаются только как ISO-строки с timezone и точностью до6 знаков; числовой Unix timestamp, naive дата и лишняя точность не преобразуются молча. Внутри Python допустим aware datetime. Предпросмотр импорта сверяет UTC-год создания от2000 и inclusive допуск exportedAt до5минут вперёд относительно часов браузера; сервер повторяет проверку по своим часам. Порядок opaque IDs при равном времени сравнивается по Unicode code points, как в Python; лимиты длины строк в контракте также считают code points, размер файла по-прежнему ограничен байтами.

Клиент проверяет реальный календарь и timestamp с явным смещением и точностью до 6 знаков дробной секунды, как в серверных снимках. Порядок истории сравнивается по UTC-микросекундам, затем id по убыванию; Date.parse не используется для проверки календаря/микросекунд. Перекрывающиеся страницы, дубли между направлениями, снимок до создания направления и снимок позже exportedAt отклоняются до показа/импорта.

Клиент ограничивает каждый запрос 15 секундами, включая чтение тела, и отменяет чтение направлений при отмене query. Записи автоматически не повторяются. После timeout исход записи может быть неизвестен: проверить историю; повтор неизменённой формы использует прежний Idempotency-Key. Ошибка чтения показывает кнопку повтора.

JSON-ответ читается потоком до10MiB, тело ошибки — до64KiB. Превышение отменяет дальнейшее чтение, malformed UTF8/MIME/JSON не выдаются за данные; сообщение сервера ограничено500 символами. Контроль смены сессии действует до обработки headers/error и после чтения тела. Ответ прежнего session epoch не возвращается как текущий, его query автоматически не повторяется; старый promise не очищает более новую сессию.

При доступном Web Locks первый bootstrap и явный reset сериализуются между вкладками; ожидание блокировки ограничено15секундами, HTTP-вызовы сохраняют собственный timeout. Reset не захватывает ту же блокировку повторно. При отсутствии Web Locks используется прежний путь; полная атомарность первого открытия нескольких вкладок на такой платформе не заявляется.

Любой SessionExpiredError из query или mutation переводит кабинет в общий expired state: карточки, старая форма, сравнение и импорт скрываются. 401 не повторяется автоматически и не запускает POST session. Только явный reset создаёт новую ownership; private queries отменяются/обновляются перед снятием expired state. Публичная информация о покрытии не зависит от гостевой сессии.

При reset вкладка после успешного DELETE уведомляет другие вкладки через localStorage. Они забывают кешированную сессию, отменяют private reads и скрывают старые карточки/черновик. Кнопка синхронизации делает GET session и перечитывает список до показа, без POST session. Точная expiresAt отображается как срок доступа; перезагрузка его не продлевает. При недоступном localStorage межвкладочное уведомление не гарантируется, серверная ownership/проверка 401 сохраняется.

GET watches/{id}/history возвращает total (1–500): число всех ручных снимков направления, независимо от размера/курсора страницы, только после проверки владельца. Клиент проверяет границы; ответ старого сервера без total отображается с неизвестным общим количеством. Новые сохранения в другой вкладке могут изменить total между запросами страниц; метка не является фиксацией конкурентной транзакции на весь просмотр.

Список и полный экспорт читают снимки пакетно, без SELECT на каждое направление. При20 направлениях проверено не более3SELECT-запросов на endpoint, включая ownership; export сохраняет все записи до500 на направление и owner lock. Это локальный SQLite query-count тест, не измерение PostgreSQL p95 или национальной нагрузки.

GET /api/ready и /api/health проверяют совпадение Alembic revision с heads из поставляемых миграций. Отсутствующая таблица/пустая, старая или неизвестная revision даёт безопасный503. Проверка ничего не мигрирует и не заменяет schema audit или проверку реального PostgreSQL. /api/live остаётся независимым от БД.

Вход API ограничен 8 MiB по фактически принятым bytes независимо от Content-Length: превышение — 413. Время приёма полного тела — 10 секунд, timeout — 408; некорректная длина — 400. Отказ не запускает endpoint. Nginx настроен на такой же размер и idle body timeout; реальный запуск контейнера ещё требует проверки.

Host должен входить в ALLOWED_HOSTS (точные имена без портов/wildcard). Запись с Origin проверяется дополнительно к custom header: чужой/null origin или Sec-Fetch-Site=cross-site — 403. В development разрешены origins доверенных локальных hosts на dev-портах; в production требуется точное совпадение с HTTPS PUBLIC_ORIGIN, включая порт. Клиенты без Origin по-прежнему требуют custom header. Readonly calculate/assess не изменяют сессию и исключены из write guard.

## Реализовано

- POST assess: внешний state ready/insufficient_data/unsupported. Неизвестные версии, automatic и archive без аттестации не содержат result. Ручной ready содержит только условный расчёт; это не вероятность. Общие случаи — shared/assessment-cases.json.
- GET sources/{id}/status: публичная ограниченная диагностика зарегистрированного источника, без строк участников/raw/хешей. Отдельные season/dataKind, lastCheckedAt, lastSuccessfulCheckAt, fetchedAt и sourceUpdatedAt (null, если неизвестно). workerState: unknown/queued/running/idle/failed/expired; unknown означает отсутствие задания, expired — истёкшую аренду. Failed/expired дают state=source_error даже при недавнем успешном снимке; disabled и quarantine сохраняют приоритет. Последний корректный снимок, его даты и архивная классификация сохраняются. Token/lease/attempts и внутренний error code не возвращаются. assessmentAvailable=false: диагностика сама по себе не является расчётом. Неизвестный source — 404.
- GET coverage: catalogUniversities отдельно от automaticSources; publishedGroups/freshGroups/archiveGroups только для включённых источников аттестованной версии, automatic coverage группы и ненулевой rules_version. Снимок должен быть complete и той же parser version с normalized hash. Свежая группа требует fresh у всех её usable источников; архивная — archive у всех. nationalTotal=null, национальный процент не вычисляется. Начальный production registry даёт 2 вуза / 0 автоисточников, ошибка endpoint не подменяется нулём в UI.

- POST/GET/DELETE session: создание, expiry, явное удаление. После 401 нельзя автоматически повторять создание или запись. Cookie Path=/api, HttpOnly, SameSite=Lax.
- GET universities?q=: items/total, максимум 50, только manual coverage в текущей версии. Всего в стартовом наборе 2 исследованных вуза.
- GET/POST watches: максимум 20 на владельца. GET detail содержит последние 100 снимков; latest совпадает с первой записью history. История не означает время обновления официального источника.
- POST snapshots: новая запись, исходная история сохраняется. DELETE watch удаляет только свою запись с каскадом истории.
- GET watches/{id}/history?before={snapshotId}&limit=100: items/nextCursor, от новых к старым по capturedAt/id. Limit 1–100, cursor только из истории этого направления; ошибочный — 400, чужое направление — 404. Новые сохранения не сдвигают следующие страницы. UI подгружает до всех 500 снимков, сохраняя уже прочитанные при ошибке следующей страницы.
- GET export: JSON `manual-export-v1`, exportedAt и все свои направления с полной историей (до 500 снимков на каждое). Чужие данные, cookie, owner hash и ключи операций не включаются. Ответ private/no-store; filename admitflow-export.json.
- POST import: `{bundle: manual-export-v1}` с обязательным Idempotency-Key, ответ importedCount/snapshotCount/replayed. Все записи проверяются до вставки: только manual-v1, арифметика, safe URL, уникальность, порядок и timezone дат, до 500 снимков и общий лимит 20 направлений с учётом имеющихся. Импорт атомарен, генерирует новые IDs и ownership текущей сессии; сохраняет даты ручного ввода. При повторе того же ключа не создаёт копии; replay после удаления не восстанавливает удалённое. В кеше операции только агрегаты без импортированного тела. 422 — плохой файл, 409 — лимит/изменённое тело при том же ключе.
- Snapshot: sourceKind=manual, modelVersion=manual-v1. Входы — четыре целых числа. Клиент перепроверяет диапазоны и совпадение place/worstPlace/seats/state с расчётом, не доверяет одному TypeScript cast. Некорректный response вызывает ошибку и не отображается как надёжные числа.

Общий пример shared/manual-watch.json проверяется против настоящего FastAPI-ответа и frontend parser. Это защита от несовместимого изменения DTO. URL с credentials и неподдержанные протоколы не принимаются. Даты без timezone не принимаются frontend.

## Архивные данные и отдельные контракты

Архивный путь реализован отдельно от Watch/Snapshot: группы, lookup, subscriptions,
история фактов и сохранённые условные сценарии. Их HTTP-контракты приведены ниже.
manual-v1 остаётся только ручной моделью. Архив определяется происхождением,
а не возрастом запроса; unknown не заменяется нулём. Сценарий не является
официальным результатом или вероятностью поступления.

GET может повторяться при сетевой ошибке; операции записи автоматически не повторяются. Для POST watches/snapshots интерфейс передаёт Idempotency-Key: один ключ на неизменённые данные до подтверждённого результата. Сервер сохраняет DTO и изменение в одной транзакции; повтор возвращает прежний 201, другие данные с тем же ключом — 409. Ключ ограничен владельцем и не даёт доступа к чужим записям. Записи владельца сериализуются; SQLite BEGIN IMMEDIATE проверен нагрузочными тестами, PostgreSQL-конкуренция и optimistic writes проверены в T017/B10 на настоящем PostgreSQL: [evidence](../evidence/b10-runtime.md). Лимиты 20 направлений, 500 снимков и 12000 ключей на сессию.

При удалении направления сохранённые response payload очищаются; остаётся только tombstone ключа/хеша до удаления/истечения сессии. Повтор такого ключа возвращает 410 и не восстанавливает направление. Полное удаление сессии удаляет и ключи. GET /groups выполняет фильтрацию и keyset-пагинацию after/limit в SQL (T201); GET /universities использует отдельную offset-пагинацию. Страница до50 элементов не является пределом общего покрытия. [Проверка T201](../evidence/b16-sql-catalog.md).

## Уточнения ручного пути B07

Файл импорта читается как строгий UTF-8 (BOM допустим). До предпросмотра проверяются дубли декодированных JSON-ключей, конечность чисел и вложенность до64 уровней. Отмена чтения разрешает выбрать другой файл и отбрасывает поздний результат; она не отменяет уже отправленный импорт. Лимиты имён160/200 и запроса справочника120 считаются по Unicode code points, как на сервере.

UTC-представление ручных дат должно находиться в годах0001–9999; выход после применения timezone возвращает422. GET export возвращает409, если сохранённые даты опережают текущие серверные часы. История не меняется; повторить после исправления часов или окончания допустимого будущего интервала импорта.

Отменённый private GET сразу завершает ожидание общей загрузки сессии, не отменяя её для других потребителей. Ответы401 и ответы со старыми headers после смены доступа освобождают непрочитанное тело. Переходы по ссылкам во время сохранения блокируются, unload защищён. Открытая форма недоступна для отправки, пока выполняется другой mutation. Защита SPA back/forward и временное восстановление после reload добавлены в B08 ниже; восстановление после аварии браузера не гарантировано.

## Восстановление ручной формы B08

GET session дополнительно возвращает draftScope:64 lowercase hex, односторонний namespace для локального черновика. Он стабилен для текущей сессии, не является cookie/owner hash и не авторизует запросы. Старый API без поля остаётся совместимым, но локальное восстановление отключено. Миграция БД для scope не требуется.

Новый React-клиент сохраняет в sessionStorage одну версионированную запись до16KiB: поля формы, scope, исходный snapshot ID, время/TTL и при попытке отправки ключ/отпечаток операции. До POST ключ записывается локально; при восстановлении неизменённой формы он используется повторно. Неполные поля сохраняются, формула проверяется при отправке. Истёкшие/повреждённые/чужие по scope записи не восстанавливаются. TTL до30 минут, ограничен гостевым сроком; чтение не продлевает его. Удаление и ограничения описаны в data-policy.md.

Восстановление требует явного нажатия. Перед заполнением формы readonly GET проверяет текущий cookie scope и перечитывает направления, не создавая сессию. Изменившийся доступ скрывает старый preview и требует синхронизации. Для удалённого направления или нового latest без прежнего intent доступен просмотр полей, без восстановления. Если прежняя отправка могла завершиться, разрешён безопасный повтор с сохранённым ключом; server replay проверяется раньше expected snapshot.

POST snapshots принимает необязательный X-Expected-Snapshot с ID базового снимка. Новый UI передаёт его всегда. Для новой операции несовпадение latest возвращает409 без записи, плохой/неоднозначный заголовок400; кешированный replay возвращает прежний ответ без добавления истории. Старые клиенты без заголовка сохраняют прежний контракт. Владелец блокируется существующей транзакцией; native PostgreSQL-конкуренция проверена в B10, включая optimistic writes; [результаты](../evidence/b10-runtime.md).

Блокировщик data router теперь защищает SPA back/forward в пределах документа; dirty departure подтверждается один раз, pending save не разрешает уход. Полная загрузка документа/другой origin по-прежнему защищены beforeunload/document guard. Восстановление после аварии браузера не гарантировано: оно зависит от сохранности sessionStorage вкладки.

## Аттестация источников B11


B11 source-adapter contract: DTO unknown/null,HMAC scope(source/group/year),official row order and immutable snapshot semantics сохранены. Adapter.attested=true теперь требует frozen Attestation:passport/fixture paths,derived/original SHA256,exact URL/season/kind/version,date и verified sample size>=min(50,total). Runtime registry не читает произвольные пути и не скачивает manifests; declaration проходит code review и CI проверку файлов/хешей. Different URL/year/kind отвергаются даже при allow_unattested. Наличие proof metadata само по себе не включает source/group и не делает source assessmentAvailable. Synthetic attestation существует только в tests fixtures; Базовый PRODUCTION_REGISTRY пуст; runtime_registry() выбирает явно настроенные reviewed-профили. Пустой базовый объект не означает отсутствие настроенных архивных источников.


B11 `GET /api/v1/groups`: q/universityId/branchId(илиmain)/year/after/limit1–50. Возвращает только метаданные,не candidate rows/keys/raw. Cursor по opaque group ID,фильтры сбрасывают pagination вUI. coverage(manual/archive/automatic/unsupported) отдельно от dataKind(archive/live),snapshot fetch time отдельно от nullable sourceUpdatedAt;lookupAvailable не означает assessmentAvailable. Root university включает свои филиалы,branchId уточняет подразделение. Неподключённый вуз имеет честныйempty/manual fallback и отдельную ссылкупредложенияисточника.

B21: `facets.branches` и `facets.years` относятся ко всему каталогу до
применения фильтров, независимо от числа элементов `items` текущей страницы.
Frontend принимает до20_000 branch facets, в соответствии с бюджетом
reviewed profile catalog MAX_PROFILES, сохраняя проверки каждого поля,
страницы максимум50 групп и transport bound10MiB. Это клиентский предел
ресурса; backend не вводит отдельный лимит100 филиалов. HTTP503/некорректный
ответ не показывается как подтверждённое отсутствие групп.

`POST /api/v1/sources/{sourceId}/lookup` — existing guest cookie +same-origin custom header,JSON publicCode (1–64ASCIIletters/digits/hyphen,outerwhitespace trimmed). No network fetch,subscription or idempotency record is created. Source/group/year scoped HMAC searches only current published validated snapshot. Output:group metadata,found,candidate factual fields(rank/score/consent/priority/participation),5minute confirmationToken/expiresAt bounded by guest deadline. Publiccode,cookie and ownerhash are not returned/persisted/logged. Token carries opaque scoped candidate key +source/group/snapshot/expiry,MAC domain-separated and owner-bound;it is not an account/session credential and cannot move to another owner. Unavailable/unpublished source409,missing source404,invalidcode422 without echo,missingcookie401,cross-origin403. Not-found does not mean withdrawal or rejection. Token consumption/stale snapshot validation occurs in POST /subscriptions;lookup itself never saves.

`GET /api/v1/direction-budget` gives limit20,total,manualCount,archiveCount for current guest. `POST /api/v1/subscriptions` consumes confirmationToken,returns201{id,groupId,sourceId,createdAt};it requires owner write lock,checks MAC before cached replay,then token expiry/current snapshot/budget for a new subscription. Repeated same confirmation returns exact saved IDs;distinct confirmations for the same owner/group/key reuse one subscription. Max12000 operation records still applies. `GET /api/v1/subscriptions` returns only own saved directions,factual candidate fields/current dated group and immutable confirmedSnapshotId;no raw/public code/key/cookie. Официальный числовой результат не поддерживается; сохранённые условные сценарии доступны только для явно включённых аттестованных групп, отдельно от фактов (см. раздел сценариев ниже). Cookie reset/expiry cascades private records,not shared source rows. Manual JSON format is still manual-export-v1 and does not transfer archive subscriptions.

## Служебное

`GET /api/status` возвращает `status` (`ok` или `degraded`), `checkedAt`, `worker` (`state`: `alive`, `stale`, `never_seen`; `lastSeenAt`; `ageSeconds`), `sources` (`total`, `byState`) и `jobs` (`byState`, `overdue`). Только агрегаты. Снаружи закрыт в nginx. Запросы к API ограничены 64 КБ, `/api/v1/import` — 8 МБ. Перегрузка пула соединений даёт 503 с `Retry-After`.

## Справочник вузов, архивные API и сохранённые сценарии

Все сокращённые маршруты ниже имеют префикс `/api/v1`.

B14 national reference directory: `GET /api/v1/universities?q=<tokens>&offset=0` returns at most 50 entries, `total`, nullable `nextOffset`, `registryTotal` and `registryEdition`. Search combines casefolded name/region tokens. Entries retain bounded manual `name`, optional full `legalName`, region, branch flag, `catalogOrigin` (operator/monitoring), nullable `officialUrl`, dated provenance and manual coverage. A registry card URL is not an admissions-list URL. Unknown site stays null. Read creates no guest and registers no automatic Source. Explicit aliases preserve existing operator IDs/values. Catalog updates are packaged artifacts, applied on process restart (rebuild/recreate for image deployments).

Coverage now returns `registryTotal`/`registryEdition` for the reference edition, and `catalogUniversities` counts its union with operator entries without duplicates. `nationalTotal` stays null until full national reconciliation. These counters do not increase reviewed/imported/fresh/automatic sources.

B11 archive UI: public `/groups` remains readonly and creates no guest. Explicit lookup uses an existing/explicitly bootstrapped guest; 30 lookups per guest per 60-second window are persisted in `lookup_budgets` across API processes (429 + Retry-After). No IP/code is stored there, and session deletion cascades the budget. This is a per-guest budget, not a distributed IP-abuse shield. Confirmation is bound to owner/source/group/snapshot, expires within 300 seconds, and never implies submission of admission consent. The UI requires a separate group/row acknowledgement before POST `/subscriptions`. Shared manual+archive direction limit is20. Archive cards remain fact-only; manual JSON/comparison/print exclude archive records explicitly.

`GET /subscriptions/{id}/history?limit=20&before=<assessment-id>`: owner-only keyset page, max100, total, nextCursor. Each item has immutable fact version, assessment time, historical group snapshot metadata, candidate or explicit absence. Foreign subscription404, foreign/unknown cursor400. Publication appends facts atomically; initial confirmation and subsequent facts share no numeric admission claim.

Source checks: GET `/sources/{id}/checks` is readonly public operational metadata, latest20 fenced completed outcomes, no source rows/keys/raw. Entries have checkedAt,success/failed,safe errorCode and retained snapshotId. Empty means no recorded completed attempts since schema0007, not proof of no prior failures. Success after recovery does not erase failed checks. History detail is loaded explicitly and does not bootstrap a guest.

GET `/archive-export`: existing guest required. Format `archive-facts-v1`, scope `current-published-facts`, exportedAt, max20 direction DTOs with current snapshot provenance. This readonly personal data export excludes public codes, normalized candidate keys, cookie/owner/session credentials. It is separate from manual-export-v1; not an import/recovery token or full-history/raw backup. History remains paginated independently.

B12 conditionalscenarios:GET `/subscriptions/{id}/scenario` and `/scenario-history?limit=20&before=<assessment-id>` are owner-only readonly views of storedversionedresults. GET never computes or writes. Eachresult has modelVersion,state,nullable numbers/reasonCodes/assumptions and literal officialResultAvailable=false;dates distinguish snapshotfetch/sourceupdate/assessment. `changes` are whitelisted candidate/scenario/capacity fields. Foreignowner404,foreigncursor400,limitmax100. `enable-scenarios <reviewed-source-id>` is operator-only,attestation-checked,explicit and idempotent;existing subscriptions backfill once per snapshot/version. New publication/confirmation appends in its transaction;failure rolls back pointer/facts/scenario together. Group scenarioAvailable is separate from official assessmentAvailable (stillfalse).

B12 scenario explanations are stored with each result as scenario-explanation-v1:summary,basis,limitations and factualchanges. Read exposes subscriptionId/groupId/sourceId for client association checks,previousId link and exactsnapshot/fetch/assessmenttimes. Frontend rejects unsupportedofficial-result flags,inconsistentbounds/state/identity/cursors. HistoricalfactDTOscenarioAvailable remainsfalse;currentgroups expose separateboolean forreviewedconditionalbudgetscenario. Explanationversion is independent of numericalmodelversion;old storedtemplates/results are not rewritten.

B12 owner changes and exact comparison:

- `GET /api/v1/changes?limit=20&before=<event-id>&unread=false` returns `{items,total,unreadCount,nextCursor}`;each event includes `id,createdAt,seenAt,title,scenario`. Scenario uses the existing immutable ScenarioRead contract. Limit1–50,stable descending(createdAt,id);cursor resolves within owner before unread filtering. Foreign/invalid cursor400;expired owner401. GET never marks seen.
- `POST /api/v1/changes/{event-id}/seen` requires the existing same-origin/custom-header write protection and owner session. Foreign event404;repeat preserves the original seenAt. Reading or following comparison alone does not acknowledge an event. No external messaging is sent.
- `GET /api/v1/subscriptions/{id}/scenarios/{assessment-id}` retrieves an exact saved model version;owner/subscription/model association checked,foreign or missing404. The public DTO field is `previousId` (internal stored facts use previousAssessmentId). UI links to `/tracker?direction=<subscription-id>&assessment=<assessment-id>` and reads both exact stored versions.

Events are inserted atomically with changed assessments/publication;unique assessment reference prevents duplicate worker retry messages. Initial/no-semantic-diff/template-only results do not create events. Deleting subscription/guest cascades through assessments to events. Source-operation journal remains operator-only and contains no applicant fields.

Coverage response adds nonnegative registeredSources,reviewedSources,importedSources,importedGroups,importedUniversities,importedRows,archiveImportedGroups,conditionalGroups and nullable lastImportedAt. Existing automaticSources/publishedGroups/freshGroups/archiveGroups retain their separate accepted-auto-policy meaning. catalogUniversities is a catalog count,nationalTotal is null. See [catalog-coverage.md](../catalog-coverage.md) for scope/denominator/disabled/held-source rules;generatedAt is report generation,lastImportedAt comes from snapshotfetch.

## V3 public catalog (S200)

New read-only facade; existing v1 APIs remain unchanged. No browser session is
created. See product-functional-audit.md for data scope and rationale.

- GET /api/v1/catalog/universities: q (120 chars), region (120 chars),
  offset 0..100000, limit 1..50 (default 12), sort name|name-desc.
  Returns items/total/nextOffset/regions/registryEdition.
- GET /api/v1/catalog/universities/{id}: stable reference ID, name/legalName,
  region/isBranch/officialUrl, provenance, knownProgramCount and years.
  Count means verified imported scopes, not all courses offered.
- GET /api/v1/catalog/programs: q, universityId, year 2000..2100, subject,
  offset/limit/sort as above. Returns items/total/nextOffset/years/subjects.
  Current verified examination dataset is absent: subjects=[], specific subject
  filters return no matches. Unknown year never falls back to another year.
- GET /api/v1/catalog/programs/{id}: group/campaign/year identity, university,
  code/title, form/funding/category, nullable seats and provenance.
  historicalCutoff, examRequirements and forecast are explicitly null.

Unknown detail IDs return 404, invalid filter bounds 422. All responses use
camelCase. Provenance includes URL, verifiedAt, nullable sourceUpdatedAt, kind
(monitoring|archive), optional edition/originalSha256. Capture/review timestamps
are never represented as the source publication timestamp. Reference edition
2025 and admission campaign 2026 are separate fields.

Explicit metadata import after migrations (backend working directory):
python -m app.catalog_import
It atomically imports two reviewed SGU archive-2026 budget/general scopes,
refuses existing identity conflicts and never enables sources or imports PII.
Without import, program endpoints correctly return an empty catalog. No schema
migration or new database is needed for this metadata-only slice.
