import { expect, test } from '@playwright/test';

test('filtered print media exports only selected real manual records to PDF', async ({ page, browserName }, info) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  test.skip(browserName !== 'chromium', 'page.pdf works only in headless Chromium; print CSS is shared');
  await page.goto('/tracker');
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  for (const title of ['Keep this direction', 'Excluded from print']) {
    const response = await page.request.post('/api/v1/watches', { headers: { 'X-Requested-With': 'abiturient' }, data: { university: 'Print University', title, sourceUrl: `https://example.org/${title.startsWith('Keep') ? 'selected' : 'excluded'}`, values: { rank: 120, seats: 90, excluded: 30, noConsent: 16 } } });
    expect(response.status()).toBe(201);
  }
  await page.reload();
  await page.locator('#watch-search').fill('Keep this');
  await expect(page.locator('.direction-card')).toHaveCount(1);
  await page.evaluate(() => {
    (window as unknown as { prints: number }).prints = 0;
    window.print = () => { (window as unknown as { prints: number }).prints++; };
  });
  await page.getByRole('button', { name: 'Распечатать выбранный список (1)', exact: true }).click();
  await expect.poll(() => page.evaluate(() => (window as unknown as { prints: number }).prints)).toBe(1);
  await page.emulateMedia({ media: 'print' });
  const report = page.getByRole('region', { name: 'Отчёт ручных сценариев' });
  await expect(report).toBeVisible();
  await expect(report.locator('article')).toHaveCount(1);
  await expect(report).toContainText('Keep this direction');
  await expect(report).not.toContainText('Excluded from print');
  await expect(report).toContainText('https://example.org/selected');
  await expect(report).toContainText('не является вероятностью');
  await expect(report).toContainText('manual-v1');
  await expect(page.getByRole('banner')).toBeHidden();
  await expect(page.locator('.tracker-data-actions')).toBeHidden();
  await expect(page.locator('.import-data')).toBeHidden();
  await expect(report.locator('button, input, select')).toHaveCount(0);
  const pdf = await page.pdf({ path: info.outputPath('filtered-report.pdf'), format: 'A4', printBackground: true });
  expect(pdf.subarray(0, 4).toString()).toBe('%PDF');
  expect(pdf.byteLength).toBeGreaterThan(1000);
  await report.screenshot({ path: process.env.RECORD_EVIDENCE === '1' ? '../docs/evidence/manual-report.png' : info.outputPath('filtered-report.png') });
});

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
