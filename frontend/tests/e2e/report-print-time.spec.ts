import { openTrackerPanel } from './helpers/tracker';
import { expect, test } from '@playwright/test';

test('browser beforeprint commits the current report time before returning', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  const opened = Date.now();
  await page.clock.setFixedTime(opened);
  await page.goto('/tracker');
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  const created = await page.request.post('/api/v1/watches', {
    headers: { 'X-Requested-With': 'abiturient' },
    data: {
      university: 'Print clock university',
      title: 'Print clock direction',
      sourceUrl: 'https://example.org/print-time',
      values: { rank: 10, seats: 20, excluded: 0, noConsent: 0 },
    },
  });
  expect(created.status()).toBe(201);
  await page.reload();
  await expect(page.locator('.direction-card')).toHaveCount(1);
  const reportTime = page.locator('.print-report > p').first();
  await expect(reportTime).toContainText(new Date(opened).toISOString());
  for (const minutes of [10, 11]) {
    const now = opened + minutes * 60_000;
    await page.clock.setFixedTime(now);
    const captured = await page.evaluate(() => {
      window.dispatchEvent(new Event('beforeprint'));
      // Native print reads the DOM immediately after the event, before another React render.
      return document.querySelector('.print-report > p')?.textContent;
    });
    expect(captured).toContain(new Date(now).toISOString());
    expect(captured).toContain('Направлений: 1.');
  }
  await page.clock.setFixedTime(opened + 12 * 60_000);
  await page.evaluate(() => {
    window.print = () => {
      document.documentElement.dataset.printedReportTime =
        document.querySelector('.print-report > p')?.textContent ?? '';
    };
  });
  await openTrackerPanel(page, 'export');
  await page.getByRole('button', { name: 'Распечатать выбранный список (1)', exact: true }).click();
  await expect(page.locator('html')).toHaveAttribute(
    'data-printed-report-time',
    new RegExp(new Date(opened + 12 * 60_000).toISOString().replaceAll('.', '\\.')),
  );
});
