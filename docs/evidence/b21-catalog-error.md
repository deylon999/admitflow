# B21/T224 — ошибка каталога и подтверждённая пустота

Исправлена F05. На B20 dist управляемый HTTP503 одновременно показывал
ошибку и «Подходящих подключённых групп пока нет». Теперь пустое состояние
появляется только при успешном ответе с пустым результатом.

При отказе следующей страницы ранее загруженные карточки сохраняются,
показан отказ загрузки, повтор добавляет страницу и убирает ошибку.

Проверено2026-11-06 на synthetic API8033/compiled preview5283:
`npx playwright test tests/e2e/source-catalog.spec.ts --grep "catalog errors|failed next" --project=chromium --project=firefox --reporter=line`.
Env:CI=1,E2E_SERVER=external,E2E_BASE_URL=http://127.0.0.1:5283.
Два сценария в двух браузерах: **4 passed**, без skips,exit0.
`npm run build`, scoped Prettier check и `git diff --check`:exit0.
Backend и данные источников не менялись; увеличение охвата этим не заявлено.
