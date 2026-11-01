import { expect, test } from '@playwright/test';
import fixture from '../../../shared/manual-watch.json' with { type: 'json' };
import { calculatePlace } from '../../src/lib/calculator';

test.beforeEach(async ({ page }) => {
  await page.route('**/api/v1/session', route => route.request().method() === 'GET' ? route.fulfill({ json: { expiresAt: '2026-12-01T00:00:00Z' } }) : route.fulfill({ status: 204 }));
});

test('можно сравнить любые два загруженных сохранения', async ({ page }) => {
  const items = [120,130,150].map((rank,index) => {
    const values = { ...fixture.latest.values, rank };
    return { ...fixture.latest, id: `snapshot-${3-index}`, values, calculation: calculatePlace(values) };
  });
  await page.route('**/api/v1/watches', route => route.fulfill({ json: [fixture] }));
  await page.route('**/api/v1/watches/*/history*', route => route.fulfill({ json: { items, nextCursor: null, total: 3 } }));
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'История', exact: true }).click();
  await expect(page.getByText('Сохранено 3 из 500. Осталось обновлений: 497.')).toBeVisible();
  await expect(page.locator('.direction-history tbody tr').first().locator('td')).toHaveCount(8);
  await expect(page.locator('.direction-history tbody tr').first()).toContainText('manual-v1');
  await expect(page.locator('.direction-history time').first()).toContainText(fixture.latest.capturedAt);
  await expect(page.locator('.history-comparison strong')).toHaveText('Место: 84 → 74');
  await page.getByLabel('Более раннее сохранение', { exact: true }).selectOption('snapshot-1');
  await expect(page.locator('.history-comparison strong')).toHaveText('Место: 104 → 74');
  await page.getByLabel('Новое сохранение', { exact: true }).selectOption('snapshot-2');
  await expect(page.locator('.history-comparison strong')).toHaveText('Место: 104 → 84');
});

test('поиск, фильтр и порядок не удаляют направления', async ({ page }) => {
  await page.route('**/api/v1/watches', route => route.fulfill({ json: [fixture, { ...fixture, id: 'second', university: 'Другой вуз' }] }));
  await page.goto('/tracker');
  await expect(page.locator('.direction-card')).toHaveCount(2);
  await page.locator('#watch-search').fill('другой');
  await expect(page.locator('.direction-card')).toHaveCount(1);
  await page.locator('#watch-state').selectOption('out');
  await expect(page.getByRole('heading', { name: 'Поиск не дал результатов' })).toBeVisible();
  await page.getByRole('button', { name: 'Сбросить поиск и фильтры' }).click();
  await expect(page.locator('.direction-card')).toHaveCount(2);
  await page.locator('#watch-order').selectOption('university');
  await expect(page.locator('.direction-top .eyebrow').first()).toHaveText('Другой вуз');
});

test('печатный отчёт содержит источник и допущения, без кнопок', async ({ page }) => {
  await page.route('**/api/v1/watches', route => route.fulfill({ json: [fixture] }));
  await page.goto('/tracker');
  await page.evaluate(() => { window.print = () => {}; });
  await page.getByRole('button', { name: /Распечатать выбранный/ }).click();
  await page.emulateMedia({ media: 'print' });
  await expect(page.locator('.print-report')).toBeVisible();
  await expect(page.locator('.print-report')).toContainText(fixture.sourceUrl);
  await expect(page.locator('.print-report')).toContainText('не гарантирует зачисление');
  await expect(page.locator('.print-report')).toContainText('manual-v1');
  await expect(page.locator('.tracker-page-heading')).toBeHidden();
});
