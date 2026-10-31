import { expect, test } from '@playwright/test';

test('реальный API: создать, обновить, прочитать историю, удалить', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Требуется API на 127.0.0.1:8000 и E2E_API=1');
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  await page.getByLabel('Вуз', { exact: true }).fill('Тестовый вуз');
  await page.getByLabel('Направление и конкурсная группа').fill('Проверка сквозного пути');
  await page.getByLabel('Ссылка на конкурсный список').fill('https://example.org/list');
  await page.getByLabel('Ваш номер в списке').fill('120');
  await page.getByLabel('Бюджетных мест').fill('90');
  await page.getByLabel('Выше вас вне общего конкурса').fill('30');
  await page.getByLabel('Выше вас без согласия на зачисление').fill('16');
  await page.getByRole('button', { name: 'Сохранить направление' }).click();
  await expect(page.locator('.direction-result strong')).toHaveText('74');
  await page.reload();
  await expect(page.locator('.direction-result strong')).toHaveText('74');
  await page.getByRole('button', { name: 'Обновить цифры' }).click();
  await page.getByLabel('Выше вас без согласия на зачисление').fill('0');
  await page.getByRole('button', { name: 'Сохранить обновление' }).click();
  await expect(page.locator('.direction-result strong')).toHaveText('90');
  await page.getByRole('button', { name: 'История' }).click();
  await expect(page.locator('.direction-history tbody tr')).toHaveCount(2);
  await page.getByRole('button', { name: 'Удалить', exact: true }).click();
  await page.getByRole('button', { name: 'Да, удалить' }).click();
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
});
