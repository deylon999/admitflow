import { expect, test } from '@playwright/test';

test('сброс в другой вкладке скрывает старый ввод без нового POST session', async ({ page, context }) => {
  test.skip(process.env.E2E_API !== '1', 'Требуется API');
  let starts = 0;
  context.on('request', request => { if (request.url().endsWith('/api/v1/session') && request.method() === 'POST') starts++; });
  try {
    await page.goto('/tracker');
    await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
    await page.request.post('/api/v1/watches', { headers: { 'X-Requested-With': 'abiturient' }, data: { university: 'Tabs test', title: 'Synthetic direction', sourceUrl: 'https://example.org/list', values: { rank: 120, seats: 90, excluded: 30, noConsent: 16 } } });
    await page.reload();
    const other = await context.newPage();
    await other.goto('/tracker');
    await other.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
    await other.locator('#tracker-rank').fill('125');
    await page.getByRole('button', { name: 'Удалить все мои данные' }).click();
    await page.getByRole('button', { name: 'Удалить всё', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
    await expect(other.getByRole('heading', { name: 'Гостевой доступ изменён в другой вкладке' })).toBeVisible();
    await expect(other.locator('.direction-card, .direction-form')).toHaveCount(0);
    const before = starts;
    await other.getByRole('button', { name: 'Синхронизировать доступ' }).click();
    await expect(other.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
    expect(starts).toBe(before);
  } finally {
    await page.request.delete('/api/v1/session', { headers: { 'X-Requested-With': 'abiturient' } });
  }
});
