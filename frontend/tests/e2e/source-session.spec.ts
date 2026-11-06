import { expect, test } from '@playwright/test';
import type { Page } from '@playwright/test';
test.beforeEach(() =>
  test.skip(process.env.E2E_SOURCE_FIXTURE !== '1', 'Requires anonymized source API'),
);
async function save(page: Page, code = 'FIXTURE-000001') {
  await page.goto('/sources');
  await page.getByRole('button', { name: 'Найти свою запись', exact: true }).click();
  await page.getByLabel('Код поступающего').fill(code);
  await page.getByRole('button', { name: 'Найти запись', exact: true }).click();
  await page.getByLabel('Подтверждаю: выбраны нужные мне группа и запись').check();
  await page.getByRole('button', { name: 'Сохранить эту запись' }).click();
  await page.getByRole('link', { name: /Открыть мои направления/ }).click();
  await expect(page.locator('.archive-direction-card')).toHaveCount(1);
}
async function reset(page: Page) {
  await page.getByRole('button', { name: 'Удалить все мои данные' }).click();
  await page.getByRole('button', { name: 'Удалить всё', exact: true }).click();
  await expect(page.locator('.archive-direction-card')).toHaveCount(0);
}
test('other tab hides old source history and explicitly syncs only the replacement guest', async ({
  page,
  context,
}) => {
  await save(page);
  const other = await context.newPage();
  let starts = 0;
  other.on('request', (r) => {
    if (r.url().endsWith('/session') && r.method() === 'POST') starts++;
  });
  await other.goto('/tracker');
  await other.getByRole('button', { name: 'История фактов', exact: true }).click();
  await expect(other.locator('.archive-fact-list li')).toHaveCount(1);
  const before = starts;
  await reset(page);
  await expect(other.getByRole('heading', { name: 'Гостевой доступ изменён' })).toBeVisible();
  await expect(other.locator('.archive-direction-card,.archive-history')).toHaveCount(0);
  await save(page, 'FIXTURE-000002');
  await other.getByRole('button', { name: 'Синхронизировать доступ' }).click();
  await expect(other.locator('.archive-direction-card')).toHaveCount(1);
  await expect(other.locator('.archive-direction-card strong').first()).toHaveText('2');
  expect(starts).toBe(before);
});
test('late old-owner history response cannot reappear after reset and sync', async ({
  page,
  context,
}) => {
  await save(page);
  const other = await context.newPage();
  await other.goto('/tracker');
  await expect(other.locator('.archive-direction-card')).toHaveCount(1);
  let release!: () => void, entered!: () => void;
  const gate = new Promise<void>((r) => (release = r)),
    requested = new Promise<void>((r) => (entered = r));
  await other.route('**/api/v1/subscriptions/*/history?*', async (route) => {
    const response = await route.fetch();
    entered();
    await gate;
    await route.fulfill({ response }).catch(() => {});
  });
  await other.getByRole('button', { name: 'История фактов', exact: true }).click();
  await requested;
  try {
    await reset(page);
    await expect(other.getByRole('heading', { name: 'Гостевой доступ изменён' })).toBeVisible();
  } finally {
    release();
  }
  await other.getByRole('button', { name: 'Синхронизировать доступ' }).click();
  await expect(other.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  await expect(other.locator('.archive-direction-card,.archive-fact-list')).toHaveCount(0);
});
