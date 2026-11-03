import { expect, test } from '@playwright/test';
test.beforeEach(() => test.skip(process.env.E2E_SOURCE_FIXTURE !== '1', 'Requires anonymized fixture API'));
async function saved(page: import('@playwright/test').Page) {
  await page.goto('/sources'); await page.getByRole('button', { name: 'Найти свою запись' }).click();
  await page.getByLabel('Код поступающего').fill('FIXTURE-000001'); await page.getByRole('button', { name: 'Найти запись', exact: true }).click();
  await page.getByLabel('Подтверждаю: выбраны нужные мне группа и запись').check();
  await page.getByRole('button', { name: 'Сохранить эту запись' }).click();
  await page.getByRole('link', { name: /Открыть мои направления/ }).click();
}
test('native archive initial history preserves snapshot and version', async ({ page }) => {
  await saved(page); await page.getByRole('button', { name: 'История фактов', exact: true }).click();
  await expect(page.locator('.archive-fact-list li')).toHaveCount(1);
  await expect(page.locator('.archive-fact-list')).toContainText('source-confirmation-v1');
  await expect(page.locator('.archive-fact-list')).toContainText('Строка списка: 1');
  await expect(page.locator('.archive-fact-list')).toContainText('Обновление источника: неизвестно');
});
test('synthetic page comparisons show consent changes and absence without inferred refusal', async ({ page }) => {
  await saved(page);
  const sub=(await (await page.request.get('/api/v1/subscriptions')).json())[0];
  const initial=(await (await page.request.get(`/api/v1/subscriptions/${sub.id}/history`)).json()).items[0];
  const older={...initial,id:'history-a',group:{...initial.group,snapshotId:'snapshot-a'},candidate:{...initial.candidate,consent:false}};
  const latest={...initial,id:'history-c',modelVersion:'source-facts-v1',group:{...initial.group,snapshotId:'snapshot-c',fetchedAt:'2026-11-02T00:00:00Z'},candidate:{...initial.candidate,consent:true}};
  const absent={...older,id:'history-b',group:{...older.group,snapshotId:'snapshot-b'},candidate:null,present:false};
  await page.route('**/api/v1/subscriptions/*/history?*', route => route.fulfill({json:new URL(route.request().url()).searchParams.has('before') ? {items:[older],total:3,nextCursor:null} : {items:[latest,absent],total:3,nextCursor:'history-b'}}));
  await page.getByRole('button', { name: 'История фактов', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Сравнение архивных фактов' })).toContainText('Отсутствие не доказывает отзыв или отказ');
  await page.getByRole('button', { name: 'Ещё архивные снимки' }).click();
  await expect(page.locator('.archive-fact-list li')).toHaveCount(3);
  await page.getByLabel('Ранний архивный снимок').selectOption('history-a');
  await expect(page.getByRole('region', { name: 'Сравнение архивных фактов' })).toContainText('Согласие: нет → да');
  await page.setViewportSize({width:320,height:1000});
  expect(await page.evaluate(() => document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});
