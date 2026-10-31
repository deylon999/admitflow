import { expect, test } from '@playwright/test';

test('форма показывает корректный расчёт и отклоняет невозможные группы', async ({ page }) => {
  // Isolate the form from API availability; CRUD is tested separately against the API.
  await page.route('**/api/v1/session', route => route.fulfill({ status: 204 }));
  await page.route('**/api/v1/watches', route => route.fulfill({ json: [] }));
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  await expect(page.locator('.tracker-preview')).toHaveCount(0);
  await page.getByLabel('Вуз', { exact: true }).fill('Тестовый вуз');
  await page.getByLabel('Направление и конкурсная группа').fill('Информатика');
  await page.getByLabel('Ссылка на конкурсный список').fill('https://example.org/list');
  await page.getByLabel('Ваш номер в списке').fill('120');
  await page.getByLabel('Бюджетных мест').fill('90');
  await page.getByLabel('Выше вас вне общего конкурса').fill('30');
  await page.getByLabel('Выше вас без согласия на зачисление').fill('16');
  await expect(page.locator('.tracker-preview strong')).toHaveText('74 из 90');
  await page.getByLabel('Выше вас без согласия на зачисление').fill('90');
  await page.getByRole('button', { name: 'Сохранить направление' }).click();
  await expect(page.locator('#tracker-calculation-error')).toContainText('меньше вашего номера');
  await expect(page.locator('.tracker-preview')).toHaveCount(0);
});
