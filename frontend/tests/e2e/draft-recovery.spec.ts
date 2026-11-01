import { expect, test } from '@playwright/test';

test('reload offers explicit restore and discard without writing directions', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  await page.getByLabel('Вуз', { exact: true }).fill('Reload draft');
  await page.getByLabel('Направление и конкурсная группа').fill('Restorable title');
  await expect(page.getByRole('status').filter({ hasText: 'Черновик сохранён' })).toBeVisible();
  page.once('dialog', dialog => dialog.accept());
  await page.reload();
  const recovery = page.getByRole('region', { name: 'Есть несохранённый черновик' });
  await expect(recovery).toContainText('Restorable title');
  await expect(page.locator('.direction-form')).toHaveCount(0);
  await recovery.getByRole('button', { name: 'Восстановить черновик', exact: true }).click();
  await expect(page.getByLabel('Вуз', { exact: true })).toHaveValue('Reload draft');
  await expect(page.getByLabel('Направление и конкурсная группа')).toHaveValue('Restorable title');
  expect((await (await page.request.get('/api/v1/watches')).json()).length).toBe(0);
  page.once('dialog', dialog => dialog.accept());
  await page.reload();
  await recovery.getByRole('button', { name: 'Удалить черновик', exact: true }).click();
  await expect(recovery).toHaveCount(0);
  expect(await page.evaluate(() => sessionStorage.getItem('admitflow-draft-v1'))).toBeNull();
  await expect(page.getByRole('button', { name: 'Добавить направление', exact: true })).toBeFocused();
  expect((await (await page.request.get('/api/v1/watches')).json()).length).toBe(0);
});

test('typing only stores a local draft and saves its retry key before sending', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  await page.getByLabel('Вуз', { exact: true }).fill('Local draft');
  await page.getByLabel('Направление и конкурсная группа').fill('Incomplete direction');
  await expect(page.getByRole('status').filter({ hasText: 'Черновик сохранён' })).toBeVisible();
  expect(await page.evaluate(() => JSON.parse(sessionStorage.getItem('admitflow-draft-v1')!).draft.title)).toBe('Incomplete direction');
  expect((await (await page.request.get('/api/v1/watches')).json()).length).toBe(0);
  await page.getByLabel('Ссылка на конкурсный список').fill('https://example.org/list');
  await page.getByLabel('Ваш номер в списке').fill('10');
  await page.getByLabel('Бюджетных мест', { exact: true }).fill('20');
  let key: string | undefined;
  await page.route('**/api/v1/watches', async route => {
    if (route.request().method() !== 'POST') return route.continue();
    key = route.request().headers()['idempotency-key'];
    const stored = await page.evaluate(() => JSON.parse(sessionStorage.getItem('admitflow-draft-v1')!));
    expect(stored.intent.key).toBe(key);
    await route.abort('failed');
  });
  await page.getByRole('button', { name: 'Сохранить направление', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Не удалось связаться');
  expect(key).toMatch(/^[a-f0-9-]{36}$/);
  await expect(page.getByLabel('Вуз', { exact: true })).toHaveValue('Local draft');
});
