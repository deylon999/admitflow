import { expect, test } from '@playwright/test';

for (const width of [390, 1440]) {
  test(`audit capture of manual tracker at ${width}px`, async ({ page }) => {
    test.skip(process.env.E2E_API !== '1', 'Requires the isolated local API');
    await page.setViewportSize({ width, height: 900 });
    await page.goto('/tracker');
    await expect(page.getByRole('heading', { name: 'Мои направления' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.screenshot({ path: `../audit/screenshots/tracker-${width}.png`, fullPage: true });
    await page.request.delete('/api/v1/session', { headers: { 'X-Requested-With': 'abiturient' } });
  });
}
