# B12 — движение к зафиксированному рубежу70%

## T187 — семейство адаптеров и границы подключения

Registry разрешает одну версию parser с несколькими неизменяемыми Attestation. Каждый URL/year/kind имеет отдельный proof;неизвестный scope остаётся invalid_binding. Старый single-proof контракт сохранён для опубликованных версий. Повтор scope,чужой домен,неверная версия и отсутствие proof отвергаются. Это архитектурная возможность,а не новое покрытие сама по себе.

Проверка: `backend/.venv/bin/python -m pytest backend/tests/test_attestation.py backend/tests/test_registry_contract.py backend/tests/test_sgu_adapter.py -q` —38passed,exit0. Включён reuse одного callable для двух точных test scopes и отказ для неподтверждённого URL/сезона/live. Реальная проверка нескольких профилей — T188.

## T188 — один parser для двух настоящих форматов

Один parse_table декодирует SGU573строки и GUAP581строку через JSONпрофили backend/app/sources/profiles/reviewed.json. Отличия rowselector,labels/positions,headers,metadata,codecприоритета и enrollment suffix заданы данными;новый алгоритм на вуз не написан. LegacySGUparser/version сохранены для старых снимков. Профили пока не включены автоматически в Source/worker.

Независимые stdlib HTMLParser audit обоих приватных оригиналов сверили все1154строки,порядок/баллы/согласие/приоритет/статус/HMAC и границы16/17 и0/1. Reports b12-sgu-family-audit.json,b12-guap-family-audit.json. GUAP:платный конкурс,явные0мест,581unknownconsent,92явныхenrolled;договор/оплата не трактуются как согласие. DerivedDOM180023bytes заменяет только ID,сохраняет остальные14cells/статусы;manifest содержит hashes/преобразования. Реальные коды не включены вGit.

Текущие targetedchecks:22passed (7family+15attestation),exit0. Проверены source/year/group/URL/kind scope,два макета,одинаковые FIXTUREкоды в разных источниках,обрезанная таблица,неверный HTMLсезон и duplicateidentity. Более ранний registry/legacy набор38passed. Отдельные SGU4570/4576 иGUAPphysics вернули только заголовки,не подтверждены как пустые и не подключаются. Два доступных оригинала относятся к разным университетам;структурный reuse доказан ими,национальное покрытие не заявлено.

## T031 — второй независимый источник подключён

GUAP581-row contract archive attested separately,with exact proof/profile JSON/hash/passport and five genuineDOMnegative variants. Same commondecoder used forbothuniversities. register-reviewed accepts onlyclosedprofilekeys,disabledbydefault,explicit--enable validatesproof;conflicting metadata/missingkey roll back. LegacySGUversion cannot be silently replaced. Runtime registry withkey includes legacy plus reviewedfamily;withoutkey still empty.

NativePG3cases passed:bothreal-format worker imports1154rows/two snapshots,private lookup+confirmation/subscriptions forbothuniversities,foreignowner403/empty,missingkey/conflict rollback,legacy version preserved. Local40registry/profile/legacy tests+12familynegative tests passed. Actual separate-process worker fetched GUAP once via bounded pinnedHTTPS and nativePG:581rows,0places,success→idle,1HTTP,cleanuptrue;minimum900s interval respected. Report b12-guap-worker.json. Captured original bytes/hash/fetchedAt then replayed without additionalHTTP into ownedlocalruntime8090,b12-guap-runtime.json. Catalog now exposes two universities/snapshots,SGU573budget andGUAP581contract,archiveonly. Paidfunding translated in UI. No officialprediction or live/24h claim.

GUAPconsent remainsunknown,capacity0literal;therefore numericmodel must decline this funding/unknowncase. This is explicitly a secondindependent factualsource,not proof that bothgroups support budget predictions. Annualcapacity is not substituted.

## T034 — версионированный условный сценарий и diff

Server derives listed-consent-v1 from an immutable officialorder in one reviewedgeneralbudgetgroup. True/false/unknownconsent produce currentlower/upperbounds;all-consent position includes all listed unknownparticipants,knownwithdrawn excluded once. Ownconsent/fixedcomposition/no cross-grouppriorities are explicit assumptions. Contract/non-general/zero-or-missingcapacity/unknownrule/missingrow refuse decision. Unknownbounds crossingcapacity give insufficient_data. Officialresult/probability never computed.

Results stored in Assessment bysubscription/snapshot/modelversion;transaction includes sourcepublication/facts/scenario. Explicitoperator enable only reviewedprofile,does not upgrade parser or change legacyhash. Initialsubscription appends once;GETcurrent/history readonly. Currentresult+causaldiff preserve all old versions and actual processingtime. Historicalfactmetadata does not acquire mutable scenarioAvailable. API/docs/DATA_RULES updated.

Checks:11domaincases including216consent/withdrawal combinations,capacity/state diff,boundaries,unknown/unsupported;3localstoragecases andsame3nativePG passed. Native checks reproduce storedresult from snapshot/model,syntheticconsent change increments currentbound without worst-position doublecount,repeatdoesnotduplicate,oldhistorybytesstayexact,foreign404/cursor400,GETdoesnotrecalculate,injectedfailure rollsback allpublication,explicitbackfill idempotent andGUAPcontract safelyunsupported. UI and explanations continue inT039;not yet the70%rubric.

## T039 — проверяемые объяснения и интерфейс сценария

Stored scenario-explanation-v1 uses only resultnumbers/reasoncodes/diff,not website prose orLLM. It states ownconsent/fixedlist/capacity/ignoredcross-grouppriorities and explicitunsupported/missingdata. UIshowsconditionalnumbers,current/all-consentconditions,dates/source snapshot,readonlyversionhistory andcausalchanges;contract0capacity getsrefusal,consentunknown remainsunknown. NumericSourceSnapshot mismatch causes reread card before display. Private scenarioqueries cancel/remove onguestchange/reset/deletion. OfficialassessmentAvailability stillfalse;separate scenarioAvailable indicateseligibleconditionalmodel.

Checks:16localmodel/storage/template cases passed (domain exhaustive loop is108combinations,correcting earlier216note);same3nativePGstorage cases passed withstoredtemplates. Frontend17contracttests passed,including malformedstate/bounds/officialflag/mixedhistory/cursors;productionbuild and3Chromium cases passed onactualtwo-source nativePG fixtureAPI:SGUscenario+history at320px/light/dark,GUAPpaidrefusal/no fabricatedconsent. Rawidentifiers never used inbrowser. FirstfiveB12tasks complete;70%rubric still requires deterministicreplay/changefeed/ops/coverage andfullcurrentlocalpath.
