import { expect, test } from '@playwright/test';
import fixture from '../../../shared/manual-watch.json' with { type: 'json' };
import { calculatePlace } from '@/entities/manual-direction';

test.beforeEach(async ({ page }) => {
  await page.route('**/api/v1/**', (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/session'))
      return route.fulfill(
        route.request().method() === 'POST'
          ? { status: 204 }
          : { json: { expiresAt: '2030-12-01T00:00:00Z' } },
      );
    if (path.endsWith('/watches')) return route.fulfill({ json: [fixture] });
    if (path.endsWith('/direction-budget'))
      return route.fulfill({ json: { total: 1, manualCount: 1, archiveCount: 0, limit: 20 } });
    if (path.endsWith('/subscriptions')) return route.fulfill({ json: [] });
    if (path.endsWith('/changes'))
      return route.fulfill({ json: { items: [], total: 0, unreadCount: 0, nextCursor: null } });
    if (path.endsWith('/history')) {
      const values = { ...fixture.latest.values, rank: fixture.latest.values.rank + 5 };
      return route.fulfill({
        json: {
          items: [
            fixture.latest,
            {
              ...fixture.latest,
              id: 'earlier',
              capturedAt: '2026-10-01T00:00:00Z',
              values,
              calculation: calculatePlace(values),
            },
          ],
          total: 2,
          nextCursor: null,
        },
      });
    }
    return route.fulfill({ status: 503, json: { detail: 'Synthetic unavailable' } });
  });
});

for (const theme of ['light', 'dark']) {
  for (const width of [320, 390, 768, 1440]) {
    test(`${theme} ${width}: directions first, no overflow, keyboard tools`, async ({
      page,
    }, testInfo) => {
      await page.setViewportSize({ width, height: 960 });
      await page.addInitScript((value) => localStorage.setItem('abiturient-theme', value), theme);
      await page.goto('/tracker');
      await expect(page.locator('.direction-result strong')).toHaveText('74');
      await expect(page.locator('.position-change')).toContainText('↑ Выше на 5');
      await expect(
        page.getByRole('heading', { name: 'Мои направления', exact: true }),
      ).toBeVisible();
      await expect(
        page.getByRole('button', { name: 'Добавить направление', exact: true }),
      ).toBeVisible();
      await expect(page.locator('.tracker-safety-note')).toContainText('потере доступа');
      await expect(page.getByRole('button', { name: 'Скачать данные (JSON)' })).toBeHidden();
      await expect(
        page.locator('.direction-card').getByText('Модель: manual-v1', { exact: false }),
      ).toBeHidden();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
        true,
      );
      const order = await page.evaluate(() => {
        const card = document.querySelector('.direction-card')!.getBoundingClientRect();
        const tools = document.querySelector('#tracker-tools-title')!.getBoundingClientRect();
        return card.top < tools.top;
      });
      expect(order).toBe(true);
      await page.screenshot({ path: testInfo.outputPath('tracker.png'), fullPage: true });
      const summary = page.getByText('Скачать данные и распечатать', { exact: true });
      await summary.focus();
      await page.keyboard.press('Enter');
      await expect(page.getByRole('button', { name: 'Скачать данные (JSON)' })).toBeVisible();
      await page.getByRole('button', { name: 'Скачать данные (JSON)' }).click();
      await expect(page.getByRole('alert').first()).toBeVisible();
      await summary.click();
      await expect(page.getByRole('alert').first()).toBeVisible();
      await page.getByRole('button', { name: 'История', exact: true }).click();
      await expect(page.locator('.history-comparison strong')).toHaveText('Место: 79 → 74');
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
        true,
      );
    });
  }
}

test('unavailable history never looks like unchanged position', async ({ page }) => {
  await page.route('**/api/v1/watches/*/history*', (route) =>
    route.fulfill({ status: 503, json: { detail: 'Unavailable history' } }),
  );
  await page.goto('/tracker');
  await expect(page.locator('.position-change')).toContainText('недоступно');
  await expect(page.locator('.direction-result strong')).toHaveText('74');
  await page.getByRole('button', { name: 'История', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Повторить загрузку истории' })).toBeVisible();
});

for (const previousRank of [null, 120, 110]) {
  test(`position change distinguishes missing, unchanged and lower: ${previousRank}`, async ({
    page,
  }) => {
    await page.route('**/api/v1/watches/*/history*', (route) => {
      const values = { ...fixture.latest.values, rank: previousRank ?? 120 };
      const items =
        previousRank === null
          ? [fixture.latest]
          : [
              fixture.latest,
              {
                ...fixture.latest,
                id: 'earlier',
                capturedAt: '2026-10-01T00:00:00Z',
                values,
                calculation: calculatePlace(values),
              },
            ];
      return route.fulfill({ json: { items, total: items.length, nextCursor: null } });
    });
    await page.goto('/tracker');
    await expect(page.locator('.position-change')).toContainText(
      previousRank === null
        ? 'нужно предыдущее сохранение'
        : previousRank === 120
          ? 'Место не изменилось'
          : '↓ Ниже на 10',
    );
  });
}

test('maximum numeric values and long titles fit a 320px card', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 960 });
  const values = { rank: 1_000_000, seats: 1_000_000, excluded: 0, noConsent: 0 };
  const watch = {
    ...fixture,
    title: 'Н'.repeat(200),
    university: 'У'.repeat(160),
    latest: { ...fixture.latest, values, calculation: calculatePlace(values) },
  };
  await page.route('**/api/v1/watches', (route) => route.fulfill({ json: [watch] }));
  await page.route('**/api/v1/watches/*/history*', (route) =>
    route.fulfill({ json: { items: [watch.latest], total: 1, nextCursor: null } }),
  );
  await page.goto('/tracker');
  await expect(page.locator('.direction-result strong')).toHaveText('1000000');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
