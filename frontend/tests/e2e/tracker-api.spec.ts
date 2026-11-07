import { openTrackerPanel } from './helpers/tracker';
import { expect, test } from '@playwright/test';
import type { Page } from '@playwright/test';
import { readFile } from 'node:fs/promises';

async function fillDirection(page: Page) {
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  await page.getByLabel('Вуз', { exact: true }).fill('Тестовый вуз');
  await page.getByLabel('Направление и конкурсная группа').fill('Проверка сквозного пути');
  await page.getByLabel('Ссылка на конкурсный список').fill('https://example.org/list');
  await page.getByLabel('Ваш номер в списке').fill('120');
  await page.getByLabel('Бюджетных мест').fill('90');
  await page.getByLabel('Выше вас вне общего конкурса').fill('30');
  await page.getByLabel('Выше вас без согласия на зачисление').fill('16');
}

test('реальный API: создать, обновить, прочитать историю, удалить', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Требуется API на 127.0.0.1:8000 и E2E_API=1');
  await page.goto('/tracker');
  await fillDirection(page);
  await page.getByRole('button', { name: 'Сохранить направление' }).click();
  await expect(page.locator('.direction-result strong')).toHaveText('74');
  await page.reload();
  await expect(page.locator('.direction-result strong')).toHaveText('74');
  await page.getByRole('button', { name: 'Обновить цифры' }).click();
  await page.getByLabel('Выше вас без согласия на зачисление').fill('0');
  await page.getByRole('button', { name: 'Сохранить обновление' }).click();
  await expect(page.locator('.direction-result strong')).toHaveText('90');
  await page.getByRole('button', { name: 'История' }).click();
  await expect(page.locator('.direction-history tbody tr')).toHaveCount(2);
  await expect(page.getByRole('region', { name: 'Сравнение ручных снимков' })).toContainText(
    'Место: 74 → 90',
  );
  await page.getByRole('button', { name: 'Удалить', exact: true }).click();
  await page.getByRole('button', { name: 'Да, удалить' }).click();
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
});

test('повтор после потерянного ответа не создаёт второе направление', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Требуется настоящий API');
  const keys: string[] = [];
  await page.route('**/api/v1/watches', async (route) => {
    if (route.request().method() !== 'POST') return route.continue();
    keys.push(route.request().headers()['idempotency-key']);
    if (keys.length === 1) {
      const committed = await route.fetch();
      expect(committed.status()).toBe(201);
      return route.abort('failed');
    }
    return route.continue();
  });
  await page.goto('/tracker');
  await fillDirection(page);
  await page.getByRole('button', { name: 'Сохранить направление' }).click();
  await expect(page.getByText('Не удалось связаться с сервером.', { exact: false })).toBeVisible();
  await page.getByRole('button', { name: 'Сохранить направление' }).click();
  await expect(page.locator('.direction-card')).toHaveCount(1);
  expect(keys).toHaveLength(2);
  expect(keys[0]).toBeTruthy();
  expect(keys[1]).toBe(keys[0]);
  const response = await page.request.get('/api/v1/watches');
  expect((await response.json()).length).toBe(1);
});

test('экспорт скачивается как JSON с полной своей историей', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Требуется настоящий API');
  await page.goto('/tracker');
  await fillDirection(page);
  await page.getByRole('button', { name: 'Сохранить направление' }).click();
  await expect(page.locator('.direction-card')).toHaveCount(1);
  const pending = page.waitForEvent('download');
  await openTrackerPanel(page, 'export');
  await page.getByRole('button', { name: 'Скачать данные (JSON)' }).click();
  const file = await pending;
  const path = await file.path();
  expect(file.suggestedFilename()).toMatch(/^admitflow-\d{4}-\d{2}-\d{2}\.json$/);
  const data = JSON.parse(await readFile(path!, 'utf8'));
  expect(data.formatVersion).toBe('manual-export-v1');
  expect(data.watches).toHaveLength(1);
  expect(data.watches[0].history).toHaveLength(1);
  expect(data.watches[0].latest.calculation.place).toBe(74);
  expect(data.watches[0]).not.toHaveProperty('ownerHash');
});

test('потеря cookies требует явного старта новой сессии', async ({ page, context }) => {
  test.skip(process.env.E2E_API !== '1', 'Требуется настоящий API');
  await page.goto('/tracker');
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  await context.clearCookies();
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Срок гостевой сессии истёк' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Начать новую сессию' }).click();
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
});

test('удаление всех данных требует подтверждения и очищает направления', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Требуется настоящий API');
  await page.goto('/tracker');
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  const created = await page.request.post('/api/v1/watches', {
    headers: { 'X-Requested-With': 'abiturient' },
    data: {
      university: 'Тестовый вуз',
      title: 'Удаление данных',
      sourceUrl: 'https://example.org/list',
      values: { rank: 10, seats: 5, excluded: 0, noConsent: 0 },
    },
  });
  expect(created.status()).toBe(201);
  await page.reload();
  await openTrackerPanel(page, 'access');
  await page.getByRole('button', { name: 'Удалить все мои данные' }).click();
  await page.getByRole('button', { name: 'Отмена' }).click();
  await expect(page.getByRole('heading', { name: 'Удаление данных' })).toBeVisible();
  await openTrackerPanel(page, 'access');
  await page.getByRole('button', { name: 'Удалить все мои данные' }).click();
  await page.getByRole('button', { name: 'Удалить всё', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
});
