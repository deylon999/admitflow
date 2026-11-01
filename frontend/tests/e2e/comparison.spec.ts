import { expect, test } from '@playwright/test';

for (const width of [390, 1440]) {
  test(`сравнение разных конкурсов обновляется после удаления (${width})`, async ({ page }) => {
    test.skip(process.env.E2E_API !== '1', 'Требуется API');
    await page.setViewportSize({ width, height: 900 });
    await page.goto('/tracker');
    await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
    for (let i = 1; i <= 4; i++) {
      const response = await page.request.post('/api/v1/watches', { headers: { 'X-Requested-With': 'abiturient' }, data: {
        university: `University ${i}`, title: `Group ${i}`, sourceUrl: 'https://example.org/list', values: { rank: i * 20, seats: 30, excluded: 0, noConsent: 5 },
      } });
      expect(response.status()).toBe(201);
    }
    await page.reload();
    await page.getByText('Сравнить направления', { exact: true }).click();
    for (let i = 1; i <= 3; i++) await page.getByRole('checkbox', { name: `University ${i} · Group ${i}` }).check();
    await expect(page.getByRole('checkbox', { name: 'University 4 · Group 4' })).toBeDisabled();
    const table = page.getByRole('table', { name: 'Сравнение ручных направлений' });
    await expect(table.getByRole('columnheader')).toHaveCount(4);
    await expect(table).toContainText('Сохранено вручную');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const card = page.locator('.direction-card').filter({ has: page.getByRole('heading', { name: 'Group 2', exact: true }) });
    await card.getByRole('button', { name: 'Удалить', exact: true }).click();
    await card.getByRole('button', { name: 'Да, удалить' }).click();
    await expect(table.getByRole('columnheader')).toHaveCount(3);
    await expect(table).not.toContainText('University 2');
    await expect(page.getByRole('checkbox', { name: 'University 4 · Group 4' })).toBeEnabled();
  });
}
