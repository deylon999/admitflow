# B21/T229 — границы поиска и сравнения

Исправлена F10: две ссылки на отсутствующую CSS variable --border заменены
существующей --line. До изменения computed border был0px/none в обеих
темах. После изменения в actual UI source lookup имеет верхнюю границу
1px solid, scenario comparison — четыре границы1px solid.

Проверено2026-11-06 на compiled preview5283 с synthetic source mocks:
светлая тема rgb(225,230,238), тёмная rgb(38,50,77), обе соответствуют
вычисленному --line. Игнорируемый probe:
`node backend/.pytest_cache/b21_border_probe.cjs --assert-fixed`,exit0;
результат `backend/.pytest_cache/b21_border_fixed_results.json`.
`npm run build`, scoped Prettier check, `git diff --check`:exit0.

Это проверка фактического computed style, без нового теста, повторяющего
две строки CSS. Для воспроизведения без локального probe открыть поиск
записи источника и сравнение сохранённых сценариев, переключить обе темы,
проверить указанные селекторы через getComputedStyle. Backend и данные
не менялись. Все восемь задач T222–T229 завершены; общий прогон отдельно.
