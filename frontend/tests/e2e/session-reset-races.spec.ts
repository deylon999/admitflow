import { openTrackerPanel } from './helpers/tracker';
import { expect, test } from '@playwright/test';

const headers = { 'X-Requested-With': 'abiturient' };
const syntheticDirection = (title: string) => ({
  university: 'Synthetic reset race university',
  title,
  sourceUrl: 'https://example.org/reset-race',
  values: { rank: 120, seats: 90, excluded: 30, noConsent: 16 },
});

for (const webLocks of [true, false]) {
  test(`synchronization during another tab reset preserves the new guest (${webLocks ? 'Web Locks' : 'fallback'})`, async ({
    page,
    context,
  }) => {
    test.skip(process.env.E2E_API !== '1', 'Requires the disposable test API');
    if (!webLocks) {
      await context.addInitScript(() => {
        Object.defineProperty(navigator, 'locks', { configurable: true, value: undefined });
      });
    }

    let starts = 0;
    let deletes = 0;
    context.on('request', (request) => {
      if (!request.url().endsWith('/api/v1/session')) return;
      if (request.method() === 'POST') starts++;
      if (request.method() === 'DELETE') deletes++;
    });

    let releaseReset!: () => void;
    const pendingReset = new Promise<void>((resolve) => {
      releaseReset = resolve;
    });
    const other = await context.newPage();
    let resetPostWaiting = false;

    try {
      await page.goto('/tracker');
      await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
      const oldRecord = await page.request.post('/api/v1/watches', {
        headers,
        data: syntheticDirection('Old guest direction'),
      });
      expect(oldRecord.status()).toBe(201);
      await page.reload();
      await other.goto('/tracker');
      await expect(other.locator('.direction-card')).toHaveCount(1);

      await other.route('**/api/v1/session', async (route) => {
        if (route.request().method() === 'POST') {
          resetPostWaiting = true;
          await pendingReset;
        }
        await route.continue();
      });
      await openTrackerPanel(other, 'access');
      await other.getByRole('button', { name: 'Удалить все мои данные', exact: true }).click();
      await other.getByRole('button', { name: 'Удалить всё', exact: true }).click();
      await expect.poll(() => resetPostWaiting).toBe(true);
      await expect(page.getByRole('heading', { name: 'Гостевой доступ изменён' })).toBeVisible();

      const sync = page.getByRole('button', { name: 'Синхронизировать доступ', exact: true });
      if (webLocks) {
        await sync.click();
        // Observe the native queue while the other tab deliberately owns its lock.
        // This establishes the interrupted state without a timing-dependent sleep.
        await expect
          .poll(() =>
            page.evaluate(async () => (await navigator.locks.query()).pending?.length ?? 0),
          )
          .toBeGreaterThan(0);
        await expect(sync).toBeDisabled();
      } else {
        const unauthorized = page.waitForResponse(
          (response) =>
            response.url().endsWith('/api/v1/session') &&
            response.request().method() === 'GET' &&
            response.status() === 401,
        );
        await sync.click();
        await unauthorized;
        await expect(sync).toBeEnabled();
        await expect(page.getByRole('alert')).toContainText('Повторите синхронизацию');
        await expect(page.getByRole('alert')).not.toContainText('Начните новую сессию');
      }

      await expect(page.getByRole('button', { name: 'Начать новую сессию' })).toHaveCount(0);
      releaseReset();
      await expect(
        other.getByText('Создана новая гостевая сессия.', { exact: true }),
      ).toBeVisible();
      const newRecord = await other.request.post('/api/v1/watches', {
        headers,
        data: syntheticDirection('New guest direction survives synchronization'),
      });
      expect(newRecord.status()).toBe(201);

      if (!webLocks) await sync.click();
      await expect(page.getByRole('button', { name: 'Начать новую сессию' })).toHaveCount(0);
      await page.reload();
      await expect(page.locator('.direction-card')).toContainText(
        'New guest direction survives synchronization',
      );
      expect(await (await page.request.get('/api/v1/watches')).json()).toHaveLength(1);
      expect(starts).toBe(2);
      expect(deletes).toBe(1);
    } finally {
      releaseReset();
      await page.request.delete('/api/v1/session', { headers });
      await other.close();
    }
  });
}
