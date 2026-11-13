# Реестр решений

2026-11-12, ADR-051, user-confirmed: KAN-238 укрепляет существующий Checks workflow;
сохраняются frontend/backend checks, native PostgreSQL guard и все 29 маршрутов.
Отдельный migrations job работает только с чистой admitflow_test*_migrations PostgreSQL БД,
сверяет heads и выполняет alembic check. Отдельный ETL status отражает существующие fixture
проверки и отсутствие dataset/model. Приёмка требует hosted NEG-01–04, PR и последнего
проверенного SHA; applied migrations, production data и repository rulesets не меняются.
Доказательства: [KAN-238-CI-REPORT.md](KAN-238-CI-REPORT.md); задачи T260–T264.

2026-11-05, ADR-029, selected: новый scope SGU4576 использует reviewed-html-table-v2 общего parser. Реальная HTTPS-проверка выявила перестановку только альтернатив экзаменов в двух колонках. V2 канонизирует лишь два явно проверенных множества названий с сохранением количества/положения колонок; новые названия/дубли/критичные поля остаются отказом. Старые V1 профили и provenance не меняются. Новый scope независимо сверяется по оригиналу, а tracked fixture содержит синтетические данные кандидатов. HTTP→worker→PG и повторный offline audit проверяются в disposable schema, без изменения пользовательской БД.

2026-11-05, ADR-028, selected: официальный опорный каталог поставляется версионированным read-only JSON с валидацией и атомарным импортом, без массового создания University/Source и изменения пользовательских подписок. API объединяет его с операторскими записями по явным внешним идентичностям. Это не включает автоматизацию для всех записей. Обновление каталога применяется при перезапуске процесса; синхронизация лицензий/действующего статуса остаётся отдельной работой.

2026-11-05, ADR-027, user-confirmed: пользователь повторно подтвердил необходимый охват всей России. T056/T057 становятся ближайшим приоритетом и не ждут T055; это supersedes их прежний порядок «после MVP», а не отмена критериев выпуска. Реализация сначала даёт датированный национальный каталог, затем проверенное подключение по семействам источников. Общий parser не доказывает совместимость всех вузов. План и ограничения: [NATIONAL_COVERAGE.md](NATIONAL_COVERAGE.md).

Статусы: `user-confirmed` — явное требование пользователя; `selected` — выбранное техническое решение исполнителя; `proposed` — предложение, требующее проверки. Изменение решения создаёт новую запись `supersedes`, не удаляет старую.

| ID | Статус | Решение | Обоснование и условие пересмотра |
| --- | --- | --- | --- |
| ADR-001 | user-confirmed | React, макеты пользователя, Inter/JetBrains Mono | Пользователь уточнил стек и дизайн. Новый визуальный стиль не изобретается |
| ADR-002 | selected | TypeScript, Vite, React Router, TanStack Query | Типизированный интерфейс, маршруты и серверное состояние; отдельный Python API. SSR рассмотреть при доказанной потребности SEO, без переписывания MVP ради моды |
| ADR-003 | selected | FastAPI + Pydantic + SQLAlchemy | Валидация контракта и общий Python-контур для обработки источников. Точные версии фиксируются в зависимостях; обновления после проверки |
| ADR-004 | selected | PostgreSQL в staging/production, Alembic | Транзакции и миграции. SQLite только для локального прототипа/быстрых тестов; PostgreSQL проверяется отдельно |
| ADR-005 | selected | Один модульный backend и отдельный worker того же репозитория | Разделяет HTTP и фоновые задачи без нескольких независимых сервисных кодовых баз. Масштабировать по измеренной нагрузке |
| ADR-006 | selected | Задания в PostgreSQL, lease/lock, отдельный worker | Для начального объёма можно избежать Redis/Celery; обязательны атомарный захват задания, повтор и восстановление после смерти процесса |
| ADR-007 | selected | Same-origin frontend/API через reverse proxy | Упрощает cookies и CORS. Разделение доменов требует пересмотра CSRF, CORS и cookie-политики |
| ADR-008 | proposed | Docker Compose + Caddy + один Linux-хост | Один управляемый контур с HTTPS. Площадка, стоимость и размещение пользовательских данных ещё не выбраны; расходы не согласованы |
| ADR-009 | selected | Гостевой режим как первый вертикальный сценарий | Уже начат. До beta обязательны срок, очистка, удаление, защита ownership; полноценный аккаунт — отдельный этап |
| ADR-010 | selected | Автоматическое получение только из зарегистрированных источников | Пользовательский URL сам по себе не разрешает fetch. Нужны проверка домена, безопасная загрузка, версия адаптера |
| ADR-011 | selected | Числа считает детерминированная модель; объяснение имеет шаблонный fallback | Числа воспроизводимы и проверяемы. LLM не является источником истинности |
| ADR-012 | selected | Вероятности после отдельного исследования и backtest | Недостаточно одного текущего списка для честной вероятности. До этого показываем сценарии и неизвестные |
| ADR-013 | user-confirmed | Цель охвата — все вузы России | Реестр покрытия разделяет каталог, ручной режим и проверенные автоматические интеграции |
| ADR-014 | proposed | Первые две независимые интеграции как релизный минимум | Инженерный план доказательства автоматизации; конкретные вузы/сезон пока не выбраны. Не означает полного национального автоматического охвата |
| ADR-015 | selected | Документы и граф задач — постоянная память проекта | TASKS.json хранит статусы, LOG — историю, STATE — точку продолжения; всё проверяется скриптом |
| ADR-016 | selected | MVP сначала для явно поддержанных групп бакалавриата/специалитета | Точный поднабор определяется после аудита. Магистратура/аспирантура/СПО и особые правила не считаются автоматически совместимыми |
| ADR-017 | user-confirmed | Разделить код на frontend/backend и убрать неиспользуемые файлы | React, npm и браузерные тесты находятся в frontend; общие fixtures в shared; макеты в docs/design; память проекта сохранена в docs |
| ADR-018 | user-confirmed | Docker Compose для локального запуска, supersedes локальную часть ADR-008 | PostgreSQL + FastAPI + Nginx с собранным React; один localhost:8080 и постоянный volume. Это не production: create_all и development cookies; worker пока не реализован |
| ADR-019 | selected | Alembic также для автоматического development setup; supersedes create_all из ADR-018 | 0003/0004 добавляют provenance и очередь; новая схема создаётся миграциями, старые совместимые 0001/0002 сохраняются. Production migration остаётся отдельным шагом. Контейнерный запуск по-прежнему требует проверки Engine |
| ADR-020 | selected | Реестр production пуст до аттестации; синтетические интеграции только в тестах | Контур fetch/parse/validate/store/publish/queue/worker проверяется независимо от доступа к исходным HTML, не повышает coverage и не закрывает проверки реальных источников/PG. Worker запускается отдельным процессом, без публичной регистрации URL |
| ADR-021 | selected | Явный HTTPS public origin/host в production, ограниченные тела API, приватные SQLite recovery bundles | Локальное восстановление и raw cleanup проверяются сейчас; PostgreSQL/production backup остаётся отдельным gate. Ручной JSON переносит значения и даты в новую ownership, не доступ к старой сессии. Метрики каталога и аттестованной автоматизации разделены |
| ADR-022 | selected | Data router установленного React Router и временный черновик в sessionStorage вкладки | useBlocker защищает SPA back/forward, beforeunload отдельно защищает загрузку документа. Черновик живёт до30 минут и окончания гостевой сессии, восстанавливается только явно и не считается серверным сохранением. Scope — односторонний namespace, не доступ к API. При недоступном storage форма работает с предупреждением |
| ADR-023 | selected | Native PG и Compose проверяются в owned disposable environments; supersedes непроверенность runtime из ADR-019/020 | B10 подтвердил legacy migration/concurrency/atomic publish и4-service recreation. CI browser проверяет fresh production build. pg_dump/raw rehearsal quiesced/synthetic, не production backup; registry остаётся пуст до реальной аттестации |
| ADR-024 | selected | Один аттестованный SGU4588 archive2026,8MiB explicit policy,operator-owned HMAC key | Genuine573rows independently checked;no live/admission/second-source claim. Default5MiB remains;no automatic Source enable. Referenced raw retained for development replay;production retention remains T049 and public-release blocker |

## Основание выбора инструментов

Для B08 проверены [useBlocker](https://reactrouter.com/api/hooks/useBlocker) и [createBrowserRouter](https://reactrouter.com/api/data-routers/createBrowserRouter), а также exports установленной версии7.18.4. Блокировщик относится к SPA-переходам; загрузка документа остаётся отдельной проверкой. Новые зависимости не добавлены.

При реорганизации удалены старые артефакты, локальный cache установки, неиспользуемые шаблоны и конфиг незапущенного Sites-хостинга. Ранее зарегистрированный Site имеет ID `appgprj_6ae35a85f638819195ea87d4207f543a`; он не удалялся из сервиса и не публиковался. Если вернёмся к Sites, проверить и переиспользовать этот ID. Новый хостинг не создавать автоматически.

React описывает Vite как один из способов самостоятельной сборки приложения и отдельно обращает внимание на необходимость маршрутизации и получения данных: [React: Build from Scratch](https://react.dev/learn/build-a-react-app-from-scratch). Поэтому Router и Query включены явно; это наш выбор для отдельного API, а не утверждение, что React всегда рекомендует именно этот набор.

FastAPI предоставляет OpenAPI и валидацию запросов: [официальные возможности](https://fastapi.tiangolo.com/features/). Миграции SQLAlchemy ведёт [Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html). Проверки браузерных сценариев проектируются на [Playwright Test](https://playwright.dev/docs/intro). Ссылки проверены при подготовке плана; точная совместимость зависит от закреплённых версий и проверяется сборкой.

2026-11-04,ADR-025,selected: подтверждение архивной записи и дальнейшая история сохраняют факты source-confirmation-v1/source-facts-v1 с unsupported числовой оценкой. Экспорт archive-facts-v1 явно ограничен текущими датированными фактами;manual-export-v1 и полный DB/rawbackup остаются отдельными форматами. Пакетное чтение фиксирует pointer каждого источника один раз на ответ. Аудит воспроизводит оригинальный parser hash и сравнивает DBDecimal семантически,сохраняя старые hashes. Это развитие одного архива;T034/T036 с двумя источниками и production release не объявлены выполненными.

2026-11-04,ADR-026,user-directed: масштабировать parser по семействам форматов с отдельной декларативной конфигурацией и доказательством каждого scope. Не создавать отдельную копию алгоритма на каждый вуз/конкурс. Даже общий parser не разрешает неизвестный URL автоматически. Старые аттестованные версии сохраняются для replay;расширение scope — новая явно проверенная конфигурация. Рубеж B12/70 фиксируется до работ в MILESTONE_70.md.

2026-11-05,ADR-030,selected: новое семейство `reviewed-section-table-v1`
поддерживает несколько явно проверенных конкурсов на одной странице. Page proof
общий для точного URL/сезона/вида; scope и HMAC отдельные для каждой секции.
Проверяются границы, форма, финансирование, места и spans заголовков. Договор
не означает согласие, нулевой приоритет означает unknown только в новой версии.
Дата без часового пояса остаётся без sourceUpdatedAt. Старые версии неизменны.
Реестр масштабируется immutable shards с атомарным manifest (B15/T197);
профиль и найденный общий шаблон сами по себе не включают Source в БД.

S178: запись семейства B15 переиндексирована из дублировавшегося ADR-027 в
ADR-030; содержание сохранено. ADR-027 выше остаётся требованием пользователя
о приоритете всей России, ADR-028/029 — решениями B14.

2026-11-05,ADR-031,selected: каталог групп фильтруется/count/page в SQL.
Для сохранения прежнего Unicode casefold добавлены производные search_name/
search_text, заполненные миграцией0011 и поддерживаемые ORM writes/Core inserts.
Оригинальные названия и факты источников неизменны; прямой SQL rename требует
обновить производное поле в той же транзакции. LIKE ищет буквальные%_ с escape.
Курсор сравнивается и сортируется в одинаковой бинарной collation независимо
от locale сервера. Каталог мониторинга остаётся отдельным read-only artifact.

2026-11-05,ADR-032,selected: filtered таблицы расширяют общий decoder отдельной
версией reviewed-filtered-table-v1. Точный GET scope доказывается выбранными
контролами, числом строк, шапкой/ролями TD и программой каждой строки.
В БГУ для lookup/HMAC используется только первый пятизначный сегмент составного
кода, уникальный среди всех109строк этого scope; остальные персональные части
не нормализуются/не запрашиваются. Дубли минимального ID отклоняются. Это новое
явно проверенное правило конкретной версии, не изменение старых идентичностей.
Явный текст зачисления сохраняется как факт источника; оплата не равна согласию,
вспомогательный платный рейтинг не равен приоритету. Неизвестные остаются null.

2026-11-06,ADR-033,user-directed: frontend писать читаемыми многострочными блоками, не упаковывать JSX/обработчики/CSS в строку. Prettier3.9.10/LF/100columns, JSX attributes per line; исходные assertions/control flow сохранены. Аудит ошибок и исправления различаются: текущая авторизация допускает поиск и форматирование, найденные функциональные дефекты остаются todo.

2026-11-06,ADR-034,user-directed: разрешены исправления только F01/F02.
Resume/reset используют общий browser guest lock и epoch guards; устаревший
destructive intent отклоняется до DELETE. При отсутствии Web Locks changed401
остаётся read-only retry, active401 по-прежнему означает expiry. Во время
reset private UI/queries скрыты; после success/error old-owner cache удаляется
после дополнительной отмены. Новые данные устанавливаются только свежим
авторизованным чтением; ошибка не объявляется пустым списком.

2026-11-06, ADR-035, user-directed: после отдельного запроса разрешены
исправления оставшихся F03–F10, T222–T229. Первая пятёрка завершена отдельно,
затем ещё три; каждый пункт проверен и закоммичен. Многострочный стиль
ADR-033 сохраняется. Черновик не теряет ключ уже отправленного сохранения;
перечитывание архивов обновляет mutable истории, сохраняя immutable
сравнения и датированные факты при отказе. Ошибка каталога не равна пустоте.
Global facets проверяются отдельно от страницы, с клиентским бюджетом20_000
филиалов, согласованным с MAX_PROFILES. Изменение мест независимо от
присутствия строки не меняет смысла отсутствия/согласия. Отмена импорта
очищает ошибку; beforeprint обновляет дату синхронно. Правила расчёта,
backend, source profiles и фактическое покрытие этим не меняются.

2026-11-06, ADR-036, user-directed: выполнить полноценную FSD-миграцию
frontend с аудитом, разделением ответственности и проверкой сохранения
поведения/дизайна. Официальные правила FSD и публичные API обязательны;
shared не содержит бизнес-моделей/формул, app владеет глобальной политикой.
Стек и backend API сохраняются. Семь этапов входят в один активный T230.
Текущее указание запрещает автоматические коммиты/push и временные
тестовые скрипты в служебных cache директориях; прежнее правило коммитить
каждый пункт здесь не применяется. План: docs/ARCHITECTURE.md.

2026-11-07, ADR-037, user-directed: T231 вводит единую визуальную систему
на базе текущей архитектуры и синего стиля AdmitFlow. Семантические CSS
tokens и layers, общие примитивы управления, единая типографика/отступы/
темы. UX, тексты, API и модели не меняются; новая FSD-миграция не проводится.
Требуемые typecheck/lint/build и короткая визуальная проверка выполняются,
длительные E2E не запускаются. Коммиты/push запрещены. Документ DESIGN_SYSTEM.md.

2026-11-07, ADR-038, user-directed: after completing T230/T231, create local logical commits for FSD, design system and documentation. This subsequent authorization supersedes the earlier no-commit instruction; push remains reserved for the user. Preserve configured author and published history.

2026-11-07, ADR-039, user-directed (T232): /tracker становится личным кабинетом
с приоритетом «Мои направления» → добавление → сохранённые направления →
расчётное место/бюджет/дата/изменение → история и сравнение → инструменты.
JSON, покрытие, архивные факты и служебные сведения раскрываются по запросу.
Риск потери доступа, ошибки основных действий и устаревшие данные остаются
видимыми. Архивные направления явно отделены от ручного расчёта; формулы,
API и backend сохранены. Используется T231, без FSD-миграции. Текущее указание
пользователя запрещает коммиты; оно имеет приоритет над ADR-038.

2026-11-07, ADR-040, user-directed: S189 explicitly authorizes local commits of the completed tracker redesign, tests and documentation, superseding the no-commit instruction for S188. No push requested.

2026-11-07, ADR-041, user-directed (T233): разнести loading/empty/error/success
во frontend, прежде всего /tracker. Общий Empty State требует успешного чтения
ручных и архивных направлений; один критический отказ с повтором. Дополнительные
ошибки локальные и компактные, кэш и черновики сохраняются при фоновом отказе.
История изменений и сведения об источниках запрашиваются при первом раскрытии.
Используются существующие React Query и контракты; backend/формулы/архитектура
не меняются. Успех подтверждается после результата операции. Коммиты запрещены
текущим запросом; разрешение S189 относилось к предыдущей работе.

2026-11-07, ADR-042, user-directed (T234): упростить добавление/редактирование
направления одной формой. Группы: вуз/направление/ссылка, числа из списка,
люди выше пользователя. Подсказки объясняют один конкурс, два непересекающихся
подсчёта и откуда брать числа. Все сохраняемые поля обязательны; необязателен
выбор вуза из справочника. Неизвестное число не предлагается заменять нулём.
Ошибки связаны с полями, ожидание/отказ/успех объяснены человеческим языком.
Математика, validation predicates, API, readonly metadata редактирования,
идемпотентность, правила черновиков/сохранения и защиты переходов сохранены.
Существующая дизайн-система; no backend/FSD migration/commits. Ранее сделанные
локальные изменения T233 сохраняются.

2026-11-07, ADR-043, user-directed (T235): согласовать остальные страницы с T231
без полного редизайна. Общая навигация четырёх направлений работы, доступное
мобильное меню/active state; прежние якоря главной сохранены локально. «О проекте»
ведёт к существующим возможностям сервиса на /#about; отдельный маршрут /about
не создаётся. Общие поверхности/отступы служебных страниц, семантика заголовков
каталога и отсутствие дубля ошибки калькулятора. Контент, фирменные цвета,
формулы/API/backend/FSD сохранены. /tracker не перерабатывается, только общая
оболочка/компоненты. Коммитов нет; прежние T233/T234 остаются локальными.

2026-11-07, ADR-044, user-directed (T236): финальная UI-проверка production
frontend на 375/768/1280/1920 px в обеих темах без нового редизайна. Нативные
summary получают общую минимальную высоту 44 px; перекрываемые CSS-правила
controls удалены. Постоянная браузерная матрица проверяет геометрию, состояния
и клавиатуру. Ограничения браузеров и живых источников записаны отдельно от
пройденных Chromium-сценариев. Формулы/API/backend/FSD сохранены; commits/push нет.

2026-11-08, ADR-048, user-directed (T242): новая стратегия полностью заменяет
прежнюю адаптацию UI и требование сохранения старых frontend-сценариев/FSD.
Источник истины — соседний admitflow-frontend-v3-main, только для чтения.
Frontend заменён прямой копией всех 29 маршрутов с исходными текстами, CSS,
данными и взаимодействиями. Допустима одна type-only правка для сборки.
Backend, база, shared и Compose не меняются; API/ML-интеграция отложена.
Новая ветка от main: feat/frontend-v3-exact-copy. Предыдущая ветка сохранена.
Визуальная приёмка — реальные React previews в одинаковом окружении:
29 маршрутов x 390/768/1024/1280/1440 px, нулевой pixel diff. Старые тесты
сценариев трекера не являются требованиями нового frontend; история сохранена.
Локальные коммиты продолжают ранее заданный порядок работы; push не запрошен.

2026-11-08, ADR-049, user-directed (T243–T247): от точной копии v3 переходим
к последовательным вертикальным срезам продукта. Дизайн v3 сохраняется.
Первый срез — публичные вузы и программы по подтверждённым данным с годом
кампании и источником. Существующий FastAPI/PostgreSQL переиспользуется;
старые APIs не удаляются, manual calculation не становится новой моделью.
Неподтверждённые cutoff/exams/forecast остаются null. Архив 2026 не выдаётся
за кампанию 2027. ML, auth и остальные модули внедряются отдельно.

2026-11-08, ADR-050, user-directed (T248–T252): очистка без новых функций
в отдельной ветке от актуального v3/catalog состояния. Удаляются только
подтверждённые dependency audit артефакты: offline HTML/имитация React,
устаревший E2E stand, неиспользуемый plugin-react и два stateless manual
HTTP calculator endpoints. Это уточняет прежний общий запрет удаления APIs:
полезные catalog/source/history/worker и data-preservation контракты остаются.
CamelModel переносится из арифметики в общий schema_base без изменения DTO.
Существующие SQL-модели, БД и applied migrations не удаляются; дальнейший
вывод legacy persistence требует inventory/backup/restore/retention плана.
Визуальный render-код v3 не меняется. Docker Engine denied — T250 blocked,
не основание обходить sandbox или заявлять PostgreSQL/Docker smoke по SQLite.
Старые release/ML задачи deferred до критериев v3. После очистки остановиться.

2026-11-10: объединить transport/DTO/session/resource states для 29 маршрутов. Старые AF-карточки исторические; не объявлять demo, legacy manual арифметику или source scenarios production ML.

2026-11-10 S203 T254: единая dev-команда python scripts/local_smoke.py использует существующий Compose project admitflow и named volumes. Backup до миграций, Alembic current/head/check, атомарный повторный metadata import, реальная PostgreSQL история после recreate;cleanup только собственной новой сессии. SQLite не является этой приёмкой;applied migrations и дизайн v3 сохраняются.

2026-11-13 S209 KAN-212 (T265-T269): continue from current main, reuse shared request/useResource/ResourceState and catalog decoders. Fix only audit-confirmed defects; preserve React v3 CSS, backend contracts and applied migrations. No new dependencies or auth/EGE/ML APIs. Owner review required before task acceptance.

2026-11-13 S210 KAN-214: independent opaque account credentials; retain BrowserSession
and owner_hash unchanged, no automatic guest migration. Additive account schema,
Argon2id RFC9106 low-memory, synchronizer CSRF and strict refresh-family replay
revocation. Target contracts/threats/review sequence in KAN-214-AUTH.md. PR1 enables
no auth endpoint; PR2-6 and production SMTP/HTTPS acceptance remain open.

2026-11-13 S211 KAN-214 PR2 after merged PR14/main494d270: bring forward synchronizer
CSRF to protect login/register immediately; default-disable auth pending full
lifecycle. Issue access only until PR3 refresh/replay/logout. Persistent HMAC budgets
use peer only (proxy aggregate, no arbitrary forwarded-header trust). Mail port
unavailable globally503; invoke delivery on accepted duplicate addresses too with
a safe existing-account notice, preventing provider-error account enumeration.
No new duplicate verification token/password mutation. Real SMTP/confirmation
remains PR4; port tests never claim production delivery. Details: KAN-214-PR2.md.
