# S183 — B21 frontend fixes

T229 done; current None. Both section borders use existing --line; actual computed1px solid and correct light/dark colors verified. Build/format/diff passed; all8 fixes complete, final integrated verification follows.

Evidence: docs/evidence/b21-section-borders.md. Synthetic API8033/preview5283. Original database/key/volumes unchanged; national coverage tasks remain open.

# S183 — B21 frontend fixes

T228 done; current T229. Browser beforeprint commits current report timestamp synchronously; repeated events, own button and filtered Chromium PDF checked. Build/format;7passed/1FirefoxPDFskip.

Evidence: docs/evidence/b21-report-print-time.md. Synthetic API8033/preview5283. Original database/key/volumes unchanged; national coverage tasks remain open.

# S183 — B21 frontend fixes

T227 done; current T228. Cancel resets failed import UI; retry key/body survive until explicit cancel, pending controls remain locked, success cleanup verified. Build/format;10Chromium+Firefox passed.

Evidence: docs/evidence/b21-import-cancel.md. Synthetic API8033/preview5283. Original database/key/volumes unchanged; national coverage tasks remain open.

# S183 — B21 frontend fixes

T226 done; current T227. Capacity changes displayed independently of candidate presence; unknown values and absence warning preserved. Build/format;10Chromium+Firefox passed. First five complete.

Evidence: docs/evidence/b21-archive-capacity.md. Synthetic API8033/preview5283. Original database/key/volumes unchanged; national coverage tasks remain open.

# S183 — B21 frontend fixes

T225 done; current T226. Global branch facets accept101 through20000 while preserving validation/resource bounds.136Vitest/build/format;2Chromium+Firefox pagination/filter cases passed.

Evidence: docs/evidence/b21-catalog-scale.md. Synthetic API8033/preview5283. Original database/key/volumes unchanged; national coverage tasks remain open.

# S183 — B21 frontend fixes

T224 done; current T225. Catalog outages no longer imply empty coverage; failed append retains cards and retry works. Build/format;4Chromium+Firefox passed.

Evidence: docs/evidence/b21-catalog-error.md. Synthetic API8033/preview5283. Original database/key/volumes unchanged; national coverage tasks remain open.

# S183 — B21 frontend fixes

T223 done; current T224. Refresh updates mutable archive queries, closed histories and changes; waits for new snapshot reads and retains dated facts on failure. Build/format;8Chromium+Firefox passed.

Evidence: docs/evidence/b21-archive-refresh.md. Synthetic API8033/preview5283. Original database/key/volumes unchanged; national coverage tasks remain open.

# S183 — B21 frontend fixes

T222 done; current T223. Reverted drafts cleared; pending retry intent and unchanged recovery TTL preserved. 126Vitest/build/format;22Chromium and7Firefox passed.

Evidence: docs/evidence/b21-draft-revert.md. Synthetic API8033/preview5283. Original database/key/volumes unchanged; national coverage tasks remain open.

# S182 — B20: ошибки1–2 исправлены

T220/T221 завершены2/2 по текущему запросу. Синхронизация ждёт guest lock,
epoch guards отклоняют устаревшее чтение и queued reset до DELETE. Без
Web Locks временный401 при changed оставляет безопасный read-only retry;
обычный active401 по-прежнему означает истечение доступа.

При reset private UI/queries временно выключены. После success/error старые
query entries удаляются после дополнительной отмены; 503 и late response
не возвращают прежние карточки/history/print/counters. Failed DELETE не
удаляет серверную запись: она появляется только после нового authorized GET.
При DELETE204/POST503 прежняя private копия не появляется даже в ожидании.

126Vitest/format/build,85compiledChromium passed/36scopedskips,
8targeted race+8cache cases Chromium/Firefox,12final critical cases с
CI=1/two workers passed. Прогоны не суммируются в уникальное покрытие.
Evidence docs/evidence/b20-session-synchronization.md,b20-session-cache.md,
b20-final-verification.json. Backend/schema/source profiles не менялись.

Временные syntheticAPI8032/preview5282 закрыты; ignoredSQLite/probes сохранены.
Исходный Docker daemon/key/volumes не менялись. Старый screenshot восстановлен.
Другие8дефектовT222–T229 остаютсяtodo; пользователь разрешил только1–2.
currentTask=null,nextTask=T222 как кандидат после следующего указания.
T056/T057 национального охвата остаются открытыми, покрытие не изменилось.

Ниже — checkpoints предыдущих подходов с их исходными ограничениями.

# S181 — B19: читаемый frontend и глубокий аудит

T215–T219 завершены5/5. Только форматирование: formatter/config,17lib files,
23components/3pages/main/2CSS,56test files. Prettier3.9.10 с JSX attributes
по строкам и LF. npm run format/check; format check входит в основной CI job.
100 TS/TSX semantic ASTs совпадают5440410 после нормализации форматирования/
JSX text. CSS byte identical; JS bundles имеют другое представление JSX.
116Vitest/build,79compiled Chromium passed/36scopedskips. Длинные строки>200:
218→2, оставшиеся — text literals. Форматирование не устранило найденные баги.

Отчёт: docs/evidence/b19-frontend-audit.md,10подтверждённых дефектов.
Самые существенные: ранняя синхронизация второй вкладки приводит к удалению
новой сессии/записи; старые private карточки остаются после успешного reset
при503refetch. Далее stale draft, stale archive history, false empty catalog,
101branch facets, скрытые seats changes, cancel-import error, print time,
undefined CSS variable. Есть точные места/шаги/ограничения и3synthetic screenshots.
T220–T229 остаются todo. Пользователь сначала просил только найти, затем
разрешил только читаемое форматирование; функционально ошибки не исправлять
до нового указания. T220 — следующий кандидат, currentTask=null.

После daemon recovery исходный Docker был выключен. Его project/key/volumes
не менялись; synthetic API8031/preview5281 использовали только отдельный
ignored SQLite. Сейчас временные процессы закрыты; probes в .pytest_cache.
Старый screenshot каталога восстановлен. Финальная Git сверка: origin/main уже8e30b43(первые4коммита), итоговый audit commit локально. Явный push в командах этого прохода не выполнялся; инициатор внешнего push не установлен.
Оригинальный national coverage:1257catalog/15archivegroups/5universities/
1884rows/2conditional/0fresh/nationalTotal=null; T056/T057 остаются открытыми.

Ниже — прежние checkpoints.

# S181 — B19 audit and readable frontend

T218done;currentT219. All56TypeScript test files formatted; format check/116Vitest/build passed.79compiledChromium passed/36scopedskips/0fail.100source+test normalized semantic ASTs match5440410; assertions unchanged, CSS identical. CI checks format after npmci. Evidence: docs/evidence/b19-tests-format.md. Same demo8091/key/volumes; national coverage unchanged.

# S181 — B19 audit and readable frontend

T217done;currentT218. 23components/3pages/main and2CSS files expanded. Targeted formatter check/build passed. Normalized semantic AST of44TS/TSX source files matches5440410; no logic fixes. CSS asset remains identical; JSX layout changes bundle representation. Evidence: docs/evidence/b19-jsx-format.md. Same demo8091/key/volumes; national coverage unchanged.

# S181 — B19 audit and readable frontend

T216done;currentT217. All17library TypeScript files expanded into readable blocks; targeted Prettier check passed. Frontend LF attributes keep formatting stable on Windows. No intentional behavior changes; complete unit/build/equivalence verification T218. Evidence: docs/evidence/b19-library-format.md. Same demo8091/key/volumes; national coverage unchanged.

# S181 — B19 audit and readable frontend

T215done;currentT216. Prettier3.9.10 pinned with LF/100columns/JSX attributes per line; npm format/check commands configured and tooling files formatted. npm install/version/config checks passed; runtime dependencies unchanged. Evidence: docs/evidence/b19-format-tools.md. Same demo8091/key/volumes; national coverage unchanged.

# S180 — B18: CI исправлен, финальный checkpoint

T210–T214 завершены 5/5; 194 done/214 total. Hosted GitHub Actions
run 42114005067@ba42976: 6/6 success. Прошли 666 backend
тестов с обязательным native PostgreSQL, четыре browser projects (broad и
source), container build/recreation/backup. Проверены 10 JUnit отчётов в
шести артефактах, failures/errors=0. Доказательства:
docs/evidence/b18-remote-ci.json и docs/evidence/b18-integration.md.

Исходный run42095492218: mobile Chromium confirmation focus failure, две
Firefox Tab failures и две отмены по лимиту 15/25 минут из-за Azure mirror.
Preview получает фокус в layout effect после React commit; tabindex=-1 на
scroll-container убирает дополнительную остановку Tab перед кнопками вузов.
CI: Ubuntu24.04, официальный HTTPS Ubuntu archive, установка browser<=5мин;
общие timeouts и assertions сохранены. Broad/source outputs и JUnit
раздельны; backend XML загружается до установки браузера.

Локально прошли 116 Vitest/build, 63 source и 27 keyboard cases в трёх
browser projects, 2+2 cases с CI=1/two workers и шесть actual-nginx checks.
Frontend demo8091 обновлён; все пять JS/CSS равны текущему dist. Прежние
API/worker/db/key/volumes не пересоздавались; схема0011. Private backups
не менялись. Временные API8029/preview5280 остановлены, свой disposable PG
удалён родительским helper. Соседние radar и внешние БД не менялись;
исторический screenshot восстановлен.

Покрытие не выросло: 1257 catalog/15 archive groups/5 universities/1884 rows,
2 conditional/0 fresh/nationalTotal=null. Следующий T057: другой официальный
GET scope из admissions-inventory.json/format-families.json; полнота, конкурс,
места, все строки и независимая аттестация. T056/T057/live/staging/release
gates открыты. Свежая browser CI проверка теперь есть; пользовательская
приёмка и живая кампания остаются отдельными проверками.

Ниже — прежние checkpoints с их исходными датами и ограничениями.

# S180 — B18 CI repair

T213done;currentT214. Separate broad/source JUnit outputs preserved;2+2CI-mode browser cases passed with2workers.116Vitest,current build,63source+27keyboard checks passed;YAML/bash validation passed. Backend artifact uploaded before browser install; unique project/attempt artifacts always retained. Evidence: docs/evidence/b18-ci-reports.md. Same demo8091/key/volumes; national coverage unchanged.

# S180 — B18 CI repair

T212done;currentT213. Firefox scroll-container Tab stop corrected;27keyboard/catalog checks passed across3browser projects,0skip. Ubuntu24.04 pinned; Azure apt mirror replaced with official HTTPS archive; install bounded5min, overalltimeouts unchanged; bash/YAML checks pass. Hosted verification T214. Evidence: docs/evidence/b18-runner-and-firefox.md. Same demo8091/key/volumes; national coverage unchanged.

# S180 — B18 CI repair

T211done;currentT212. Confirmation focus moved to committed preview layout effect; old8cases reproduce3failures, fixed63source cases passed acrossChromium/Firefox/mobileChromium,0skip;116Vitest/build passed. Evidence: docs/evidence/b18-confirmation-focus.md. Same demo8091/key/volumes; national coverage unchanged.

# S180 — B18 CI repair

T210done;currentT211. Exact remote logs: mobile confirmation focus failure, Firefox2Tab-focus failures, Azure apt mirror22m35s download; checks15m andFirefox25m timeout. Backend666 andcontainers passed. Evidence: docs/evidence/b18-ci-diagnosis.md. Same demo8091/key/volumes; national coverage unchanged.

# S179 — B17: финальный checkpoint

T205–T209 завершены5/5;189done/209total. БГУ стал пятым вузом с импортом:
default GET08.03.01 «Организация строительного производства»,платно/очно,
архив2026,20мест/109строк. Независимый parser сверил все строки; новый общий
reviewed-filtered-table-v1 проверяет форму, count, программу и роли ячеек.
Lookup/HMAC берут только первые5цифр до `/`; персональные части отбрасываются,
согласия/приоритеты остаютсяunknown. Прежние14профилей/proofs не изменены.

Проверки:666native backend/0skip(428.96s),116Vitest/build,
84compiledChromium/31scopedskips(2.3m),1syntheticBGUlookup,
18actual-nginx checks. Исправлена потеря фокуса при пагинации справочника;
проверка задерживает реальный ответ offset50 и сохраняет открытые варианты.
Evidence: docs/evidence/b17-final-verification.json.

Стенд: http://127.0.0.1:8091/sources, тот же projectadmitflow-b15-demo,
schema0011,четыре сервиса/APIloopback8092. Все15stored audits прошли;
hash/count прежних14снимков/1775строк совпали до/после. Env/key и оба volumes
сохранены, private backup backend/var/b17-before-bgu.dump не публиковать.
Worker перепроверяет15архивов каждые86400секунд. Native B17schemas0,
контейнеры admitflow-b17-linux/pg и сеть удалены, preview5273/5274 и
syntheticAPI8028 остановлены. Соседние radar/внешние пользовательские БД не менялись.

Покрытие:1257catalog/15archivegroups/5universities/1884rows,
2conditionalbudget/0fresh/nationalTotal=null. T056/T057 открыты.
Следующий T057: другой официальный GET scope из admissions-inventory.json/
format-families.json, полный scope/план/строки и независимая сверка. БГУ
другие настройки формы и POST не поддержаны этой аттестацией. Исходный
proofhash не заменять хэшем новой загрузки; новый ответ проверять отдельно.
Для UI lookup использовать syntheticfixture, не реальные коды. Приватные
оригиналы содержат персональные сегменты; в tracked reports только агрегаты.
Полный лицензированный знаменатель,live2027,сутки,staging/release gates открыты.

Ниже — промежуточные и прежние checkpoints; актуально резюме выше.

# S179 — B17

T208 done; current T209. Actual bounded HTTPS->worker->native PG->independent/current/stored audit109rows/20seats passed.7native owner/API tests,116Vitest/build and1synthetic browser lookup/privacy/save passed. Evidence: docs/evidence/b17-worker-lookup.md. Same demo8091/key/volumes; T056/T057 open.

# S179 — B17

T207 done; current T208. All109original rows independently matched,20seats/14explicit enrolled; immutable exact BGU profile added,old14unchanged.46native targeted passed/0skip; Source not enabled by attestation. Evidence: docs/evidence/b17-attestation.md. Same demo8091/key/volumes; T056/T057 open.

# S179 — B17

T206 done; current T207. Generic filtered version,109synthetic rows, closed scope/count/roles/minimal-ID/enrollment checks;65native targeted passed,0skip. Legacy profiles/proofs unchanged; no runtime attestation yet. Evidence: docs/evidence/b17-filtered-family.md. Same demo8091/key/volumes; T056/T057 open.

# S179 — B17

T205 done; current T206. Fresh official exact contract/full-time construction scope:20seats/109rows/109unique minimal lookup IDs,14explicit enrolled; controls/count/order reviewed,0attestations yet. Evidence: docs/evidence/b17-bgu-scope.md. Same demo8091/key/volumes; T056/T057 open.

# S178 — B16: финальный checkpoint

T200–T204 завершены 5/5;184 done/204 total. Каталог вузов доступен целиком в
фильтре источников; SQL count/filter/cursor/limit групп сохраняют Unicode casefold;
миграция0011 добавила только производные поля. Batch1–100профилей атомарный,
с общим catalog mutex; конфликт/карантин/legacy version не обходятся.

Проверки:648native backend passed/0skip(412.15s),116Vitest/build,
83compiledChromium passed/30scopedskips(2.4m). После финальной CSS правки
выравнивания rebuilt image и12affectedactual-nginx passed(13.3s).
Исторический screenshotB14 восстановлен, новые desktop/mobileB16 просмотрены.
Evidence: docs/evidence/b16-final-verification.json.

Рабочий стенд прежний: http://127.0.0.1:8091/sources, Compose project
admitflow-b15-demo,4services, schema0011, APIloopback8092. Env/key и оба volumes
сохранены;14sourceaudits/1775rows прошли после миграции. Перед ней pg_dump
сохранён private/ignored backend/var/b16-before-0011.dump; копия восстановлена
в disposable DB, все прежние столбцы19таблиц сохранили hash/count. Ключ не
печатать/не регенерировать. Архивы проверяются каждые86400секунд, не fresh.
Native containers admitflow-b16-linux/pg/rehearsal и сеть удалены;preview5272
остановлен. Соседние radar и внешние пользовательские БД не менялись.

Покрытие прежнее:1257catalog/14archivegroups/4universities/1775rows,
2conditionalbudgetgroups/0fresh/nationalTotal=null. T056/T057 открыты.
Следующий конкретный T057: БГУ bachelor https://bgu.ru/abitur/bach/rating.aspx,
109видимых строк/5select/WebForms state. Проверить точное состояние формы,
конкурс/места/полноту/смысл полей и независимо сверить до аттестации.
Пять исследованных страниц docs/sources/stateful-format-research.json пока
не поддержаны; ИГУ dynamic/header-only не является полным пустым списком,
МСПИ содержит postgraduate columns и требует отдельной проверки уровня.
Полный лицензионный знаменатель,live2027,сутки,staging и release gates открыты.

Ниже — промежуточные и прежние checkpoints; актуально резюме выше.

# S178 — B16

T203 done; current T204. 5official pages/3institutions, verified linked BGU bachelor with109visible rows; stateful/dynamic/level gaps explicit.3synthetic tests and network-forbidden identical offline replay passed;0sources attested. Evidence: docs/evidence/b16-stateful-research.md. Demo8091/key/volumes retained; broad T056/T057 open.

# S178 — B16

T202 done; current T203. Atomic1-100 exact manifest IDs, shared catalog mutex, late-conflict/quarantine rollback and legacy preservation;41targeted+14expanded native checks passed,0skip. Evidence: docs/evidence/b16-profile-batch.md. Demo8091/key/volumes retained; broad T056/T057 open.

# S178 — B16

T201 done; current T202. SQL filters/count/cursor/limit preserve Unicode and literals;10001 synthetic groups hydrate<=8 for page7. Migration0011 backfill/reversal/offline PG passed;34 targeted+4 expanded native checks,0skipped. Evidence: docs/evidence/b16-sql-catalog.md. Demo8091/key/volumes retained; broad T056/T057 open.

# S178 — B16

T200 done; current T201. Full directory search/pagination, retained selection and next-page retry at320px;116Vitest/build and4compiledChromium passed. Evidence: docs/evidence/b16-university-filter.md. Demo8091/key/volumes retained; broad T056/T057 open.

# S177 — B15: масштабирование подключения

**Финал B15, T195–T199 5/5.** 179done/199total; T056/T057 открыты.
Проверки:627native backend passed/0skip(431.66s),116Vitest/build,79compiled
Chromium passed/32scopedskips(2.2m),5targetedactual-nginx passed(4.1s).
Первый nginx broad run72pass/7fail/32skip:6per-IP429,1ошибка селектора теста;
после исправления селектора fullpreview иtargetednginx прошли, лимиты не менялись.
См. docs/evidence/b15-final-verification.json.

Рабочий локальный стенд: **http://127.0.0.1:8091/sources**, Compose project
admitflow-b15-demo,4services.14реальных архивных групп/4вуза/1775строк,
2условных бюджетных сценария,0fresh/automaticeligibility,nationalTotal=null.
Ключ private/ignored backend/var/b15-demo.env сохранён; override рядом,
два собственных постоянных volumes (postgres_data/raw_data). API8092
опубликован только на127.0.0.1 для локальных проверок; PostgreSQL не опубликован.
Все14storedaudits/1775rows прошли после пересоздания API, ключ согласован.
Worker loop перепроверяет архивы раз в86400секунд; свежей кампании это не даёт.
Native test containers/network удалены, demo/его volumes сохранены.
B14preview5270/API8027 уже остановлены средой; temporarypreview5271 остановлен
после browser checks. Соседние radar-контейнеры/пользовательские БД не менять.

Следующий шаг T057: брать другие семейства из admissions-inventory/format-families,
получать официальные originals, независимо проверять точные scopes и расширять
manifest. Не считать no-table/robots/TLS-error поддержкой. Текущий каталог
SourcesPage берёт50вузов для фильтра, а backend group catalog пока загружает
все группы перед фильтром: это следующие ограничения массового подключения,
не объявлять их устранёнными. Полный лицензированный реестр T056 всё ещё
требует доступной официальной выгрузки; live2027/сутки/staging/release gates открыты.

Ниже — промежуточные checkpoints S177; актуально резюме выше.

T198 done: два новых вуза,11 групп/10 страниц/168 реальных строк архивного платного приёма; независимый stdlib audit и настоящий bounded HTTPS→worker→PG→offline audit прошли, disposable schema удалена. 68 targeted native passed, после усиления page-proof completeness ещё23passed. Старые3profiles/proofs не менялись. Текущая T199: native массовая очередь/domain leases, краткий process-local page cache для общих URL, метрики фактического покрытия и финальная регрессия. Не выдавать эти архивы за fresh или национальное покрытие. Docker Desktop перезапущен после остановки среды; собственные admitflow-b15-linux/pg вновь запущены, соседние radar не менялись. B14preview процессы проверить перед сообщением URL.

T196 завершена:14реальных child pages по verifiedparentlinks на3сайтах,1структурный межвузовский кандидат МИЭПП/УИФР. У НИБ ответы безтаблиц,неподключён;8целевыхtests/offline replay. ТекущаяT198 — аудит/decoder для конкретных секций этого шаблона. Нужно учитывать несколько форм/конкурсов на одномURL, не смешивать договор с согласием,0priority с известным положительным приоритетом; новые fixtures только synthetic. T197done/48nativepassed;T195done/1073URL. T199послеаттестации остаётсяtodo. Подробности docs/evidence/b15-format-families.md.

T195 теперь завершена:1073URL/633учреждения,624безвыбранной ссылки с исходной причиной; offline replay идентичен,6unitpassed. ТекущаяT196: реальные структуры и общие семейства. Ручное исследование официальных bachelor страниц нашло одинаковый `/abitur/.../competition/` шаблон на www.miepl.ru (4ссылки),uifr.ru (7),nibmoscow.ru (3); это пока кандидаты, не аттестация. Приватные parent bodies в backend/var/research/b15-family. www.mrsei.ru TLSerror, проверка сертификатов не отключалась. T197уже done(48nativepassed),T198/T199ещё todo.

T197 завершена первой из независимых задач: активный manifest/immutable shards вместо одного JSON, старые3profiles/proofs сохранены;1001synthetic profiles/11shards проверены, native targeted48passed/0skip. ТекущаяT195: bounded admissions crawl выполнен по1073URL/633учреждениям, завершается offline replay/evidence. ЗатемT196 реальные структуры, T198 новое семейство, T199 массовая очередь. T056/T057 открыты. Соседние проекты и пользовательские БД не менять; собственные test PG/runner/network admitflow-b15-* работают для проверок. B14 preview5270/API8027 пока сохранены.

# S176 — B14: национальный каталог

**Финальный checkpoint, 2026-11-05: T190–T194 завершены 5/5**, отдельный commit на задачу. 174 done/194 total; широкие T056/T057 открыты, национальный знаменатель неизвестен. Опорный каталог 1257 организаций/521 филиал/89 региональных страниц, 1166 сайтов и 91 неизвестный; API/UI с поиском и пагинацией. Инвентаризация всех записей: 1083 уникальных страниц, 641 запись с кандидатными ссылками. Третий проверенный scope общего parser — SGU4576 archive2026,453 строки/24 места, новая V2 для явно проверенных перестановок альтернатив экзаменов; прежние V1/профили/история сохранены. Настоящие HTTPS→worker→PG→offline audit прошли в disposable schema, пользовательская БД не менялась.

Финальные проверки: **571 backend passed/0 skipped с обязательным PG, 116 Vitest/build exit0, 77 compiled Chromium passed/32 scoped skips**. Windows native full не поддержан из-за resource; Linux full сначала выявил CRLF/медленный mount, fixture bytes восстановлены по Git blob, .gitattributes закрепил точность. Финальный Linux FS прогон с V2 — 325.04s/exit0. Новые synthetic fixture не копируют реальные кандидатные значения; старые privacy decisions не закрыты. Firefox/WebKit/staging/nginx в B14 не переаттестованы. Все исходные release gates сохраняются. Итог: docs/evidence/b14-final-verification.json.

Локальный **http://127.0.0.1:5270/tracker**, preview session39597/API_TARGET8027. API session40167/PID14164, отдельная backend/.pytest_cache/b14-demo.db, схема0010; тестовая API10244 остановлена. Preview HTML и entry JS точно совпали с dist; через proxy доступны 1257 записей, 50 на первой странице. Demo не регистрирует источники автоматически и не содержит старую пользовательскую БД/архивы из другого окружения. Raw originals/cache приватны в ignored backend/var. Собственные admitflow-b14-linux/runtime/test-pg и сеть admitflow-b14-test удалены; соседние radar-контейнеры не трогались. Docker Desktop оставлен работающим.

Следующее действие T057: проверять кандидатные страницы списков, выделять реальные повторяющиеся форматы и расширять профильный реестр (нынешний один JSON с лимитом100 не подходит для национального масштаба). T057 больше не ждёт полного T056: неизвестный национальный знаменатель не мешает проверять отдельные источники. T056 остаётся открытым: мониторинг исключает часть вузов, islod.obrnadzor.gov.ru/rlic timeout, дополнительная официальная выгрузка не получена. Никаких claims полного каталога/свежих национальных импортов. Ниже — история промежуточных checkpoints B14/B13.

T193: завершена инвентаризация всех 1257 записей/1083 уникальных страниц, 641 запись с кандидатными ссылками, остальные с явными отказами/неизвестностью; автоматических источников не прибавилось. Текущая T194 — новый проверенный scope общего table parser: архив СГУ4576, оригинал 453 строки/24 места получен приватно, ещё не аттестован. Native full regression повторяется в admitflow-b14-linux на Linux FS после восстановления exact fixture bytes и .gitattributes; прежний Windows bind mount run дал 563 passed/5 failed (hash/процессы). Собственные тестовые PG/сеть admitflow-b14-test; чужие radar-контейнеры не менять.

Первая пятёрка T190–T194 в работе. T190 завершён: официальный опорный перечень MICCEDU 2025 — 1257 организаций/521 филиал/89 региональных страниц, число сверено, offline replay идентичен. T191 завершён: проверяемый атомарный импорт read-only artifact, явные legacy aliases. T192 завершён: поиск/API/UI, все 1257 записей доступны постранично, регион и филиал видимы; 1166 URL сайтов, 91 неизвестный. Проверки: 21 backend, 116 Vitest/build, compiled-preview 12 Chromium passed/2 fixture-only skipped; мобильный screenshot просмотрен. Текущая T193: инвентаризация официальных сайтов и ссылок на приём. Полный национальный знаменатель не установлен; автоматизация подтверждена только на двух архивных группах. Подробности: docs/evidence/b14-national-catalog.md. Capture-процессы завершены; SQLite API 8027/PID10244 остаётся для текущих проверок, backend/.pytest_cache/b14-preview.db, не пользовательская БД.

# S175 — приоритет: охват всей России

2026-11-05. Пользователь повторно подтвердил необходимый национальный охват. Оценка 80% относилась к ограниченному MVP. Проверены две архивные группы, общероссийского знаменателя нет. T056/T057 перенесены из этапа после MVP в ближайший приоритет, без ожидания T055. Следующий шаг T056: выбрать датированный официальный реестр и определить состав каталога. План пяти результатов: [NATIONAL_COVERAGE.md](NATIONAL_COVERAGE.md). Реализация национального охвата ещё не начата; статусы задач не повышены. Условия публичного выпуска B13 сохраняются.

# B13 — код MVP закрыт, выпуск ждёт внешних условий

2026-11-05, S174. Ветка `mvp-readiness`. **Публичный MVP не выпущен.** Что мешает и кто решает: [RELEASE_GATES.md](RELEASE_GATES.md).

Сделано и проверено: T042 доменная регрессия, T041 наблюдаемость, T045 браузеры, T006 удалённый CI, T047 контейнеры, аудит безопасности с исправлениями. T044 в статусе review: цель достигнута на `dev-container-2cpu`, повтор на staging ждёт T048.

Проверки на коммите `345ac07`, CI 41928404413: 551 backend с обязательным PostgreSQL без пропусков, 115 Vitest, сборка, 5 браузерных профилей, настоящий nginx, бэкап с проверкой восстановления. Детали: [t045-browsers.md](evidence/t045-browsers.md), [t044-load.md](evidence/t044-load.md), [security-audit-2026-11-05.md](evidence/security-audit-2026-11-05.md), [regression.md](evidence/regression.md).

Схема 0010: `worker_heartbeats` и `source_checks.run_id`. Новые коды карантина: `capacity_growth`, `capacity_mismatch`. Новые лимиты: 64 КБ на запрос, кроме импорта; лимиты на IP в nginx. Образ nginx непривилегированный и слушает 8080.

Заблокированы с условием снятия: T046, T048, T049, T050, T051, T052. T053–T055 зависят от них, T056–T065 от выпуска. Критерии выпуска не снижены. Открытые решения: настоящие данные в fixtures и истории Git, срок гостевой сессии на время кампании, оператор данных и сроки хранения.

Ниже сохранена история B12 и B11; их цифры относятся к прежним этапам.

---

# B12 — рубеж около 70% выполнен

2026-11-04, S173. Поручение «не останавливаться до 70%» выполнено по шести критериям, заранее записанным в [MILESTONE_70.md](MILESTONE_70.md). Это экспертная оценка функциональной готовности MVP; процент карточек и охват вузов России её не заменяют. Полный публичный выпуск ещё не подтверждён.

Завершены две пятёрки, каждая задача закреплена отдельным коммитом:

| Пятёрка | Карточки | Проверенный результат |
| --- | --- | --- |
| 1–5 | T187, T188, T031, T034, T039 | Один parser с JSON-профилями двух вузов; второй независимый официальный архив; неизменяемые условные оценки, diff и объяснения в UI |
| 6–10 | T036, T040, T037, T038, T189 | Воспроизводимый replay; личная лента/прочтение/сравнение; управление источниками и журнал; честное покрытие; текущая сквозная приёмка |

Текущая сборка доступна на http://127.0.0.1:8090: Docker PostgreSQL/backend/nginx healthy, схема 0009, worker loop выключен. СГУ: 573 строки, общий бюджет, 16 мест. ГУАП: 581 строка, платный конкурс, 0 мест, согласие неизвестно — числовой сценарий явно не поддержан. Оба источника — архивы 2026 года. В справочнике 3 вуза, проверенных импортов 2, условных числовых групп 1, свежих автоматических групп 0. Последние реальные снимки сохранены; финальная проверка не загружала источники заново.

Текущие проверки: 502 backend (85 обязательных native PostgreSQL, 0 skipped), 115 frontend unit, 100 основных Chromium + 4 новых сценария/изменения + 2 actual nginx. Ещё два coverage-сценария повторены на двух источниках. Два replay-прогона по 6 шагов идентичны; изменения синтетические и явно помечены. Восстановление точно сохраняет 19 таблиц, сценарии, seen-state, владельцев и referenced raw. Оба настоящих архива офлайн сверены в работающем контейнере; сравнение с 1154 приватными кодами в tracked-файлах/сборке дало 0 совпадений.

Все временные fixture API/PostgreSQL и preview-процессы остановлены. Основной контур 8090 оставлен работающим; чужие Docker-проекты не изменялись. SOURCE_IDENTITY_KEY и оригиналы остаются приватными в backend/var с режимами 600/700, не печатать и не менять ключ без миграционного плана. Не повторять уже прошедшие проверки без нового изменения или основания.

Итог: [b12-milestone70.json](evidence/b12-milestone70.json), [b12-progress.md](evidence/b12-progress.md), [b12-current-runtime.json](evidence/b12-current-runtime.json), [b12-postgres-restore.json](evidence/b12-postgres-restore.json), [b12-private-artifacts.json](evidence/b12-private-artifacts.json). TASKS.json: 164 done из 189, 1 blocked, 24 todo; in_progress нет. Сгенерированные TASKS.md/CHECKLIST.md отражают только done.

Следующий конкретный шаг: T042 — сопоставить весь перечень доменных случаев QUALITY.md с подтверждёнными expected outcomes и явно зафиксировать оставшиеся неизвестные. Затем T041 наблюдаемость и T045 браузеры. Открыты HTTPS staging/production, remote CI (T006), суточное live-наблюдение, нагрузка/Firefox/WebKit/пользовательская приёмка и production source-use/retention/abuse-политики. Национальный охват не достигнут; исходные release gates не снижены.

Ниже сохранена история B11; её цифры и ограничения относятся к прежнему этапу.

---

# Контекст для продолжения

2026-11-04, S170. **B11: запрос «следующие 30 задач» выполнен — 30/30, шесть пятёрок и 30 отдельных коммитов.** Следующая работа требует нового поручения. TASKS.json — статусы, STATE.json — точка продолжения, LOG.md — история. Закрыто 154 из 186 карточек; это не процент готовности продукта к выпуску.

## Завершено в B11

| Пятёрка | Карточки | Результат |
| --- | --- | --- |
| 1–5 | T019, T007, T008, T013, T027 | Ручная приёмка, локальные шрифты с лицензиями, сверка макетов, настоящие исходники и обезличенные DOM, аттестация |
| 6–10 | T174, T029, T030, T032, T033 | Ограничение размера, адаптер архива SGU, quarantine/unknown, worker и доменные lease, атомарная публикация на PostgreSQL |
| 11–15 | T175, T022, T176, T177, T021 | Явная регистрация, каталог групп, поиск, идемпотентные подписки, подтверждение записи в UI |
| 16–20 | T178, T179, T180, T024, T023 | Удаление и tombstones, история и сравнение фактов, происхождение данных, сохранение ручной модели по версии |
| 21–25 | T035, T181, T182, T025, T026 | История сбоев и восстановление, экспорт, PG/raw restore, ошибки и повторы, доступность |
| 26–30 | T183, T184, T185, T186, T043 | Изоляция вкладок, контейнеры, измерение и пакетное чтение, offline audit, проверка безопасности |

Результаты, найденные ошибки и ограничения: docs/evidence/b11-progress.md. Итог: docs/evidence/b11-final-verification.json. Финальная сверка отдельно исправила время обработки новых фактов: assessedAt теперь берётся из часов обработки, а не копируется из fetchedAt. Старые записи не переписаны; повтор сохраняет прежнее assessedAt.

## Проверенное состояние

Один аттестованный источник: SGU4588, архив 2026 года, 09.03.04, 573 строки, 16 мест общего бюджета. Поиск ограничен источником, группой и сезоном; пользователь явно подтверждает запись. Карточки показывают факты и отдельные даты. Вероятность или официальный результат зачисления не рассчитываются. История source-confirmation-v1/source-facts-v1 неизменяема; отсутствие строки не означает отзыв. Общий лимит ручных и архивных направлений — 20, поиск — 30 запросов в минуту на гостя. Ручной manual-v1 закреплён по версии; новая модель не заменяет прошлую. archive-facts-v1 экспортирует текущие датированные факты; ручной JSON и полная DB/raw копия — отдельные форматы.

Финальные проверки: **454 backend passed, 0 skipped, включая 72 native PostgreSQL** с require-postgres; 102 Vitest; production build; 100 Chromium passed и 2 nginx-only skipped, причём эти два случая отдельно passed на настоящем Nginx. Проверены клавиатура, контраст, обе темы, длинные названия и 320px. Восстановлены 17 таблиц и два обезличенных снимка по 573 строки; последний отчёт b11-sgu-restore-current.json. В проверенных tracked/build артефактах не найдены реальные коды или стабильный ключ; b11-privacy-scan.json.

Профиль одного архива, 20 подписок и четырёх читателей: p95 после batching — 30.90 мс, до — 202.24 мс; 680 SQL вместо 11 120 на 80 чтений, все ответы 200. Это локальный ASGI/PostgreSQL опыт без TLS и параллельной публикации, а не production SLA.

## Runtime и приватные данные

Свой локальный Compose **admitflow-b11**, http://127.0.0.1:8090: PostgreSQL, API и Nginx healthy, схема 0007. Образы admitflow-b11-backend:latest и admitflow-b11-frontend:latest; актуальные digest — в b11-runtime-security.json. Настоящий архив и snapshot `8bf8bd49-df21-4265-9dc0-ff7e23c69b96` пережили recreate. fetchedAt: 2026-11-03T17:45:52.985785Z; sourceUpdatedAt неизвестно. Финальные проверки не делали внешнего HTTP fetch. Worker loop выключен; случайный запуск может начать новую загрузку, поскольку job уже due.

Override /tmp/admitflow-b11/images.yaml подключает API/worker к backend/var/b11-identity.env: приватный файл 600, ignored. Ключ не печатать, не коммитить и не менять без отдельной миграции идентичностей. .dockerignore исключает backend/var. Настоящий HTML: backend/var/research/sgu4588.original.html; коды не должны попадать в логи, скриншоты или traces. Браузерные тесты используют только FIXTURE-коды.

Из backend `python -m app.sources.audit sgu-2026-4588` проверяет raw, строки, hash и соответствие ключа без HTTP и изменения enabled. Аудит настоящего архива успешен: b11-source-integrity.json. Нужны соответствующие DATABASE_URL, RAW_STORE_PATH и приватный SOURCE_IDENTITY_KEY.

Disposable PostgreSQL, временный четырёхсервисный стенд и fixture API 8013 остановлены/очищены. Тестовый preview 4192 завершён runner. Оставлен постоянный локальный B11. Соседние Docker-проекты не трогать, свои постоянные volumes не удалять. /tmp может исчезнуть; команды и отчёты сохранены в scripts/ и docs/evidence/.

## Следующий шаг и ограничения

**T031: второй независимый источник.** У STU1348 настоящий HTML содержит только заголовки; формат пока неподдержан и не считается подтверждённым пустым конкурсом. При новом поручении выбрать доступный официальный архив, получить оригинал, описать источник и отдельно сверить минимум 50 строк и границу бюджета. Совпадение названий колонок не доказывает совместимость. Держать одну задачу in_progress и выполнять работу пятёрками по AGENTS.md.

Remote CI и push не подтверждены, T006 blocked. Остаются второй адаптер, 24-часовое наблюдение, HTTPS staging, Firefox/WebKit и пользовательская приёмка. T034, T036, T044, T048, T049 и релизные gates не закрывать частичными локальными опытами. Условия источников, основания обработки, оператор и регион, production-ротация referenced raw/backup/journal, удаление из копий и защита от массового создания гостей блокируют публичный запуск. Все B11-коммиты локальные; публикация не выполнена.
