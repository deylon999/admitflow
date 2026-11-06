# Чек-лист AdmitFlow

`[x]` — сделано и проверено. `[ ]` — ещё не завершено.

**Закрыто 201 из 229 задач.** Это счёт задач, не процент готовности продукта.

Частично реализованные пункты остаются без галочки. Последний раздел относится к развитию после MVP.

Подробности и доказательства: [карточки задач](docs/TASKS.md). Файл обновляется из `docs/TASKS.json` командой `python scripts/roadmap.py --render`.

## Стабилизация

- [x] T001 Зафиксировать фактическое состояние проекта
- [x] T002 Исправить React production build
- [x] T003 Перенести проверки калькулятора на Vitest и TS
- [x] T004 Сделать воспроизводимый backend setup
- [x] T005 Покрыть ручной API и Python-расчёт
- [x] T006 Настроить CI для проверяемого checkout
- [x] T007 Закрепить шрифты и дизайн-токены
- [x] T008 Сверить React-лендинг с исходными макетами
- [x] T066 Разделить frontend/backend и очистить структуру
- [x] T067 Добавить локальный запуск через Docker Compose
- [x] T103 Fix PostgreSQL legacy CHECK reflection during migration adoption

## Источники и правила

- [x] T009 Исследовать источники и выбрать технический пилот
- [x] T010 Зафиксировать сезон и правила поддержанного конкурса
- [x] T011 Описать доступ к данным и минимизацию
- [x] T012 Создать начальный каталог с происхождением записей
- [x] T013 Подготовить реальные и негативные fixtures
- [ ] T056 Расширить проверенный каталог до национального охвата
- [x] T083 Получать проверяемый пакет исходных страниц пилота
- [x] T190 Сохранить официальный опорный перечень вузов и границы охвата
- [x] T191 Импортировать национальный опорный каталог без дублей

## Ядро продукта

- [x] T014 Ввести Alembic и PostgreSQL-проверки
- [x] T015 Утвердить идентичность и каноническую модель данных
- [x] T016 Довести гостевой доступ и жизненный цикл сессии
- [x] T017 Сделать записи и лимиты устойчивыми к повторам
- [x] T018 Согласовать API-контракты и frontend types
- [x] T019 Завершить ручное сохранение направлений
- [x] T020 Уточнить сценарную модель и безопасные формулировки
- [x] T023 Довести неизменяемую историю и сравнение снимков
- [x] T068 Реализовать атомарные ручные записи и идемпотентность
- [x] T069 Объяснить ручной сценарий проверяемыми числами
- [x] T070 Показать сравнение ручных снимков
- [x] T071 Экспортировать свои ручные направления и полную историю
- [x] T072 Довести управление ручной формой с клавиатуры
- [x] T073 Таймауты ручного API и восстановление чтения
- [x] T074 Загрузка полной ручной истории страницами
- [x] T090 Импортировать ручную историю атомарно через API
- [x] T091 Восстанавливать ручную историю из файла в интерфейсе
- [x] T094 Разрешить безопасный replay импорта при заполненном лимите
- [x] T095 Проверять действительные даты и порядок полной истории на клиенте
- [x] T098 Согласовать истечение сессии во всех действиях кабинета
- [x] T106 Expose exact history totals and remaining snapshot capacity
- [x] T113 Invalidate private state when another tab resets access
- [x] T119 Reject control characters in manual metadata
- [x] T124 Batch manual direction and export reads
- [x] T125 Order same-time snapshots and refuse clock regression
- [x] T126 Enforce ISO aware timestamps on manual DTOs
- [x] T128 Compare opaque IDs by Unicode code point
- [x] T135 Serialize guest bootstrap between browser tabs
- [x] T136 Fence stale session results after access changes
- [x] T149 Keep manual UTC timestamps inside the supported calendar
- [x] T150 Refuse inconsistent exports after clock regression
- [x] T153 Verify manual data across API process restarts
- [x] T192 Показать национальный каталог и статусы подключения в поиске

## Автоматический сбор

- [x] T021 Найти абитуриента в конкретном источнике
- [x] T027 Определить интерфейс адаптера и registry
- [x] T028 Реализовать ограниченный безопасный fetcher
- [x] T029 Подключить первый официальный источник
- [x] T030 Ввести нормализацию и карантин
- [x] T031 Подключить второй независимый источник
- [x] T032 Реализовать планировщик и отдельный worker
- [x] T033 Сохранять и публиковать снимки атомарно
- [x] T034 Считать автоматические assessments и diff
- [x] T035 Обработать отказ и восстановление источника
- [x] T036 Сделать детерминированный replay архивов
- [x] T037 Добавить эксплуатационное управление источниками
- [x] T038 Посчитать честные метрики покрытия
- [ ] T057 Масштабировать адаптеры по платформам вузов
- [x] T076 Базовый контракт и закрытый реестр адаптеров
- [x] T077 Нормализация и карантин неполного списка
- [x] T078 Приватное хранилище исходных ответов
- [x] T079 Атомарная публикация нормализованного снимка
- [x] T080 Диагностика свежести зарегистрированного источника
- [x] T081 Очередь обновлений с lease и ограниченными повторами
- [x] T082 Worker и локальные команды управления источниками
- [x] T099 Соблюдать deadline блокировки внутри процесса и между процессами
- [x] T100 Ограничить весь обмен результата дочернего fetch-процесса
- [x] T102 Показывать исчерпанные и истёкшие задания в диагностике источника
- [x] T129 Reject truncated HTTP source responses
- [x] T130 Reject ambiguous HTTP headers and malformed redirects
- [x] T131 Validate immutable fetch policies strictly
- [x] T132 Preserve fetch outcome when spool cleanup fails
- [x] T133 Validate adapter declarations before registry use
- [x] T134 Apply queue policies on explicit eligible reenqueue
- [x] T174 Bound larger verified source responses by explicit adapter policy
- [x] T175 Register the reviewed archive group through an explicit operator command
- [x] T187 Поддержать конфигурируемые семейства адаптеров с аттестацией каждого источника
- [x] T188 Доказать переиспользование общего parser на настоящих конкурсных группах
- [x] T193 Составить воспроизводимую инвентаризацию страниц приёма и форматов
- [x] T194 Проверить следующее семейство или новый scope на реальном источнике
- [x] T195 Проверить найденные страницы приёма и признаки списков
- [x] T196 Сгруппировать реальные структуры списков для повторного использования
- [x] T197 Масштабировать реестр профилей без одного ограниченного файла
- [x] T198 Аттестовать повторяемое семейство на новых настоящих источниках
- [x] T199 Проверить массовую очередь и отчёт расширенного покрытия
- [x] T200 Выбирать вузы во всём каталоге конкурсных групп
- [x] T201 Фильтровать и ограничивать группы на стороне БД
- [x] T202 Подключать набор проверенных профилей атомарно
- [x] T203 Исследовать следующий подтверждаемый формат списков
- [x] T204 Проверить масштабирование каталога и итог покрытия B16
- [x] T205 Проверить точный GET scope БГУ и места конкурса
- [x] T206 Добавить общий decoder для таблиц с проверенными фильтрами
- [x] T207 Независимо сверить и аттестовать архивную группу БГУ
- [x] T208 Проверить worker и сохранение записи новой группы
- [x] T209 Обновить стенд и сверить покрытие B17

## Объяснения и UX

- [x] T022 Добавить поиск вузов и групп с coverage
- [x] T024 Показывать provenance и отдельные времена
- [x] T025 Закрыть ошибки загрузки и повторных действий
- [x] T026 Проверить доступность кабинета и мобильный UX
- [x] T039 Объяснять оценку и изменение проверенными фактами
- [x] T040 Показать изменения внутри приложения
- [x] T075 Сравнение сохранённых ручных направлений
- [x] T092 Показывать фактическое покрытие источников
- [x] T093 Убрать категоричные обещания из ручного пользовательского пути
- [x] T096 Привязать ошибки ручной формы к полям и фокусу
- [x] T097 Защитить несохранённую форму от случайного переключения
- [x] T104 Search, filter and sort saved directions
- [x] T105 Compare any two loaded manual snapshots
- [x] T107 Show all saved inputs and exact timestamps in history
- [x] T108 Print a readable manual directions report
- [x] T109 Guard deletion of the direction being edited
- [x] T110 Manage focus and Escape for delete confirmations
- [x] T111 Retain saved cards after background read failure
- [x] T112 Display the exact guest access deadline
- [x] T114 Add skip navigation and focus route headings
- [x] T115 Make history overflow usable from the keyboard
- [x] T116 Refresh saved directions without losing a form draft
- [x] T117 Preview direction names before confirming file import
- [x] T127 Align import preview date rules with server validation
- [x] T138 Recover from lazy page loading failures
- [x] T139 Reject ambiguous JSON import files
- [x] T140 Reject invalid UTF-8 import files
- [x] T141 Cancel import preparation safely
- [x] T142 Align form Unicode length limits with the API
- [x] T143 Cancel abandoned catalog searches
- [x] T144 Navigate university choices with the keyboard
- [x] T145 Stop canceled private reads after session bootstrap
- [x] T146 Release response bodies discarded by session fencing
- [x] T147 Guard navigation while a save is pending
- [x] T148 Prevent form submission during another mutation
- [x] T151 Verify long manual cards at320px in both themes
- [x] T152 Verify filtered manual report printing
- [x] T154 Enable data-router navigation blocking
- [x] T155 Protect unsaved forms on browser back and forward
- [x] T156 Expose an isolated guest draft namespace
- [x] T157 Validate bounded session-local draft storage
- [x] T158 Save form drafts and retry keys locally
- [x] T159 Offer explicit draft restore and discard
- [x] T160 Refuse stale draft updates without losing retry safety
- [x] T161 Clear local drafts when access or saved data changes
- [x] T162 Verify draft recovery across real browser reloads
- [x] T163 Verify keyboard and narrow-screen draft recovery
- [x] T176 Find a candidate by scoped public code and issue owner-bound confirmation
- [x] T177 Save owner-isolated source subscriptions within combined direction limits
- [x] T178 Удалять отдельную архивную запись без её восстановления повтором
- [x] T179 Сохранять и читать неизменяемую историю фактов одного архивного источника
- [x] T180 Показывать историю и сравнение подтверждённых архивных фактов
- [x] T215 Закрепить читаемый стиль frontend и команды форматирования
- [x] T216 Развернуть библиотечный TypeScript в многострочный код
- [x] T217 Сделать JSX компонентов, страниц и стили читаемыми
- [x] T218 Привести тесты к тому же стилю и проверить поведение
- [x] T219 Подтвердить и описать найденные ошибки frontend
- [x] T220 Не терять новую сессию при синхронизации вкладок
- [x] T221 Очищать старые карточки после сброса гостевой сессии
- [ ] T222 Не восстанавливать отменённые значения черновика
- [ ] T223 Обновлять открытую историю вместе с архивной карточкой
- [ ] T224 Разделить ошибку каталога и подтверждённую пустоту
- [ ] T225 Согласовать branch facets frontend и backend выше100
- [ ] T226 Показывать изменение мест при отсутствии записи
- [ ] T227 Очищать сообщение ошибки при отмене импорта
- [ ] T228 Обновлять время отчёта при штатной печати браузера
- [ ] T229 Восстановить границы секций поиска и сравнения

## Качество и эксплуатация

- [x] T041 Добавить наблюдаемость API/worker/источников
- [x] T042 Собрать регрессию правил и качества данных
- [x] T043 Проверить безопасность и пользовательские данные
- [ ] T044 Измерить нагрузку и устранить узкие места — **нужна проверка / завершение**
- [x] T045 Проверить браузеры и визуальные состояния
- [ ] T046 Наблюдать циклы импорта и свежесть — **заблокировано**
- [x] T047 Подготовить контейнерный контур
- [ ] T048 Развернуть staging с HTTPS — **заблокировано**
- [ ] T049 Проверить backup, restore и retention — **заблокировано**
- [ ] T050 Настроить эксплуатационные сигналы и откат — **заблокировано**
- [ ] T051 Пройти полный путь автоматизированного MVP — **заблокировано**
- [ ] T052 Провести продуктовую приёмку — **заблокировано**
- [x] T084 Ограничить размер и время приёма API-запросов
- [x] T085 Проверять Host и Origin запросов записи
- [x] T086 Добавить безопасную диагностику HTTP и readiness
- [x] T087 Очищать неиспользуемые raw-файлы с защитой публикации
- [x] T088 Сохранять согласованную SQLite-копию с raw-файлами
- [x] T089 Восстанавливать копию в новое SQLite-окружение
- [x] T101 Не перезаписывать назначение при конкурентном restore
- [x] T118 Reject readiness when database revision is incompatible
- [x] T120 Reject ambiguous JSON request documents
- [x] T121 Bound and redact validation error responses
- [x] T122 Fail closed on invalid environment and production settings
- [x] T123 Bound PostgreSQL connection establishment
- [x] T137 Bound JSON response consumption in the browser
- [x] T164 Isolate every PostgreSQL migration test
- [x] T165 Fail mandatory CI checks when PostgreSQL tests are absent or skipped
- [x] T166 Provide read-only redacted database diagnostics
- [x] T167 Prepare the Compose worker and shared raw volume
- [x] T168 Verify the compiled React application in the browser
- [x] T169 Verify PostgreSQL queue concurrency and worker fencing
- [x] T170 Verify atomic PostgreSQL snapshot publication
- [x] T171 Rehearse PostgreSQL and raw backup restoration
- [x] T172 Serve production assets without SPA fallback on missing chunks
- [x] T173 Verify Compose recreation persistence and worker recovery
- [x] T181 Экспортировать архивные факты отдельно от ручных расчётов
- [x] T182 Восстановить SGU-архив и подписки из PostgreSQL/raw backup
- [x] T183 Проверить архивные данные при смене гостя между вкладками
- [x] T184 Проверить текущий архивный контур в локальных контейнерах
- [x] T185 Измерить чтение573-строчного архива с20подписками
- [x] T186 Добавить offline аудит целостности архива и ключа сопоставления
- [x] T189 Проверить полный локальный путь двух источников до рубежа70%
- [x] T210 Установить причины ошибок и отмен GitHub Actions
- [x] T211 Исправить сбой мобильного браузерного сценария
- [x] T212 Устранить причины зависаний CI и Firefox
- [x] T213 Проверить исправленный workflow и диагностику
- [x] T214 Проверить зелёный удалённый запуск и передать состояние

## Резерв и выпуск

- [ ] T053 Собрать релизный кандидат и отчёт gates
- [ ] T054 Использовать резерв на исправления и повторную проверку
- [ ] T055 Выпустить MVP и передать рабочий контекст

## После MVP: аккаунты, уведомления, ИИ и следующий сезон

- [ ] T058 Добавить аккаунт и перенос гостевых направлений
- [ ] T059 Подключить внешние уведомления по подписке
- [ ] T060 Проверить реализуемость статистического прогноза
- [ ] T061 Построить baseline на временно разделённых данных
- [ ] T062 Проверить калибровку и применимость прогноза
- [ ] T063 Добавить ИИ-объяснение с контролем фактов
- [ ] T064 Пересмотреть инфраструктуру по стоимости и нагрузке
- [ ] T065 Подготовить следующий сезон приёма
