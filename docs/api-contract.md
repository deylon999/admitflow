# Контракт API v1

Same-origin `/api/v1`, JSON camelCase, даты ISO 8601 с явной timezone. GET не изменяет пользовательские данные. Все записи требуют X-Requested-With: abiturient. 204 не содержит JSON. 401 означает утрату гостевого доступа, 404 — отсутствующее или чужое направление, 409 — лимит, 422 — невалидный ввод. Ошибки имеют detail; массив валидации преобразуется в безопасное сообщение интерфейса.

## Реализовано

- POST/GET/DELETE session: создание, expiry, явное удаление. После 401 нельзя автоматически повторять создание или запись. Cookie Path=/api, HttpOnly, SameSite=Lax.
- GET universities?q=: items/total, максимум 50, только manual coverage в текущей версии. Всего в стартовом наборе 2 исследованных вуза.
- GET/POST watches: максимум 20 на владельца. GET detail содержит последние 100 снимков; latest совпадает с первой записью history. История не означает время обновления официального источника.
- POST snapshots: новая запись, исходная история сохраняется. DELETE watch удаляет только свою запись с каскадом истории.
- Snapshot: sourceKind=manual, modelVersion=manual-v1. Входы — четыре целых числа. Клиент перепроверяет диапазоны и совпадение place/worstPlace/seats/state с расчётом, не доверяет одному TypeScript cast. Некорректный response вызывает ошибку и не отображается как надёжные числа.

Общий пример shared/manual-watch.json проверяется против настоящего FastAPI-ответа и frontend parser. Это защита от несовместимого изменения DTO. URL с credentials и неподдержанные протоколы не принимаются. Даты без timezone не принимаются frontend.

## Следующий автоматический контракт

Automatic/archive пока не реализованы и не маскируются под manual. Будущий DTO должен включать mode, campaign/group/source, fetchedAt, sourceUpdatedAt (nullable), assessedAt, rulesVersion, quality, freshness и assumptions. Архив определяется происхождением, не возрастом HTTP-запроса. Unsupported и insufficient_data не содержат выдуманного place/процента. До реализации отдельного parser неизвестные sourceKind/modelVersion отклоняются.

GET может повторяться при сетевой ошибке; операции записи автоматически не повторяются. Идемпотентность и конкурентные лимиты — T017, пока не подтверждены. Массовый каталог потребует cursor/limit; не выдавать текущий лимит 50 за национальную пагинацию.
