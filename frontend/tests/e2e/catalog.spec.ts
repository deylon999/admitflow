import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.route('**/api/v1/subscriptions', route => route.fulfill({ json: [] }));
  await page.route('**/api/v1/direction-budget', route => route.fulfill({ json: { limit: 20, total: 0, manualCount: 0, archiveCount: 0 } }));
});

test('university choices support arrows, Escape and Enter without losing the form', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  const input = page.getByLabel('Вуз', { exact: true });
  await input.focus();
  const options = page.locator('.catalog-option');
  await expect(options).toHaveCount(2);
  await input.press('ArrowDown');
  await expect(options.nth(0)).toBeFocused();
  await page.keyboard.press('ArrowDown');
  await expect(options.nth(1)).toBeFocused();
  await page.keyboard.press('ArrowUp');
  await expect(options.nth(0)).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(input).toBeFocused();
  await expect(options).toHaveCount(0);
  await expect(page.locator('.direction-form')).toBeVisible();
  await input.press('Tab');
  await input.focus();
  await expect(options).toHaveCount(2);
  await input.press('ArrowUp');
  await expect(options.nth(1)).toBeFocused();
  const name = await options.nth(1).locator('span').innerText();
  await page.keyboard.press('Enter');
  await expect(input).toHaveValue(name);
  await expect(input).toBeFocused();
  await expect(page.getByLabel('Ссылка на конкурсный список')).toHaveValue(/^https:\/\//);
});

test('каталог выбирает вуз с честной пометкой ручного режима', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Требуется настоящий API');
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  await page.getByLabel('Вуз', { exact: true }).fill('ЧЕРНЫШЕВСКОГО');
  const choice = page.getByRole('button', { name: /СГУ имени.*Ручной режим/ });
  await expect(choice).toBeVisible();
  await expect(page.getByRole('link', { name: 'Официальный список' })).toHaveAttribute('href', 'https://www.sgu.ru/svodka');
  await choice.click();
  await expect(page.getByLabel('Вуз', { exact: true })).toHaveValue('СГУ имени Н. Г. Чернышевского');
  await expect(page.getByLabel('Ссылка на конкурсный список')).toHaveValue('https://www.sgu.ru/svodka');
  await page.getByLabel('Вуз', { exact: true }).fill('Другой университет');
  await expect(page.getByText('Вуз пока не добавлен в справочник.', { exact: false })).toBeVisible();
  await expect(page.getByLabel('Вуз', { exact: true })).toHaveValue('Другой университет');
});

test('ошибка справочника сохраняет возможность ручного ввода', async ({ page }) => {
  await page.route('**/api/v1/session', route => route.request().method() === 'GET'
    ? route.fulfill({ json: { expiresAt: '2027-01-01T00:00:00Z' } }) : route.fulfill({ status: 204 }));
  await page.route('**/api/v1/watches', route => route.fulfill({ json: [] }));
  await page.route('**/api/v1/universities?*', route => route.fulfill({ status: 503, json: { detail: 'Unavailable' } }));
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  await page.getByLabel('Вуз', { exact: true }).fill('Название вручную');
  await expect(page.getByText('Справочник недоступен.', { exact: false })).toBeVisible();
  await expect(page.getByLabel('Вуз', { exact: true })).toHaveValue('Название вручную');
});
