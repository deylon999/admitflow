# T008 — сверка лендинга с PNG,2026-11-03

Оригиналы: docs/design/{desktop,mobile}/{Light,Dark}.png. Desktop1440×5315, mobile390×7269. Все4 оригинала и4 актуальных screenshots визуально просмотрены. Current screenshots: b11-landing-{light,dark}-{1440,390}.png. Fresh production build с локальными Inter/JetBrains Mono; viewport1440/390×900, fullPage. Внешние шрифты не нужны (отдельный fonts.spec.ts доказывает actual FontFace для Latin/Cyrillic).

## Что совпадает

- Порядок и композиция9 основных блоков, hero two-column/stacked mobile, statistics3-column/stacked, sources2-column/stacked, diagram, calculator, quotes,3 feature cards, FAQ и финальный CTA.
- Основные цвета измерены чтением пикселей originals (без изменения изображений) и совпадают с CSS tokens: light bg#fff,surface#f5f7fa,primary#1b4dff,text#0f172a,muted#566178,line#e1e6ee; dark bg#0f172a,surface#151f36,primary#6c93ff,text#f1f5f9,muted#93a0b8,line#26324d.
- Inter/JetBrains Mono, скругления карточек/кнопок, границы, grid spacing и общий типографический масштаб. На390/1440 нет потери текста и горизонтального overflow.

## Явные расхождения, предъявленные приёмке

1. Копирайт расчёта/FAQ/карточек длиннее оригинала: факт ручного ввода, непересекающиеся группы, неизвестные приоритеты, отсутствие гарантии и автоматизации. Эти изменения уже приняты в PRODUCT/ADR и DATA_RULES; возврат исходного «реальное место» нарушил бы фактический контракт. Дополнительная высота ожидаема: текущий main5439px desktop/7422px mobile плюс header/footer; полный original5315/7269.
2. Доступны ссылка в кабинет и статусы «Ручной режим»/«Доступно» вместо всех «В разработке». Дополнительная ссылка в CTA/footer соответствует реализованному ручному сценарию.
3. После загрузки/SPA навигации h1 имеет видимую focus outline. На снимках cue сохранён, стили/фокус перед screenshot не подделывались. Это отличие от статического PNG для доступности; keyboard/navigation regressions сохранены.
4. Калькулятор показывает отдельные исходные сценарии, legend и раскрываемое объяснение; статус «В пределах мест в обоих рассмотренных сценариях» уточняет ограничения исходного макета.

Это визуальная приёмка реализации с перечисленными функциональными изменениями, не заявление о pixel-identical Figma или завершении всей автоматической UX-приёмки T026/T045.

## Проверка

Добавлена отсутствовавшая ширина1024 в landing.spec.ts. `E2E_SERVER=external E2E_BASE_URL=http://127.0.0.1:4190 npm run test:e2e -- tests/e2e/landing.spec.ts tests/e2e/fonts.spec.ts --reporter=line` →6 passed,exit0,4.9s.320/390/768/1024/1440, обе темы,calculator validation/74/empty,FAQ,overflow и local FontFace. Screenshot command uses Chromium and document.fonts.ready, никаких CSS overrides/скрытия фокуса. API для лендинга не требуется.
