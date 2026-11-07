# T230 — миграция frontend на FSD

Update after completion: user authorized local commits. Source commit `de1821b`; no push. Earlier no-commit statements below describe the original implementation stage.

Исходное дерево чистое, HEAD `3f8eee8`; пользовательские незакоммиченные
изменения отсутствовали. Коммиты/push запрещены текущим запросом.

## Аудит

Прочитаны конфигурации package/TypeScript/Vite/Vitest/Playwright/Prettier,
три страницы, компоненты, все lib-модули и сценарии связанных тестов.
ESLint в исходном проекте отсутствует. Сетевой монолит смешивает HTTP,
гостевой singleton и предметные операции; contracts смешивает четыре
разных предметных области. Tracker содержит вложенную карточку и смешивает
редактор/сессии/историю/импорт/печать с большой JSX-композицией. Calculator
экспортирует поля, нужные редактору, создавая неправильное UI-сцепление.

План и границы: [ARCHITECTURE.md](../ARCHITECTURE.md). Один активный T230
с семью этапами; промежуточные этапы не отмечаются как завершённая задача.

Baseline: `npm test` —136/136 в23 файлах, exit0; `npm run build` — exit0.
До переключения entrypoint записаны12 детерминированных снимков. После
миграции все12 совпали побайтово (390/1440, light/dark, три страницы).

## Реализованные этапы

В app выделены entrypoint, routes, shell, PagePosition и query provider.
Shared содержит только HTTP/auth lifecycle, transport, валидаторы и
общие библиотеки. Shared request получает явный public/private policy,
не знает предметных URL; один singleton сохраняет epoch/locks/errors.

Четыре entities содержат DTO, парсеры, предметные API и представления.
Calculator fields/output доступны обеим features через manual-direction.
Ручная формула, строгий JSON и время сохранены; AST-сравнение исходных
тел30 парсеров и28 API-методов не нашло изменений wire semantics.

Features владеют редактором/черновиком/навигационными guards, восстановлением,
удалением, импортом/экспортом/печатью, историей/сравнением и сессиями.
TrackerPage стал композицией примерно88 строк, координация — useTrackerModel.
Форма разделена на UI/model/navigation guard; карточка — entity с action slots.
Источник lookup/ack/save/retry остаётся одним связным сценарием.
Лендинг собирает локальные секции, Sources — filters/card/catalog model.
Widgets не созданы: эти композиции привязаны к конкретным страницам.

Старые src/lib, src/components, три старые страницы и корневые CSS удалены.
Глобальный CSS перенесён без изменения результата: CSS asset hash совпадает.
Все212 прежних matcher-вызовов unit-тестов сохранены; добавлены11 проверок
архитектурных правил. Нет facade со старым api или feature cross-imports.

## Проверки и команды

Из frontend: `npm run typecheck`, `npm run lint`, `npm run format:check`,
`npm run architecture:check`, `npm test`, `npm run build`.
147 unit tests в24 файлах passed; архитектура119 TS/TSX модулей,
279 зависимостей, ноль циклов. Typecheck проверяет unused locals/parameters.
ESLint добавлен как dev-инструмент, runtime зависимости прежние.

`scripts/check-architecture.mjs` разрешает aliases/relative/dynamic/type imports
через TypeScript и проверяет layers, sibling imports, public API, deep imports,
cycles и legacy layout. Скрипты находятся в frontend/scripts; cache scripts
не создавались. `capture-appearance.mjs baseline|after` даёт12 точных совпадений.

E2E: compiled preview5284, отдельный SQLite API8034, E2E_API=1,
E2E_SERVER=external, CI=1, workers2, retries0.
`npx playwright test --project=chromium --reporter=dot,json --retries=0`:
105 passed,36 scoped skips. После первого прогона обновлён перехват chunk
в проверке load-error (TrackerPage-* → tracker-*); assertions сохранены.
Первый DELETE имел сетевой отказ, повторный полный Chromium прошёл без ошибок.
Финальный Firefox:104 passed,37 scoped skips,0 failures/flaky. Chromium:105 passed,36 scoped skips,0 failures/flaky. Подробная статистика: fsd-verification.json.

Пропуски требуют отдельных source/scenario/NGINX стендов; они не объявляются
прошедшими. Backend/native PostgreSQL/deployment не менялись и здесь не
проверялись. Реальные ключи/данные/volumes не затрагивались. Коммитов/push нет.

Финальные typecheck/lint/format/architecture/unit/build прошли (exit0).
Node minimum22.13 нужен ESLint10; runtime библиотеки не менялись.
Transitive minimatch закреплён override11.0.1 (исправление advisory): npm install сообщает0 vulnerabilities.
Изменения остались в рабочем дереве без staging/commits/push.
