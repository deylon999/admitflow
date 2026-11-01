# Контекст для продолжения

Последняя запись: **S112, 2026-11-01**. **B07 завершён15/15: T139–T153**, отдельный английский Conventional Commit на задачу. Последний запрос пользователя —15 задач. Активной задачи нет; nextTask=T103 (review: реальный PostgreSQL upgrade и сохранность старых данных). История B01–B06 и S058/S059 сохранена в LOG.

## Состояние продукта

- **100 done из153,3blocked,4review,46todo.** Все7 release gates открыты. Оценка автоматического MVP **около40%, D1/30**, старт2026-11-01. Закрытые карточки не равны готовности: реальные источники/PG/CI остаются критическим путём.
- Ручной React-кабинет: CRUD,500 снимков страницами, сравнение любой загруженной пары и до3 направлений, все числа/модель/точное время, поиск/фильтры/сортировка, readonly refresh, печатный отчёт, экспорт и подтверждённый импорт JSON. Лимиты20 направлений/500 снимков/12000 ключей,8MiB файл/тело API. Replay импорта при заполненном лимите разрешён, удалённое не восстанавливается.
- Гость30дней, expiry не продлевается чтением, явный reset, ownership и обработка401. Защита dirty-form/cancel/switch/link/delete; pending save блокирует уход по ссылкам и защищает unload даже при неизменённой форме. SPA back/forward/crash recovery и хранение черновика на диске не реализованы.
- Background GET failure оставляет датированные карточки;401 скрывает приватные данные. Cross-tab reset скрывает старую форму, отменяет приватные queries и требует readonly synchronization. Web Locks сериализует bootstrap/reset; без него гарантия межвкладочной сериализации отсутствует. Epoch защищает старые headers/body/promises; отменённый private GET сразу завершает ожидание shared bootstrap без отмены его для других.
- **Каталог2, автоисточников0, published groups0**, nationalTotal=null. Production registry пуст, assessmentAvailable=false. Формула manual-v1 не менялась; вероятность и ML не реализованы. Ручной ввод/архив/автоматическая проверка не смешиваются.
- Source DTO/HMAC/fetch/validation/quarantine/raw/immutable publish/queue/lease/fencing/worker проверен синтетически, не на аттестованных реальных adapters. Source status учитывает failed/expired jobs без потери последнего snapshot/archive. Не переписывать готовый контур вместо снятия внешних блокеров.
- Alembic0001–0004. Development upgrade, production отдельная миграция. Legacy adoption только после проверки совместимости. T103 сравнивает CHECK через пустую временную PG-таблицу; blind stamp и reset volume не применялись. HTTP smoke8080 из S059 не доказывает native migration/сохранность прежних данных.

## Что изменил B07

- Импорт файла: strict structural JSON parser до JSON.parse, decoded duplicate keys/nonfinite/depth>64 отвергаются. Fatal UTF-8 decoding с BOM; повреждённые bytes не заменяют названия. Отмена чтения освобождает UI, разрешает новый файл, поздний результат не подменяет preview. Отмена подготовки не отменяет уже отправленный import POST.
- Имена160/200 и запрос справочника120 считаются по Unicode code points. Поиск потребляет AbortSignal при смене query/unmount. Варианты доступны стрелками/Enter/Escape, ручной fallback сохранён.
- Отменённый private read не ждёт общий bootstrap; старый epoch не становится новым доступом. Unread bodies при401 и stale headers отменяются. Открытая форма не отправляется во время другого mutation; поля сохраняются. Pending save защищает обычные ссылки/unload; пользователь видит причину.
- ManualTimestamp после offset должен укладываться в UTC годы0001–9999: иначе422, без OverflowError. Экспорт наблюдает время после owner-locked чтения и возвращает409, если сохранённые даты опережают часы, не меняя историю. Это кратковременно касается и разрешённых будущих дат импорта до5min. DATA_RULES обновлён; формула/сезон/согласия прежние.
- Реально воспроизведено расширение мобильной grid до1919px на длинном имени в открытой форме. Minmax(0,1fr), bounded sidebar/form и перенос preview устранили проблему:320px, обе темы,160/200 непрерывных букв,1000000, история и редактирование проходят.
- Печать проверена на двух реальных API-записях с фильтром: в области отчёта только выбранная запись, source/model/ограничения, без controls; Chromium создаёт A4 PDF в ignored test-results. docs/evidence/manual-report.png просмотрен. Обычный тест не переписывает evidence; RECORD_EVIDENCE=1 делает это явно.
- tests/test_restart.py трижды запускает новый локальный процесс Uvicorn на одной временной SQLite-базе. История/даты/ownership/create-update replay/tombstone410 сохраняются. Отдельный lifespan-test не оживляет expired owner. Это не PostgreSQL/Compose/production recovery.

## Проверки и ограничения

- Финальные **276 backend passed/7 actual PG skipped;87 frontend passed; build exit0;53 Chromium passed** на final API8006. Один существующий Starlette/httpx warning. B07 backend полный54.96s, Chromium полный1.5m; ошибки ожиданий не ослаблялись.
- Во время targeted pending-form теста исправлен неверный текст label; преждевременный параллельный rerun столкнулся с каталогом Playwright artifacts. Все runners завершены перед успешным последовательным2/2 и финальным53/53. В restart-test исправлен Domain искусственно заданного cookie, чтобы он совпадал с host semantics.
- Новый docs/evidence/manual-mobile-b07.png снят на final API8006/390px с явно названным примером ручного ввода; снимок просмотрен, тестовая сессия удалена. Обычные preview-desktop/mobile.png остаются B05. Шрифты/точная Figma-приёмка не подтверждены.
- T006 blocked: GitHub:443 по-прежнему недоступен; push/remote CI не подтверждены. T007 blocked: Inter/JetBrains Mono/лицензии не получены. T013 blocked: original HTML нет, ранее web source/font API недоступны. Нельзя подделывать original HTML из извлечённого текста.
- Docker Engine/config ACL снова denied. Native PG migration/concurrency, полный Compose/staging/HTTPS/backup и реальные источники не подтверждены. T014/T022/T067/T103 review; широкие требования сохранены. Host/domain/budget и релизный сезон не выбраны;2026 вне кампании требует archive label.
- Старые вопросы о путях HTML/fonts/PG и пересборке/сохранности прежних направлений остаются без ответа. Не повторять без нового основания; сначала проверить новые сообщения/реальные входы. Приоритет — снять блокеры, не создавать очередные синтетические adapters и не повышать процент по количеству мелких исправлений.

## Git, процессы и продолжение

Текущий preview **http://127.0.0.1:5186/tracker**, frontend session91203/API_TARGET8006. Final API **session26232/PID5096**,8006,изолированная backend/.pytest_cache/batch07.db,revision0004,без reload/access-log. Первоначальный B07 API session8562/PID19116 остановлен перед полным прогоном; Get-CimInstance denied, PID известен из собственного запуска. Старые previews5185/8005 и ранее, Docker8080 не затрагивались. Перед использованием проверять реальную доступность: запись session/PID сама по себе не доказательство жизни.

B07 содержит15 task commits от c27e851 до финального checkpoint; author deylon999 и origin сохранены. Коммиты локальные, push/CI не подтверждены, force push не разрешён. Список SHA получить git log c27e851..HEAD. Старый Site ID — ADR-017; новые Site не создавать.

Resume: STATE/ROADMAP, roadmap --check/--next, карточка/DECISIONS/LOG, реальные файлы/git status. Источники истины — PRODUCT/DECISIONS/TASKS.json/STATE.json/LOG. TASKS.md/CHECKLIST генерируются. Helpers backend/.pytest_cache/batch06.py и batch07.py — только статусы завершённых batches, init повторно не запускать. Одновременно одна in_progress; blocked/review не закрывать без новых доказательств.