import { expect, test } from '@playwright/test';

test('real BGU archive exposes one reviewed contract group and a minimal-code hint without applicant access', async ({ page }) => {
  test.skip(process.env.E2E_BGU !== '1', 'Requires the actual reviewed BGU import in the current demo');
  let posts = 0;
  page.on('request', request => { if (request.method() === 'POST') posts++; });
  await page.goto('/sources');
  await page.getByLabel('Вуз', { exact: true }).selectOption('miccedu-12');
  const card = page.locator('.source-catalog-card');
  await expect(card).toHaveCount(1);
  await expect(card).toContainText('08.03.01');
  await expect(card).toContainText('Архив 2026 года');
  await expect(card).toContainText('20 мест в этой группе');
  await expect(card).toContainText('Строк: 109.');
  await expect(card).toContainText('числовой сценарий не подключён');
  await card.getByRole('button', { name: 'Найти свою запись' }).click();
  await expect(card.getByText('Введите первые 5 цифр', { exact: false })).toBeVisible();
  await expect(card.getByLabel('Код поступающего', { exact: true })).toHaveValue('');
  expect(posts).toBe(0);
});
