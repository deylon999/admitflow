import { openTrackerPanel } from './helpers/tracker';
import { expect, test } from '@playwright/test';
import type { Page } from '@playwright/test';

const headers = { 'X-Requested-With': 'abiturient' };
const oldTitle = 'Previous guest private cache record';

test.beforeEach(() => {
  test.skip(process.env.E2E_API !== '1', 'Requires the isolated test API');
});

test.afterEach(async ({ page }) => {
  await page.request.delete('/api/v1/session', { headers });
});

async function seedPreviousGuest(page: Page) {
  await page.goto('/tracker');
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  const saved = await page.request.post('/api/v1/watches', {
    headers,
    data: {
      university: 'Synthetic cache regression university',
      title: oldTitle,
      sourceUrl: 'https://example.org/synthetic-cache-regression',
      values: { rank: 120, seats: 90, excluded: 30, noConsent: 16 },
    },
  });
  expect(saved.status()).toBe(201);
  await page.reload();
  await expect(page.locator('.direction-card')).toHaveCount(1);
  await expect(page.locator('.print-report')).toContainText(oldTitle);
}

async function confirmReset(page: Page) {
  await openTrackerPanel(page, 'access');
  await page.getByRole('button', { name: 'Удалить все мои данные', exact: true }).click();
  await page.getByRole('button', { name: 'Удалить всё', exact: true }).click();
}

async function expectNoPreviousGuestData(page: Page) {
  await expect(page.locator('.direction-card')).toHaveCount(0);
  await expect(page.locator('.direction-history')).toHaveCount(0);
  await expect(page.locator('body')).not.toContainText(oldTitle);
  await expect(page.locator('.watch-filters')).toHaveCount(0);
  // Tools can remain as disabled controls inside a closed disclosure, or be absent during reset.
  await expect(page.locator('.print-action:enabled')).toHaveCount(0);
  await expect(
    page
      .getByRole('button', { name: 'Скачать данные (JSON)', includeHidden: true })
      .and(page.locator(':enabled')),
  ).toHaveCount(0);
  await expect(
    page.locator('.tracker-list-heading .small-copy').filter({ hasText: /^1 из 20/ }),
  ).toHaveCount(0);
}

test('successful guest reset clears cards history and print data even when the new list fails', async ({
  page,
}) => {
  await seedPreviousGuest(page);
  await page.getByRole('button', { name: 'История', exact: true }).click();
  await expect(page.locator('.history-scroll')).toBeVisible();

  let resetStarted = false;
  page.on('request', (request) => {
    if (request.url().endsWith('/api/v1/session') && request.method() === 'DELETE') {
      resetStarted = true;
    }
  });
  await page.route('**/api/v1/watches', (route) => {
    if (resetStarted && route.request().method() === 'GET') {
      return route.fulfill({
        status: 503,
        json: { detail: 'Synthetic new guest list failure' },
      });
    }
    return route.continue();
  });

  await confirmReset(page);
  await expect(page.getByText('Создана новая гостевая сессия.', { exact: true })).toBeVisible();
  await expect(
    page.getByRole('heading', { name: 'Не удалось загрузить направления' }),
  ).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toHaveCount(0);
  await expectNoPreviousGuestData(page);
  expect(await (await page.request.get('/api/v1/watches')).json()).toEqual([]);

  await page.unroute('**/api/v1/watches');
  await page.getByRole('button', { name: 'Обновить направления', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  await expectNoPreviousGuestData(page);
});

test('a delayed old-owner list cannot repopulate the new guest after reset', async ({ page }) => {
  await seedPreviousGuest(page);
  let releaseOldResponse!: () => void;
  const oldResponseGate = new Promise<void>((resolve) => {
    releaseOldResponse = resolve;
  });
  let oldResponseCaptured!: () => void;
  const captured = new Promise<void>((resolve) => {
    oldResponseCaptured = resolve;
  });
  let oldResponseSettled!: () => void;
  const settled = new Promise<void>((resolve) => {
    oldResponseSettled = resolve;
  });
  let first = true;
  await page.route('**/api/v1/watches', async (route) => {
    if (route.request().method() !== 'GET') return route.continue();
    if (!first) {
      return route.fulfill({
        status: 503,
        json: { detail: 'Synthetic new guest list failure' },
      });
    }
    first = false;
    const response = await route.fetch();
    oldResponseCaptured();
    try {
      await oldResponseGate;
      await route.fulfill({ response });
    } catch {
      // Canceling the old request is an expected way to reject its stale response.
    } finally {
      oldResponseSettled();
    }
  });

  try {
    await page.getByRole('button', { name: 'Обновить направления', exact: true }).click();
    await captured;
    await confirmReset(page);
    await expect(page.getByText('Создана новая гостевая сессия.', { exact: true })).toBeVisible();
    await expectNoPreviousGuestData(page);
    releaseOldResponse();
    await settled;
    await expect(
      page.getByRole('heading', { name: 'Не удалось загрузить направления' }),
    ).toBeVisible();
    await expectNoPreviousGuestData(page);
    expect(await (await page.request.get('/api/v1/watches')).json()).toEqual([]);
  } finally {
    releaseOldResponse();
  }
});

test('failed deletion recovers the same owner only after a fresh authorized read', async ({
  page,
}) => {
  await seedPreviousGuest(page);
  let deleteFailed = false;
  let authorizedReads = 0;
  let releaseFreshRead!: () => void;
  const freshReadGate = new Promise<void>((resolve) => {
    releaseFreshRead = resolve;
  });
  await page.route('**/api/v1/session', (route) => {
    if (route.request().method() === 'DELETE') {
      deleteFailed = true;
      return route.fulfill({
        status: 503,
        json: { detail: 'Synthetic deletion failure' },
      });
    }
    return route.continue();
  });
  await page.route('**/api/v1/watches', async (route) => {
    if (deleteFailed && route.request().method() === 'GET') {
      authorizedReads++;
      await freshReadGate;
    }
    await route.continue();
  });

  try {
    await confirmReset(page);
    await expect(page.getByRole('alert')).toContainText(
      'Сервис временно недоступен. Попробуйте ещё раз чуть позже.',
    );
    await expectNoPreviousGuestData(page);
    expect(await (await page.request.get('/api/v1/watches')).json()).toHaveLength(1);
    await expect(page.getByText('Создана новая гостевая сессия.', { exact: true })).toHaveCount(0);
    releaseFreshRead();
    await expect(page.locator('.direction-card')).toHaveCount(1);
    await expect(page.locator('.direction-card')).toContainText(oldTitle);
    expect(authorizedReads).toBeGreaterThan(0);
  } finally {
    releaseFreshRead();
  }
});

test('confirmed deletion followed by failed creation never restores the previous private UI', async ({
  page,
}) => {
  await seedPreviousGuest(page);
  let releaseCreation!: () => void;
  const creationGate = new Promise<void>((resolve) => {
    releaseCreation = resolve;
  });
  let creationRequests = 0;
  let deletes = 0;
  page.on('request', (request) => {
    if (request.url().endsWith('/api/v1/session') && request.method() === 'DELETE') deletes++;
  });
  await page.route('**/api/v1/session', async (route) => {
    if (route.request().method() !== 'POST') return route.continue();
    creationRequests++;
    await creationGate;
    await route.fulfill({
      status: 503,
      json: { detail: 'Synthetic session creation failure' },
    });
  });

  try {
    await confirmReset(page);
    await expect.poll(() => creationRequests).toBeGreaterThan(0);
    await expectNoPreviousGuestData(page);
    await expect(page.getByRole('heading', { name: 'Срок гостевой сессии истёк' })).toHaveCount(0);
    releaseCreation();
    await expect(
      page.getByRole('alert').filter({ hasText: 'Сервис временно недоступен' }).first(),
    ).toBeVisible();
    await expect(
      page.getByRole('heading', { name: 'Не удалось загрузить направления' }),
    ).toBeVisible();
    await expectNoPreviousGuestData(page);
    expect((await page.request.get('/api/v1/watches')).status()).toBe(401);
    expect(deletes).toBe(1);
  } finally {
    releaseCreation();
  }
});
