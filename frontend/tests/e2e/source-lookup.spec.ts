import { expect, test } from '@playwright/test';

test.beforeEach(() => test.skip(process.env.E2E_SOURCE_FIXTURE !== '1', 'Requires disposable anonymized fixture API'));
async function find(page: import('@playwright/test').Page, code = 'FIXTURE-000001') {
  await page.goto('/sources');
  await page.getByRole('button', { name: 'Найти свою запись' }).click();
  await expect(page.getByLabel('Код поступающего')).toBeFocused();
  await page.getByLabel('Код поступающего').fill(code);
  await page.getByRole('button', { name: 'Найти запись', exact: true }).click();
}
test('explicit group confirmation saves once, reloads and does not persist public code', async ({ page }) => {
  let saves = 0;
  page.on('request', request => { if (request.method() === 'POST' && request.url().endsWith('/subscriptions')) saves++; });
  await find(page);
  await expect(page.getByRole('heading', { name: 'Проверьте выбранную запись' })).toBeFocused();
  await expect(page.locator('.source-candidate-preview')).toContainText('2026');
  await expect(page.locator('.source-candidate-preview')).toContainText('Строка официального списка: 1');
  await expect(page.getByRole('button', { name: 'Сохранить эту запись' })).toBeDisabled();
  expect(saves).toBe(0);
  await page.getByLabel('Подтверждаю: выбраны нужные мне группа и запись').check();
  await page.getByRole('button', { name: 'Сохранить эту запись' }).click();
  await expect(page.getByText('Архивное направление сохранено.', { exact: false })).toBeVisible();
  await page.getByRole('link', { name: /Открыть мои направления/ }).click();
  await expect(page.locator('.archive-direction-card')).toHaveCount(1);
  await page.reload();
  await expect(page.locator('.archive-direction-card')).toHaveCount(1);
  expect(saves).toBe(1);
  expect(await page.evaluate(() => JSON.stringify({ ...localStorage, ...sessionStorage }))).not.toContain('FIXTURE-');
  await page.getByRole('button', { name: 'Удалить все мои данные' }).click();
  await page.getByRole('button', { name: 'Удалить всё', exact: true }).click();
  await expect(page.locator('.archive-direction-card')).toHaveCount(0);
});
test('lost save response retries the same confirmation without duplicates', async ({ page }) => {
  await find(page, 'FIXTURE-000002');
  await page.getByLabel('Подтверждаю: выбраны нужные мне группа и запись').check();
  let first = true;
  await page.route('**/api/v1/subscriptions', async route => {
    if (route.request().method() === 'POST' && first) { first = false; await route.fetch(); await route.abort(); } else await route.continue();
  });
  await page.getByRole('button', { name: 'Сохранить эту запись' }).click();
  await page.getByRole('button', { name: 'Повторить сохранение записи' }).click();
  await expect(page.getByText('Архивное направление сохранено.', { exact: false })).toBeVisible();
  expect(await (await page.request.get('/api/v1/subscriptions')).json()).toHaveLength(1);
});
test('not found never enables save and close restores focus', async ({ page }) => {
  await find(page, 'not-present');
  await expect(page.getByRole('heading', { name: 'Запись не найдена в выбранном снимке' })).toBeFocused();
  await expect(page.getByRole('button', { name: 'Сохранить эту запись' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Закрыть поиск' }).click();
  await expect(page.getByRole('button', { name: 'Найти свою запись' })).toBeFocused();
});
for (const theme of ['light', 'dark']) test(`confirmation keyboard at320px ${theme}`, async ({ page }) => {
  await page.addInitScript(value => localStorage.setItem('abiturient-theme', value), theme);
  await page.setViewportSize({ width: 320, height: 1100 });
  await find(page);
  await page.getByLabel('Подтверждаю: выбраны нужные мне группа и запись').focus();
  await page.keyboard.press('Space'); await page.keyboard.press('Tab');
  await expect(page.getByRole('button', { name: 'Сохранить эту запись' })).toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test('individual delete confirms and releases slot while preserving the source', async ({ page }) => {
  await find(page);
  await page.getByLabel('Подтверждаю: выбраны нужные мне группа и запись').check();
  await page.getByRole('button', { name: 'Сохранить эту запись' }).click();
  await page.getByRole('link', { name: /Открыть мои направления/ }).click();
  await page.getByRole('button', { name: 'Удалить архивную запись', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Отмена', exact: true })).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(page.locator('.archive-direction-card')).toHaveCount(1);
  await page.getByRole('button', { name: 'Удалить архивную запись', exact: true }).click();
  await page.getByRole('button', { name: 'Да, удалить архивную запись', exact: true }).click();
  await expect(page.locator('.archive-direction-card')).toHaveCount(0);
  expect((await (await page.request.get('/api/v1/groups')).json()).items[0].rowCount).toBe(573);
});
