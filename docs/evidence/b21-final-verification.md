# B21 — исправлены оставшиеся восемь ошибок frontend

Проверено6 ноября2026. T222–T229 завершены: сначала пять задач, затем три,
после каждой — отдельный Conventional Commit, проверки и обновление плана.
Вместе с T220/T221 предыдущего подхода исправлены все10 дефектов аудита B19.
Исходный аудит и прежние ограничения сохранены как история.

| Дефект | Результат | Доказательства |
| --- | --- | --- |
| F03 | Отменённый ввод не восстанавливается; ключ отправленного сохранения и TTL сохранены | [Черновик](b21-draft-revert.md) |
| F04 | Явное обновление перечитывает архивные истории, сценарии и изменения, включая новый ключ снимка | [История](b21-archive-refresh.md) |
| F05 | Ошибка каталога отделена от успешного пустого результата | [Ошибка/пустота](b21-catalog-error.md) |
| F06 | 101 филиал и все страницы доступны; проверки ресурса/полей сохранены | [Масштаб](b21-catalog-scale.md) |
| F07 | Изменение мест видно независимо от присутствия строки | [Места](b21-archive-capacity.md) |
| F08 | Отмена импорта очищает ошибку; повтор до отмены сохраняет ключ/данные | [Импорт](b21-import-cancel.md) |
| F09 | Штатная печать получает актуальную дату до захвата DOM | [Печать](b21-report-print-time.md) |
| F10 | Границы секций используют существующий цвет обеих тем | [Границы](b21-section-borders.md) |

Общий прогон compiled Chromium: **105 passed,36 scoped skips,0 failed,
0 flaky**,92.4s, retries0,2 workers. JSON статистика сохранена в
[машиночитаемом отчёте](b21-final-verification.json). Пропущены прежние
проверки, требующие reviewed source/fixture API либо nginx; новых skips
не добавлено. Synthetic archive regressions выполняются без этих флагов.
Отдельно повторены все6 критичных session reset/race cases в Firefox:
**6 passed**,13.9s. Они также входят в полный Chromium прогон.

Функциональные focus suites прошли в Chromium и Firefox; CSS-границы
отдельно проверены computed style в Chromium в обеих темах. Числа разных
прогонов не суммируются в уникальное покрытие. Суммарный unit suite:
**136/136 в23 файлах**,exit0. Build и общий Prettier check:exit0.
Backend/schema/source profiles не менялись; новый локальный native PostgreSQL
прогон не заявлен. OS print dialog не автоматизирован; beforeprint проверен
синхронным чтением DOM, реальный PDF — в Chromium.

Все npm-команды выполняются из `frontend` с закреплённым lockfile:

```powershell
npm test
npm run build
npm run format:check
$env:E2E_API = '1'
$env:E2E_SERVER = 'external'
$env:E2E_BASE_URL = 'http://127.0.0.1:5283'
$env:CI = '1'
npx playwright test --project=chromium --reporter=line --retries=0
npx playwright test tests/e2e/session-reset-races.spec.ts tests/e2e/session-reset-cache.spec.ts --project=firefox --reporter=line --retries=0
npx playwright test tests/e2e/draft-revert.spec.ts tests/e2e/archive-refresh.spec.ts tests/e2e/source-catalog.spec.ts tests/e2e/import-cancel.spec.ts tests/e2e/import.spec.ts tests/e2e/report-print-time.spec.ts --project=chromium --project=firefox --reporter=line
```

Последняя команда объединяет воспроизводимые focus suites; в текущем
подходе они запускались по отдельным задачам. Неиспользуемые source-only
сценарии source-catalog требуют отдельного E2E_SOURCE=1, как прежде.

Использовались отдельные SQLite API8033 и compiled preview5283. Для повторного
запуска из `backend` задать DATABASE_URL к отдельной SQLite базе и
AUTO_CREATE_SCHEMA=true, выполнить `.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8033 --no-access-log`.
Из `frontend` с API_TARGET=http://127.0.0.1:8033 выполнить
`npm run preview -- --port 5283` после сборки. Использованные временные
процессы2336/4720 остановлены; ignored база и probes сохранены. Исходный
Docker/key/volumes не затрагивались. Исторический screenshot каталога восстановлен.

Покрытие источников осталось прежним:1257 записей каталога,15 архивных групп
пяти вузов,1884 строки,2 conditional,0 fresh,nationalTotal=null. T056/T057
открыты; следующий кандидат — новый точный scope с независимой сверкой.
