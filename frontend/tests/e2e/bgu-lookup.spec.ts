import { expect, test } from '@playwright/test';

test('minimal BGU code finds and saves once without persisting code or asking for other identifier parts', async ({
  page,
}) => {
  test.skip(process.env.E2E_BGU_FIXTURE !== '1', 'Requires the separate synthetic BGU fixture API');
  await page.goto('/tracker');
  await expect(page.getByRole('button', { name: 'Добавить первое направление' })).toBeVisible();
  const storageBefore = await page.evaluate(() => ({
    local: { ...localStorage },
    session: { ...sessionStorage },
  }));
  await page.goto('/sources');
  await page.getByLabel('Вуз', { exact: true }).selectOption('miccedu-12');
  const card = page.locator('.source-catalog-card');
  await expect(card).toHaveCount(1);
  await card.getByRole('button', { name: 'Найти свою запись' }).click();
  await expect(page.getByText('Введите первые 5 цифр', { exact: false })).toBeVisible();
  const input = page.getByLabel('Код поступающего', { exact: true });
  await input.fill('70001/00000000000/0000001');
  await expect(page.getByRole('button', { name: 'Найти запись', exact: true })).toBeDisabled();
  await input.fill('70001');
  await page.getByRole('button', { name: 'Найти запись', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Проверьте выбранную запись' })).toBeVisible();
  await expect(page.getByText('Согласие в источнике: неизвестно.', { exact: false })).toBeVisible();
  await page
    .getByLabel('Подтверждаю: выбраны нужные мне группа и запись', { exact: false })
    .check();
  await page.getByRole('button', { name: 'Сохранить эту запись', exact: true }).click();
  await expect(page.getByText('Архивное направление сохранено.', { exact: false })).toBeVisible();
  await expect(input).toHaveValue('');
  expect(
    await page.evaluate(() => ({ local: { ...localStorage }, session: { ...sessionStorage } })),
  ).toEqual(storageBefore);
  await page.getByRole('link', { name: 'Открыть мои направления →' }).click();
  await page.reload();
  expect((await (await page.request.get('/api/v1/subscriptions')).json()).length).toBe(1);
});
