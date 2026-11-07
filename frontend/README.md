# Frontend AdmitFlow v3

Один React entry `src/main.tsx` → `App.tsx`, History API router, общий AppShell.
Исходные компоненты и CSS v3 сохранены. `src/catalog/` содержит только
DTO/API/state/композиции реального каталога. Остальные страницы используют
исходные demo-данные с явной маркировкой прогнозов.

Из этой папки:

```powershell
npm ci
npm run dev
```

Адрес localhost:5173. Backend по умолчанию localhost:8000; изменить через
API_PROXY_TARGET. Watch-build пересобирает исходники; страницу обновлять
вручную, HMR в этом launcher отсутствует.

```powershell
npm run typecheck
npm run lint
npm run build
npm test
```

`npm test` сам запускает настоящий FastAPI с миграциями в временной SQLite
и Vite production preview, затем закрывает свои серверы. Требуются Python
requirements-dev backend и Chromium. Полный read-only reference test:
`npm run test:visual`. Native PostgreSQL проверяется отдельно.

Скриншоты и вспомогательные proof-файлы по умолчанию попадают в ignored
`test-results/evidence`; для сохраняемого отчёта задать `QA_EVIDENCE_DIR`.
После visual run выполнить `node scripts/summarize-visual.mjs`;
`npm run verify:source` проверяет неизменность исходных UI-файлов с явными
исключениями подключения каталога, demo-подписей и удаления dead route map.
Для проверки каталога по ранее зафиксированным PNG есть `QA_BASELINE_REF`.

Статические HTML previews и самописный renderer удалены. Нет второго приложения,
отдельного Python screenshot stack или неиспользуемого React/Babel-плагина.
Все runtime страницы перечислены в [SCREEN_INVENTORY.md](SCREEN_INVENTORY.md).
Запуск backend/metadata import: [runbook](../docs/catalog-runbook.md).
Прежняя инструкция дизайн-кита сохранена в
[архиве](../docs/archive/frontend-readme-before-foundation.md).
