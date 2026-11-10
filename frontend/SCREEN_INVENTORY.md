# Реализованные маршруты AdmitFlow

| Страница | URL | Статус |
|---|---|---|
| Лендинг | `/` | Реализован |
| Каталог вузов | `/universities` | Реализован |
| Вуз СГУ | `/universities/sgu-saratov` | Реальный API, стабильный ID |
| Каталог программ | `/programs` | Реализован |
| Страница программы | `/programs/sgu-2026-4588` | Реальный API, кампания 2026 |
| Аналитика ЕГЭ | `/ege-analytics` | Нет feature API; opt-in demo, без серверного успеха |
| Как работает прогноз | `/how-it-works` | Реализован |
| FAQ | `/faq` | Реализован |
| Вход | `/auth/login` | Нет feature API; opt-in demo, без серверного успеха |
| Регистрация | `/auth/register` | Нет feature API; opt-in demo, без серверного успеха |
| Восстановление | `/auth/recovery` | Нет feature API; opt-in demo, без серверного успеха |
| Обзор кабинета | `/app` | Live subscriptions; явный гостевой доступ |
| Профиль | `/app/profile` | Нет feature API; opt-in demo, без серверного успеха |
| Ввод баллов/прогноз | `/app/forecast` | Нет feature API; opt-in demo, без серверного успеха |
| Результат прогноза | `/app/forecast/example` | Нет feature API; opt-in demo, без серверного успеха |
| Объяснение прогноза | `/app/forecast/method` | Нет feature API; opt-in demo, без серверного успеха |
| Трекер направлений | `/app/watchlist` | Live subscriptions; localStorage только в opt-in demo |
| Добавить направление | `/app/watchlist/add` | Live groups → lookup → подтверждение подписки |
| Конкурсный список | `/app/competitions/mtuci-se` | Live ID lookup/не найдено; demo только при opt-in |
| Анализ конкуренции | `/app/competitions/mtuci-se/competitors` | Нет feature API; opt-in demo, без серверного успеха |
| Сравнение | `/app/compare` | Нет feature API; opt-in demo, без серверного успеха |
| История | `/app/history` | Live private changes; loading/empty/error/retry |
| Уведомления | `/app/notifications` | Live private changes, без вымышленных событий |
| Настройки | `/app/settings` | Нет feature API; opt-in demo, без серверного успеха |
| Источники данных | `/app/sources` | Live coverage, архив отдельно от свежего импорта |
| Пустое состояние | `/app/states/empty` | Нет feature API; opt-in demo, без серверного успеха |
| Ошибка данных | `/app/states/error` | Нет feature API; opt-in demo, без серверного успеха |
| Успешное сохранение | `/app/states/success` | Нет feature API; opt-in demo, без серверного успеха |
| 404 | `/not-found` | Реализован |

**29 URL в комплекте, включая 4 сценарных/ошибочных и 3 страницы авторизации.**

Все страницы открываются в React-приложении. Устаревшие статические HTML-превью
удалены; эталон дизайна хранится в исходном sibling-проекте и Git-истории.
Каталог поддерживает динамические ID; остальные demo-маршруты v3 сохранены.

S202: все 29 исходных URL сохранены. Дополнительный алиас списка конкурсов: /app/competitions; детали используют настоящий subscription ID. Матрица: docs/evidence/v3-production-api.md.
