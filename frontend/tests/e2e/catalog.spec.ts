import { expect, test } from '@playwright/test';

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
