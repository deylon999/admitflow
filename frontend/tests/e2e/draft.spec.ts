import { expect, test } from '@playwright/test';

test('отказ от закрытия и смены формы сохраняет черновик, сохранение не спрашивает', async ({
  page,
}) => {
  test.skip(process.env.E2E_API !== '1', 'Требуется API');
  await page.goto('/tracker');
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  await page.request.post('/api/v1/watches', {
    headers: { 'X-Requested-With': 'abiturient' },
    data: {
      university: 'Existing',
      title: 'Existing group',
      sourceUrl: 'https://example.org/list',
      values: { rank: 10, seats: 20, excluded: 0, noConsent: 0 },
    },
  });
  await page.reload();
  await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
  await page.getByLabel('Ваш номер в списке').fill('11');
  page.once('dialog', (dialog) => dialog.dismiss());
  await page.getByRole('button', { name: 'Добавить направление', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Обновить цифры' })).toBeVisible();
  await expect(page.getByLabel('Ваш номер в списке')).toHaveValue('11');
  page.once('dialog', (dialog) => dialog.dismiss());
  await page.getByRole('button', { name: 'Закрыть форму' }).click();
  await expect(page.getByLabel('Ваш номер в списке')).toHaveValue('11');
  let unexpected = 0;
  const reject = (dialog: import('@playwright/test').Dialog) => {
    unexpected++;
    void dialog.dismiss();
  };
  page.on('dialog', reject);
  await page.getByRole('button', { name: 'Сохранить обновление' }).click();
  await expect(page.locator('.direction-result strong')).toHaveText('11');
  expect(unexpected).toBe(0);
  page.off('dialog', reject);
  await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
  await page.getByLabel('Ваш номер в списке').fill('12');
  page.once('dialog', (dialog) => dialog.accept());
  await page.getByRole('button', { name: 'Добавить направление', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Добавить направление', exact: true }),
  ).toBeVisible();
  await expect(page.getByLabel('Ваш номер в списке')).toHaveValue('');
});

test('ссылка на другую страницу не теряет ввод при отказе', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Требуется API');
  await page.goto('/tracker');
  await page
    .locator('.empty-state')
    .getByRole('button', { name: 'Добавить направление', exact: true })
    .click();
  await page.getByLabel('Вуз', { exact: true }).fill('Unsaved university');
  const dialog = page.waitForEvent('dialog');
  page.once('dialog', (dialog) => dialog.dismiss());
  await page.getByRole('link', { name: 'Абитуриент — в начало' }).click();
  await dialog;
  await expect(page).toHaveURL(/\/tracker$/);
  await expect(page.getByLabel('Вуз', { exact: true })).toHaveValue('Unsaved university');
  page.once('dialog', (dialog) => dialog.accept());
  await page.getByRole('button', { name: 'Закрыть форму' }).click();
  await expect(page.locator('.direction-form')).toHaveCount(0);
});
