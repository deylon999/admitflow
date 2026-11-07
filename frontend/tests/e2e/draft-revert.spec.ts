import { expect, test } from '@playwright/test';

test.beforeEach(() => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
});

test('clearing a new form removes the previously typed draft', async ({ page }) => {
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  const university = page.getByLabel('Вуз', { exact: true });
  await university.fill('Erased university');
  await expect(page.getByRole('status').filter({ hasText: 'Черновик сохранён' })).toBeVisible();
  await university.fill('');
  await expect
    .poll(() => page.evaluate(() => sessionStorage.getItem('admitflow-draft-v1')))
    .toBeNull();
  await expect(page.getByRole('status').filter({ hasText: 'Черновик сохранён' })).toHaveCount(0);
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  await expect(page.locator('.draft-recovery')).toHaveCount(0);
});

test('reverting an edit removes the abandoned values from recovery', async ({ page }) => {
  await page.goto('/tracker');
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  const watch = await (
    await page.request.post('/api/v1/watches', {
      headers: { 'X-Requested-With': 'abiturient' },
      data: {
        university: 'Reverted edit',
        title: 'Initial values',
        sourceUrl: 'https://example.org/list',
        values: { rank: 10, seats: 20, excluded: 0, noConsent: 0 },
      },
    })
  ).json();
  await page.reload();
  await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
  const rank = page.getByLabel('Ваш номер в списке');
  await rank.fill('11');
  await expect(page.getByRole('status').filter({ hasText: 'Черновик сохранён' })).toBeVisible();
  await rank.fill('10');
  await expect
    .poll(() => page.evaluate(() => sessionStorage.getItem('admitflow-draft-v1')))
    .toBeNull();
  await page.reload();
  await expect(page.locator('.direction-result strong')).toHaveText('10');
  await expect(page.locator('.draft-recovery')).toHaveCount(0);
  const saved = await (await page.request.get(`/api/v1/watches/${watch.id}`)).json();
  expect(saved.latest.values.rank).toBe(10);
  expect(saved.history).toHaveLength(1);
});

test('restoring a pristine pending save keeps its retry key and original expiry', async ({
  page,
}) => {
  await page.goto('/tracker');
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  const watch = await (
    await page.request.post('/api/v1/watches', {
      headers: { 'X-Requested-With': 'abiturient' },
      data: {
        university: 'Unchanged retry',
        title: 'Unchanged group',
        sourceUrl: 'https://example.org/list',
        values: { rank: 10, seats: 20, excluded: 0, noConsent: 0 },
      },
    })
  ).json();
  await page.reload();
  await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
  const pattern = '**/api/v1/watches/*/snapshots';
  let originalKey: string | undefined;
  await page.route(pattern, async (route) => {
    originalKey = route.request().headers()['idempotency-key'];
    expect((await route.fetch()).status()).toBe(201);
    await route.abort('failed');
  });
  await page.getByRole('button', { name: 'Сохранить обновление', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Не удалось связаться');
  const original = await page.evaluate(() =>
    JSON.parse(sessionStorage.getItem('admitflow-draft-v1')!),
  );
  expect(original.intent.key).toBe(originalKey);
  await page.unroute(pattern);
  await page.clock.install();
  await page.clock.fastForward(1000);
  await page.reload();
  await page.getByRole('button', { name: 'Восстановить черновик', exact: true }).click();
  await expect(page.getByLabel('Ваш номер в списке')).toHaveValue('10');
  const restored = await page.evaluate(() =>
    JSON.parse(sessionStorage.getItem('admitflow-draft-v1')!),
  );
  expect(restored.expiresAt).toBe(original.expiresAt);
  expect(restored.intent.key).toBe(originalKey);
  let retryKey: string | undefined;
  await page.route(pattern, async (route) => {
    retryKey = route.request().headers()['idempotency-key'];
    await route.continue();
  });
  await page.getByRole('button', { name: 'Сохранить обновление', exact: true }).click();
  await expect(page.locator('.direction-form')).toHaveCount(0);
  expect(retryKey).toBe(originalKey);
  const saved = await (await page.request.get(`/api/v1/watches/${watch.id}`)).json();
  expect(saved.latest.values.rank).toBe(10);
  expect(saved.history).toHaveLength(2);
  expect(await page.evaluate(() => sessionStorage.getItem('admitflow-draft-v1'))).toBeNull();
});

test('reverting after a failed save stores the current fields without losing the intent', async ({
  page,
}) => {
  await page.goto('/tracker');
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  await page.request.post('/api/v1/watches', {
    headers: { 'X-Requested-With': 'abiturient' },
    data: {
      university: 'Reverted retry',
      title: 'Pending group',
      sourceUrl: 'https://example.org/list',
      values: { rank: 10, seats: 20, excluded: 0, noConsent: 0 },
    },
  });
  await page.reload();
  await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
  const rank = page.getByLabel('Ваш номер в списке');
  await rank.fill('11');
  await page.route('**/api/v1/watches/*/snapshots', (route) => route.abort('failed'));
  await page.getByRole('button', { name: 'Сохранить обновление', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Не удалось связаться');
  const originalIntent = await page.evaluate(
    () => JSON.parse(sessionStorage.getItem('admitflow-draft-v1')!).intent,
  );
  await rank.fill('10');
  await expect
    .poll(() =>
      page.evaluate(
        () => JSON.parse(sessionStorage.getItem('admitflow-draft-v1')!).draft.values.rank,
      ),
    )
    .toBe('10');
  expect(
    await page.evaluate(() => JSON.parse(sessionStorage.getItem('admitflow-draft-v1')!).intent),
  ).toEqual(originalIntent);
  await page.reload();
  await page.getByRole('button', { name: 'Восстановить черновик', exact: true }).click();
  await expect(page.getByLabel('Ваш номер в списке')).toHaveValue('10');
});

test('restoring a dirty draft and refocusing its form do not extend the stored expiry', async ({
  page,
}) => {
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  await page.getByLabel('Вуз', { exact: true }).fill('Original expiry');
  await expect(page.getByRole('status').filter({ hasText: 'Черновик сохранён' })).toBeVisible();
  const expiry = await page.evaluate(
    () => JSON.parse(sessionStorage.getItem('admitflow-draft-v1')!).expiresAt,
  );
  await page.clock.install();
  await page.clock.fastForward(1000);
  page.once('dialog', (dialog) => dialog.accept());
  await page.reload();
  await page.getByRole('button', { name: 'Восстановить черновик', exact: true }).click();
  await expect(page.getByLabel('Вуз', { exact: true })).toHaveValue('Original expiry');
  await page.clock.fastForward(1000);
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  expect(
    await page.evaluate(() => JSON.parse(sessionStorage.getItem('admitflow-draft-v1')!).expiresAt),
  ).toBe(expiry);
  await page.clock.fastForward(30 * 60_000);
  await expect
    .poll(() => page.evaluate(() => sessionStorage.getItem('admitflow-draft-v1')))
    .toBeNull();
});

for (const writesBlocked of [false, true]) {
  test(`failed draft removal reports the failure with writes ${writesBlocked ? 'blocked' : 'available'}`, async ({
    page,
  }) => {
    await page.goto('/tracker');
    await page.getByRole('button', { name: 'Добавить первое направление' }).click();
    const university = page.getByLabel('Вуз', { exact: true });
    await university.fill('Reverted storage failure');
    await expect(page.getByRole('status').filter({ hasText: 'Черновик сохранён' })).toBeVisible();
    await page.evaluate((blockWrites) => {
      const remove = Storage.prototype.removeItem;
      const set = Storage.prototype.setItem;
      Storage.prototype.removeItem = function (key) {
        if (this === sessionStorage && key === 'admitflow-draft-v1')
          throw new DOMException('denied', 'SecurityError');
        return remove.call(this, key);
      };
      if (blockWrites) {
        Storage.prototype.setItem = function (key, value) {
          if (this === sessionStorage && key === 'admitflow-draft-v1')
            throw new DOMException('full', 'QuotaExceededError');
          return set.call(this, key, value);
        };
      }
    }, writesBlocked);
    await university.fill('');
    await expect(
      page.getByRole('status').filter({ hasText: 'Не удалось удалить черновик' }),
    ).toBeVisible();
    await expect(page.getByRole('status').filter({ hasText: 'Черновик сохранён' })).toHaveCount(0);
    await expect(university).toHaveValue('');
    if (!writesBlocked) {
      expect(
        await page.evaluate(
          () => JSON.parse(sessionStorage.getItem('admitflow-draft-v1')!).draft.university,
        ),
      ).toBe('');
      await page.reload();
      await page.getByRole('button', { name: 'Восстановить черновик', exact: true }).click();
      await expect(university).toHaveValue('');
    }
  });
}
