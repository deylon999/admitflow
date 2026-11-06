import { expect, test } from '@playwright/test';

test('back and forward preserve a dirty form when rejected and leave once when accepted', async ({
  page,
}) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.goto('/');
  await page.getByRole('link', { name: 'Мои направления →', exact: true }).click();
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  const input = page.getByLabel('Вуз', { exact: true });
  await input.fill('History draft');
  let dialogs = 0;
  const reject = (dialog: import('@playwright/test').Dialog) => {
    dialogs++;
    void dialog.dismiss();
  };
  page.on('dialog', reject);
  await page.evaluate(() => history.back());
  await expect.poll(() => dialogs).toBe(1);
  await expect(input).toHaveValue('History draft');
  await expect(page).toHaveURL(/\/tracker$/);
  page.off('dialog', reject);
  page.once('dialog', (dialog) => dialog.accept());
  await page.evaluate(() => history.back());
  await expect(page).toHaveURL(/\/$/);
  await page.evaluate(() => history.forward());
  await expect(page).toHaveURL(/\/tracker$/);
  await page.getByRole('link', { name: 'Абитуриент — в начало' }).click();
  await expect(page).toHaveURL(/\/$/);
  await page.evaluate(() => history.back());
  await expect(page).toHaveURL(/\/tracker$/);
  await page.getByRole('button', { name: 'Удалить черновик', exact: true }).click();
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  await input.fill('Forward draft');
  page.on('dialog', reject);
  await page.evaluate(() => history.forward());
  await expect.poll(() => dialogs).toBe(2);
  await expect(page).toHaveURL(/\/tracker$/);
  await expect(input).toHaveValue('Forward draft');
  page.off('dialog', reject);
});
