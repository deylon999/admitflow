# T019 — приёмка ручного сохранения,2026-11-03

Acceptance широкого ручного пути сопоставлена с уже проверенными шагами; автоматические источники не входят в T019.

| Требование | Текущее доказательство |
| --- | --- |
| Create/update/history/delete, empty и input validation | frontend/tests/e2e/tracker-api.spec.ts,tracker-form.spec.ts; B10 full72 Chromium |
| Pending без повторного submit/потери полей, серверный отказ | pending-form.spec.ts,tracker-form.spec.ts; B10 native PG writes |
| Потерянный ответ/reload/retry | draft-recovery.spec.ts,tracker-api.spec.ts; B10 native idempotency/expected snapshot |
| Browser reload и отдельный новый API/Compose process сохраняют историю/owner | B10 b10-compose-restart.json exactHistory/ownership/retryAndTombstone; browser recovery suite |
| Ручной источник/история/модель отличимы от automatic | manual-quality.spec.ts,coverage.spec.ts; ManualReport/DirectionCard/API sourceKind=manual |
| XSS/невалидный JSON/Unicode boundaries | tracker-tools.spec.ts/import*.spec.ts; backend contract/import tests |

Финальные B10 backend332/0skip и browser72 относятся к исходному2c866bd. В B11 проверено чистое состояние Git и новый actual PostgreSQL/nginx стенд на8090; targeted run ниже. Старые результаты не объявляются новой проверкой ещё не изменённого кода. Native PG данные/volumes других проектов не затрагиваются.

B11 targeted check: `E2E_API=1 E2E_SERVER=external E2E_BASE_URL=http://127.0.0.1:8090 npm run test:e2e -- tests/e2e/tracker-api.spec.ts tests/e2e/tracker-form.spec.ts tests/e2e/pending-form.spec.ts --reporter=line` →10 passed,exit0,23.4s. Native PG/restart proof preserved from B10; no implementation changes precede this audit. T019 acceptance and DoD satisfied.
