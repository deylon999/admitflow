# AdmitFlow

React/TypeScript-интерфейс v3 и FastAPI/PostgreSQL backend. Дизайн v3 —
визуальный эталон. Все 29 маршрутов сохраняются. Реально подключены каталог
вузов, страница вуза, каталог направлений и страница направления; остальные
разделы пока демонстрационные. ML не подключена.

Каталог использует датированный справочник MICCEDU и два проверенных архивных
конкурса СГУ 2026. Неизвестные проходные и требования ЕГЭ не выдумываются.

Запуск и явный импорт metadata: [catalog-runbook](docs/catalog-runbook.md).
Для frontend из `frontend/`: `npm ci`, `npm run dev`, localhost:5173.
API proxy по умолчанию localhost:8000; адрес задаётся `API_PROXY_TARGET`.
Для локальной изолированной проверки предусмотрен `node scripts/test-api.mjs`
с временной SQLite; это не замена native PostgreSQL-проверке.

Проверки из frontend: `npm run typecheck`, `npm run lint`, `npm run build`,
`npm test`. Полное сравнение с read-only sibling: `npm run test:visual`.
Нужны backend requirements-dev и установленный Chromium.

- [Текущая архитектура](docs/ARCHITECTURE.md)
- [API и удалённые старые endpoints](docs/API.md)
- [KEEP / REFACTOR / DELETE и план сохранности данных](docs/foundation-cleanup-audit.md)
- [Результаты очистки и ограничения инфраструктуры](docs/evidence/foundation-cleanup.md)
- [Состояние и задачи](docs/STATE.md)

PostgreSQL через Compose и Docker smoke не подтверждены в текущем sandbox:
доступ к Docker Engine запрещён. Данные и миграции не удалялись.
Документация прежнего ручного продукта находится в
[архиве](docs/archive/readme-before-foundation.md), код — в Git-истории.
