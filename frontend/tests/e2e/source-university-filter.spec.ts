import { expect, test } from '@playwright/test';

test.beforeEach(() =>
  test.skip(process.env.E2E_API !== '1', 'Requires the packaged national directory API'),
);

test('source university filter loads beyond fifty, searches the full directory and retains its choice', async ({
  page,
}) => {
  const second = await (await page.request.get('/api/v1/universities?q=&offset=50')).json();
  const target = second.items[0];
  await page.goto('/sources');
  const select = page.getByLabel('Вуз', { exact: true });
  await expect(select.locator('option')).toHaveCount(51);
  await page.getByRole('button', { name: 'Показать ещё вузы' }).click();
  await expect(select.locator('option')).toHaveCount(101);
  await select.selectOption(target.id);
  await page.getByLabel('Поиск вуза', { exact: true }).fill('nonexistent-directory-filter');
  await expect(page.getByText('Найдено вузов: 0. Показано: 0.', { exact: true })).toBeVisible();
  await expect(select).toHaveValue(target.id);
  await page.getByLabel('Поиск вуза', { exact: true }).fill(target.id);
  await expect(page.getByText('Найдено вузов: 1. Показано: 1.', { exact: true })).toBeVisible();
  await expect(select).toHaveValue(target.id);
  await expect(select.locator('option')).toHaveCount(2);
  await select.selectOption('');
  await select.focus();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await expect(select).toHaveValue(target.id);
  await expect(select).toBeFocused();
});

test('failed next directory page keeps the selection and retries at320px', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 900 });
  let fail = true;
  await page.route('**/api/v1/universities?*', (route) => {
    const url = new URL(route.request().url());
    return fail && url.searchParams.get('offset') === '50'
      ? route.fulfill({ status: 503, json: { detail: 'Unavailable' } })
      : route.continue();
  });
  await page.goto('/sources');
  const select = page.getByLabel('Вуз', { exact: true });
  await expect(select.locator('option')).toHaveCount(51);
  const selected = await select.locator('option').nth(1).getAttribute('value');
  await select.selectOption(selected!);
  await page.getByRole('button', { name: 'Показать ещё вузы' }).click();
  await expect(page.getByRole('alert')).toContainText('Выбор сохранён');
  await expect(select).toHaveValue(selected!);
  await expect(select.locator('option')).toHaveCount(51);
  fail = false;
  await page.getByRole('button', { name: 'Повторить загрузку вузов' }).click();
  await expect(select.locator('option')).toHaveCount(101);
  await expect(select).toHaveValue(selected!);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
