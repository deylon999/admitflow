import { expect, test } from '@playwright/test';
import fixture from '../../../shared/manual-watch.json' with { type: 'json' };

for (const action of ['history', 'export', 'delete', 'import']) {
  test(`401 из ${action} закрывает старую форму без автоматического старта`, async ({ page, context }) => {
    test.skip(process.env.E2E_API !== '1', 'Требуется API');
    let sessionStarts = 0;
    page.on('request', request => { if (request.url().endsWith('/api/v1/session') && request.method() === 'POST') sessionStarts++; });
    await page.goto('/tracker');
    await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
    expect((await page.request.post('/api/v1/watches', { headers: { 'X-Requested-With': 'abiturient' }, data: { university: fixture.university, title: fixture.title, sourceUrl: fixture.sourceUrl, values: fixture.latest.values } })).status()).toBe(201);
    await page.reload();
    await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
    await page.getByLabel('Ваш номер в списке').fill('121');
    const starts = sessionStarts;
    await context.clearCookies();
    if (action === 'history') await page.getByRole('button', { name: 'История', exact: true }).click();
    if (action === 'export') await page.getByRole('button', { name: 'Скачать данные (JSON)' }).click();
    if (action === 'delete') {
      await page.getByRole('button', { name: 'Удалить', exact: true }).click();
      await page.getByRole('button', { name: 'Да, удалить' }).click();
    }
    if (action === 'import') {
      await page.getByText('Восстановить из JSON', { exact: true }).click();
      const bundle = { formatVersion: 'manual-export-v1', exportedAt: '2026-11-01T01:00:00Z', watches: [{ ...fixture, history: [fixture.latest] }] };
      await page.getByLabel('Файл выгрузки, до 8 МБ').setInputFiles({ name: 'history.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(bundle)) });
      await page.getByRole('button', { name: 'Импортировать файл', exact: true }).click();
    }
    await expect(page.getByRole('heading', { name: 'Срок гостевой сессии истёк' })).toBeVisible();
    await expect(page.locator('.direction-card')).toHaveCount(0);
    await expect(page.locator('.direction-form')).toHaveCount(0);
    expect(sessionStarts).toBe(starts);
    await page.getByRole('button', { name: 'Начать новую сессию' }).click();
    await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
    expect(sessionStarts).toBe(starts + 1);
  });
}
