# B18/T211: фокус подтверждения после React commit

Удалённый mobile-Chromium упал на ожидании фокуса heading подтверждения.
Локальное воспроизведение исходного compiled build на отдельном synthetic
PostgreSQL/API8029/preview5280:8cases,5passed/3failed,37.4s. Firefox повторил
две ошибки Tab из CI и потерю фокуса confirmation dark. Реальные абитуриенты
и постоянный demo в проверке не использовались.

`SourceLookup` больше не планирует focus через requestAnimationFrame в
mutation.onSuccess: React может ещё не опубликовать новый DOM и ref отсутствует.
Фокус назначается `useLayoutEffect` при committed preview. Подтверждение,
ownership, повтор сохранения и приватность кода сохраняют прежние assertions.
При not-found заголовок также получает фокус после появления.

Команды из frontend: `npm test`, `npm run build` и
`npx playwright test tests/e2e/source-failure.spec.ts tests/e2e/source-history.spec.ts tests/e2e/source-lookup.spec.ts tests/e2e/source-provenance.spec.ts tests/e2e/source-session.spec.ts --project=mobile-chromium --project=firefox --project=chromium --reporter=line`.
Env:E2E_SERVER=external,E2E_API=1,E2E_SOURCE_FIXTURE=1,E2E_BASE_URL=http://127.0.0.1:5280;
API_TARGET=http://127.0.0.1:8029. Fixture сервер:
`E2E_API_PORT=8029 backend/.venv/Scripts/python.exe scripts/serve_source_e2e.py`.
Скрипт создаёт только собственный disposable PG и синтетические данные.

116Vitest/build exit0. Полные21source cases пройдены в каждом из трёх
режимов:63passed/0skipped/0failed. Финальный удалённый результат относится
к T214; Firefox Tab/медленная установка ещё остаются отдельной T212.
