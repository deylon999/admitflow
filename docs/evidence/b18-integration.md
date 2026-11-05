# B18: восстановлены проверки GitHub Actions

Исходный [run42095492218](https://github.com/deylon999/admitflow/actions/runs/42095492218)
имел2cancelled/3success/1failure. [Диагноз](b18-ci-diagnosis.md) основан на
полных job logs и annotations конкретного c44c21c, а не на предположении,
что отмена вызвана новым push.

## Исправления

1. `SourceLookup` фокусирует heading через layout effect после React commit.
   requestAnimationFrame из mutation callback мог выполниться до появления ref.
2. `UniversityPicker` явно исключает scroll container из Tab order. Firefox
   раньше фокусировал этот DIV перед первой кнопкой; теперь порядок совпадает
   с ожидаемым, Arrow/Escape/Tab проверки сохранены.
3. Workflow закреплён на Ubuntu24.04. Прежняя команда установки Playwright
   использует официальный HTTPS Ubuntu archive вместо Azure mirror,
   который скачивал42МБ за22мин35сек. Установка ограничена5минутами,
   job timeouts15/25/20минут сохранены. Проверки не отключались.
   В подтверждённом новом run установка заняла22–44секунды в шести заданиях.
4. JUnit и test outputs общего/source stages разделены; отчёт backend
   загружается до установки браузера. Артефакты публикуются также при ошибках
   и имеют уникальное имя project/run_attempt. Повтор не конфликтует с именами.
5. Исправления отправлены обычным push; все шесть заданий нового hosted run
   проверены, XML из артефактов скачаны и разобраны. Точные SHA, run/job IDs,
   длительности установки, counts/skips — в [remote proof](b18-remote-ci.json).

## Проверки и состояние

Локально:116Vitest/production build,63source cases и27keyboard/catalog cases
в Chromium/Firefox/mobile-Chromium. Дополнительно2+2cases сCI=1/two workers
проверили раздельные отчёты: после второго stage оба XML сохранились, в каждом
2tests/0failures. На обновлённом настоящем Nginx ещё6cases прошли за9.7s.
Числа разных прогонов не складываются в число уникальных тестов.

На GitHub:666backend passed с обязательным PostgreSQL; все четыре matrix
projects прошли общий иsource stages; основной Chromium иcontainers также
прошли. Неактивные fixture/edge cases остаются явными skips в своих broad
reports. Они не выдаются за passed, при этом source stages каждой matrix
проверены отдельно. [CI reports](b18-ci-reports.md).

[Локальный demo](b18-local-demo.json) работает на http://127.0.0.1:8091/sources
с исправленным frontend. Все5JS/CSS, включая lazy chunks, равны текущему
dist. API/worker/db/key/volumes/schema0011 прежние; private backups не менялись.
Реальные коды абитуриентов не вводились. Локальные focus/lookup tests использовали
только synthetic API8029 и собственный disposable PostgreSQL.

Temporary API8029/preview5280 остановлены; родительский helper завершился
успешно и удалил свой disposable PG. Исторический national-catalog screenshot
восстановлен. Соседние radar и внешние пользовательские БД не менялись.

Покрытие прежнее:1257catalog/15archivegroups/5вузов/1884строки,
2conditional/0fresh/nationalTotal=null. Правила приёма и профили источников
не менялись. Следующий T057 — новый официальный GET scope из инвентаризации
с проверкой полноты/мест/всех строк и независимой аттестацией. T056/T057,
живая кампания, пользовательская приёмка и staging/release gates открыты.
