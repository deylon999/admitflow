import { expect, test } from '@playwright/test';
import fixture from '../../../shared/manual-watch.json' with { type: 'json' };

test('canceling a slow file permits a new choice and ignores the late result', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.addInitScript(() => {
    const read = File.prototype.arrayBuffer;
    File.prototype.arrayBuffer = function () {
      if (this.name !== 'slow.json') return read.call(this);
      return new Promise<ArrayBuffer>(resolve => {
        (window as unknown as { releaseFile: () => Promise<void> }).releaseFile = () => read.call(this).then(resolve);
      });
    };
  });
  await page.goto('/tracker');
  await page.getByText('Восстановить из JSON', { exact: true }).click();
  const file = page.getByLabel('Файл выгрузки, до 8 МБ');
  const upload = (name: string, title: string) => ({ name, mimeType: 'application/json', buffer: Buffer.from(JSON.stringify({ formatVersion: 'manual-export-v1', exportedAt: '2026-11-01T01:00:00Z', watches: [{ ...fixture, title, history: [fixture.latest] }] })) });
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
