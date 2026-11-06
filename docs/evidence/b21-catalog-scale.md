# B21/T225 — каталог со101 филиалом

Исправлена F06. На исходном B20 dist100 global branch facets принимались,
а101 отклонял весь корректный каталог, даже при маленькой странице.
Backend возвращает эти фильтры до ограничения/фильтрации списка групп.

Frontend теперь допускает до20_000 филиалов — в соответствии с бюджетом
reviewed profile catalog MAX_PROFILES. Это предел проверки ресурса, а не
заявление о фактически подключённых филиалах. Лимит50 групп на странице,
проверки полей, сезонов и общий transport bound10MiB сохранены. Backend
по-прежнему возвращает global facets; его данные и API не менялись.

Проверено2026-11-06:

- `npx vitest run tests/source-contracts.test.ts`:20 passed,exit0.
  Допуск101/20_000, отказ20_001 и семь некорректных branch payloads.
- `npx playwright test tests/e2e/source-catalog.spec.ts --grep "101 global" --project=chromium --project=firefox --reporter=line`:
  2 passed,без skips,exit0. Карточки50→100→101, затем выбор101-го филиала
  даёт одну карточку при сохранении всех global filters.
- Общий `npm test`:136 passed; build, scoped Prettier и diff check:exit0.

Env:CI=1,E2E_SERVER=external,E2E_BASE_URL=http://127.0.0.1:5283;
отдельный API8033 и synthetic responses. Национальный охват не увеличен.
