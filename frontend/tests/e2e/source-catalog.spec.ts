import { expect, test } from '@playwright/test';

const syntheticGroup = {
  id: 'catalog-a',
  universityId: 'university-synthetic',
  universityName: 'Synthetic University',
  parentUniversityId: null,
  year: 2026,
  level: 'bachelor',
  title: 'Synthetic catalog group',
  studyForm: 'full-time',
  funding: 'budget',
  category: 'general',
  seats: 2,
  coverage: 'unsupported',
  dataKind: null,
  sourceId: null,
  sourceUrl: null,
  sourceState: null,
  snapshotId: null,
  fetchedAt: null,
  sourceUpdatedAt: null,
  lastCheckedAt: null,
  rowCount: null,
  lookupAvailable: false,
  assessmentAvailable: false,
  scenarioAvailable: false,
};

test('real catalog is readonly, filters season/university and keeps a manual fallback', async ({
  page,
}) => {
  test.skip(process.env.E2E_SOURCE !== '1', 'Requires reviewed archive registered in current API');
  let creates = 0;
  page.on('request', (request) => {
    if (request.method() === 'POST') creates++;
  });
  await page.goto('/sources');
  await expect(page.getByRole('heading', { name: 'Вузы и конкурсные группы' })).toBeFocused();
  await expect(page.getByRole('link', { name: 'Калькулятор', exact: true })).toHaveAttribute(
    'href',
    '/#calculator',
  );
  await page.getByLabel('Вуз', { exact: true }).selectOption('sgu-saratov');
  await page.getByLabel('Группа или направление', { exact: true }).fill('ПРОГРАММНАЯ');
  await expect(page.locator('.source-catalog-card')).toHaveCount(1);
  await expect(page.locator('.source-catalog-card').first()).toContainText('09.03.04');
  await expect(page.locator('.source-catalog-card').first()).toContainText('Архив 2026 года');
  await page.getByLabel('Сезон', { exact: true }).selectOption('2026');
  await page.getByLabel('Подразделение', { exact: true }).selectOption('main');
  await page.getByLabel('Вуз', { exact: true }).selectOption('sgups-novosibirsk');
  await expect(
    page.getByText('Подходящих подключённых групп пока нет.', { exact: false }),
  ).toBeVisible();
  await expect(page.getByRole('link', { name: 'Сохранить направление вручную' })).toHaveAttribute(
    'href',
    '/tracker',
  );
  await expect(page.getByRole('link', { name: /Предложить источник на GitHub/ })).toHaveAttribute(
    'href',
    'https://github.com/deylon999/admitflow/issues/new',
  );
  expect(creates).toBe(0);
});

test('catalog errors have retry and do not invent zero coverage', async ({ page }) => {
  let fail = true;
  await page.route('**/api/v1/groups?*', (route) =>
    fail
      ? route.fulfill({ status: 503, json: { detail: 'Unavailable' } })
      : route.fulfill({
          json: { items: [], total: 0, nextCursor: null, facets: { branches: [], years: [] } },
        }),
  );
  await page.goto('/sources');
  await expect(page.getByText('Не удалось загрузить группы.', { exact: true })).toBeVisible();
  await expect(
    page.getByText('Подходящих подключённых групп пока нет.', { exact: false }),
  ).toHaveCount(0);
  fail = false;
  await page.getByRole('button', { name: 'Повторить загрузку групп' }).click();
  await expect(page.getByRole('button', { name: 'Повторить загрузку групп' })).toHaveCount(0);
  await expect(
    page.getByText('Подходящих подключённых групп пока нет.', { exact: false }),
  ).toBeVisible();
});

test('failed next catalog page preserves loaded groups and can be retried', async ({ page }) => {
  let failNext = true;
  await page.route('**/api/v1/groups?*', (route) => {
    const second = new URL(route.request().url()).searchParams.has('after');
    if (second && failNext) {
      return route.fulfill({ status: 503, json: { detail: 'Synthetic next-page outage' } });
    }
    return route.fulfill({
      json: {
        items: [{ ...syntheticGroup, id: second ? 'catalog-b' : 'catalog-a' }],
        total: 2,
        nextCursor: second ? null : 'catalog-a',
        facets: { branches: [], years: [2026] },
      },
    });
  });
  await page.goto('/sources');
  await expect(page.locator('article.source-catalog-card')).toHaveCount(1);
  await page.getByRole('button', { name: 'Загрузить ещё группы' }).click();
  await expect(
    page.getByText('Не удалось загрузить следующие группы.', { exact: false }),
  ).toBeVisible();
  await expect(page.locator('article.source-catalog-card')).toHaveCount(1);
  await expect(
    page.getByText('Подходящих подключённых групп пока нет.', { exact: false }),
  ).toHaveCount(0);
  failNext = false;
  await page.getByRole('button', { name: 'Повторить загрузку групп' }).click();
  await expect(page.locator('article.source-catalog-card')).toHaveCount(2);
  await expect(page.getByRole('alert')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Загрузить ещё группы' })).toHaveCount(0);
});

test('101 global branches remain usable across bounded catalog pages and filtering', async ({
  page,
}) => {
  const branches = Array.from({ length: 101 }, (_, index) => ({
    id: `branch-${String(index).padStart(3, '0')}`,
    name: `Synthetic branch ${index}`,
  }));
  const groups = branches.map((branch, index) => ({
    ...syntheticGroup,
    id: `catalog-${String(index).padStart(3, '0')}`,
    title: `Synthetic group ${index}`,
    universityId: branch.id,
    universityName: branch.name,
    parentUniversityId: 'parent-synthetic',
  }));
  await page.route('**/api/v1/universities?*', (route) =>
    route.fulfill({ json: { items: [], total: 0, nextOffset: null } }),
  );
  await page.route('**/api/v1/groups?*', (route) => {
    const query = new URL(route.request().url()).searchParams;
    const branch = query.get('branchId');
    const matching = branch ? groups.filter((item) => item.universityId === branch) : groups;
    const cursor = query.get('after');
    const start = cursor ? matching.findIndex((item) => item.id === cursor) + 1 : 0;
    const items = matching.slice(start, start + 50);
    return route.fulfill({
      json: {
        items,
        total: matching.length,
        nextCursor: start + items.length < matching.length ? items[items.length - 1].id : null,
        facets: { branches, years: [2026] },
      },
    });
  });
  await page.goto('/sources');
  await expect(page.locator('article.source-catalog-card')).toHaveCount(50);
  const branchFilter = page.getByLabel('Подразделение', { exact: true });
  await expect(branchFilter.locator('option')).toHaveCount(103);
  await page.getByRole('button', { name: 'Загрузить ещё группы' }).click();
  await expect(page.locator('article.source-catalog-card')).toHaveCount(100);
  await page.getByRole('button', { name: 'Загрузить ещё группы' }).click();
  await expect(page.locator('article.source-catalog-card')).toHaveCount(101);
  await expect(page.getByRole('button', { name: 'Загрузить ещё группы' })).toHaveCount(0);
  await branchFilter.selectOption('branch-100');
  await expect(page.locator('article.source-catalog-card')).toHaveCount(1);
  await expect(
    page.getByRole('heading', { name: 'Synthetic group 100', exact: true }),
  ).toBeVisible();
  await expect(branchFilter.locator('option')).toHaveCount(103);
  await expect(page.getByRole('alert')).toHaveCount(0);
});

test('catalog pages append once and filter changes clear the old pages', async ({ page }) => {
  test.skip(process.env.E2E_SOURCE !== '1', 'Requires a reviewed group DTO');
  const result = await (await page.request.get('/api/v1/groups')).json();
  const group = result.items[0];
  await page.route('**/api/v1/groups?*', (route) => {
    const query = new URL(route.request().url()).searchParams;
    const empty = query.get('q') === 'Other';
    const second = query.has('after');
    return route.fulfill({
      json: {
        ...result,
        items: empty ? [] : [{ ...group, id: second ? 'catalog-b' : 'catalog-a' }],
        total: empty ? 0 : 2,
        nextCursor: empty || second ? null : 'catalog-a',
      },
    });
  });
  await page.goto('/sources');
  await expect(page.locator('.source-catalog-card')).toHaveCount(1);
  await page.getByRole('button', { name: 'Загрузить ещё группы' }).click();
  await expect(page.locator('.source-catalog-card')).toHaveCount(2);
  await expect(page.getByRole('button', { name: 'Загрузить ещё группы' })).toHaveCount(0);
  await page.getByLabel('Группа или направление', { exact: true }).fill('Other');
  await expect(page.locator('.source-catalog-card')).toHaveCount(0);
});

for (const theme of ['light', 'dark'])
  test(`catalog remains usable at320px in ${theme}`, async ({ page }) => {
    await page.addInitScript((value) => localStorage.setItem('abiturient-theme', value), theme);
    await page.setViewportSize({ width: 320, height: 900 });
    await page.goto('/sources');
    await expect(page.getByLabel('Группа или направление', { exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
  });
