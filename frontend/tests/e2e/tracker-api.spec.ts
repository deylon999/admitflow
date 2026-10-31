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

test('потеря cookies требует явного старта новой сессии', async ({ page, context }) => {
  test.skip(process.env.E2E_API !== '1', 'Требуется настоящий API');
  await page.goto('/tracker');
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  await context.clearCookies();
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Срок гостевой сессии истёк' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Начать новую сессию' }).click();
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
});

test('удаление всех данных требует подтверждения и очищает направления', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Требуется настоящий API');
  await page.goto('/tracker');
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  const created = await page.request.post('/api/v1/watches', {
    headers: { 'X-Requested-With': 'abiturient' },
    data: { university: 'Тестовый вуз', title: 'Удаление данных', sourceUrl: 'https://example.org/list', values: { rank: 10, seats: 5, excluded: 0, noConsent: 0 } },
  });
  expect(created.status()).toBe(201);
  await page.reload();
  await page.getByRole('button', { name: 'Удалить все мои данные' }).click();
  await page.getByRole('button', { name: 'Отмена' }).click();
  await expect(page.getByRole('heading', { name: 'Удаление данных' })).toBeVisible();
  await page.getByRole('button', { name: 'Удалить все мои данные' }).click();
  await page.getByRole('button', { name: 'Удалить всё', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
});
