# B11 —30 задач,2026-11-03

Основа2c866bd, clean Git. Шесть подходов по5; отдельный Conventional Commit/acceptance/evidence на задачу. Первые5: T019,T007,T008,T013,T027. Дальнейший выбор по реальным зависимостям/оригиналам; release gates не сокращаются. Все source original bytes приватны в ignored backend/var, реальные публичные ID в Git не добавляются.

Новое основание исследований: capture СГУПС1348 успешен, attested=false/archive2026. Capture СГУ4588 отказал response_too_large; отдельное офлайн-исследование ограничено20MiB, production limit5MiB не меняется. Предыдущий preview остановлен вне этой сессии; новый изолированный admitflow-b11/8090 поднимается из B10 images, пользовательские volumes не переиспользуются.

## 1/30 T019

Ручная приёмка сведена в manual-acceptance.md. Текущий targeted Chromium10/10 на новом PostgreSQL/nginx8090,exit0; предыдущие native restart/ownership/limits/replay доказательства проверены и применимы к неизменённому коду. Не реализованные automatic карточки не закрыты. Плановые deliverables исправлены на реальные файлы тестов.
