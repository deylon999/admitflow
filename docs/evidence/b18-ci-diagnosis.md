# B18/T210: фактические причины красного CI

Исследован [run42095492218](https://github.com/deylon999/admitflow/actions/runs/42095492218),
commit `c44c21c033b23e63b2de8f9a6ec9a2d3ce46cdc8`. Public API jobs/check annotations
и полные логи загружены через существующую Git credential helper. Реквизиты
не выводились; исходные логи остаются в ignored `backend/var/ci-b18/`.

| Задание | Реальный результат и причина |
| --- | --- |
| containers | success: build, recreation, nginx, backup/restore и production config |
| browsers(webkit) | success |
| browsers(mobile-webkit) | success |
| browsers(mobile-chromium) | failure: `source-lookup.spec.ts`, confirmation keyboard320px dark; heading подтверждения остаётся без фокуса, повтор тоже не прошёл.20других source cases passed. |
| checks | cancelled: лимит15минут; остановлено на `playwright install --with-deps chromium`, Azure Ubuntu mirror скачивает пакеты крайне медленно. До этого666backend passed,116Vitest/build/roadmap passed. |
| browsers(firefox) | cancelled25минут: установка42МБ с Azure mirror заняла22мин35сек; затем реальный broad browser run76passed/37skipped/2failed. Обе ошибки в keyboard.spec.ts: Tab не переводит фокус на первый вариант справочника,390/1440px. |

Отмены не были вызваны новым push или fail-fast. Ошибки фокуса не заменяются
пропусками/снятием assertions; медленную сеть установки нужно исправлять отдельно.
`ubuntu-latest` фактически был `ubuntu-24.04`, image20261101.360.

Проверка:06.11.2026, API jobs6/6,annotations и скачанный архив логов.
Выводы ограничены данным run. Рабочий demo/профили/данные/национальное покрытие
не менялись. Следующие T211/T212: воспроизвести browser errors; исправить фокус
после React commit и проверить фактическую навигацию Firefox. T213/T214:
сохранить отдельные диагностические артефакты и подтвердить новый remote run.
