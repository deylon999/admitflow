# Архив сравнения frontend v3

[Отчёт S199](../frontend-v3-exact.md) и [галерея](comparison.html) показывают
145 сравнений оригинала с копией. `visual-results.json` сохраняет результаты,
в том числе оба хеша каждой пары. Каждый прежний `<width>/<route>-copy.png`
совпадает с `<width>/<route>-original.png`, на который ссылается галерея.

[Исходные пути обеих сторон в Git](https://github.com/deylon999/admitflow/tree/a6d2f742976880414e64435d31a15c225350cfdc/docs/evidence/frontend-v3-exact).
[Манифест PNG](../visual-baselines.sha256).

[Манифест исходного кода](source-manifest.json) читает
[`verify-source.mjs`](../../../frontend/scripts/verify-source.mjs). Сравнение
требует оригинальный соседний React-проект `admitflow-frontend-v3-main`.
При повторном запуске `test:visual` оригинал рендерится заново.
