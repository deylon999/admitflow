# Скриншоты аудита

Все PNG сняты Playwright с локально запущенного AdmitFlow и синтетическими данными.
Дата 2026-11-08. Файлы не являются макетами или изображениями из генератора.

| Файл | Среда и содержание |
| --- | --- |
| [session-cache-before.png](screenshots/session-cache-before.png) | Chromium, старая версия: reset новой сессии + 503 на чтение; интерфейс ошибочно показывает старый cache как «последние сохранения». |
| [session-cache-after.png](screenshots/session-cache-after.png) | Chromium, исправление: тот же управляемый 503, старые карточки отсутствуют; показана ошибка с повтором. Снимок fullPage, проверен визуально. |
| [draft-before.png](screenshots/draft-before.png) | Chromium, сбой: возвращённое к исходному значению поле остаётся в черновике. Это screenshot падения регрессии; наличие draft подтверждается DOM/assertion. |
| [tracker-390.png](screenshots/tracker-390.png) | Chromium, 390 px, ручной трекер с реальным SQLite API, после исправлений. Пустое состояние, покрытие и предупреждение видны; горизонтального overflow нет. |
| [tracker-1440.png](screenshots/tracker-1440.png) | Chromium, 1440 px, тот же путь. Сверено визуально. |

WebKit-дефект выбора вуза и дефект фокуса подтверждены браузерными assertions и
trace. Статичный PNG не может доказать получателя фокуса; для этого приведены
сравнения до/после в BUG_REPORT.md и FIX_REPORT.md. Данных настоящих абитуриентов
на снимках нет.
