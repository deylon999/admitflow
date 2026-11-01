import { expect, test } from '@playwright/test';

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
