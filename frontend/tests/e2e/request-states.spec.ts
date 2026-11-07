import { expect, test } from '@playwright/test';
import type { Page } from '@playwright/test';
import fixture from '../../../shared/manual-watch.json' with { type: 'json' };
import { calculatePlace } from '@/entities/manual-direction';

async function install(page: Page) {
  const values = { ...fixture.latest.values, rank: fixture.latest.values.rank + 5 };
  const state = {
    watches: [] as (typeof fixture)[],
    fail: '' as '' | 'server' | 'network',
    archiveFails: false,
    budgetFails: false,
    historyFails: false,
    historyEmpty: false,
    optionalFails: false,
    optionalReads: 0,
    historyReads: 0,
    waitWatches: Promise.resolve(),
    waitArchive: Promise.resolve(),
  };
  await page.route('**/api/v1/**', async (route) => {
    const path = new URL(route.request().url()).pathname.replace('/api/v1', '');
    if (path === '/session')
      return route.fulfill(
        route.request().method() === 'POST'
          ? { status: 204 }
          : { json: { expiresAt: '2030-12-01T00:00:00Z' } },
      );
    if (path === '/watches' && route.request().method() === 'POST') {
      state.watches = [fixture];
      return route.fulfill({ status: 201, json: fixture });
    }
    if (path === '/changes' || path === '/coverage') state.optionalReads++;
    if (state.fail && ['/watches', '/subscriptions', '/direction-budget'].includes(path)) {
      return state.fail === 'network'
        ? route.abort('failed')
        : route.fulfill({
            status: 503,
            json: { detail: 'Internal database pool error: private_debug' },
          });
    }
    if (path === '/watches') {
      await state.waitWatches;
      return route.fulfill({ json: state.watches });
    }
    if (path === '/subscriptions') {
      await state.waitArchive;
      return route.fulfill(
        state.archiveFails ? { status: 503, json: { detail: 'private_debug' } } : { json: [] },
      );
    }
    if (path === '/direction-budget')
      return route.fulfill(
        state.budgetFails
          ? { status: 503, json: { detail: 'private_debug' } }
          : {
              json: {
                limit: 20,
                total: state.watches.length,
                manualCount: state.watches.length,
                archiveCount: 0,
              },
            },
      );
    if (path.endsWith('/history')) {
      state.historyReads++;
      return route.fulfill(
        state.historyFails
          ? { status: 503, json: { detail: 'private_debug' } }
          : {
              json: {
                items: state.historyEmpty
                  ? []
                  : [
                      fixture.latest,
                      {
                        ...fixture.latest,
                        id: 'previous',
                        capturedAt: '2026-10-01T00:00:00Z',
                        values,
                        calculation: calculatePlace(values),
                      },
                    ],
                total: state.historyEmpty ? null : 2,
                nextCursor: null,
              },
            },
      );
    }
    if (state.optionalFails && ['/changes', '/coverage'].includes(path))
      return route.fulfill({ status: 503, json: { detail: 'private_debug' } });
    if (path === '/changes')
      return route.fulfill({ json: { items: [], nextCursor: null, total: 0, unreadCount: 0 } });
    if (path === '/export')
      return route.fulfill({
        json: {
          formatVersion: 'manual-export-v1',
          exportedAt: '2026-11-07T00:00:00Z',
          watches: state.watches.map((watch) => ({ ...watch, history: [watch.latest] })),
        },
      });
    if (path === '/universities')
      return route.fulfill({ json: { items: [], total: 0, nextOffset: null } });
    if (path === '/groups')
      return route.fulfill({
        json: { items: [], total: 0, nextCursor: null, facets: { branches: [], years: [] } },
      });
    if (path === '/coverage')
      return route.fulfill({
        json: {
          registeredSources: 0,
          reviewedSources: 0,
          importedSources: 0,
          importedGroups: 0,
          importedUniversities: 0,
          importedRows: 0,
          archiveImportedGroups: 0,
          conditionalGroups: 0,
          lastImportedAt: null,
          catalogUniversities: 2,
          automaticSources: 0,
          publishedGroups: 0,
          freshGroups: 0,
          archiveGroups: 0,
          nationalTotal: null,
          generatedAt: '2026-11-07T00:00:00Z',
        },
      });
    return route.fulfill({ status: 503, json: { detail: 'private_debug' } });
  });
  return state;
}

test('waits for both lists before declaring no directions', async ({ page }) => {
  const state = await install(page);
  let releaseWatches!: () => void, releaseArchive!: () => void;
  state.waitWatches = new Promise<void>((resolve) => {
    releaseWatches = resolve;
  });
  state.waitArchive = new Promise<void>((resolve) => {
    releaseArchive = resolve;
  });
  try {
    await page.goto('/tracker');
    await expect(page.getByRole('heading', { name: 'Загружаем направления…' })).toBeVisible();
    await expect(
      page.getByRole('heading', { name: 'Направлений пока нет', exact: true }),
    ).toHaveCount(0);
    releaseWatches();
    await expect(page.getByRole('heading', { name: 'Загружаем направления…' })).toBeVisible();
    releaseArchive();
    await expect(
      page.getByRole('heading', { name: 'Направлений пока нет', exact: true }),
    ).toBeVisible();
    expect(state.optionalReads).toBe(0);
    await page
      .locator('.empty-state')
      .getByRole('button', { name: 'Добавить направление', exact: true })
      .click();
    await expect(page.locator('.direction-form')).toBeVisible();
  } finally {
    releaseWatches();
    releaseArchive();
  }
});

for (const failure of ['server', 'network'] as const) {
  test(`${failure}: one blocking error, no false empty or success, retry recovers`, async ({
    page,
  }) => {
    const state = await install(page);
    state.fail = failure;
    await page.goto('/tracker');
    await expect(
      page.getByRole('heading', { name: 'Не удалось загрузить направления' }),
    ).toBeVisible();
    await expect(page.getByRole('alert')).toHaveCount(1);
    await expect(
      page.getByRole('heading', { name: 'Направлений пока нет', exact: true }),
    ).toHaveCount(0);
    await expect(page.locator('main')).not.toContainText('private_debug');
    await expect(page.locator('.tracker-notice')).toBeEmpty();
    expect(state.optionalReads).toBe(0);
    state.fail = '';
    await page.getByRole('button', { name: 'Повторить', exact: true }).click();
    await expect(
      page.getByRole('heading', { name: 'Направлений пока нет', exact: true }),
    ).toBeVisible();
    await expect(page.getByRole('alert')).toHaveCount(0);
    await expect(page.locator('.tracker-notice')).toContainText('Список направлений обновлён');
  });
}

test('manual empty plus unavailable archive is an error, not a global empty state', async ({
  page,
}) => {
  const state = await install(page);
  state.archiveFails = true;
  await page.goto('/tracker');
  await expect(
    page.getByRole('heading', { name: 'Не удалось загрузить направления' }),
  ).toBeVisible();
  await expect(page.getByRole('alert')).toHaveCount(1);
  await expect(
    page.getByRole('heading', { name: 'Направлений пока нет', exact: true }),
  ).toHaveCount(0);
});

test('archive-only failure stays local when manual directions are available', async ({ page }) => {
  const state = await install(page);
  state.watches = [fixture];
  state.archiveFails = true;
  await page.goto('/tracker');
  await expect(page.locator('.direction-result strong')).toHaveText('74');
  const archive = page.getByRole('region', { name: 'Архивные направления', exact: true });
  await expect(archive.getByRole('status')).toContainText(
    'Не удалось загрузить архивные направления',
  );
  await expect(page.getByRole('alert')).toHaveCount(0);
  state.archiveFails = false;
  await archive.getByRole('button', { name: 'Повторить', exact: true }).click();
  await expect(archive).toHaveCount(0);
});

test('background failure preserves cards and draft; successful retry clears warning', async ({
  page,
}) => {
  const state = await install(page);
  state.watches = [fixture];
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
  await page.locator('#tracker-rank').fill('125');
  state.fail = 'network';
  await page.getByRole('button', { name: 'Обновить направления', exact: true }).click();
  await expect(page.locator('.stale-warning')).toBeVisible();
  await expect(page.getByRole('alert')).toHaveCount(1);
  await expect(page.locator('.direction-result strong')).toHaveText('74');
  await expect(page.locator('#tracker-rank')).toHaveValue('125');
  await expect(page.locator('.tracker-notice')).toBeEmpty();
  state.fail = '';
  await page.getByRole('button', { name: 'Повторить обновление' }).click();
  await expect(page.locator('.stale-warning')).toHaveCount(0);
  await expect(page.locator('#tracker-rank')).toHaveValue('125');
});

test('a cached empty list is not presented as a confirmed empty after refresh failure', async ({
  page,
}) => {
  const state = await install(page);
  await page.goto('/tracker');
  await expect(
    page.getByRole('heading', { name: 'Направлений пока нет', exact: true }),
  ).toBeVisible();
  state.fail = 'server';
  await page.getByRole('button', { name: 'Обновить направления', exact: true }).click();
  await expect(page.locator('.stale-warning')).toContainText(
    'При последней успешной загрузке направлений не было',
  );
  await expect(
    page.getByRole('heading', { name: 'Направлений пока нет', exact: true }),
  ).toHaveCount(0);
});

test('optional sections load on opening and show compact recoverable failures', async ({
  page,
}) => {
  const state = await install(page);
  state.optionalFails = true;
  await page.goto('/tracker');
  await expect(
    page.getByRole('heading', { name: 'Направлений пока нет', exact: true }),
  ).toBeVisible();
  expect(state.optionalReads).toBe(0);
  const summary = page.getByText('Изменения сохранённых списков', { exact: true });
  await summary.focus();
  await page.keyboard.press('Enter');
  const changes = page.getByRole('region', { name: 'Изменения в ваших списках', exact: true });
  await expect(changes.getByRole('status')).toContainText('Не удалось загрузить изменения');
  await expect(changes.getByText('Новых изменений пока нет.', { exact: false })).toHaveCount(0);
  await expect(changes.getByRole('button')).toHaveCount(1);
  await page.getByText('Источники и охват вузов', { exact: true }).click();
  await expect(
    page.getByRole('region', { name: 'Покрытие источников' }).getByRole('status'),
  ).toContainText('Не удалось загрузить сведения');
  await expect(page.getByRole('alert')).toHaveCount(0);
  state.optionalFails = false;
  await changes.getByRole('button', { name: 'Повторить изменения', exact: true }).click();
  await expect(changes).toContainText('Новых изменений пока нет.');
});

test('history failure is shown once; retry can return a genuinely empty history', async ({
  page,
}) => {
  const state = await install(page);
  state.watches = [fixture];
  state.historyFails = true;
  await page.goto('/tracker');
  await expect(page.locator('.position-change')).toContainText('недоступно');
  await page.getByRole('button', { name: 'История', exact: true }).click();
  await expect(page.locator('.direction-history .request-feedback')).toContainText(
    'Не удалось загрузить историю',
  );
  await expect(page.locator('.position-change')).toHaveCount(0);
  await expect(page.locator('.direction-history')).not.toContainText(
    'Сохранений в истории пока нет.',
  );
  state.historyFails = false;
  state.historyEmpty = true;
  await page.getByRole('button', { name: 'Повторить загрузку истории' }).click();
  await expect(page.locator('.direction-history')).toContainText('Сохранений в истории пока нет.');
});

test('budget failure explains disabled adding and can be retried locally', async ({ page }) => {
  const state = await install(page);
  state.budgetFails = true;
  await page.goto('/tracker');
  await expect(
    page.getByRole('heading', { name: 'Направлений пока нет', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText('Не удалось проверить число сохранённых направлений.', { exact: false }),
  ).toBeVisible();
  await expect(
    page.locator('.empty-state').getByRole('button', { name: 'Добавить направление', exact: true }),
  ).toBeDisabled();
  state.budgetFails = false;
  await page.getByRole('button', { name: 'Повторить', exact: true }).click();
  await expect(
    page.locator('.empty-state').getByRole('button', { name: 'Добавить направление', exact: true }),
  ).toBeEnabled();
});

test('saving a direction and preparing export acknowledge actual success', async ({ page }) => {
  const state = await install(page);
  await page.goto('/tracker');
  await page
    .locator('.empty-state')
    .getByRole('button', { name: 'Добавить направление', exact: true })
    .click();
  await page.getByLabel('Вуз', { exact: true }).fill(fixture.university);
  await page.getByLabel('Направление', { exact: true }).fill(fixture.title);
  await page.getByLabel('Ссылка на конкурсный список').fill(fixture.sourceUrl);
  await page.getByLabel('Ваш номер в списке').fill('120');
  await page.getByLabel('Бюджетных мест').fill('90');
  await page.getByLabel('Не участвуют в этом конкурсе', { exact: true }).fill('30');
  await page.getByLabel('Не подали согласие', { exact: true }).fill('16');
  await page.getByRole('button', { name: 'Сохранить направление', exact: true }).click();
  await expect(page.locator('.tracker-notice')).toContainText('Данные сохранены');
  await expect(page.locator('.direction-result strong')).toHaveText('74');
  expect(state.watches.length).toBe(1);
  await page.getByText('Скачать данные и распечатать', { exact: true }).click();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Скачать данные (JSON)' }).click();
  await download;
  await expect(page.locator('.tracker-notice')).toContainText('подготовлен для скачивания');
});

test('invalid empty history is still an error when its total violates the contract', async ({
  page,
}) => {
  const state = await install(page);
  state.watches = [fixture];
  await page.route('**/api/v1/watches/*/history*', (route) =>
    route.fulfill({ json: { items: [], total: 0, nextCursor: null } }),
  );
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'История', exact: true }).click();
  await expect(page.locator('.direction-history')).toContainText(
    'Не удалось проверить полученные данные',
  );
  await expect(page.locator('.direction-history')).not.toContainText(
    'Сохранений в истории пока нет.',
  );
});

test('catalog network error is separate from a valid empty response', async ({ page }) => {
  await install(page);
  let failed = true;
  await page.route('**/api/v1/groups?*', (route) =>
    failed
      ? route.abort('failed')
      : route.fulfill({
          json: { items: [], total: 0, nextCursor: null, facets: { branches: [], years: [] } },
        }),
  );
  await page.goto('/sources');
  await expect(page.getByRole('alert')).toContainText('Проверьте соединение');
  await expect(
    page.getByText('Подходящих подключённых групп пока нет.', { exact: false }),
  ).toHaveCount(0);
  failed = false;
  await page.getByRole('button', { name: 'Повторить загрузку групп' }).click();
  await expect(
    page.getByText('Подходящих подключённых групп пока нет.', { exact: false }),
  ).toBeVisible();
  await expect(page.getByRole('alert')).toHaveCount(0);
});

test('coverage keeps previously loaded numbers when a background request fails', async ({
  page,
}) => {
  const state = await install(page);
  await page.clock.install();
  await page.goto('/tracker');
  await page.getByText('Источники и охват вузов', { exact: true }).click();
  const coverage = page.getByRole('region', { name: 'Покрытие источников' });
  await expect(coverage.locator('dd').first()).toHaveText('2');
  await page.clock.fastForward(31_000);
  state.optionalFails = true;
  await page.getByRole('link', { name: 'Источники', exact: true }).click();
  await page.getByRole('link', { name: 'Мои направления →', exact: true }).click();
  await page.getByText('Источники и охват вузов', { exact: true }).click();
  await page.clock.runFor(2_000);
  await expect(coverage.getByRole('status')).toContainText('Показаны ранее загруженные сведения');
  await expect(coverage.locator('dd').first()).toHaveText('2');
  await expect(page.getByRole('alert')).toHaveCount(0);
});
