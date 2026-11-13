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
