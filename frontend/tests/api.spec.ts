import { test, expect } from '@playwright/test';
const record = { id: 'subscription-real-id', createdAt: '2026-11-01T00:00:00Z', group: { id: 'source-group', title: 'Архивный конкурс', universityName: 'Проверенный вуз', year: 2026, seats: 12, sourceUrl: 'https://example.org/list', dataKind: 'archive' } };
for (const status of [400, 401, 403, 404, 409, 410, 422, 429, 500])
    test(`subscriptions ${status}: no demo fallback and retry`, async ({ page }) => { let fail = true; let starts = 0; await page.route('**/api/v1/session', route => { starts++; return route.fulfill({ status: 204 }); }); await page.route('**/api/v1/subscriptions', route => route.fulfill(fail ? { status, json: { detail: 'raw internal error' } } : { json: [] })); await page.goto('/app/watchlist'); await expect(page.getByRole('alert')).toBeVisible(); await expect(page.getByText('Направлений пока нет', { exact: true })).toHaveCount(0); await expect(page.locator('.af-program-card')).toHaveCount(0); expect(starts).toBe(0); fail = false; await page.getByRole('button', { name: status === 401 ? 'Начать гостевую сессию' : 'Повторить', exact: true }).click(); await expect(page.getByText('Направлений пока нет', { exact: true })).toBeVisible(); expect(starts).toBe(status === 401 ? 1 : 0); });
for (const body of [null, {}, [{ id: 'broken' }]])
    test(`malformed subscriptions ${JSON.stringify(body)} is error not empty`, async ({ page }) => { await page.route('**/api/v1/subscriptions', route => route.fulfill({ contentType:'application/json', body: JSON.stringify(body) })); await page.goto('/app/watchlist'); await expect(page.getByRole('alert')).toContainText('Не удалось проверить'); await expect(page.getByText('Направлений пока нет', { exact: true })).toHaveCount(0); });
test('network failure is retryable; real IDs open and delete succeeds only after server confirmation', async ({ page }) => { let fail = true, deleted = false; await page.route('**/api/v1/subscriptions', route => fail ? route.abort('failed') : route.fulfill({ json: deleted ? [] : [record] })); await page.route('**/api/v1/subscriptions/subscription-real-id', route => { deleted = true; return route.fulfill({ status: 204 }); }); await page.goto('/app/watchlist'); await expect(page.getByRole('alert')).toBeVisible(); fail = false; await page.getByRole('button', { name: 'Повторить', exact: true }).click(); await page.getByRole('link', { name: 'Открыть конкурс', exact: false }).click(); await expect(page).toHaveURL(/subscription-real-id$/); await expect(page.getByRole('heading', { name: 'Архивный конкурс' })).toBeVisible(); page.once('dialog', d => d.accept()); await page.getByRole('button', { name: 'Удалить подписку' }).click(); await expect(page.getByRole('status').filter({hasText:'Подписка удалена'})).toBeVisible(); await expect(page.getByRole('heading', { name: 'Запись не найдена' })).toBeVisible(); });
test('owner change discards cards and later 401 keeps private data hidden', async ({ page }) => { let status = 200; await page.route('**/api/v1/subscriptions', r => r.fulfill(status === 200 ? { json: [record] } : { status, json: {} })); await page.goto('/app/watchlist'); await expect(page.getByText('Проверенный вуз')).toBeVisible(); status = 503; await page.evaluate(() => dispatchEvent(new StorageEvent('storage', { key: 'admitflow-session-change' }))); await expect(page.getByRole('alert')).toBeVisible(); status = 401; await page.getByRole('button', { name: 'Повторить', exact: true }).click(); await expect(page.getByRole('alert')).toContainText('гостевой'); await expect(page.getByText('Проверенный вуз')).toHaveCount(0); });
test('catalog invalid DTO and HTML errors never render fake university', async ({ page }) => { await page.route('**/api/v1/catalog/universities?**', r => r.fulfill({ json: { items: [{ id: 'x' }], total: 1, nextOffset: null, regions: [], registryEdition: 2025 } })); await page.goto('/universities'); await expect(page.getByRole('alert')).toContainText('Не удалось проверить'); await expect(page.locator('.af-program-card')).toHaveCount(0); });
test('unsupported forecast requires explicit demo and can leave demo', async ({ page }) => { await page.goto('/app/forecast/example'); await expect(page.getByRole('heading', { name: 'Функция пока не подключена' })).toBeVisible(); await expect(page.locator('.af-spotlight')).toHaveCount(0); await page.getByRole('link', { name: 'Посмотреть демо интерфейса' }).click(); await expect(page.getByRole('heading', { name: 'Демонстрация интерфейса' })).toBeVisible(); await expect(page.locator('.af-spotlight')).toContainText('74%'); await page.getByRole('link', { name: 'Выйти из демо' }).click(); await expect(page.locator('.af-spotlight')).toHaveCount(0); });
test('lookup save retains token and input on failed save, retries real confirmation', async ({ page }) => { let saves = 0; await page.route('**/api/v1/groups?**', r => r.fulfill({ json: { items: [{ id: 'group', title: 'Подтверждённый конкурс', universityName: 'Вуз', year: 2026, sourceId: 'source', lookupAvailable: true }], total: 1, nextCursor: null } })); await page.route('**/api/v1/sources/source/lookup', r => r.fulfill({ json: { found: true, group: { title: 'Подтверждённый конкурс', year: 2026 }, candidate: { officialRank: 7 }, confirmationToken: 'test-token', expiresAt: '2030-01-01T00:00:00Z' } })); await page.route('**/api/v1/subscriptions', r => { if (r.request().method() === 'GET') return r.fulfill({ json: [{ ...record, id: 'saved-id' }] }); saves++; expect(r.request().postDataJSON()).toEqual({ confirmationToken: 'test-token' }); return r.fulfill(saves === 1 ? { status: 503, json: {} } : { status: 201, json: { id: 'saved-id', createdAt: '2026-11-10T00:00:00Z' } }); }); await page.goto('/app/watchlist/add'); await page.getByRole('button', { name: 'Выбрать', exact: true }).click(); await page.getByLabel('Публичный код в списке').fill('123-45'); await page.getByRole('button', { name: 'Найти запись', exact: true }).click(); await expect(page.getByText(/Номер в официальном списке: 7/)).toBeVisible(); await page.getByRole('button', { name: 'Подтвердить и сохранить' }).click(); await expect(page.getByRole('alert')).toBeVisible(); await expect(page.getByLabel('Публичный код в списке')).toHaveValue('123-45'); await expect(page.getByText('Сервер подтвердил сохранение подписки.')).toHaveCount(0); await page.getByRole('button', { name: 'Подтвердить и сохранить' }).click(); await expect(page.getByText('Сервер подтвердил сохранение подписки.')).toBeVisible(); expect(saves).toBe(2); await expect(page.getByRole('link', { name: 'Открыть направление' })).toHaveAttribute('href', '/app/watchlist/saved-id'); await page.getByRole('link', { name: 'Открыть направление' }).click(); await expect(page.getByRole('heading', { name: 'Архивный конкурс' })).toBeVisible(); });

test('background refresh keeps dated data on server failure and drops it on 401',async({page})=>{let status=200;await page.route('**/api/v1/subscriptions',r=>r.fulfill(status===200?{json:[record]}:{status,json:{}}));await page.goto('/app/watchlist');await expect(page.getByText('Проверенный вуз')).toBeVisible();status=503;await page.getByRole('button',{name:'Обновить',exact:true}).click();await expect(page.getByRole('alert')).toContainText('Показаны предыдущие сведения');await expect(page.getByText('Проверенный вуз')).toBeVisible();status=401;await page.getByRole('button',{name:'Повторить',exact:true}).click();await expect(page.getByRole('alert')).toContainText('гостевой');await expect(page.getByText('Проверенный вуз')).toHaveCount(0);});
test('native guest API starts only on request and exposes actual empty history',async({page})=>{await page.goto('/app/watchlist');await page.getByRole('button',{name:'Начать гостевую сессию'}).click();await expect(page.getByRole('heading',{name:'Направлений пока нет'})).toBeVisible();await page.locator('.af-sidebar').getByRole('link',{name:'История',exact:false}).click();await expect(page.getByRole('heading',{name:'Изменений пока нет'})).toBeVisible();});

test('unexpected success-shaped delete response is not an acknowledged deletion',async({page})=>{await page.route('**/api/v1/subscriptions',r=>r.fulfill({json:[record]}));await page.route('**/api/v1/subscriptions/subscription-real-id',r=>r.fulfill({status:200,json:{detail:'not a deletion acknowledgement'}}));await page.goto('/app/watchlist');await expect(page.getByText('Проверенный вуз')).toBeVisible();page.once('dialog',d=>d.accept());await page.getByRole('button',{name:'Удалить подписку'}).click();await expect(page.getByRole('alert')).toContainText('Не удалось проверить');await expect(page.getByText('Подписка удалена.',{exact:true})).toHaveCount(0);await expect(page.getByText('Проверенный вуз')).toBeVisible();});

const competitionInfo = { groupId: 'g1', title: '09.03.04 Программная инженерия', universityId: 'u1', universityName: 'Проверенный вуз', year: 2026, level: 'bachelor', studyForm: 'full-time', funding: 'budget', category: 'general', sourceState: 'archived',
  snapshot: { id: 's2', fetchedAt: '2026-11-03T10:00:00+00:00', sourceUpdatedAt: null, kind: 'archive', rowCount: 120, complete: true, seats: 16, sourceUrl: 'https://example.org/list' },
  warnings: ['archive', 'priorities_not_published'], prioritiesPublished: false, consentPublished: true, myRank: 3,
  history: [{ id: 's2', fetchedAt: '2026-11-03T10:00:00+00:00', rowCount: 120, seats: 16, published: true }, { id: 's1', fetchedAt: '2026-11-01T10:00:00+00:00', rowCount: 118, seats: 16, published: false }] };
const competitionRow = (rank: number) => ({ officialRank: rank, score: String(300 - rank), consent: rank % 2 === 0, priority: null, participation: rank === 2 ? 'withdrawn' : 'active', mine: rank === 3 });

test('competition list shows the official order, own row and honest warnings', async ({ page }) => {
  const queries: string[] = [];
  await page.route('**/api/v1/competitions/g1', r => r.fulfill({ json: competitionInfo }));
  await page.route('**/api/v1/competitions/g1/rows?**', r => {
    const url = new URL(r.request().url()); queries.push(url.search);
    const offset = Number(url.searchParams.get('offset') ?? 0);
    const from = Number(url.searchParams.get('rankFrom') ?? 1) + offset;
    return r.fulfill({ json: { items: Array.from({ length: 50 }, (_, i) => competitionRow(from + i)), total: 120, nextOffset: offset + 50 < 120 ? offset + 50 : null } });
  });
  await page.goto('/app/competitions/g1');
  await expect(page.locator('h1')).toContainText('Программная инженерия');
  await expect(page.locator('.af-metric').first()).toContainText('3');
  await expect(page.locator('.af-competition-warnings')).toContainText('Архивный список');
  await expect(page.locator('.af-competition-warnings')).toContainText('не публикует приоритеты');
  await expect(page.locator('thead th')).toHaveText(['№', 'Баллы', 'Согласие', 'Участие']);
  await expect(page.locator('tbody tr.is-me')).toHaveCount(1);
  await expect(page.locator('tbody tr.is-me')).toContainText('Вы');
  await expect(page.locator('tbody tr').nth(1)).toContainText('Отозвал');
  await page.getByRole('button', { name: 'Согласие есть', exact: true }).click();
  await expect.poll(() => queries.at(-1)).toContain('consent=yes');
  await page.getByRole('button', { name: 'Далее', exact: true }).click();
  await expect.poll(() => queries.at(-1)).toContain('offset=50');
  await page.getByLabel('Перейти к месту').fill('100');
  await expect.poll(() => queries.at(-1)).toContain('rankFrom=100');
  await expect.poll(() => queries.at(-1)).toContain('offset=0');
  await expect(page.locator('.af-info-row').filter({ hasText: 'показан' })).toContainText('120 строк');
  await expect(page.getByRole('link', { name: 'Официальный список ↗' })).toHaveAttribute('href', 'https://example.org/list');
  await expect(page).toHaveURL(/rankFrom=100/);
  await page.reload();
  await expect(page.getByLabel('Перейти к месту')).toHaveValue('100');
  await expect.poll(() => queries.at(-1)).toContain('consent=yes');
  await page.goBack();
  await expect(page.getByLabel('Перейти к месту')).toHaveValue('');
  await expect.poll(() => queries.at(-1)).toContain('offset=50');
});

test('competition rows with identifiers are rejected instead of rendered', async ({ page }) => {
  await page.route('**/api/v1/competitions/g1', r => r.fulfill({ json: competitionInfo }));
  await page.route('**/api/v1/competitions/g1/rows?**', r => r.fulfill({ json: { items: [{ ...competitionRow(1), candidateKey: 'secret' }], total: 1, nextOffset: null } }));
  await page.goto('/app/competitions/g1');
  await expect(page.locator('tbody tr')).toHaveCount(0);
  await expect(page.getByText('secret')).toHaveCount(0);
  await expect(page.getByRole('button', { name: /Повторить/ }).first()).toBeVisible();
});

test('competitors page shows aggregates above the guest only', async ({ page }) => {
  await page.route('**/api/v1/competitions/g1', r => r.fulfill({ json: competitionInfo }));
  await page.route('**/api/v1/competitions/g1/summary', r => r.fulfill({ json: { total: 120, seats: 16, byConsent: { yes: 60, no: 50, unknown: 10 },
    byParticipation: { unknown: 0, active: 118, withdrawn: 2, enrolled: 0 }, priorityKnown: 0, priorityFirst: 0, scoreKnown: 120,
    scoreBins: [{ lower: 180, upper: 190, count: 4 }, { lower: 190, upper: 200, count: 12 }], myRank: 3,
    aboveMe: { total: 2, consentYes: 1, consentNo: 1, consentUnknown: 0, withdrawn: 1, priorityFirst: 0 }, warnings: ['archive'] } }));
  await page.goto('/app/competitions/g1/competitors');
  await expect(page.locator('.af-spotlight strong')).toHaveText('2');
  await expect(page.locator('.af-info-row').filter({ hasText: 'Отозвали заявление' })).toContainText('1');
  await expect(page.locator('.af-score-bins > div')).toHaveCount(2);
  await expect(page.getByText('Источник не публикует приоритеты.')).toBeVisible();
});

test('competitions index lists imported lists only', async ({ page }) => {
  const group = (id: string, coverage: string) => ({ id, title: `Конкурс ${id}`, universityId: 'u', universityName: 'Вуз', parentUniversityId: null, year: 2026, level: 'bachelor', studyForm: 'full-time', funding: 'budget', category: 'general', seats: 10, coverage, sourceId: coverage === 'manual' ? null : 's', sourceUrl: null, lookupAvailable: coverage !== 'manual' });
  await page.route('**/api/v1/groups?**', r => r.fulfill({ json: { items: [group('a', 'archive'), group('m', 'manual'), group('x', 'automatic')], total: 3, nextCursor: null, facets: {} } }));
  await page.goto('/app/competitions');
  await expect(page.locator('.af-program-card')).toHaveCount(2);
  await expect(page.locator('.af-program-card').first().getByRole('link').first()).toHaveAttribute('href', '/app/competitions/a');
});

test('groups pagination reaches imported lists beyond a manual first page and survives reload/history', async ({ page }) => {
  const queries: string[] = [];
  await page.route('**/api/v1/groups?**', route => {
    const after = new URL(route.request().url()).searchParams.get('after');
    queries.push(after ?? '');
    return route.fulfill({ json: { items: [{ id: after ? 'imported' : 'manual', title: after ? 'Импортированная группа' : 'Ручная группа', universityName: 'Вуз', year: 2026, seats: null, coverage: after ? 'archive' : 'manual' }], total: 51, nextCursor: after ? null : 'cursor-50' } });
  });
  await page.goto('/app/competitions');
  await expect(page.getByText('На этой странице списков нет', { exact: true })).toBeVisible();
  await expect(page.getByText('Ни один конкурсный список ещё не импортирован.')).toHaveCount(0);
  await page.getByRole('button', { name: 'Далее', exact: true }).click();
  await expect(page).toHaveURL(/after=cursor-50/);
  await expect(page.locator('.af-program-card')).toHaveCount(1);
  await page.reload();
  await expect(page.locator('.af-program-card')).toContainText('Импортированная группа');
  await page.goBack();
  await expect(page.getByText('На этой странице списков нет', { exact: true })).toBeVisible();
  expect(queries).toContain('cursor-50');
});

test('competitors metadata failure is visible even if summary succeeded', async ({ page }) => {
  await page.route('**/api/v1/competitions/g1', route => route.fulfill({ status: 500, json: {} }));
  await page.route('**/api/v1/competitions/g1/summary', route => route.fulfill({ json: { total: 0, seats: null, byConsent: { yes: 0, no: 0, unknown: 0 }, byParticipation: { unknown: 0, active: 0, withdrawn: 0, enrolled: 0 }, priorityKnown: 0, priorityFirst: 0, scoreKnown: 0, scoreBins: [], myRank: null, aboveMe: null, warnings: [] } }));
  await page.goto('/app/competitions/g1/competitors');
  await expect(page.getByRole('alert')).toContainText('Не удалось загрузить данные');
  await expect(page.locator('.af-spotlight')).toHaveCount(0);
});

test('direct add offers explicit guest recovery and never repeats POST automatically', async ({ page }) => {
  let lookups = 0, sessions = 0;
  await page.route('**/api/v1/groups?**', route => route.fulfill({ json: { items: [{ id: 'group', title: 'Тестовый конкурс', universityName: 'Вуз', year: 2026, sourceId: 'source', lookupAvailable: true }], total: 1, nextCursor: null } }));
  await page.route('**/api/v1/sources/source/lookup', route => { lookups++; return route.fulfill({ status: 401, json: {} }); });
  await page.route('**/api/v1/session', route => { sessions++; return route.fulfill({ status: 204 }); });
  await page.goto('/app/watchlist/add');
  await page.getByRole('button', { name: 'Выбрать', exact: true }).click();
  await page.getByLabel('Публичный код в списке').fill('123-45');
  await page.getByRole('button', { name: 'Найти запись', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Начать гостевую сессию' })).toBeVisible();
  expect(sessions).toBe(0);
  await page.getByRole('button', { name: 'Начать гостевую сессию' }).click();
  await expect(page.getByRole('alert')).toHaveCount(0);
  await expect(page.getByLabel('Публичный код в списке')).toHaveValue('');
  expect(lookups).toBe(1); expect(sessions).toBe(1);
});

test('session change cancels pending lookup and clears public code without reloading public groups', async ({ page }) => {
  let release = () => {}, calls = 0;
  await page.route('**/api/v1/groups?**', route => { calls++; return route.fulfill({ json: { items: [{ id: 'group', title: 'Тестовый конкурс', universityName: 'Вуз', year: 2026, sourceId: 'source', lookupAvailable: true }], total: 1, nextCursor: null } }); });
  await page.route('**/api/v1/sources/source/lookup', async route => {
    await new Promise<void>(resolve => { release = resolve; });
    await route.fulfill({ json: { found: true, group: { title: 'Тестовый конкурс', year: 2026 }, candidate: { officialRank: 7 }, confirmationToken: 'old-token', expiresAt: '2030-01-01T00:00:00Z' } }).catch(() => {});
  });
  await page.goto('/app/watchlist/add');
  await page.getByRole('button', { name: 'Выбрать', exact: true }).click();
  await page.getByLabel('Публичный код в списке').fill('123-45');
  const sent = page.waitForRequest('**/api/v1/sources/source/lookup');
  await page.getByRole('button', { name: 'Найти запись', exact: true }).click(); await sent;
  await page.evaluate(() => dispatchEvent(new StorageEvent('storage', { key: 'admitflow-session-change' })));
  release();
  await expect(page.getByLabel('Публичный код в списке')).toHaveValue('');
  await expect(page.getByRole('button', { name: 'Найти запись', exact: true })).toBeEnabled();
  await expect(page.getByRole('button', { name: 'Подтвердить и сохранить' })).toHaveCount(0);
  expect(calls).toBe(1);
});

test('catalog rejects response from a different campaign', async ({ page }) => {
  await page.route('**/api/v1/catalog/programs?**', async route => {
    const response = await route.fetch({ url: new URL('/api/v1/catalog/programs?year=2026', route.request().url()).href });
    await route.fulfill({ response });
  });
  await page.goto('/programs?year=2027');
  await expect(page.getByRole('alert')).toContainText('Не удалось проверить');
  await expect(page.locator('.af-program-card')).toHaveCount(0);
});

test('two tabs share expiry without a request loop and restart only after explicit action', async ({ page, context }) => {
  let authorized = true, reads = 0, starts = 0;
  await context.route('**/api/v1/subscriptions', route => {
    reads++;
    return route.fulfill(authorized ? { json: [record] } : { status: 401, json: {} });
  });
  await context.route('**/api/v1/session', route => { starts++; authorized = true; return route.fulfill({ status: 204 }); });
  const second = await context.newPage();
  await page.goto('/app/watchlist'); await second.goto('/app/watchlist');
  for (const tab of [page, second]) await expect(tab.getByText('Проверенный вуз')).toBeVisible();
  expect(reads).toBe(2);
  authorized = false;
  await page.getByRole('button', { name: 'Обновить', exact: true }).click();
  for (const tab of [page, second]) {
    await expect(tab.getByRole('button', { name: 'Начать гостевую сессию' })).toBeVisible();
    await expect(tab.getByText('Проверенный вуз')).toHaveCount(0);
  }
  expect(reads).toBe(3); expect(starts).toBe(0);
  await page.getByRole('button', { name: 'Начать гостевую сессию' }).click();
  for (const tab of [page, second]) await expect(tab.getByText('Проверенный вуз')).toBeVisible();
  expect(reads).toBe(5); expect(starts).toBe(1);
  await second.close();
});
