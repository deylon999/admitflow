import { expect, test } from '@playwright/test';
import fixture from '../../../shared/manual-watch.json' with { type: 'json' };

test.beforeEach(async ({ page }) => {
  await page.route('**/api/v1/session', route => route.request().method() === 'GET' ? route.fulfill({ json: { expiresAt: '2026-12-01T00:00:00Z' } }) : route.fulfill({ status: 204 }));
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
