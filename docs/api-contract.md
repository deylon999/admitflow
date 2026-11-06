# Контракт API v1

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

## Следующий автоматический контракт

Automatic/archive пока не реализованы и не маскируются под manual. Будущий DTO должен включать mode, campaign/group/source, fetchedAt, sourceUpdatedAt (nullable), assessedAt, rulesVersion, quality, freshness и assumptions. Архив определяется происхождением, не возрастом HTTP-запроса. Unsupported и insufficient_data не содержат выдуманного place/процента. До реализации отдельного parser неизвестные sourceKind/modelVersion отклоняются.

GET может повторяться при сетевой ошибке; операции записи автоматически не повторяются. Для POST watches/snapshots интерфейс передаёт Idempotency-Key: один ключ на неизменённые данные до подтверждённого результата. Сервер сохраняет DTO и изменение в одной транзакции; повтор возвращает прежний 201, другие данные с тем же ключом — 409. Ключ ограничен владельцем и не даёт доступа к чужим записям. Записи владельца сериализуются; SQLite BEGIN IMMEDIATE проверен нагрузочными тестами, PostgreSQL FOR UPDATE требует отдельного реального прогона в T017. Лимиты 20 направлений, 500 снимков и 12000 ключей на сессию.

При удалении направления сохранённые response payload очищаются; остаётся только tombstone ключа/хеша до удаления/истечения сессии. Повтор такого ключа возвращает 410 и не восстанавливает направление. Полное удаление сессии удаляет и ключи. Массовый каталог потребует cursor/limit; не выдавать текущий лимит 50 за национальную пагинацию.

## Уточнения ручного пути B07

Файл импорта читается как строгий UTF-8 (BOM допустим). До предпросмотра проверяются дубли декодированных JSON-ключей, конечность чисел и вложенность до64 уровней. Отмена чтения разрешает выбрать другой файл и отбрасывает поздний результат; она не отменяет уже отправленный импорт. Лимиты имён160/200 и запроса справочника120 считаются по Unicode code points, как на сервере.

UTC-представление ручных дат должно находиться в годах0001–9999; выход после применения timezone возвращает422. GET export возвращает409, если сохранённые даты опережают текущие серверные часы. История не меняется; повторить после исправления часов или окончания допустимого будущего интервала импорта.

Отменённый private GET сразу завершает ожидание общей загрузки сессии, не отменяя её для других потребителей. Ответы401 и ответы со старыми headers после смены доступа освобождают непрочитанное тело. Переходы по ссылкам во время сохранения блокируются, unload защищён. Открытая форма недоступна для отправки, пока выполняется другой mutation. Защита SPA back/forward и временное восстановление после reload добавлены в B08 ниже; восстановление после аварии браузера не гарантировано.

## Восстановление ручной формы B08

GET session дополнительно возвращает draftScope:64 lowercase hex, односторонний namespace для локального черновика. Он стабилен для текущей сессии, не является cookie/owner hash и не авторизует запросы. Старый API без поля остаётся совместимым, но локальное восстановление отключено. Миграция БД для scope не требуется.

Новый React-клиент сохраняет в sessionStorage одну версионированную запись до16KiB: поля формы, scope, исходный snapshot ID, время/TTL и при попытке отправки ключ/отпечаток операции. До POST ключ записывается локально; при восстановлении неизменённой формы он используется повторно. Неполные поля сохраняются, формула проверяется при отправке. Истёкшие/повреждённые/чужие по scope записи не восстанавливаются. TTL до30 минут, ограничен гостевым сроком; чтение не продлевает его. Удаление и ограничения описаны в data-policy.md.

Восстановление требует явного нажатия. Перед заполнением формы readonly GET проверяет текущий cookie scope и перечитывает направления, не создавая сессию. Изменившийся доступ скрывает старый preview и требует синхронизации. Для удалённого направления или нового latest без прежнего intent доступен просмотр полей, без восстановления. Если прежняя отправка могла завершиться, разрешён безопасный повтор с сохранённым ключом; server replay проверяется раньше expected snapshot.

POST snapshots принимает необязательный X-Expected-Snapshot с ID базового снимка. Новый UI передаёт его всегда. Для новой операции несовпадение latest возвращает409 без записи, плохой/неоднозначный заголовок400; кешированный replay возвращает прежний ответ без добавления истории. Старые клиенты без заголовка сохраняют прежний контракт. Владелец блокируется существующей транзакцией; native PostgreSQL-конкуренция пока не проверена.

Блокировщик data router теперь защищает SPA back/forward в пределах документа; dirty departure подтверждается один раз, pending save не разрешает уход. Полная загрузка документа/другой origin по-прежнему защищены beforeunload/document guard. Восстановление после аварии браузера не гарантировано: оно зависит от сохранности sessionStorage вкладки.

## Аттестация источников B11


B11 source-adapter contract: DTO unknown/null,HMAC scope(source/group/year),official row order and immutable snapshot semantics сохранены. Adapter.attested=true теперь требует frozen Attestation:passport/fixture paths,derived/original SHA256,exact URL/season/kind/version,date и verified sample size>=min(50,total). Runtime registry не читает произвольные пути и не скачивает manifests; declaration проходит code review и CI проверку файлов/хешей. Different URL/year/kind отвергаются даже при allow_unattested. Наличие proof metadata само по себе не включает source/group и не делает source assessmentAvailable. Synthetic attestation существует только в tests fixtures; PRODUCTION_REGISTRY пока пуст.


B11 `GET /api/v1/groups`: q/universityId/branchId(илиmain)/year/after/limit1–50. Возвращает только метаданные,не candidate rows/keys/raw. Cursor по opaque group ID,фильтры сбрасывают pagination вUI. coverage(manual/archive/automatic/unsupported) отдельно от dataKind(archive/live),snapshot fetch time отдельно от nullable sourceUpdatedAt;lookupAvailable не означает assessmentAvailable. Root university включает свои филиалы,branchId уточняет подразделение. Неподключённый вуз имеет честныйempty/manual fallback и отдельную ссылкупредложенияисточника.

B21: `facets.branches` и `facets.years` относятся ко всему каталогу до
применения фильтров, независимо от числа элементов `items` текущей страницы.
Frontend принимает до20_000 branch facets, в соответствии с бюджетом
reviewed profile catalog MAX_PROFILES, сохраняя проверки каждого поля,
страницы максимум50 групп и transport bound10MiB. Это клиентский предел
ресурса; backend не вводит отдельный лимит100 филиалов. HTTP503/некорректный
ответ не показывается как подтверждённое отсутствие групп.

`POST /api/v1/sources/{sourceId}/lookup` — existing guest cookie +same-origin custom header,JSON publicCode (1–64ASCIIletters/digits/hyphen,outerwhitespace trimmed). No network fetch,subscription or idempotency record is created. Source/group/year scoped HMAC searches only current published validated snapshot. Output:group metadata,found,candidate factual fields(rank/score/consent/priority/participation),5minute confirmationToken/expiresAt bounded by guest deadline. Publiccode,cookie and ownerhash are not returned/persisted/logged. Token carries opaque scoped candidate key +source/group/snapshot/expiry,MAC domain-separated and owner-bound;it is not an account/session credential and cannot move to another owner. Unavailable/unpublished source409,missing source404,invalidcode422 without echo,missingcookie401,cross-origin403. Not-found does not mean withdrawal or rejection. Token consumption/stale snapshot validation comes with subscription API;lookup itself never saves.

`GET /api/v1/direction-budget` gives limit20,total,manualCount,archiveCount for current guest. `POST /api/v1/subscriptions` consumes confirmationToken,returns201{id,groupId,sourceId,createdAt};it requires owner write lock,checks MAC before cached replay,then token expiry/current snapshot/budget for a new subscription. Repeated same confirmation returns exact saved IDs;distinct confirmations for the same owner/group/key reuse one subscription. Max12000 operation records still applies. `GET /api/v1/subscriptions` returns only own saved directions,factual candidate fields/current dated group and immutable confirmedSnapshotId;no raw/public code/key/cookie. Numeric model remains unsupported. Cookie reset/expiry cascades private records,not shared source rows. Manual JSON format is still manual-export-v1 and does not transfer archive subscriptions.

## Служебное

`GET /api/status` возвращает `status` (`ok` или `degraded`), `checkedAt`, `worker` (`state`: `alive`, `stale`, `never_seen`; `lastSeenAt`; `ageSeconds`), `sources` (`total`, `byState`) и `jobs` (`byState`, `overdue`). Только агрегаты. Снаружи закрыт в nginx. Запросы к API ограничены 64 КБ, `/api/v1/import` — 8 МБ. Перегрузка пула соединений даёт 503 с `Retry-After`.
