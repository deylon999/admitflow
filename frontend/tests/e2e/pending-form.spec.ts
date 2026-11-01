import { expect, test } from '@playwright/test';

test('an unchanged pending edit guards links and unload until its result arrives', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.goto('/tracker');
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  const created = await page.request.post('/api/v1/watches', { headers: { 'X-Requested-With': 'abiturient' }, data: { university: 'Pending', title: 'Pending edit', sourceUrl: 'https://example.org/list', values: { rank: 10, seats: 20, excluded: 0, noConsent: 0 } } });
  expect(created.status()).toBe(201);
  await page.reload();
  await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  await page.route('**/api/v1/watches/*/snapshots', async route => { await gate; await route.continue(); });
  await page.getByRole('button', { name: 'Сохранить обновление', exact: true }).click();
  try {
    await expect(page.getByRole('status').filter({ hasText: 'Дождитесь результата' })).toBeVisible();
    await page.getByRole('link', { name: 'Абитуриент — в начало' }).click();
    await expect(page).toHaveURL(/\/tracker$/);
    await expect(page.locator('.direction-form')).toBeVisible();
    expect(await page.evaluate(() => {
      const event = new Event('beforeunload', { cancelable: true });
      window.dispatchEvent(event);
      return event.defaultPrevented;
    })).toBe(true);
  } finally { release(); }
  await expect(page.locator('.direction-form')).toHaveCount(0);
  await page.getByRole('link', { name: 'Абитуриент — в начало' }).click();
  await expect(page).toHaveURL(/\/$/);
});
