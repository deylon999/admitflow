# T231 — аудит и рефакторинг визуальной системы

Update after completion: user authorized local commits. Source commit `ac11756`; no push. Earlier no-commit statements below describe the original implementation stage.

Проверено7 ноября2026. Работа выполнена поверх незакоммиченной FSD-миграции;
предыдущие изменения сохранены. Архитектура, бизнес-модели, расчёты, запросы
API, тексты, навигация и последовательность действий не перерабатывались.

## Подтверждённые проблемы

В styles.css найдено25 разных font-size значений, включая64px h1,
128px числовой результат и мобильные подписи8–10px. Tracker использовал
другие размеры заголовков, labels и радиусов. Из55 кнопок шесть не имели
оформляющего класса: повтор каталога, загрузка вузов, ошибки/пагинация
изменений, сравнение сценариев и проверка источника.

Нативные поля/кнопки, глобальные правила и стили конкретных страниц
конфликтовали. Карточки имели разные padding/radius; hover/focus/disabled
не имели одного владельца. Поэтому исправление включает реальные
переиспользуемые примитивы и очистку прежних правил, не только CSS overrides.

## Реализация

Единые tokens/base, CSS layers, общие Button/Input/Select/Card/Badge/Alert,
подключение ко всем55 прежним кнопкам и существующим полям/поверхностям.
Нативная DOM-семантика и обработчики сохранены. Заголовки32/28,24,20px;
основной текст16px, secondary14px, captions12px. Controls44px, общие
границы/радиусы/состояния; обе темы используют семантические цвета.
Кнопка шапки имеет компактный вариант без разрыва слова на320px.
Оформление печати отделено и сохранено. Детали: [система](../DESIGN_SYSTEM.md).

## Фактические проверки

Все команды ниже выполнялись из frontend и завершились exit0:

- `npm run typecheck`;
- `npm run lint`;
- `npm run build`;
- `npm run format:check`;
- `npm run architecture:check`:124 modules,318 dependencies,0 cycles;
- `npm test`:147 passed,24 files;
- `node scripts/check-design-system.mjs`:12 сочетаний трёх страниц,
  двух тем и ширин320/1440;4 проверки редактора/состояний и4 ошибки каталога.

Браузерная проверка занимает десятки секунд и не обращается к backend.
Проверены размеры h1/h2/h3, отсутствие горизонтального overflow (включая
число1000000), общие классы и минимальная высота кнопок/ссылок-действий,
редактор, focus3px, disabled opacity, primary hover и контраст≥4.5,
ошибка503/retry. Снимки просмотрены визуально; это не полный аудит WCAG.
Длительные E2E и проверки backend/deployment не запускались.

Артефакты: `frontend/test-results/design-system/verification.json`,
снимки страниц/редактора/error, а также две сохраняемые иллюстрации:
[светлая тема](design-system-light.png), [тёмная тема320px](design-system-dark.png).
Данные в них синтетические. Временный preview5285 остановлен после проверки.
Коммитов, staging и push в этом подходе нет.

## Затронутые файлы

Полный список файлов этого визуального изменения приведён ниже отдельно
от ранее выполненной FSD-миграции.

- `frontend/scripts/check-design-system.mjs`
- `frontend/src/app/App.tsx`
- `frontend/src/app/styles/base.css`
- `frontend/src/app/styles/print.css`
- `frontend/src/app/styles/styles.css`
- `frontend/src/app/styles/tokens.css`
- `frontend/src/app/styles/tracker.css`
- `frontend/src/app/ui/Layout.tsx`
- `frontend/src/app/ui/PageErrorBoundary.tsx`
- `frontend/src/app/ui/ThemeToggle.tsx`
- `frontend/src/entities/admission-source/ui/SourceProvenance.tsx`
- `frontend/src/entities/manual-direction/ui/CalculationInputs.tsx`
- `frontend/src/entities/manual-direction/ui/CalculationOutput.tsx`
- `frontend/src/entities/manual-direction/ui/ManualDirectionCard.tsx`
- `frontend/src/entities/university/ui/SourceUniversityFilter.tsx`
- `frontend/src/entities/university/ui/UniversityPicker.tsx`
- `frontend/src/features/calculate-admission/ui/Calculator.tsx`
- `frontend/src/features/compare-manual-directions/ui/WatchComparison.tsx`
- `frontend/src/features/delete-manual-direction/ui/DeleteManualDirectionFeedback.tsx`
- `frontend/src/features/edit-manual-direction/ui/DirectionForm.tsx`
- `frontend/src/features/edit-manual-direction/ui/DraftRecovery.tsx`
- `frontend/src/features/import-manual-directions/ui/ImportData.tsx`
- `frontend/src/features/review-archive-history/ui/ArchiveHistory.tsx`
- `frontend/src/features/review-manual-history/ui/HistoryComparison.tsx`
- `frontend/src/features/review-manual-history/ui/ManualDirectionHistory.tsx`
- `frontend/src/features/review-source-changes/ui/ChangeFeed.tsx`
- `frontend/src/features/review-source-scenario/ui/ArchiveScenario.tsx`
- `frontend/src/features/review-source-scenario/ui/ScenarioComparison.tsx`
- `frontend/src/features/save-source-record/ui/SourceLookup.tsx`
- `frontend/src/pages/landing/ui/RankingDiagram.tsx`
- `frontend/src/pages/landing/ui/sections.tsx`
- `frontend/src/pages/sources/ui/SourceCatalogFilters.tsx`
- `frontend/src/pages/sources/ui/SourceGroupCard.tsx`
- `frontend/src/pages/sources/ui/SourcesPage.tsx`
- `frontend/src/pages/tracker/ui/ArchiveDirections.tsx`
- `frontend/src/pages/tracker/ui/CoverageSummary.tsx`
- `frontend/src/pages/tracker/ui/DirectionCard.tsx`
- `frontend/src/pages/tracker/ui/ManualDirectionsPanel.tsx`
- `frontend/src/pages/tracker/ui/TrackerAccess.tsx`
- `frontend/src/pages/tracker/ui/TrackerFeedback.tsx`
- `frontend/src/pages/tracker/ui/TrackerFilters.tsx`
- `frontend/src/pages/tracker/ui/TrackerHeading.tsx`
- `frontend/src/pages/tracker/ui/TrackerPage.tsx`
- `frontend/src/shared/ui/Alert.tsx`
- `frontend/src/shared/ui/Badge.tsx`
- `frontend/src/shared/ui/Button.tsx`
- `frontend/src/shared/ui/Card.tsx`
- `frontend/src/shared/ui/DeleteConfirmation.tsx`
- `frontend/src/shared/ui/Input.tsx`
- `frontend/src/shared/ui/index.ts`
- `frontend/src/shared/ui/ui.css`

Documentation/status: docs/DESIGN_SYSTEM.md, docs/evidence/design-system.md,
design-system-files.json, design-system-light.png, design-system-dark.png,
docs/DECISIONS.md, docs/PRODUCT.md, docs/STATE.json, docs/STATE.md,
docs/TASKS.json, generated docs/TASKS.md/CHECKLIST.md, docs/LOG.md.
