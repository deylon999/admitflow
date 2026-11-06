# B20/T220: сохранность новой сессии при синхронизации вкладок

Исправлена F01 из [аудита](b19-frontend-audit.md). До исправления две новые
браузерные регрессии падали: после промежуточного401 исчезала безопасная
кнопка синхронизации и появлялось предложение создать сессию через DELETE.

Теперь resumeSession использует тот же guest lock, что создание/сброс.
Epoch фиксируется до ожидания и проверяется перед чтением/после ответа.
Устаревшая команда reset также отклоняется до DELETE; поздние результаты
изменившегося доступа не устанавливаются как текущая сессия.

Без Web Locks временный401 при уже изменённом доступе оставляет состояние
changed и read-only retry. Интерфейс предлагает повторить синхронизацию,
а не удалять текущую сессию. Обычный401 из active по-прежнему означает
истечение доступа. Fallback не заявляется полной сериализацией всех
одновременных намеренных reset; исходный destructive recovery устранён.

Проверки текущего кода:

- 15 targeted unit cases, включая queued/in-flight epoch, failed reset,
  отсутствие лишних POST/DELETE, query/mutation401 policies.
- Все126Vitest прошли, production build прошёл.
- `session-reset-races.spec.ts` и существующий `session-tabs.spec.ts`:
  **8passed/0skipped**, Chromium+Firefox,24.7s.
- В обоих браузерах проверены настоящий guest lock и режим без него.
  Во время прерванного reset нет destructive recovery; новая запись
  сохраняется после синхронизации. POST/session=2, DELETE/session=1
  до cleanup, включая начальную сессию и явно подтверждённый сброс.

Из frontend: `npm test`, `npm run build`;
`npx playwright test tests/e2e/session-reset-races.spec.ts tests/e2e/session-tabs.spec.ts --project=chromium --project=firefox --reporter=line`.
Env:E2E_API=1,E2E_SERVER=external,E2E_BASE_URL=http://127.0.0.1:5282.
Использован только отдельный synthetic SQLite API8032. Реальные данные,
сырьё источников, schema/key/volumes прежнего demo не менялись.

Следующая T221: исключить старую private копию из UI при успешном reset,
ошибке обновления и поздних запросах. Остальные ошибки3–10 не исправлялись.
