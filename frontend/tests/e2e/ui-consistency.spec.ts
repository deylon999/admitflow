import { expect, test } from '@playwright/test';
import type { Page } from '@playwright/test';
import fixture from '../../../shared/manual-watch.json' with { type: 'json' };

const group = {
  id: 'audit-group',
  universityId: 'audit-university',
  universityName: 'Тестовый университет',
  parentUniversityId: null,
  year: 2026,
  level: 'bachelor',
  title: 'Прикладная информатика',
  studyForm: 'full-time',
  funding: 'budget',
  category: 'general',
  seats: 20,
  coverage: 'archive',
  dataKind: 'archive',
  sourceId: null,
  sourceUrl: 'https://example.org/list',
  sourceState: 'archived',
  snapshotId: 'audit-snapshot',
  fetchedAt: '2026-11-01T00:00:00Z',
  sourceUpdatedAt: null,
  lastCheckedAt: '2026-11-01T00:00:00Z',
  rowCount: 12,
  lookupAvailable: false,
  assessmentAvailable: false,
  scenarioAvailable: false,
};

async function mock(page: Page) {
  await page.route('**/api/v1/**', (route) => {
    const path = new URL(route.request().url()).pathname.replace('/api/v1', '');
    if (path === '/session')
      return route.fulfill(
        route.request().method() === 'POST'
          ? { status: 204 }
          : { json: { expiresAt: '2030-12-01T00:00:00Z', draftScope: 'a'.repeat(64) } },
      );
    if (path === '/groups')
      return route.fulfill({
        json: {
          items: [group],
          total: 1,
          nextCursor: null,
          facets: { branches: [], years: [2026] },
        },
      });
    if (path === '/universities')
      return route.fulfill({ json: { items: [], total: 0, nextOffset: null } });
    if (path === '/watches') return route.fulfill({ json: [fixture] });
    if (path.endsWith('/history'))
      return route.fulfill({ json: { items: [fixture.latest], total: 1, nextCursor: null } });
    if (path === '/subscriptions') return route.fulfill({ json: [] });
    if (path === '/direction-budget')
      return route.fulfill({ json: { limit: 20, total: 1, manualCount: 1, archiveCount: 0 } });
    return route.fulfill({ status: 503, json: { detail: 'Synthetic unavailable' } });
  });
}

for (const theme of ['light', 'dark'])
  for (const width of [320, 390, 768, 1024, 1440]) {
    for (const route of ['/', '/sources', '/missing-page']) {
      test(`${theme} ${width} ${route}: consistent shell, typography, controls and surfaces`, async ({
        page,
      }, info) => {
        await page.setViewportSize({ width, height: 960 });
        await page.addInitScript((value) => localStorage.setItem('abiturient-theme', value), theme);
        await mock(page);
        await page.goto(route);
        await expect(page.locator('main h1')).toBeVisible();
        await expect(page.locator('html')).toHaveAttribute('data-theme', theme);
        expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
          true,
        );
        expect(
          await page.locator('main h1').evaluate((element) => getComputedStyle(element).fontSize),
        ).toBe(width <= 600 ? '28px' : '32px');
        expect(
          await page
            .locator('main h2, main h3')
            .evaluateAll((nodes) =>
              nodes.every(
                (node) =>
                  getComputedStyle(node).fontSize === (node.tagName === 'H2' ? '24px' : '20px'),
              ),
            ),
        ).toBe(true);
        expect(
          await page
            .locator('button, a.button')
            .evaluateAll((nodes) =>
              nodes
                .filter((node) => node.getClientRects().length)
                .every(
                  (node) =>
                    node.classList.contains('button') && node.getBoundingClientRect().height >= 44,
                ),
            ),
        ).toBe(true);
        if (route === '/') {
          await expect(page.locator('#hero-title br')).toHaveCount(0);
          await expect(page.locator('.quote-card.surface')).toHaveCount(2);
          expect(
            await page
              .locator('.quote-card')
              .first()
              .evaluate((node) => getComputedStyle(node).backgroundColor),
          ).toBe(
            await page
              .locator('.example-card')
              .evaluate((node) => getComputedStyle(node).backgroundColor),
          );
          await expect(page.getByRole('navigation', { name: 'На этой странице' })).toBeVisible();
        }
        if (route === '/sources') {
          await expect(page.locator('.source-catalog-card h3')).toHaveText(group.title);
          await expect(
            page.getByRole('region', { name: 'Фильтры конкурсных групп' }),
          ).toBeVisible();
          await expect(page.locator('main')).toContainText('Архив 2026 года');
        }
        if (route === '/missing-page') {
          await expect(page.locator('.page-message h1')).toHaveText('Страница не найдена');
          await expect(page.locator('.page-actions .button')).toHaveText('На главную');
        }
        const navigation = page.getByRole('navigation', { name: 'Разделы сайта', exact: true });
        if (width <= 900) {
          const toggle = page.getByRole('button', { name: 'Разделы сайта', exact: false });
          await expect(toggle).toHaveAttribute('aria-expanded', 'false');
          await toggle.focus();
          await page.keyboard.press('Enter');
          await expect(navigation).toBeVisible();
          await expect(navigation.getByRole('link')).toHaveCount(4);
          await expect(
            navigation.getByRole('link', { name: 'Мои направления', exact: true }),
          ).toBeVisible();
          await page.keyboard.press('Escape');
          await expect(toggle).toBeFocused();
          await expect(navigation).toBeHidden();
        } else {
          await expect(navigation).toBeVisible();
          await expect(
            page.getByRole('button', { name: 'Разделы сайта', exact: false }),
          ).toBeHidden();
        }
        if (width === 320 || width === 1440)
          await page.screenshot({ path: info.outputPath('page.png'), fullPage: true });
      });
    }
  }

test('mobile navigation follows existing project and calculator sections and marks the active route', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 900 });
  await mock(page);
  await page.goto('/sources');
  await expect(
    page.getByRole('heading', { name: 'Вузы и конкурсные группы', exact: true }),
  ).toBeFocused();
  const toggle = page.getByRole('button', { name: 'Разделы сайта', exact: false });
  const navigation = page.getByRole('navigation', { name: 'Разделы сайта', exact: true });
  await toggle.click();
  await expect(navigation.getByRole('link', { name: 'Источники', exact: true })).toHaveAttribute(
    'aria-current',
    'page',
  );
  await navigation.getByRole('link', { name: 'Источники', exact: true }).click();
  await expect(toggle).toBeFocused();
  await expect(toggle).toHaveAttribute('aria-expanded', 'false');
  await toggle.click();
  await navigation.getByRole('link', { name: 'О проекте', exact: true }).click();
  await expect(page).toHaveURL(/\/#about$/);
  await expect(page.locator('#about')).toBeFocused();
  await expect(page.locator('#about')).toContainText('Один экран вместо пяти сайтов');
  await toggle.click();
  await navigation.getByRole('link', { name: 'Калькулятор', exact: true }).click();
  await expect(page.locator('#calculator')).toBeFocused();
  await expect(page.locator('#result-place')).toHaveText('74');
  await toggle.click();
  await navigation.getByRole('link', { name: 'Мои направления', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Мои направления', exact: true })).toBeFocused();
});

test('shared navigation preserves the existing unsaved direction guard', async ({ page }) => {
  await mock(page);
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
  await page.locator('#tracker-rank').fill('125');
  const calculator = page
    .getByRole('navigation', { name: 'Разделы сайта', exact: true })
    .getByRole('link', { name: 'Калькулятор', exact: true });
  page.once('dialog', (dialog) => dialog.dismiss());
  await calculator.click();
  await expect(page).toHaveURL(/\/tracker$/);
  await expect(page.locator('#tracker-rank')).toHaveValue('125');
  page.once('dialog', (dialog) => dialog.accept());
  await calculator.click();
  await expect(page).toHaveURL(/\/#calculator$/);
  await expect(page.locator('#calculator')).toBeFocused();
});

test('a similarly named unknown route has 404 title and no false active source navigation', async ({
  page,
}) => {
  await page.goto('/sources-missing');
  await expect(page).toHaveTitle('Страница не найдена — Абитуриент');
  await expect(page.locator('main h1')).toHaveText('Страница не найдена');
  await expect(page.locator('.navigation [aria-current]')).toHaveCount(0);
});

test('source lookup uses subordinate headings and returns focus when closed on mobile', async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 900 });
  await mock(page);
  await page.route('**/api/v1/groups?*', (route) =>
    route.fulfill({
      json: {
        items: [{ ...group, sourceId: 'audit-source', lookupAvailable: true }],
        total: 1,
        nextCursor: null,
        facets: { branches: [], years: [2026] },
      },
    }),
  );
  await page.goto('/sources');
  const open = page.getByRole('button', { name: 'Найти свою запись', exact: true });
  await open.click();
  await expect(
    page.getByRole('heading', { name: 'Найти запись в этой группе', level: 4 }),
  ).toBeVisible();
  await expect(page.getByLabel('Код поступающего')).toBeFocused();
  await expect(page.getByRole('button', { name: 'Найти запись', exact: true })).toBeDisabled();
  await page.getByLabel('Код поступающего').fill('SYNTHETIC-001');
  await expect(page.getByRole('button', { name: 'Найти запись', exact: true })).toBeEnabled();
  await page.getByRole('button', { name: 'Закрыть поиск', exact: true }).click();
  await expect(open).toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test('calculator has one field error, a neutral incomplete result and normal recovery', async ({
  page,
}) => {
  await page.goto('/#calculator');
  const form = page.getByRole('form', { name: 'Данные для расчёта', exact: true });
  await expect(form).toContainText('Сейчас заполнен пример');
  await page.getByLabel('Ваш номер в списке', { exact: true }).fill('');
  await expect(form.getByRole('alert')).toHaveCount(1);
  await expect(page.locator('#calculation-error').locator('..')).toHaveClass('field');
  await expect(page.locator('#result-status')).toHaveText(
    'Исправьте отмеченные поля, чтобы увидеть расчёт.',
  );
  await expect(page.locator('#result-place')).toHaveText('—');
  await expect(page.locator('.result-legend')).toHaveCount(0);
  await page.getByLabel('Ваш номер в списке', { exact: true }).fill('120');
  await expect(form.getByRole('alert')).toHaveCount(0);
  await expect(page.locator('#result-place')).toHaveText('74');
  await expect(page.locator('.result-legend')).toBeVisible();
});

test('source loading, empty and failed requests share the same page layout without false empty', async ({
  page,
}) => {
  await mock(page);
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  let failed = true;
  await page.route('**/api/v1/groups?*', async (route) => {
    await gate;
    return route.fulfill(
      failed
        ? { status: 503, json: { detail: 'Unavailable' } }
        : { json: { items: [], total: 0, nextCursor: null, facets: { branches: [], years: [] } } },
    );
  });
  try {
    await page.goto('/sources');
    await expect(page.getByText('Загружаем конкурсные группы…', { exact: true })).toBeVisible();
    await expect(page.locator('.catalog-empty')).toHaveCount(0);
    release();
    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.locator('.catalog-empty')).toHaveCount(0);
    failed = false;
    await page.getByRole('button', { name: 'Повторить загрузку групп' }).click();
    await expect(page.locator('.catalog-empty h3')).toHaveText('Ничего не найдено');
    await expect(
      page.getByRole('link', { name: 'Сохранить направление вручную', exact: true }),
    ).toBeVisible();
  } finally {
    release();
  }
});

test('loading a lazy route keeps the shell; a chunk error uses the shared recovery surface', async ({
  page,
}) => {
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route(
    /\/(?:src\/pages\/sources\/index\.ts|assets\/sources-[^/?]+\.js)(?:\?.*)?$/,
    async (route) => {
      await gate;
      await route.abort('failed');
    },
  );
  try {
    await page.goto('/sources', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('.page-message [role="status"]')).toHaveText('Загружаем страницу…');
    await expect(page.getByRole('banner')).toBeVisible();
    release();
    await expect(page.locator('.page-message h1')).toHaveText('Не удалось открыть страницу');
    await expect(page.locator('.page-message h1')).toBeFocused();
    await expect(page.locator('.page-actions .button')).toHaveCount(2);
  } finally {
    release();
  }
});
