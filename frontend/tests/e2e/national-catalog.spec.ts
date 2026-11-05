import { expect, test } from '@playwright/test';

for (const width of [390, 1440]) test(`national directory pages through real API without substituting registry card for a list (${width})`, async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Requires real API and packaged national directory');
  await page.setViewportSize({ width, height: 900 });
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  await page.getByLabel('Вуз', { exact: true }).focus();
  await expect(page.locator('.catalog-option')).toHaveCount(50);
  await page.getByRole('button', { name: 'Показать ещё вузы' }).click();
  await expect(page.locator('.catalog-option')).toHaveCount(100);
  await page.getByLabel('Вуз', { exact: true }).fill('Саратовская Чернышевского');
  await expect(page.locator('.catalog-results')).toContainText('Филиал');
  const branch = page.locator('.catalog-option').filter({ hasText: 'Филиал' }).first();
  await expect(branch).toBeVisible();
  if (width === 390) {
    await page.getByLabel('Вуз', { exact: true }).scrollIntoViewIfNeeded();
    await page.screenshot({ path: '../docs/evidence/national-catalog-mobile.png' });
  }
  await branch.click();
  await expect(page.getByLabel('Ссылка на конкурсный список')).toHaveValue('');
  await expect(page.getByLabel('Вуз', { exact: true })).not.toHaveValue('');
  await expect(page.locator('.catalog-results')).toHaveCount(0);
});
