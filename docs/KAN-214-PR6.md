# KAN-214 PR6 — финальная проверка и приёмка

S215, 2026-11-13. Основа: main `12c78e4bf10dbc69d6558d91da85a040c7798a28`,
owner merge [PR18](https://github.com/deylon999/admitflow/pull/18).
PR5 source `6ae95ad3a016f6e44e23dc36ca951d3abe4d3fc1`,
[Checks43474248315](https://github.com/deylon999/admitflow/actions/runs/43474248315)
проверены: четыре job success, backend976/0skip, frontend175. Это доказательство
предыдущего этапа, а не результат PR6. Отдельная ветка feat/kan-214-final-acceptance.

## План и acceptance до реализации

1. T300: текущие auth/session/guest lifecycle, тесты, инфраструктура и пробелы приёмки.
2. T301: матрица критических угроз с воспроизводимыми security-тестами; исправление
   выявленных проблем без ослабления CSRF, лимитов, password hashing или проверок.
3. T302: native PostgreSQL браузерный lifecycle и негативные сценарии в Chromium,
   Firefox и WebKit. Один приватный test mailbox/clock и disposable schema на запуск.
   Добавление проверок в существующий backend CI job с его PostgreSQL service;
   не менять инфраструктурную модель, обязательные старые проверки и dependencies.
4. T303: полный regression, миграции/сохранность гостевой истории, desktop/mobile
   визуальное сравнение без автоматического обновления утверждённых эталонов.
5. T304: итоговый воспроизводимый отчёт, проверенные SHA/CI и PR для review;
   реальные SMTP/HTTPS и owner acceptance остаются отдельными условиями.

## Аудит T300

Проверены текущие account API/models/security/action/mail/limits, независимый
BrowserSession, existing security tests, account store/API/DTO/fragment capture,
формы/guard, Playwright runtime/config/runner, CI, миграции и visual comparator.
PR5 уже проверил основные сценарии Chromium локально. В hosted frontend нет
PostgreSQL service; native browser suite opt-in и пока не входит в обязательный CI.
Браузерные тесты используют общий изменяемый clock и одинаковые адреса, поэтому
параллельные проекты в одном runtime не обеспечивают независимость. Для PR6 каждый
engine запускается последовательно в собственном runtime/schema/mailbox.

Production-критерии: AUTH_ENABLED=false по умолчанию; TLS SMTP integration есть,
но реальная доставка не подтверждена. HTTPS deployment и реальный proxy/egress
не предоставлены. Изолированные тесты не закрывают эти условия. PR6 не вправе
самостоятельно принять внешний gate, включить production auth или выполнить merge.
Профиль/глобальные protected routes/ML остаются вне KAN-214.

Infrastructure findings (без применения изменений): compose.prod backend подключён
только к internal network и не получает AUTH/SMTP env. Для реальной доставки нужен
согласованный deployment overlay: передача auth/mail env только backend, устойчивый
AUTH_RATE_KEY, разрешённый исходящий SMTP/TLS трафик, HTTPS/Origin/cookies smoke.
Nginx/Caddy security headers и production-cookie tests уже существуют; deployment
не считается проверенным по Settings/TestClient или localhost. Не добавляем
новый mail/queue service и не меняем production networks/secrets автоматически.

## T301 — security evidence

[Матрица32 критических контролей](KAN-214-SECURITY-MATRIX.md) и
[machine manifest](evidence/kan-214-controls.json) связывают угрозы с конкретными
pytest selectors. Проверка selectors по AST выполнена до публикации матрицы.
Новый native-PG test заполняет BrowserSession/Watch/Snapshot/LookupBudget/
OperationRecord/Subscription/Assessment/ChangeEvent, затем сравнивает строки после
регистрации, настоящего подтверждения email, login/logout и смены аккаунта. Account
cookies в другом браузере не дают владение исходными guest subscriptions/history.
Отдельно проверяется неизменность populated graph при0011→0012 и no-store/отсутствие
password/action/access/refresh/context secrets в response и HTTP logs.

`check_auth_acceptance.py` требует фактически выполненные backend JUnit cases без
failure/error/skip и успешные JSON результаты каждого из трёх browsers. Он не
принимает внешние release gates и всегда сохраняет productionReady=false.
Проверки самого валидатора отклоняют missing/failed/skipped/truncated evidence;
успешный synthetic report не может автоматически принять SMTP gate.

Проверено: новые native-PG3 passed; выбранная security-регрессия112 passed
(42.34s,1 существующий Starlette/httpx deprecation warning); validator unit3 passed.
Начальная ошибка нового теста GET subscription была исправлена на существующий
`/subscriptions/{id}/history` (вместо несуществующего GET detail); контракт API не менялся.

## T302 — native PostgreSQL browser acceptance (в работе)

Набор расширен до5 реальных сценариев на engine: lifecycle/parallel refresh/logout/
recovery/revocation; переключение A/B и resetA при текущемB; unverified login,
resend, purpose separation и истёкшая verification; CSRF/Origin/чужой synchronizer,
HttpOnly/path/storage и refresh replay; uniform recovery, expired reset и503 от
настоящего изолированного test-mail port. Fragment навигация обёрнута так, чтобы
ошибка теста не выводила raw ссылку. Trace/video/screenshots этого набора выключены.

`npm run test:auth` последовательно создаёт независимые runtime/schema/mailbox/clock
для Chromium/Firefox/WebKit, сохраняет отдельные JSON/JUnit и не использует старый
успешный JSON при ошибке старта. Default175 frontend tests не заменяются этим набором.
CI дополнен только test steps в существующем backend job: его существующий PG17,
Node24/Playwright engines, пять сценариев на каждый engine и проверка исполненной
матрицы. Сервисы, networks, production compose и dependencies не изменены.

Локально Chromium5 passed (8.8s), Firefox5 passed (14.7s), lint/typecheck passed.
На Fedora44 WebKit не запускается без libicu74/libjpeg-turbo8; это не skip/успех.
Обязательный WebKit run подготовлен в Ubuntu24.04 CI с `install --with-deps`.
T302 остаётся in_progress до фактического результата всех трёх engines.

## T303 — regression, migrations и визуальная сверка

Локальный полный backend `--require-postgres`:979 passed,0 skipped,4 существующих
Alembic warnings,315.55s. Default frontend175 passed (23.7s). ETL55 passed и1 explicit
skip из-за отсутствующей внешней MICCEDU выгрузки; repository tools20 tests,1 local
optional PDF dependency skip (hosted устанавливает dependency). pip check clean;
server-lifecycle3 passed. Чистая отдельная PostgreSQL база миграций:0012/head,
`alembic check` без новых операций. Новых миграций/редактирования applied migrations нет.

Повторная сверка всех29 исходных и2 технических маршрутов, Live/Demo,390/1440:
123/124 пар byte-identical. /programs Live1440 отличается15 pixels в bbox
(301,391)-(304,399), max RGB delta1 на округлённой границе первой карточки.
Повторные снимки каждой стороны стабильны; исходные `frontend/src` целиком
идентичны reviewed main12c78e4: Git tree0b245e8e108d5c1a0b93e9a8290969bd6321c021
с обеих сторон, working tree clean. Это наблюдение растеризации, не изменение
CSS/разметки/контента. Raw failed comparison и обе картинки сохраняются для review;
порог не ослаблен, результат не переписан в124/124, исторические baselines не изменены.
Команда comparator честно возвращает exit1 при этом различии. Source equality и
ручная проверка пары дополняют screenshot evidence; отдельная pixel-perfect
проверка на целевой машине остаётся на review. Production визуальный gate не принят.

Новый `--acceptance` режим comparator сравнивает reviewed PR5 main, включая реальные
формы и технические экраны. Исходный PR5 режим и его baseline остаются доступными.
Фиксируется только request-time coverage.generatedAt одинаково для обеих сборок.
Дополнительные повторные capture — диагностика; исходный mismatch не маскируется.

В native browser harness исправлена гонка старого теста: исчезновение названия
кнопки при loading не доказывало получение guest cookie. Теперь ожидаются реальный
POST session204 и наличие cookie. Product/session lifecycle не менялся.

## Итоговый технический отчёт KAN-214 (code acceptance)

### 10.1 Архитектура

Переиспользованы FastAPI/SQLAlchemy/PostgreSQL, диагностический middleware,
Origin/X-Requested-With, shared/api.ts и KAN-212 epoch/abort/resource/router.
Добавлены шесть таблиц0012: account_users, account_sessions, account_refresh_tokens,
account_action_tokens, account_csrf_contexts, account_rate_buckets. UUID пользователя
стабилен и не зависит от email. Email ASCII, strip/lower,<=254, local<=64;
plus/dot aliases не объединяются. UNIQUE в PostgreSQL защищает от concurrent insert.
FK/constraints и единый user→session→refresh→context lock order сохраняют целостность.
Личных данных минимум: email, password hash, security timestamps/status; budgets
хранят HMAC subjects, а не открытые email/IP. Guest BrowserSession независим.

### 10.2 Модель безопасности

Argon2id RFC9106 low-memory:64MiB,t3,p4,salt16/hash32, уникальный salt, dummy verify
для отсутствующего аккаунта и rehash при изменении параметров. Новый пароль15..128
Unicode codepoints/512 UTF8 bytes, без silent trim/truncation/composition rules;
небольшой offline common-password list, не полная база компрометаций. Параметры
не ослаблялись для тестов. Секреты входа — в HttpOnly host-only Lax cookies:
access15мин /api/v1, refresh idle7д /api/v1/auth, absolute30д. Secure обязателен
production. Сервер хранит purpose-separated SHA256 проверку случайного256-bit
credential (это не password hashing). CSRF synchronizer proof хранится отдельно
и привязан к HttpOnly context и конкретной сессии; сам proof доступен same-origin
клиенту только в памяти. Origin/custom header/SameSite дополняют его.

Refresh атомарно меняет access/refresh; старый spent refresh с корректным bound
proof отзывает семейство. Ошибка CSRF не позволяет чужому клиенту принудительно
отозвать семейство. Logout коммитит отзыв до Set-Cookie deletion и поддерживает
безопасный повтор через короткий CSRF tombstone. Password reset под user lock
меняет hash и отзывает все target sessions/actions; текущий другой аккаунт/guest
не затрагиваются. Absolute expiry не продлевается; idle продлевается при refresh,
не от произвольного чтения. Очистка удаляет истёкшие records; spent hashes сохраняются
до absolute deadline. Database-backed budgets переживают рестарт/несколько workers.

Frontend: server-proof после login/reload/refresh, единственный transport, независимые
guest/account epochs, проверка после headers/body/decoder и отмена private pending.
Web Lock и single-flight исключают конкурентный refresh между вкладками; перед
rotation повторный GET session под lock. Нет blind retry refresh POST. Без Web Locks
автоматический refresh недоступен, нужен re-login; network503 не anonymous.
Broadcast/storage — только случайные phase markers, не user IDs или credentials.
Ни password, ни access/refresh/CSRF/action tokens не хранятся в local/sessionStorage.

### 10.3 API и доступ

Все account endpoints отдельно от `/api/v1/session`, prefix `/api/v1/auth/`.
DTO/статусы/CSRF и browser policy полностью перечислены в
[PR5 contracts](KAN-214-PR5.md#final-implementation-and-contracts-t299), backend
лимиты — [PR2](KAN-214-PR2.md), [PR3](KAN-214-PR3.md), [PR4](KAN-214-PR4.md).

- GET csrf200: same-origin/custom header, bounded rate, proof в памяти.
- POST register202 {email,password}: CSRF; generic accepted, no auto-login.
- POST login200 {email,password}: CSRF; verified active only; новый контекст.
- GET session200: только current-account id/email/verified/expiry.401 terminal
  либо access_expired для контролируемого refresh;503 — временная недоступность.
- POST refresh200 {} и logout204 {}: bound CSRF, server locks/revocation.
- POST verification/request и recovery/request202 {email}: generic message,
  общие mail budgets, провайдер unavailable→503; не обещают фактическую доставку.
- POST verification/confirm204 {token}, recovery/confirm204 {token,password}:
  CSRF, purpose-bound single-use24ч/30мин, invalid/expired/reused→400 invalid_token.

422 invalid_input,403 csrf_invalid/Origin,429 rate_limited+Retry-After,503
unavailable; backend validation не раскрывает входные secrets. В JSON нет account
credentials/hash. GET/current-user не принимает произвольный user ID; бизнес
account data endpoints в KAN-214 не добавлены. Новые mutable endpoints следующих
задач обязаны определить backend ownership, CSRF и transactional/idempotency contract;
одна frontend-классификация account/* никогда не является авторизацией ресурса.

### 10.4 Гостевые сессии

Cookie abiturient_session /api, owner_hash и существующие guest endpoints сохранены.
Нет повышения guest credential, автоматического объединения данных или удаления
истории при account register/login/logout/reset. Заполненная native-PG цепочка
подписок, assessments, events, watches/snapshots/operation records сохраняется
после auth transitions и migration0011→0012. Копия account credentials без исходной
guest cookie не получает эти ресурсы. Guest delete отдельно не удаляет аккаунт.
Полный перенос guest data требует будущего явного ownership/consent контракта.

### 10.5 Email

Stdlib SMTP port отделён от auth: starttls/ssl с certificate verification,
фиксированным HTTPS PUBLIC_ORIGIN, env configuration, bounded socket timeout,
двумя send slots/worker и одной попыткой. Паролей/credentials в письмах нет.
Действительные action links — только /auth/verify#token=… и /auth/reset#token=…;
fragment сразу удаляется из URL и хранится только в памяти страницы. Подтверждение
явной кнопкой; callback/query credentials не принимаются. Resend инвалидирует старую
ссылку; provider failure явно503. Тесты используют RecordingMailer, private FileMailer
и изолированный SMTP protocol client. **Ни один из них не доказывает реальную доставку.**
Реальный провайдер/ящик не предоставлен; [процедура внешнего smoke](KAN-214-DELIVERY-SMOKE.md)
подготовлена, но не выполнена. AUTH_ENABLED=false; внешние условия не приняты.

### 10.6 Тестирование

Полные команды ниже и machine evidence фиксируют фактические результаты. Backend979,
frontend175, security selection112 и validator3 прошли локально; PostgreSQL migration
head0012 без drift; server lifecycle3. Chromium/Firefox по5 native-PG браузерных
сценариев. Обязательные hosted WebKit/все engine результаты и finalSHA находятся в
PR19 description, без evidence-only коммита поверх проверенного source.
Матрица32 контролей требует actual JUnit/browser proof. CI сохраняет исходные
четыре jobs и добавляет native-PG browser steps в backend job, используя существующий
PostgreSQL service. Нет новых infrastructure services или отключённых проверок.
Непроверенные внешние условия всегда перечисляются отдельно от automated success.

### 10.7 Визуальная регрессия

Ни один frontend/src файл и CSS не изменён PR6 относительно merged PR5. Все29
исходных маршрутов плюс2 технических доступны.124 Live/Demo desktop/mobile pairs,
123 exact,15px/max-channel-delta1 border variance документированы выше и оставлены
для review. No baseline rewrite/threshold relaxation. PR5 также содержит108/108
сверку сохранённых экранов с pre-auth reviewed source. Дизайн v3 не перерабатывался.

### 10.8 Миграции и данные

Единственная auth migration0012 additive, применённые migration files не редактировались.
Чистая disposable база upgrade/head/check прошла. Дополнительный тест0011→0012
с populated guest subscription/change graph сравнивает все существовавшие строки.
Все native tests — в admitflow_test* БД со случайными schema; рабочие БД не использованы.
Тестовый контейнер/volume не являются production. Volumes не удаляются; по окончании
временные schema/mailbox/процессы очищаются, owned test container останавливается.

### 10.9 GitHub и review

Все предыдущие PR owner-merged. GitHub API повторно подтвердил final-source Checks
success для каждого; отдельных GitHub review submissions не найдено (не утверждаем,
что были независимые approvals). Merge владельца — факт интеграции code этапа,
не принятие production delivery gate.

| PR | Final source SHA | Verified Checks run |
|---|---|---|
| [14](https://github.com/deylon999/admitflow/pull/14) |754e9ddfb933339f6e8e89fc2124558c022e87bb |[43410643949](https://github.com/deylon999/admitflow/actions/runs/43410643949) |
| [15](https://github.com/deylon999/admitflow/pull/15) |efbd0e657374fa50dd57fa8c87a13e7fc8ffd3ad |[43414762564](https://github.com/deylon999/admitflow/actions/runs/43414762564) |
| [16](https://github.com/deylon999/admitflow/pull/16) |873f8847df2655975f217e8f584dde527ccf8af6 |[43452948773](https://github.com/deylon999/admitflow/actions/runs/43452948773) |
| [17](https://github.com/deylon999/admitflow/pull/17) |0451f7af8c53b5fbd455ab7c2f77d76accaf3652 |[43464449737](https://github.com/deylon999/admitflow/actions/runs/43464449737) |
| [18](https://github.com/deylon999/admitflow/pull/18) |6ae95ad3a016f6e44e23dc36ca951d3abe4d3fc1 |[43474248315](https://github.com/deylon999/admitflow/actions/runs/43474248315) |

[PR19](https://github.com/deylon999/admitflow/pull/19): final source/run/job outcomes
поддерживаются в описании PR. Review/merge владельца пока не получены; agent не merges.

### 10.10 Ограничения

Реальная SMTP acceptance/inbox delivery, production HTTPS/domain/cookies/Origin smoke,
trusted-proxy client-IP policy и SMTP egress не проверены. Текущий proxy peer aggregate
может объединять бюджеты разных пользователей; нельзя выдавать это за готовую
per-IP production защиту. Deployment overlay и его review — внешнее условие; production
networks/secrets/flags не менялись. Общий penetration test/формальная сертификация
не выполнялись. Pixel-perfect variance на целевой машине требует review, а не
автоматического принятия нового эталона. Full KAN-214 DoD не объявляется выполненной.

### 10.11 Передача KAN-215/216/225/226

Готовы stable account ID, whitelist current-session DTO, HttpOnly opaque session
lifecycle, CSRF/refresh/logout/reset contracts и useAccount/epoch boundaries.
KAN-215 добавляет профиль, KAN-216 — общую protected-route/redirect policy,
KAN-225/226 — account-owned business data с backend authorization. Guest /app не
должен блокироваться глобальным account guard. Автоматический guest merge и новый
business scope не реализованы. Gate внешней доставки нельзя закрывать кодом этих задач.

Hosted milestone T302: source79a40fc914a712e96e9bbb99507dab3f96909b90,
[run43478500035](https://github.com/deylon999/admitflow/actions/runs/43478500035),
все4 jobs success. Backend979/0skip (519.58s); Chromium5 (12.3s), Firefox5 (21.2s),
WebKit5 (22.5s), evidence validator32 controls; repository tools20/0skip.
WebKit действительно выполнен в Ubuntu, не помечен skip. Финальный source дополнительно
помечает engine в project/metadata и проверяет фактический browser fixture; validator
отклоняет отчёт от другого engine. Local Chromium5 (9.2s), Firefox5 (13.3s) после
добавления metadata и исправления ожидания guest cookie повторно прошли. Final head
повторно проверяется CI; ссылка/результаты поддерживаются в PR19 description.
