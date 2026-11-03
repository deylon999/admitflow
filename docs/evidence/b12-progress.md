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

## T036 — детерминированный replay двух архивов

Reproducible `scripts/replay_archives.py --output docs/evidence/b12-replay.json` ran the two real-derived anonymized formats twice in separate nativePGdatabases. Sixstages:baseline,clearlysyntheticconsent/templatechange,samepayloadrepeat,badsourceanswer,recovery,explicitrowabsence. Worker/queue/publication/scenario/history/API are real code;transport is deterministiclocalreplay with0externalHTTP. Bothruns produced identicalsemanticresults;randomowner/assessmentIDs and actualprocessingclock excluded from comparison,not replaced with sourceclock.

Observed:SGUcurrentbound increments1 withconsentchange,worstpositionunchanged;GUAPtemplate-only change producesnodiff andstillunsupportedcontract;repeat/recovery do notduplicate orrefresh originalsnapshotfetch;failure keepslastgood;absence givescandidate_not_in_snapshot/numbersnull,notwithdrawal. Histories3SGU/2GUAP,archive2026 remainsvisible. Report recordsalloutcomes andfake sourceclock separately fromprocessingtime. Cleanuptrue. This is not24h/liveobservation or evidence ofactualhistoricalconsentchanges. CI native replaycase added.

## T040 — личная лента изменений и сравнение

Migration0008 persists one cascading event per changed assessment;initial/template-only/retried publications produce no messages. Read-only owner-scoped keyset API resolves cursor before unread filtering;acknowledgement preserves first timestamp. Comparison links retrieve exact stored current/previous assessment,not frontend recomputation. Session reset/deletion remove private events and caches.

Checks:3SQLite+same3nativePG cases passed,including template-only/retry,foreign404,stable same-clockcursor afterseen,cascadingdeletion/reset andatomicrollback on eventfailure. 23migration checks included in26native run passed.6TSfeedcontract cases passed;productionbuild and4Chromium checks passed againstactualtwo-sourceAPI/PostgreSQL,including syntheticpublication→feed→comparison→seen→reload andsecondownerisolation. Test-only controlfile mode600 in/tmp targetsowneddisposableDB;no public mutation endpoint,noexternalHTTP.

## T037 — управление источниками и безопасный журнал

Migration0009 adds safe transactional SourceOperation journal for registration/enable/disable/retry/quarantine/resume/model-enable. Read-only status shows configured/published versions and latest20 bounded operations. Local CLI only,no public control API. Operator quarantine blocks enqueue/claim/publication,invalidates current lease and survives late failures/registration. Explicit resume verifies reviewed binding and respects stored interval;refresh_pending remains until actual worker success. Source clocks/last good pointer untouched.

Checks:6local queue/operator cases and2native operator+23migration cases passed. Verified stale worker token cannot renew,publish held snapshot refused,disabled/unknown version enable atomic refusal,held source cannot silentlyresume,no rate-limit bypass,old snapshot unchanged,no lease tokens/credentials in status. RUNBOOK documents exactcommands and release limits.

## T038 — честное покрытие

Coverage now counts actual DB registrations,enabled exact reviewed scopes,complete current published imports/dedupedgroups/universities/rows,archive imports andeligibleconditionalgroups separately from accepted automatic/live policy. No registration/proof-only inflation;legacy/common proofs do not doublecountscope;GUAPpaid not conditionalnumeric. Latestimportdate comes from originalfetchedAt,reportdate separate;nationalTotalnull. UI/docs/DATA_RULES explain semantics.

Checks:8local coverage/status cases,1nativePG two-source case andstrictTScoveragecontract negatives passed;productionbuild passed. Native genuine-derived2archives count1154rows/2universities/2groups,1conditional/0automatic/0fresh;registeredbutunpublished0imports,heldlastgoodarchive unchanged,disabled/corruptsnapshot excluded. PrimaryDocker stillT031 until finalT189 deployment;do not claim currentUIbeforethat.
