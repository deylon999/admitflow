import { expect, test } from '@playwright/test';
import fixture from '../../../shared/manual-watch.json' with { type: 'json' };

test('canceling a slow file permits a new choice and ignores the late result', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.addInitScript(() => {
    const read = File.prototype.arrayBuffer;
    File.prototype.arrayBuffer = function () {
      if (this.name !== 'slow.json') return read.call(this);
      return new Promise<ArrayBuffer>((resolve) => {
        (window as unknown as { releaseFile: () => Promise<void> }).releaseFile = () =>
          read.call(this).then(resolve);
      });
    };
  });
  await page.goto('/tracker');
  await page.getByText('Восстановить из JSON', { exact: true }).click();
  const file = page.getByLabel('Файл выгрузки, до 8 МБ');
  const upload = (name: string, title: string) => ({
    name,
    mimeType: 'application/json',
    buffer: Buffer.from(
      JSON.stringify({
        formatVersion: 'manual-export-v1',
        exportedAt: '2026-11-01T01:00:00Z',
        watches: [{ ...fixture, title, history: [fixture.latest] }],
      }),
    ),
  });
  await file.setInputFiles(upload('slow.json', 'Discarded slow file'));
  await page.getByRole('button', { name: 'Отменить чтение', exact: true }).click();
  await expect(file).toBeEnabled();
  await file.setInputFiles(upload('new.json', 'Current file'));
  await expect(page.locator('.import-preview')).toContainText('Current file');
  await page.evaluate(async () => {
    await (window as unknown as { releaseFile: () => Promise<void> }).releaseFile();
    await new Promise(requestAnimationFrame);
    await new Promise(requestAnimationFrame);
  });
  await expect(page.locator('.import-preview')).not.toContainText('Discarded slow file');
  await expect(page.locator('.import-preview')).toContainText('Current file');
  expect((await (await page.request.get('/api/v1/watches')).json()).length).toBe(0);
});

test('cancel clears a failed import and a new selection keeps its own safe retry', async ({
  page,
}) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  const keys: string[] = [];
  const bodies: unknown[] = [];
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route('**/api/v1/import', async (route) => {
    keys.push(route.request().headers()['idempotency-key']);
    bodies.push(route.request().postDataJSON());
    if (keys.length <= 2) {
      return route.fulfill({ status: 503, json: { detail: 'Synthetic import unavailable' } });
    }
    await gate;
    await route.continue();
  });
  const upload = (title: string) => ({
    name: 'synthetic.json',
    mimeType: 'application/json',
    buffer: Buffer.from(
      JSON.stringify({
        formatVersion: 'manual-export-v1',
        exportedAt: '2026-11-01T01:00:00Z',
        watches: [{ ...fixture, title, history: [fixture.latest] }],
      }),
    ),
  });
  await page.goto('/tracker');
  await page.getByText('Восстановить из JSON', { exact: true }).click();
  const panel = page.locator('.import-data');
  const file = panel.getByLabel('Файл выгрузки, до 8 МБ');
  const submit = panel.getByRole('button', { name: 'Импортировать файл', exact: true });
  const cancel = panel.getByRole('button', { name: 'Отменить импорт', exact: true });
  await file.setInputFiles(upload('Canceled import'));
  await submit.click();
  await expect(panel.getByRole('alert')).toContainText('Synthetic import unavailable');
  await expect(panel.getByRole('alert')).toContainText('Повтор использует тот же ключ операции');
  await cancel.click();
  await expect(panel.getByRole('alert')).toHaveCount(0);
  await expect(
    panel.getByText('Повтор использует тот же ключ операции.', { exact: false }),
  ).toHaveCount(0);
  await expect(panel.locator('.import-preview')).toHaveCount(0);
  await expect(submit).toHaveCount(0);
  expect(await file.evaluate((node: HTMLInputElement) => node.files?.length)).toBe(0);
  expect(keys).toHaveLength(1);
  await file.setInputFiles(upload('Current import'));
  await expect(panel.getByRole('alert')).toHaveCount(0);
  await submit.click();
  await expect(panel.getByRole('alert')).toContainText('Synthetic import unavailable');
  await submit.click();
  try {
    await expect.poll(() => keys.length).toBe(3);
    expect(keys[0]).not.toBe(keys[1]);
    expect(keys[1]).toBe(keys[2]);
    expect(bodies[1]).toEqual(bodies[2]);
    expect(bodies[2]).toMatchObject({ bundle: { watches: [{ title: 'Current import' }] } });
    await expect(file).toBeDisabled();
    await expect(cancel).toBeDisabled();
  } finally {
    release();
  }
  await expect(page.locator('.direction-card')).toHaveCount(1);
  await expect(page.locator('.direction-card')).toContainText('Current import');
  await expect(panel.getByRole('alert')).toHaveCount(0);
  await expect(panel.locator('.import-preview')).toHaveCount(0);
  await expect(submit).toHaveCount(0);
  expect(await file.evaluate((node: HTMLInputElement) => node.files?.length)).toBe(0);
});
