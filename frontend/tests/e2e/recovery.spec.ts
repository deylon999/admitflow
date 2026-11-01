import { expect, test } from '@playwright/test';
import fixture from '../../../shared/manual-watch.json' with { type: 'json' };

test('ошибка чтения 503 позволяет повторить загрузку без создания записей', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Требуется API');
  let failed = true;
  await page.route('**/api/v1/watches', route => failed && route.request().method() === 'GET'
    ? route.fulfill({ status: 503, json: { detail: 'Источник временно недоступен.' } }) : route.continue());
  await page.goto('/tracker');
  await expect(page.getByRole('heading', { name: 'Не удалось загрузить направления' })).toBeVisible();
  failed = false;
  await page.getByRole('button', { name: 'Повторить', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
});

test('ошибка следующей страницы не скрывает уже загруженную историю', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Требуется API');
  await page.route('**/api/v1/watches', route => route.fulfill({ json: [fixture] }));
  let failed = true;
  const items = Array.from({ length: 150 }, (_, i) => ({ ...fixture.latest, id: `row-${String(150-i).padStart(4, '0')}` }));
  await page.route('**/api/v1/watches/*/history*', route => {
    const next = new URL(route.request().url()).searchParams.has('before');
    if (next && failed) return route.fulfill({ status: 503, json: { detail: 'Временная ошибка страницы.' } });
    return route.fulfill({ json: next ? { items: items.slice(100), nextCursor: null } : { items: items.slice(0, 100), nextCursor: items[99].id } });
  });
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'История', exact: true }).click();
  await expect(page.locator('.direction-history tbody tr')).toHaveCount(100);
  await page.getByRole('button', { name: 'Загрузить ещё', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Повторить загрузку истории' })).toBeVisible();
  await expect(page.locator('.direction-history tbody tr')).toHaveCount(100);
  failed = false;
  await page.getByRole('button', { name: 'Повторить загрузку истории' }).click();
  await expect(page.locator('.direction-history tbody tr')).toHaveCount(150);
  await expect(page.getByRole('button', { name: 'Загрузить ещё', exact: true })).toHaveCount(0);
});
