# B21/T228 — актуальное время штатной печати

Исправлена F09. До изменения browser beforeprint после10 минут оставлял
в DOM время открытия страницы; новая регрессия завершилась exit1.
TrackerPage теперь слушает beforeprint с очисткой обработчика при unmount.
flushSync обновляет дату до возврата события: браузер получает актуальный
DOM для печати. Кнопка приложения сохраняет прежнее обновление перед rAF.

Проверено2026-11-06 на synthetic API8033/compiled preview5283:

`npx playwright test tests/e2e/report-print-time.spec.ts tests/e2e/manual-quality.spec.ts --project=chromium --project=firefox --reporter=line`.
Env:CI=1,E2E_API=1,E2E_SERVER=external,E2E_BASE_URL=http://127.0.0.1:5283.
**7 passed /1 scoped skip**,11.9s,exit0. Новая проверка в обоих браузерах
синхронно читает DOM сразу после beforeprint, повторяет на11-й минуте и
проверяет кнопку на12-й. Проверены filtered PDF Chromium и длинные
карточки320px в двух темах. Единственный skip: page.pdf недоступен в
Firefox; проверка события там выполнена. OS print dialog не автоматизирован.
Build, Prettier и diff check:exit0. Backend/данные не менялись.
