import { expect, test } from '@playwright/test';

for (const theme of ['light', 'dark']) test(`long manual card remains usable at320px in ${theme} theme`, async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.setViewportSize({ width: 320, height: 780 });
  await page.addInitScript(value => localStorage.setItem('abiturient-theme', value), theme);
  await page.goto('/tracker');
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  const response = await page.request.post('/api/v1/watches', { headers: { 'X-Requested-With': 'abiturient' }, data: { university: 'У'.repeat(160), title: 'Н'.repeat(200), sourceUrl: 'https://example.org/list', values: { rank: 1_000_000, seats: 1_000_000, excluded: 0, noConsent: 0 } } });
  expect(response.status()).toBe(201);
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-theme', theme);
  await expect(page.locator('.direction-result strong')).toHaveText('1000000');
  const card = page.locator('.direction-card');
  await expect(card.getByRole('heading')).toHaveText('Н'.repeat(200));
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(await card.locator('.direction-result strong').evaluate(node => {
    const rect = node.getBoundingClientRect();
    return rect.left >= 0 && rect.right <= innerWidth && node.scrollWidth <= node.clientWidth;
  })).toBe(true);
  await card.getByRole('button', { name: 'История', exact: true }).click();
  await expect(card.getByRole('region', { name: /История/ })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await card.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
  await expect(page.getByLabel('Ваш номер в списке')).toHaveValue('1000000');
  await expect(page.getByRole('button', { name: 'Сохранить обновление', exact: true })).toBeVisible();
  const overflow = await page.evaluate(() => Array.from(document.querySelectorAll('main *')).filter(node => node.getBoundingClientRect().right > innerWidth && !node.closest('.history-scroll')).slice(0, 8).map(node => ({ tag: node.tagName, class: node.className, width: node.getBoundingClientRect().width })));
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), JSON.stringify(overflow)).toBe(true);
});
