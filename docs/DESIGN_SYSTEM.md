# Визуальный эталон AdmitFlow

Источник истины — v3 и его исходные React/CSS, а не прежний ручной UI.
Все 29 runtime страниц сохраняются. Никакого самостоятельного редизайна
при очистке проекта не выполняется.

- `src/styles.css` — landing v3.
- `src/internal.css` — исходные `--af-*` tokens, Shell, primitives и страницы.
- `src/shared/UI.tsx` — Surface, Action, Pill и другие исходные primitives.
- `src/catalog/catalog.css` — уже интегрированные scoped constraints для
  реальных длинных имён/unknown-state, без изменения базовой палитры.

Эти render-файлы не менялись при S201. В `data/demo.ts` удалён лишь
неиспользуемый routeLabels export, обслуживавший удалённый offline renderer.
V3 Calculator остаётся demo-компонентом; это не старый ручной калькулятор.
Тёмная тема в источнике полноценно не реализована; её наличие не заявляется.

Сверка выполняется на реально запущенном React при одинаковых шрифтах,
viewport, dpr, теме и состоянии. Для каталога — PNG до очистки, для остальных
страниц — sibling reference с четырьмя ранее разрешёнными demo-подписями.
Результаты и точные ограничения: [evidence](evidence/foundation-cleanup.md).

Старые требования четырёх PNG/FSD находятся в
[архиве](archive/design-system-before-foundation.md) и не меняют эталон v3.
