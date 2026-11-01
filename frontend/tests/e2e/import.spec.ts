import { expect, test } from '@playwright/test';
import fixture from '../../../shared/manual-watch.json' with { type: 'json' };

const bundle = { formatVersion: 'manual-export-v1', exportedAt: '2026-11-01T01:00:00Z', watches: [{ ...fixture, history: [fixture.latest] }] };
const upload = (data: unknown) => ({ name: 'admitflow.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(data)) });

test('новая сессия импортирует реальную выгрузку после подтверждения и безопасного повтора', async ({ page, context }) => {
  test.skip(process.env.E2E_API !== '1', 'Требуется API');
  await page.goto('/tracker');
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  const created = await page.request.post('/api/v1/watches', { headers: { 'X-Requested-With': 'abiturient' }, data: { university: fixture.university, title: fixture.title, sourceUrl: fixture.sourceUrl, values: fixture.latest.values } });
  expect(created.status()).toBe(201);
  const watch = await created.json();
  expect((await page.request.post(`/api/v1/watches/${watch.id}/snapshots`, { headers: { 'X-Requested-With': 'abiturient' }, data: { ...fixture.latest.values, noConsent: 0 } })).status()).toBe(201);
  const exported = await (await page.request.get('/api/v1/export')).json();
  await context.clearCookies();
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  await page.getByText('Восстановить из JSON', { exact: true }).click();
  const file = page.getByLabel('Файл выгрузки, до 8 МБ');
  await file.setInputFiles(upload(exported));
  await expect(page.getByText('Найдено направлений: 1; сохранений: 2.')).toBeVisible();
  expect((await (await page.request.get('/api/v1/watches')).json()).length).toBe(0);
  await page.getByRole('button', { name: 'Отменить импорт' }).click();
  await expect(page.getByRole('button', { name: 'Импортировать файл', exact: true })).toHaveCount(0);
  const keys: string[] = [];
  await page.route('**/api/v1/import', async route => {
    keys.push(route.request().headers()['idempotency-key']);
    if (keys.length === 1) {
      expect((await route.fetch()).status()).toBe(201);
      return route.abort('failed');
    }
    return route.continue();
  });
  await file.setInputFiles(upload(exported));
  await page.getByRole('button', { name: 'Импортировать файл', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Не удалось связаться с сервером');
  await page.getByRole('button', { name: 'Импортировать файл', exact: true }).click();
  await expect(page.locator('.direction-card')).toHaveCount(1);
  await expect(page.locator('.tracker-notice')).toContainText('Этот файл уже импортирован');
  expect(keys).toHaveLength(2);
  expect(keys[0]).toBe(keys[1]);
  const restored = await (await page.request.get('/api/v1/export')).json();
  expect(restored.watches[0].id).not.toBe(exported.watches[0].id);
  expect(restored.watches[0].history[0].capturedAt).toBe(exported.watches[0].history[0].capturedAt);
  expect(restored.watches[0].history.map((snapshot: { values: unknown }) => snapshot.values)).toEqual(exported.watches[0].history.map((snapshot: { values: unknown }) => snapshot.values));
});

test('невалидный или слишком большой файл не отправляется на сервер', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Требуется API');
  let requests = 0;
  page.on('request', request => { if (request.url().endsWith('/api/v1/import')) requests++; });
  await page.goto('/tracker');
  await page.getByText('Восстановить из JSON', { exact: true }).click();
  const file = page.getByLabel('Файл выгрузки, до 8 МБ');
  const invalid = { ...bundle, watches: [{ ...bundle.watches[0], latest: { ...fixture.latest, calculation: { ...fixture.latest.calculation, place: 1 } } }] };
  await file.setInputFiles(upload(invalid));
  await expect(page.getByRole('alert')).toContainText('корректную выгрузку');
  await file.setInputFiles({ name: 'large.json', mimeType: 'application/json', buffer: Buffer.alloc(8 * 1024 * 1024 + 1) });
  await expect(page.getByRole('alert')).toContainText('больше 8 МБ');
  expect(requests).toBe(0);
});

test('полный лимит разрешает replay, но не импорт нового файла', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Требуется API');
  const data = { ...bundle, watches: Array.from({ length: 20 }, (_, index) => {
    const latest = { ...fixture.latest, id: `old-snapshot-${index}` };
    return { ...fixture, id: `old-watch-${index}`, title: `Quota ${index}`, latest, history: [latest] };
  }) };
  await page.goto('/tracker');
  await page.getByText('Восстановить из JSON', { exact: true }).click();
  await page.getByLabel('Файл выгрузки, до 8 МБ').setInputFiles(upload(data));
  await page.getByRole('button', { name: 'Импортировать файл', exact: true }).click();
  await expect(page.locator('.direction-card')).toHaveCount(20);
  await page.reload();
  await page.getByText('Восстановить из JSON', { exact: true }).click();
  const file = page.getByLabel('Файл выгрузки, до 8 МБ');
  await file.setInputFiles(upload(data));
  await page.getByRole('button', { name: 'Проверить повтор импорта' }).click();
  await expect(page.locator('.tracker-notice')).toContainText('Этот файл уже импортирован');
  await expect(page.locator('.direction-card')).toHaveCount(20);
  const changed = { ...data, watches: data.watches.map(watch => ({ ...watch, title: `${watch.title} changed` })) };
  await file.setInputFiles(upload(changed));
  await page.getByRole('button', { name: 'Проверить повтор импорта' }).click();
  await expect(page.locator('.import-data').getByRole('alert')).toContainText('больше 20 направлений');
  expect((await (await page.request.get('/api/v1/watches')).json()).length).toBe(20);
});
