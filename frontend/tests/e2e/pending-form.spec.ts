import { expect, test } from '@playwright/test';
import fixture from '../../../shared/manual-watch.json' with { type: 'json' };

test('an open form preserves values and cannot submit during import', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.goto('/tracker');
  await page
    .locator('.empty-state')
    .getByRole('button', { name: 'Добавить направление', exact: true })
    .click();
  await page.getByLabel('Вуз', { exact: true }).fill('Draft during import');
  await page.getByLabel('Направление', { exact: true }).fill('Draft group');
  await page.getByLabel('Ссылка на конкурсный список').fill('https://example.org/draft');
  await page.getByLabel('Ваш номер в списке').fill('10');
  await page.getByLabel('Бюджетных мест', { exact: true }).fill('20');
  await page.getByText('Восстановить из JSON', { exact: true }).click();
  await page.getByLabel('Файл выгрузки, до 8 МБ').setInputFiles({
    name: 'import.json',
    mimeType: 'application/json',
    buffer: Buffer.from(
      JSON.stringify({
        formatVersion: 'manual-export-v1',
        exportedAt: '2026-11-01T01:00:00Z',
        watches: [{ ...fixture, history: [fixture.latest] }],
      }),
    ),
  });
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route('**/api/v1/import', async (route) => {
    await gate;
    await route.continue();
  });
  let creates = 0;
  page.on('request', (request) => {
    if (request.method() === 'POST' && request.url().endsWith('/api/v1/watches')) creates++;
  });
  await page.getByRole('button', { name: 'Импортировать файл', exact: true }).click();
  const save = page.getByRole('button', { name: 'Сохранить направление', exact: true });
  try {
    await expect(save).toBeDisabled();
    await expect(page.getByLabel('Вуз', { exact: true })).toBeDisabled();
    await page.locator('.direction-form').dispatchEvent('submit');
    expect(creates).toBe(0);
  } finally {
    release();
  }
  await expect(save).toBeEnabled();
  await expect(page.getByLabel('Вуз', { exact: true })).toHaveValue('Draft during import');
  await save.click();
  await expect(page.locator('.direction-card')).toHaveCount(2);
  expect(creates).toBe(1);
});

test('an unchanged pending edit guards links and unload until its result arrives', async ({
  page,
}) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.goto('/');
  await page.getByRole('link', { name: 'Мои направления →', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  const created = await page.request.post('/api/v1/watches', {
    headers: { 'X-Requested-With': 'abiturient' },
    data: {
      university: 'Pending',
      title: 'Pending edit',
      sourceUrl: 'https://example.org/list',
      values: { rank: 10, seats: 20, excluded: 0, noConsent: 0 },
    },
  });
  expect(created.status()).toBe(201);
  await page.reload();
  await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route('**/api/v1/watches/*/snapshots', async (route) => {
    await gate;
    await route.continue();
  });
  await page.getByRole('button', { name: 'Сохранить обновление', exact: true }).click();
  try {
    await expect(
      page.getByRole('status').filter({ hasText: 'Дождитесь результата' }),
    ).toBeVisible();
    await page.getByRole('link', { name: 'Абитуриент — в начало' }).click();
    await expect(page).toHaveURL(/\/tracker$/);
    await page.evaluate(() => history.back());
    await expect(page).toHaveURL(/\/tracker$/);
    await expect(page.locator('.direction-form')).toBeVisible();
    expect(
      await page.evaluate(() => {
        const event = new Event('beforeunload', { cancelable: true });
        window.dispatchEvent(event);
        return event.defaultPrevented;
      }),
    ).toBe(true);
  } finally {
    release();
  }
  await expect(page.locator('.direction-form')).toHaveCount(0);
  await page.getByRole('link', { name: 'Абитуриент — в начало' }).click();
  await expect(page).toHaveURL(/\/$/);
});
