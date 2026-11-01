import { expect, test } from '@playwright/test';

test('expiry during a readonly restore check cannot reopen the draft', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  await page.getByLabel('Вуз', { exact: true }).fill('Expires during check');
  await expect(page.getByRole('status').filter({ hasText: 'Черновик сохранён' })).toBeVisible();
  const expiry = await page.evaluate(() => JSON.parse(sessionStorage.getItem('admitflow-draft-v1')!).expiresAt as number);
  page.once('dialog', dialog => dialog.accept());
  await page.reload();
  await expect(page.getByRole('region', { name: 'Есть несохранённый черновик' })).toBeVisible();
  await page.clock.install();
  let release!: () => void;
  let checking = false;
  const gate = new Promise<void>(resolve => { release = resolve; });
  await page.route('**/api/v1/watches', async route => { checking = true; await gate; await route.continue(); });
  await page.getByRole('button', { name: 'Восстановить черновик', exact: true }).click();
  try {
    await expect.poll(() => checking).toBe(true);
    // Change wall time only: the network timeout must not cause this refusal.
    await page.clock.setSystemTime(new Date(expiry + 1));
  } finally { release(); }
  await expect(page.locator('.tracker-notice')).toContainText('Черновик больше недоступен');
  await expect(page.locator('.direction-form, .draft-recovery')).toHaveCount(0);
  expect(await page.evaluate(() => sessionStorage.getItem('admitflow-draft-v1'))).toBeNull();
});

for (const theme of ['light', 'dark']) test(`draft recovery is keyboard accessible at320px in ${theme} theme`, async ({ page }, info) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.setViewportSize({ width: 320, height: 780 });
  await page.addInitScript(value => localStorage.setItem('abiturient-theme', value), theme);
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  await page.getByLabel('Вуз', { exact: true }).fill('У'.repeat(160));
  await page.getByLabel('Направление и конкурсная группа').fill('Н'.repeat(200));
  await page.getByLabel('Ссылка на конкурсный список').fill('https://example.org/' + 'a'.repeat(1800));
  await page.getByLabel('Ваш номер в списке').fill('1000000');
  await page.getByLabel('Бюджетных мест', { exact: true }).fill('1000000');
  await expect(page.getByRole('status').filter({ hasText: 'Черновик сохранён' })).toBeVisible();
  page.once('dialog', dialog => dialog.accept());
  await page.reload();
  const recovery = page.getByRole('region', { name: 'Есть несохранённый черновик' });
  await expect(recovery).toBeVisible();
  await recovery.locator('summary').focus();
  await page.keyboard.press('Enter');
  await expect(recovery.locator('details')).toHaveAttribute('open', '');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await recovery.getByRole('button', { name: 'Восстановить черновик', exact: true }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading', { name: 'Добавить направление', exact: true })).toBeFocused();
  await expect(page.getByLabel('Ваш номер в списке')).toHaveValue('1000000');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.locator('.direction-form').screenshot({ path: info.outputPath(`restored-${theme}.png`) });
});

for (const failure of ['denied', 'quota']) test(`the form remains usable when local storage is ${failure}`, async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.addInitScript(mode => {
    if (mode === 'denied') Object.defineProperty(window, 'sessionStorage', { get() { throw new DOMException('denied', 'SecurityError'); } });
    else {
      const set = Storage.prototype.setItem;
      Storage.prototype.setItem = function (key, value) {
        if (this === sessionStorage) throw new DOMException('full', 'QuotaExceededError');
        return set.call(this, key, value);
      };
    }
  }, failure);
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  await page.getByLabel('Вуз', { exact: true }).fill('Storage unavailable');
  await page.getByLabel('Направление и конкурсная группа').fill('Still usable');
  await page.getByLabel('Ссылка на конкурсный список').fill('https://example.org/list');
  await page.getByLabel('Ваш номер в списке').fill('10');
  await page.getByLabel('Бюджетных мест', { exact: true }).fill('20');
  await expect(page.getByRole('status').filter({ hasText: 'Не удалось сохранить черновик' })).toBeVisible();
  expect((await (await page.request.get('/api/v1/watches')).json()).length).toBe(0);
  await page.getByRole('button', { name: 'Сохранить направление', exact: true }).click();
  await expect(page.locator('.direction-card')).toHaveCount(1);
});

for (const mode of ['create', 'update']) test(`reload after a lost ${mode} response reuses its stored key without duplicating history`, async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.goto('/tracker');
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  const values = { rank: 10, seats: 20, excluded: 0, noConsent: 0 };
  let watchId: string | undefined;
  if (mode === 'update') {
    const watch = await (await page.request.post('/api/v1/watches', { headers: { 'X-Requested-With': 'abiturient' }, data: { university: 'Retry owner', title: 'Retry group', sourceUrl: 'https://example.org/list', values } })).json();
    watchId = watch.id;
    await page.reload();
    await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
    await page.getByLabel('Ваш номер в списке').fill('11');
  } else {
    await page.getByRole('button', { name: 'Добавить первое направление' }).click();
    await page.getByLabel('Вуз', { exact: true }).fill('Retry owner');
    await page.getByLabel('Направление и конкурсная группа').fill('Retry group');
    await page.getByLabel('Ссылка на конкурсный список').fill('https://example.org/list');
    await page.getByLabel('Ваш номер в списке').fill('10');
    await page.getByLabel('Бюджетных мест', { exact: true }).fill('20');
  }
  const pattern = mode === 'update' ? '**/api/v1/watches/*/snapshots' : '**/api/v1/watches';
  let originalKey: string | undefined;
  await page.route(pattern, async route => {
    if (route.request().method() !== 'POST') return route.continue();
    originalKey = route.request().headers()['idempotency-key'];
    expect((await route.fetch()).status()).toBe(201);
    await route.abort('failed');
  });
  const saveLabel = mode === 'update' ? 'Сохранить обновление' : 'Сохранить направление';
  await page.getByRole('button', { name: saveLabel, exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Не удалось связаться');
  expect(await page.evaluate(() => JSON.parse(sessionStorage.getItem('admitflow-draft-v1')!).intent.key)).toBe(originalKey);
  await page.unroute(pattern);
  if (watchId) expect((await page.request.post(`/api/v1/watches/${watchId}/snapshots`, { headers: { 'X-Requested-With': 'abiturient' }, data: { ...values, rank: 12 } })).status()).toBe(201);
  page.once('dialog', dialog => dialog.accept());
  await page.reload();
  await page.getByRole('button', { name: 'Восстановить черновик', exact: true }).click();
  let retryKey: string | undefined;
  await page.route(pattern, async route => {
    if (route.request().method() === 'POST') retryKey = route.request().headers()['idempotency-key'];
    await route.continue();
  });
  await page.getByRole('button', { name: saveLabel, exact: true }).click();
  await expect(page.locator('.direction-form')).toHaveCount(0);
  expect(retryKey).toBe(originalKey);
  const saved = await (await page.request.get('/api/v1/export')).json();
  expect(saved.watches).toHaveLength(1);
  expect(saved.watches[0].history).toHaveLength(mode === 'update' ? 3 : 1);
  expect(saved.watches[0].latest.values.rank).toBe(mode === 'update' ? 12 : 10);
  expect(await page.evaluate(() => sessionStorage.getItem('admitflow-draft-v1'))).toBeNull();
});

test('a cookie owner replacement without a storage event cannot restore the previous draft', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  await page.getByLabel('Вуз', { exact: true }).fill('Previous owner secret');
  await expect(page.getByRole('status').filter({ hasText: 'Черновик сохранён' })).toBeVisible();
  const previousScope = await page.evaluate(() => JSON.parse(sessionStorage.getItem('admitflow-draft-v1')!).scope);
  await page.request.delete('/api/v1/session', { headers: { 'X-Requested-With': 'abiturient' } });
  await page.request.post('/api/v1/session', { headers: { 'X-Requested-With': 'abiturient' } });
  expect((await (await page.request.get('/api/v1/session')).json()).draftScope).not.toBe(previousScope);
  page.once('dialog', dialog => dialog.accept());
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  await expect(page.getByRole('region', { name: 'Есть несохранённый черновик' })).toHaveCount(0);
  await expect(page.locator('body')).not.toContainText('Previous owner secret');
  expect(await page.evaluate(() => sessionStorage.getItem('admitflow-draft-v1'))).toBeNull();
});

test('restore revalidates an owner changed while the preview is already open', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  await page.getByLabel('Вуз', { exact: true }).fill('Old active preview');
  await expect(page.getByRole('status').filter({ hasText: 'Черновик сохранён' })).toBeVisible();
  page.once('dialog', dialog => dialog.accept());
  await page.reload();
  await expect(page.getByRole('region', { name: 'Есть несохранённый черновик' })).toBeVisible();
  await page.request.delete('/api/v1/session', { headers: { 'X-Requested-With': 'abiturient' } });
  await page.request.post('/api/v1/session', { headers: { 'X-Requested-With': 'abiturient' } });
  let posts = 0;
  page.on('request', request => { if (request.method() === 'POST') posts++; });
  await page.getByRole('button', { name: 'Восстановить черновик', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Гостевой доступ изменён' })).toBeVisible();
  await expect(page.locator('.direction-form, .draft-recovery')).toHaveCount(0);
  expect(posts).toBe(0);
  expect(await page.evaluate(() => sessionStorage.getItem('admitflow-draft-v1'))).toBeNull();
});

test('expired local draft disappears without extending its lifetime', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  await page.getByLabel('Вуз', { exact: true }).fill('Expiring draft');
  await expect(page.getByRole('status').filter({ hasText: 'Черновик сохранён' })).toBeVisible();
  page.once('dialog', dialog => dialog.accept());
  await page.reload();
  const recovery = page.getByRole('region', { name: 'Есть несохранённый черновик' });
  await expect(recovery).toBeVisible();
  await page.clock.install();
  // Re-mount so the already installed clock owns the expiry timer.
  await page.getByRole('link', { name: 'Абитуриент — в начало' }).click();
  await page.getByRole('link', { name: 'Мои направления →', exact: true }).click();
  await expect(recovery).toBeVisible();
  await page.clock.fastForward(30 * 60_000 + 1);
  await expect(recovery).toHaveCount(0);
  expect(await page.evaluate(() => sessionStorage.getItem('admitflow-draft-v1'))).toBeNull();
  expect((await (await page.request.get('/api/v1/watches')).json()).length).toBe(0);
});

test('loss of guest access clears local recovery before explicit reset', async ({ page, context }) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  await page.getByLabel('Вуз', { exact: true }).fill('Private draft');
  await expect(page.getByRole('status').filter({ hasText: 'Черновик сохранён' })).toBeVisible();
  await context.clearCookies();
  await page.getByRole('button', { name: 'Обновить направления', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Срок гостевой сессии истёк' })).toBeVisible();
  expect(await page.evaluate(() => sessionStorage.getItem('admitflow-draft-v1'))).toBeNull();
  await page.getByRole('button', { name: 'Начать новую сессию', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  await expect(page.getByRole('region', { name: 'Есть несохранённый черновик' })).toHaveCount(0);
});

test('a stale or deleted edit draft stays readable without replacing newer data', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.goto('/tracker');
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  const watch = await (await page.request.post('/api/v1/watches', { headers: { 'X-Requested-With': 'abiturient' }, data: { university: 'Versioned', title: 'Versioned group', sourceUrl: 'https://example.org/list', values: { rank: 10, seats: 20, excluded: 0, noConsent: 0 } } })).json();
  await page.reload();
  await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
  await page.getByLabel('Ваш номер в списке').fill('11');
  await expect(page.getByRole('status').filter({ hasText: 'Черновик сохранён' })).toBeVisible();
  expect((await page.request.post(`/api/v1/watches/${watch.id}/snapshots`, { headers: { 'X-Requested-With': 'abiturient' }, data: { rank: 12, seats: 20, excluded: 0, noConsent: 0 } })).status()).toBe(201);
  page.once('dialog', dialog => dialog.accept());
  await page.reload();
  const recovery = page.getByRole('region', { name: 'Есть несохранённый черновик' });
  await expect(recovery).toContainText('более новое сохранение');
  await expect(recovery.getByRole('button', { name: 'Восстановить черновик' })).toBeDisabled();
  await recovery.getByText('Посмотреть поля черновика', { exact: true }).click();
  await expect(recovery).toContainText('11 / 20');
  await expect(page.locator('.direction-result strong')).toHaveText('12');
  expect((await (await page.request.get(`/api/v1/watches/${watch.id}`)).json()).history).toHaveLength(2);
  expect((await page.request.delete(`/api/v1/watches/${watch.id}`, { headers: { 'X-Requested-With': 'abiturient' } })).status()).toBe(204);
  await page.getByRole('button', { name: 'Обновить направления', exact: true }).click();
  await expect(recovery).toContainText('Направление уже удалено');
  await expect(recovery.getByRole('button', { name: 'Восстановить черновик' })).toBeDisabled();
  await expect(page.locator('.direction-card')).toHaveCount(0);
});

test('an already open edit cannot overwrite a newer snapshot', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.goto('/tracker');
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  const values = { rank: 10, seats: 20, excluded: 0, noConsent: 0 };
  const watch = await (await page.request.post('/api/v1/watches', { headers: { 'X-Requested-With': 'abiturient' }, data: { university: 'Concurrent', title: 'Concurrent group', sourceUrl: 'https://example.org/list', values } })).json();
  await page.reload();
  await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
  await page.getByLabel('Ваш номер в списке').fill('11');
  await page.request.post(`/api/v1/watches/${watch.id}/snapshots`, { headers: { 'X-Requested-With': 'abiturient' }, data: { ...values, rank: 12 } });
  await page.getByRole('button', { name: 'Сохранить обновление', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('более новое сохранение');
  await expect(page.getByLabel('Ваш номер в списке')).toHaveValue('11');
  const saved = await (await page.request.get(`/api/v1/watches/${watch.id}`)).json();
  expect(saved.latest.values.rank).toBe(12);
  expect(saved.history).toHaveLength(2);
});

test('reload offers explicit restore and discard without writing directions', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  await page.getByLabel('Вуз', { exact: true }).fill('Reload draft');
  await page.getByLabel('Направление и конкурсная группа').fill('Restorable title');
  await expect(page.getByRole('status').filter({ hasText: 'Черновик сохранён' })).toBeVisible();
  page.once('dialog', dialog => dialog.accept());
  await page.reload();
  const recovery = page.getByRole('region', { name: 'Есть несохранённый черновик' });
  await expect(recovery).toContainText('Restorable title');
  await expect(page.locator('.direction-form')).toHaveCount(0);
  await recovery.getByRole('button', { name: 'Восстановить черновик', exact: true }).click();
  await expect(page.getByLabel('Вуз', { exact: true })).toHaveValue('Reload draft');
  await expect(page.getByLabel('Направление и конкурсная группа')).toHaveValue('Restorable title');
  expect((await (await page.request.get('/api/v1/watches')).json()).length).toBe(0);
  page.once('dialog', dialog => dialog.accept());
  await page.reload();
  await recovery.getByRole('button', { name: 'Удалить черновик', exact: true }).click();
  await expect(recovery).toHaveCount(0);
  expect(await page.evaluate(() => sessionStorage.getItem('admitflow-draft-v1'))).toBeNull();
  await expect(page.getByRole('button', { name: 'Добавить направление', exact: true })).toBeFocused();
  expect((await (await page.request.get('/api/v1/watches')).json()).length).toBe(0);
});

test('typing only stores a local draft and saves its retry key before sending', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  await page.getByLabel('Вуз', { exact: true }).fill('Local draft');
  await page.getByLabel('Направление и конкурсная группа').fill('Incomplete direction');
  await expect(page.getByRole('status').filter({ hasText: 'Черновик сохранён' })).toBeVisible();
  expect(await page.evaluate(() => JSON.parse(sessionStorage.getItem('admitflow-draft-v1')!).draft.title)).toBe('Incomplete direction');
  expect((await (await page.request.get('/api/v1/watches')).json()).length).toBe(0);
  await page.getByLabel('Ссылка на конкурсный список').fill('https://example.org/list');
  await page.getByLabel('Ваш номер в списке').fill('10');
  await page.getByLabel('Бюджетных мест', { exact: true }).fill('20');
  let key: string | undefined;
  await page.route('**/api/v1/watches', async route => {
    if (route.request().method() !== 'POST') return route.continue();
    key = route.request().headers()['idempotency-key'];
    const stored = await page.evaluate(() => JSON.parse(sessionStorage.getItem('admitflow-draft-v1')!));
    expect(stored.intent.key).toBe(key);
    await route.abort('failed');
  });
  await page.getByRole('button', { name: 'Сохранить направление', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Не удалось связаться');
  expect(key).toMatch(/^[a-f0-9-]{36}$/);
  await expect(page.getByLabel('Вуз', { exact: true })).toHaveValue('Local draft');
  await page.unroute('**/api/v1/watches');
  await page.getByRole('button', { name: 'Сохранить направление', exact: true }).click();
  await expect(page.locator('.direction-card')).toHaveCount(1);
  expect(await page.evaluate(() => sessionStorage.getItem('admitflow-draft-v1'))).toBeNull();
  await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
  await page.getByLabel('Ваш номер в списке').fill('11');
  await expect(page.getByRole('status').filter({ hasText: 'Черновик сохранён' })).toBeVisible();
  page.once('dialog', dialog => dialog.accept());
  await page.getByRole('button', { name: 'Закрыть форму' }).click();
  await expect(page.locator('.direction-form')).toHaveCount(0);
  expect(await page.evaluate(() => sessionStorage.getItem('admitflow-draft-v1'))).toBeNull();
});
