# B18/T213: диагностика двух browser stages

В browser matrix общий и source прогоны используют разные output directories:
`test-results/broad` и `test-results/source`. Их JUnit XML лежат рядом в
`test-results/broad.xml` и `source.xml`; второй Playwright invocation не стирает
результат первого. У каждой matrix project собственный upload artifact,
имя включает run_attempt для повторного запуска без конфликта имени.

Backend JUnit загружается сразу после pytest, до установки браузера.
Browser/Chromium результаты загружаются с if:always(),retention7дней;
предыдущий вывод первых60строк page state в общий job log заменён файлами
артефакта. Failure propagation и все четыре browser projects сохранены.

Локальные проверки из frontend:

- `npm test`:116passed.
- Production build после обеих UI правок:exit0.
- T211:63source cases/3projects,0skip,1.9m.
- T212:27keyboard/catalog cases/3projects,0skip,54.0s.
- CI=1/two workers:Firefox national-catalog2passed,4.5s; затем mobile-Chromium
  confirmation light/dark2passed с отдельными JUnit/output directories.
  Оба XML после второго прогона сохранились; в каждом2tests/0failures.
- YAML parsed:3jobs/4browser matrix entries,failure propagation сохранён.
  `bash -n scripts/install_playwright_ci.sh`:exit0.

Использовался только synthetic PG/API8029 и compiled preview5280.
Постоянный demo/key/volumes не изменялись. Исторический screenshot каталога
восстановлен из Git после тестов. Эти локальные результаты не доказывают
успех hosted Linux runner; T214 остаётся активной до фактического remote run.
