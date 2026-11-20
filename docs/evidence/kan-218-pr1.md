# KAN-218 PR1: проверка архитектуры и идентичности

Работа начата 2026-11-20, проверка продолжена 2026-11-21.
База `main@e121d5d`. Архитектура и конкретные границы:
[KAN-218-ARCHITECTURE.md](../KAN-218-ARCHITECTURE.md).

Первый этап: отдельные identity helpers и Program/M:N хранение. Новых
подключённых официальных источников и публичных программ — **0**. Публикация
каталога по-прежнему ограничена двумя reviewed scopes СГУ 2026. Это не
достижение цели 2027, не финальный отчёт KAN-218 и не приёмка release gate.

## Проверки хранения

Команда из корня:

```text
python scripts/test_postgres.py --python backend/.venv/Scripts/python.exe tests/test_catalog_identity.py tests/test_program_identity_storage.py tests/test_migrations.py tests/test_migration_metadata.py tests/test_database_diagnostics.py
```

**88 passed, 0 skipped, 26.16s, exit0**. Native PostgreSQL17-alpine, собственный
disposable контейнер, случайные schemas; штатный runner останавливает свой
контейнер. Рабочая БД/volumes не использовались.

Проверены заполненная0012→0013, metadata alignment, повтор upgrade/import,
сохранение строк источников/персональных snapshots и pointers (всё synthetic),
M:N и standalone, cross-year continuity только явной связью, отказ чужого
вуза/филиала/уровня/кампании, duplicate natural identity, rollback, RESTRICT.
API проверен настоящим FastAPI TestClient с nativePG и теми же двумя СГУ.

Дополнительно: frontend `npm run typecheck`, `npm run lint`, `npm run build`
из `frontend/` — exit0. Публичный DTO, дизайн, авторизация и workflows сохранены.

Два промежуточных88-case прогона:87 passed/1 failed из-за предпосылок нового
теста; история и исправления приведены в архитектурном документе. CI и полный
прогон здесь ещё не заявлены; результаты будут добавлены перед передачей PR.
