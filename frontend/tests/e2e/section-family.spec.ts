import { expect, test } from '@playwright/test';

test.beforeEach(() =>
  test.skip(
    process.env.E2E_SECTION_FAMILY !== '1',
    'Requires the reviewed MIEPP/UIFR archive scopes',
  ),
);

for (const [university, count] of [
  ['miccedu-1881', 4],
  ['miccedu-110420', 7],
] as const) {
  test(`reviewed sections remain separate dated contract groups: ${university}`, async ({
    page,
  }) => {
    await page.goto('/sources');
    await page.getByLabel('Вуз', { exact: true }).selectOption(university);
    const cards = page.locator('.source-catalog-card');
    await expect(cards).toHaveCount(count);
    for (const card of await cards.all()) {
      await expect(card).toContainText('Архив 2026 года');
      await expect(card).toContainText('Платное обучение');
      await expect(card).toContainText('числовой сценарий не подключён');
      await expect(card.getByRole('button', { name: 'Найти свою запись' })).toBeVisible();
    }
    if (university === 'miccedu-1881') {
      await page.getByLabel('Группа или направление', { exact: true }).fill('Юриспруденция');
      await expect(cards).toHaveCount(2);
      await expect(cards.locator('p').filter({ hasText: /^Заочная форма ·/u })).toHaveCount(1);
      await expect(cards.locator('p').filter({ hasText: /^Очная форма ·/u })).toHaveCount(1);
      const links = await cards
        .locator('a[href*="competition/"]')
        .evaluateAll((nodes) => nodes.map((node) => (node as HTMLAnchorElement).href));
      expect(new Set(links).size).toBe(1);
    }
  });
}
