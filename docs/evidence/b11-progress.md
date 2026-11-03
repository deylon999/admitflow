# B11 —30 задач,2026-11-03

Основа2c866bd, clean Git. Шесть подходов по5; отдельный Conventional Commit/acceptance/evidence на задачу. Первые5: T019,T007,T008,T013,T027. Дальнейший выбор по реальным зависимостям/оригиналам; release gates не сокращаются. Все source original bytes приватны в ignored backend/var, реальные публичные ID в Git не добавляются.

Новое основание исследований: capture СГУПС1348 успешен, attested=false/archive2026. Capture СГУ4588 отказал response_too_large; отдельное офлайн-исследование ограничено20MiB, production limit5MiB не меняется. Предыдущий preview остановлен вне этой сессии; новый изолированный admitflow-b11/8090 поднимается из B10 images, пользовательские volumes не переиспользуются.

## 1/30 T019

Ручная приёмка сведена в manual-acceptance.md. Текущий targeted Chromium10/10 на новом PostgreSQL/nginx8090,exit0; предыдущие native restart/ownership/limits/replay доказательства проверены и применимы к неизменённому коду. Не реализованные automatic карточки не закрыты. Плановые deliverables исправлены на реальные файлы тестов.

## 2/30 T007

Локально vendored13 variable normal WOFF2 subsets Inter/JetBrains Mono из Fontsource5.3.0,304756bytes, обе OFL лицензии, provenance и SHA256 manifest. Внешний Google CSS import удалён. Actual FontFace Latin/Cyrillic600 загружаются со своего origin с запретом всех внешних запросов; тест проверяет loaded,2+faces/family,manifest/лицензии200. Fresh preview build + fonts/landing:5 passed,exit0,7.5s. Четыре исходных PNG визуально прочитаны; tokens в styles.css используют правильные families и light/dark hierarchy. Визуальные расхождения/размеры подробно относятся к T008.

При завершении T019 validator поймал nextTask=T007 со старым blocked status. Устранён уже неактуальный font-network blocker, T007 назначена in_progress; приватный незапубликованный T019 commit исправлен до реализации fonts,render/check снова валидны. Опубликованная история не менялась.

## 3/30 T008

Все4 original/current PNG просмотрены, основные6 цветов каждой темы совпадают с измеренными пикселями originals.4 screenshots с actual local fonts сохранены; visual.md перечисляет отличия принятого copy/manual states/дополнительной высоты/видимого focus cue. Добавлена1024px проверка; landing+fonts6 passed,exit0,320–1440/две темы. Pixel-identical или вся T026/T045 не заявлены.

## 4/30 T013

Получены genuine SGU/STU originals. Derived SGU573-row DOM fixture с manifest,SHA256/OFL-neutral provenance и privacy transform; оригинальныеIDs не остались. Sanitizer сохранил все573retained non-identifier rows точно,deterministic rerun unchanged. Missing/login/header/encoding/oversize/capture corruption cases:9passed,exit0. Ошибка sanitizer при удалённом active ancestor исправлена до создания fixture; первичный test missing fixture зафиксирован как setup failure,после исправления9/9. Original dirs700/files600,raw не вGit. STU headers-only не выдан за confirmed-empty; registry остаётся пуст. Source passport обновлён. Offline8MiB inspection не меняет production5MiB limit.

## 5/30 T027

Контракт закрыт на genuine fixtures: frozen explicit Attestation привязывает паспорт/fixture+original hashes,exact URL/year/kind/version,date и минимум50проверенных строк(либо весь меньший непустой sample). Голый attested=true отвергается; test-only synthetic proof явно отделён от production. Unknown/null и HMAC scope сохраняются; scope mismatch не обходится allow_unattested. Registry/DTO/coverage/fixture/attestation regressions ниже; production пока не включает адаптер. Не добавлены выдуманные original pages или unsupported empty-STU.

T027 validation:33passed,exit0,0.80s (attestation,registry,DTO,coverage and real derived fixture). Первые5 завершены. Следующая пятёрка: T174 explicit8MiB policy,T029 real SGU adapter,T030 real-source quarantine,T032 actual worker,T033 actual atomic publication. Второй источник/STU и live-soak не будут отмечены done без данных.

## 6/30 T174

Default5MiB сохранён; frozen Adapter max_bytes имеет absolute8MiB cap. Worker передаёт declared policy в child,проверяет metadata against selected limit before payload read;raw/backup/restore cap8MiB. Initial transport/storage/backup suite71passed;added large referenced raw backup/verify/restore and size/envelope/worker boundary suite4passed,exit0. Отвергаются default5MiB для5851174byte sample,8MiB+1,hash/size mismatch. Actual pinned-DNS/TLS bounded_fetch8MiB successfully fetched SGU5851174bytes at2026-11-03T17:11:06Z,SHA256309968faf6ab11f172589adfe7f4a5fb43797b14c18c515055b206387dca4e9a;private600 file. Actual HTML hash differs from first capture although byte count same; adapter must normalize factual cells,not infer a list change from template hash. docs/api-contract.md consolidated adapter contract; duplicate newly-created API.md merged,old history retained in Git.

## 7/30 T029

Archive-only SGU4588 adapter с exactURL/group/year/layout/573row scope и8MiB policy. Official order/score/consent/priority сохранены;---unknown,sourceUpdatedAt=null. Конкретный passport и fixture hashes обязательны; runtime registry опционально строится только при operator-owned SOURCE_IDENTITY_KEY32–64bytes,без автоматического enable/утечки key черезrepr. Независимый stdlib HTMLParser сверил все573 genuine original rows с BeautifulSoup adapter,включая16/17boundary и119tie-score groups:successtrue,IDs/keys не выведены (sgu-4588-attestation.json). Два предыдущих parser failures были из-за doubled whitespace в public metadata; whitespace нормализован без изменения смысла,не ослаблена привязкагруппы. Derived fixture теперь сохраняет скопированные original html/head/body wrappers для terminal-completeness check,с новым hash;ни один originalID не добавлен. SourceURL/year/kind/header/seats/duplicate/truncation/unknown cases проходят regression suite. Это один проверенный archive-format,неlive24h/второйисточник/официальныйпрогноз.

## 8/30 T030

Real SGU573-row DTO проходит existing normalization;quarantine suite verified incomplete/wrong-group/duplicate/order/count/revalidation failures and immutable last-good pointer/573entries. Unknown consent/priority/score остаютсяnull. Publication теперь отдельно проверяет declared adapter byte cap перед raw write,чтобы internal injection не обходил transport policy;large backup test explicitly declares8MiB. Current real-source/publishing/validation/size suite25passed,exit0,2.45s. Formula/season/consent meaning не менялись;failed pages не освежают published snapshot.

## 9/30 T032

Actual separate app.worker once fetched SGU viaHTTPS,published573rows/16seats inownedPG17;secondprocessidle/onesnapshot/900s,noHTTPstorm(report b11-sgu-worker.json). После этого добавлены progress heartbeats междуphases иPGdomain concurrency mutex+running-jobfilter:expired/stolen/disabled token нельзяrevive,onedomain serialized,otherdomains parallel.16 local worker/queue checks,11nativePGqueuechecks и2nativePGreal-format/API-isolationchecks passed. While genuine-formatfetchgated,manualhealth/session/list/catalog доступнычерезsamePG. Currentcode separately replayed private original in2workerprocesses(noHTTP),573rows/success+idle,cleanuptrue(b11-sgu-worker-replay.json);externalfetchnotrepeatedwithin900s. Fixedlease/boundedfetch fencing andB10processdeath proofs retained. 24h/live/secondsource не заявлены.

## 10/30 T033

Native PG genuine-format573-row publication:8parallel retries→1snapshot;injected rowflush failure retains last-good/573entries;crashaftercommit replay→1snapshot/573entries;archive/provenance/version/timestampunknown preserved. Real-format retention keeps2referenced versions and deletes onlyexpiredorphan afterdry-run. Native SGU+existingatomic suite11passed;new retention completeSGU suite5passed,exit0. No already-checked step repeated without new code/data reason. DATA_POLICY contradiction about raw7day cap resolved explicitly:developmentorphan TTL7days,referencedhistoryretained;productioncampaignretention remainsopenT049,notclaimedready. Source/rawhistoryretention criteria documented without silently deleting evidence.

Second5/5 complete. Next5:T175 explicitoperatorbootstrap,T022 groupcatalogfilters/coverage,T176 owner-bound lookup,T177 isolated20-limit subscriptions,T021 explicit frontend candidate confirmation. GenuineSTUstillunsupported;T031/live-soak remainopen.

## 11/30 T175

Explicit register-sgu creates known archive group disabled bydefault,idempotently(serializedPG/SQLite),thenenable requires exact reviewed registry/key. Conflictingmetadata rollback,arbitraryURLnotaccepted. Currentpreview rebuiltfromB11code/fonts;privateoperatorenv600/ignored/excludedbuildcontext,neverprinted. ActualcontainerCLI returnedcreatedtrue/enabledfalse,thencreatedfalse/enabledtrue twice;source status viaAPIconfirmedarchive/adapteravailable/assessmentfalse/nopublishedsnapshot.7nativeSGU/registrationtests+25localregistration/worker/adapter passed. Integrationrun uncovered3older synthetic-status fixtures missing new proof;updatedtest-only attestation(kind live/archive),notweakenedruntimegate. Fullcurrentbackend396passed,0skipped,exit0,49.08s viaownedPG. Existingwarningsonly. Noexternalworkerloopstarted.

## 12/30 T022

Public group catalog implemented:university(parentincludesbranches),branch/main,season,q,cursor/limit50;metadataonly,noIDs/rows/raw. Honestcoverage axis separatefromdataKind;missing/failedsource keepsdatedarchive distinct,assessmentfalse. UIreadonly(noPOST),manualfallback,proposalGitHublink(noautomaticmessage/enable),paginationclearswhenfilterschange. SourceHeaderanchorsfixedtoactualhomecalculator;mobiletrackerlinkexposesnewroute. Backendcatalog6passed;TScontract8passed;freshbuild10Chromiumpassed(landing320–1440+sourcefilter/error/pagination/320themes). Initial select-label test failed becausewrappedselectoptiontext affectedexactlabelmatching;explicit aria-labelsfixedwithoutlooseningassertions. Afterheaderfix3currentcasespassed. OnecontrolledactualComposeworkerfetchafter1382s>900 succeeded,realpreviewPGnow573archive rows/lookupAvailabletrue,noongoingloop. Nativeformat/worker/oldmanualproofretained. Productionarchive source isnotnumericadmissionassessment/nationwidecoverage.

## 13/30 T176

Authenticated scoped public-code lookup implemented without full-listendpoint/networkfetch/automaticwrite. Candidate facts preserveDecimal/unknowns and carrycorrectarchive group/snapshot/time. Confirmation≤300s/guestdeadline,MACdomain+ownerbound,opaque candidatekey only;rawcode/cookie/ownerhashneverreturned. Success,missingguest,notfound,wrongsource,CSRF,invalidcode/noecho,owner/key/tamper/expiry/tokenlength tested. Lookupcreates0Subscription/Watch/OperationRecords. Registrykeyreadercentralized;noautoenabledsources/IDcrossmatching. Tokenconsumptionstalechecks deferredtoT177,notmarkedcompleteimplicitly.

T176 final:12local lookup/catalog/origin/session cases passed,exit0;9nativePGsource/lookup/atomic cases passed,exit0,14.11s. HMAC lookup uses actual migratedPGnumeric/datetime fields and stillcreates0subscriptions. API confirmation expiry/tamper/owner checks are currentcode;not a user-facing source subscription yet.

## 14/30 T177

Owner-locked confirmation creates1Subscription+immutable factual unsupported assessment,never a calculated admission result.12parallel replays return1ID/1assessment/1operation. Combinedmanual+archive20-limit and manualimport enforced;18manual+4archiveconcurrent gives2success/2conflict,manual/importextra refused,replaystill201. Foreign/tampered/stale/expired/newconfirmationrefusals and successcacheafterexpiry verified. Guestreset/expiry deletesprivateSub/Assessment/Op,sharedsourcepersists. NativePG exposed old compositefk_assessment_subscription_group NOACTION cascade bug (reset500,SQLitepassed);dedicated0005migration makesCASCADE agree withsimpleFK,keepsoldIDs/facts across4→5→4→5,nohistoryrewrite. Current37native+SQLite/migration cases passed27.46s,exit0/0skip;22localsubscription/manual/import cases+5expanded casespassed. Native initially1resetfailurebeforefix recorded,notreclassifiedaspass. Operation12000cap retained. APIbudget/listpublished,nofrontendautosave.

### T021 — 15/30 — explicit archive lookup and confirmation

Current production UI: group/year/source-bound lookup, no save before checkbox, keyboard focus, unknown values and archive labels; public code stays in transient component memory and is cleared on save/session change. Source records now visible in tracker, combined20 limit, private source query cancellation/removal on guest switch, separate manual export/print semantics. Snapshot seats come from immutable snapshot, not mutable group metadata.

2026-11-03 checks: 5 new Chromium source-flow cases passed on disposable native PostgreSQL via `scripts/serve_source_e2e.py` with explicitly anonymized 573-row SGU-derived fixture. Includes response lost after commit, same-token retry/one record, reload, delete-all, not-found, keyboard and320px/light/dark. No real applicant codes in artifacts. 5 catalog cases passed. Frontend unit100 passed before extra contract case. TypeScript production build passed. API lookup4 passed; native source+migration runner37 passed with one failure from old hardcoded table count (15→16 after new lookup budget table), corrected and affected migration case rerun. Per-guest30/min lookup budget migrated0006, no codes/IPs, across-process locking; reset/cascade tested. Broad second-source/live/staging gates remain open.

### T178 — 16/30 — remove one archive direction

Owner-locked DELETE removes a subscription/its assessments, retains shared573-row source snapshot, and turns all consumed archive confirmations for that subscription fingerprint into payload-free410 tombstones. Replayed successful confirmations cannot resurrect a deleted record. New explicit lookup can start a fresh save; deletion is not permanent suppression of the applicant. Total quota released. UI requires confirmation; Escape/cancel restores focus. Native PostgreSQL2 cases passed (including concurrent DELETE/replay); one new Chromium deletion case passed, five earlier lookup cases passed on rebuiltUI; production build passed.

### T179 — 17/30 — immutable factual archive history

Publication now appends source-facts-v1 assessments only for subscriptions confirmed in that exact source; repeat publication is a no-op for history. Confirmation serializes with publication source lock. Endpoint returns owner-only stable keyset history (fetchedAt+ID), snapshot seats/URL/times, explicit nullable candidate, separate model version. History is fact-only/unsupported, not T034 automated numerical assessment or T036 second-source replay.

Native PostgreSQL3 cases passed: five same-time snapshots across two-row pages with no duplicates/omissions, unchanged original confirmation, duplicate publication, foreign ownership/cursor, synthetic consent toggle (clearly not a real observed event), and injected history failure rolling back snapshot/pointer/rows. First run exposed500 from validating confirmation extras as CandidateFact; fixed by selecting explicit candidate fields. Historical current-check fields removed to keep old responses stable. Command scripts/test_postgres.py selectors test_postgres_sgu::{history cases};exit0.

### T180 — 18/30 — archive history and comparison UI

Added strict fact-history contracts (snapshot/source/season identity, presence, stable microsecond+ID order, cursor consistency across pages), private lazy paginated history, source/version/times and explicit older-version selection. Comparison shows only observed field differences; missing row does not imply withdrawal; no probability. Session resets cancel/remove archive-history queries. Two Chromium cases passed: native single-version API and explicitly synthetic paginated comparison/absence at320px. Current production build passed, new invalid DTO/order cases tested separately. Synthetic changes are test scenarios, not claimed actual source events.

### T024 — 19/30 — provenance and distinct times

Shared source provenance now accompanies catalog/lookup/saved archive numbers: snapshot ID, actual fetched time, nullable source-updated time, separate last-check time, original official URL, current archive/stale/quarantine/error/disabled/unsupported state. Manual cards name manual-v1 and explain that capture is input time. Historical URL label no longer implies a link to frozen website contents. Browser verifies quarantine changes only lastCheckedAt/status, preserving snapshot/fetched/unknown-source time;6 source status/worker tests passed,8 lookup/history browser regression cases passed. New provenance test originally raced catalog rendering; explicit loaded assertion added, rerun passed. Build also exposed widened types in the newly added history unit fixture; corrected with actual strict parser before current build/browser. No numeric automatic assessment claimed.
