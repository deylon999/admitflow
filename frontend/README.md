# Frontend AdmitFlow v3

Один React entry `src/main.tsx` → `App.tsx`, History API router, общий AppShell.
Исходные компоненты и CSS v3 сохранены. `src/catalog/` содержит только
DTO/API/state/композиции реального каталога. Подписки, события, списки и покрытие
используют существующие API. Будущие функции показывают Unsupported; исходные
demo-экраны доступны только после явного включения демонстрации.

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
requirements-dev backend и Chromium. Исторический comparator с исходным sibling
v3: `npm run test:visual` (ожидания периода до live-интеграций). Для текущего
frontend приёмка KAN-212 использует свежую Git-копию main без перезаписи baseline:

```powershell
node scripts/compare-main.mjs 07526c3
```

Все 29 экранов проверяются на 390/1440, default/demo; ответы локального API
читаются один раз для обеих картинок, поэтому это visual replay. PNG/metrics
сохраняются в ignored test-results/compare-main-*. Для проверки настоящего API
нужен работающий стек `python scripts/local_smoke.py` из корня, затем:

```powershell
$env:QA_API_TARGET='http://127.0.0.1:8080'
npm test
Remove-Item Env:QA_API_TARGET
node scripts/verify-postgres.mjs
```

QA_API_TARGET разрешает только локальный HTTP origin и не запускает SQLite.
verify-postgres создаёт отдельную PostgreSQL-базу и временный API-контейнер,
публикует только в ней явно тестовый архивный fixture, проходит guest → lookup →
confirm → список/summary. Удаляет только свою базу и контейнер, пользовательские
источники/volumes не меняет; требует свободные 5301/5303. Это проверка реального
backend с архивным fixture, не новая загрузка официального списка.

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
