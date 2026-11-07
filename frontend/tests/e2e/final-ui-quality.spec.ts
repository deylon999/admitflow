import { expect, test } from '@playwright/test';
import type { Page } from '@playwright/test';
import fixture from '../../../shared/manual-watch.json' with { type: 'json' };

const widths = [375, 768, 1280, 1920];
const themes = ['light', 'dark'];
const group = {
  id: 'quality-group',
  universityId: 'quality-university',
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
  snapshotId: 'quality-snapshot',
  fetchedAt: '2026-11-01T00:00:00Z',
  sourceUpdatedAt: null,
  lastCheckedAt: '2026-11-01T00:00:00Z',
  rowCount: 12,
  lookupAvailable: false,
  assessmentAvailable: false,
  scenarioAvailable: false,
};

async function setup(page: Page, theme: string, width: number) {
  await page.setViewportSize({ width, height: 960 });
  await page.addInitScript((value) => localStorage.setItem('abiturient-theme', value), theme);
  const state = {
    watches: [fixture],
    groups: [group],
    failCore: false,
    failGroups: false,
    failOptional: false,
    gate: Promise.resolve(),
  };
  await page.route('**/api/v1/**', async (route) => {
    const path = new URL(route.request().url()).pathname.replace('/api/v1', '');
    if (path === '/session')
      return route.fulfill(
        route.request().method() === 'POST'
          ? { status: 204 }
          : { json: { expiresAt: '2030-12-01T00:00:00Z', draftScope: 'a'.repeat(64) } },
      );
    if (
      (state.failCore && ['/watches', '/subscriptions', '/direction-budget'].includes(path)) ||
      (state.failGroups && path === '/groups') ||
      (state.failOptional && ['/changes', '/coverage'].includes(path))
    )
      return route.fulfill({ status: 503, json: { detail: 'Synthetic unavailable' } });
    if (path === '/watches') {
      await state.gate;
      return route.fulfill({ json: state.watches });
    }
    if (path === '/subscriptions') {
      await state.gate;
      return route.fulfill({ json: [] });
    }
    if (path === '/direction-budget')
      return route.fulfill({
        json: {
          limit: 20,
          total: state.watches.length,
          manualCount: state.watches.length,
          archiveCount: 0,
        },
      });
    if (path.endsWith('/history'))
      return route.fulfill({ json: { items: [fixture.latest], total: 1, nextCursor: null } });
    if (path === '/groups') {
      await state.gate;
      return route.fulfill({
        json: {
          items: state.groups,
          total: state.groups.length,
          nextCursor: null,
          facets: { branches: [], years: [2026] },
        },
      });
    }
    if (path === '/universities')
      return route.fulfill({ json: { items: [], total: 0, nextOffset: null } });
    if (path === '/changes')
      return route.fulfill({ json: { items: [], total: 0, unreadCount: 0, nextCursor: null } });
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
    return route.fulfill({ status: 503, json: { detail: 'Unexpected synthetic request' } });
  });
  return state;
}

async function layout(page: Page) {
  const issues = await page.evaluate(() => {
    const visible = (node: Element) =>
      node.getClientRects().length > 0 &&
      getComputedStyle(node).visibility !== 'hidden' &&
      !node.closest('.print-report');
    return {
      documentOverflow: document.documentElement.scrollWidth > innerWidth,
      containers: Array.from(
        document.querySelectorAll('main .surface, main .container, main fieldset'),
      )
        .filter(visible)
        .filter((node) => {
          const rect = node.getBoundingClientRect();
          return rect.left < -1 || rect.right > innerWidth + 1;
        })
        .map((node) => node.className),
      smallText: Array.from(document.querySelectorAll('main p, main label, main a, .footer'))
        .filter(visible)
        .filter((node) => parseFloat(getComputedStyle(node).fontSize) < 12)
        .map((node) => node.textContent?.slice(0, 40)),
      headings: Array.from(document.querySelectorAll('main h1, main h2, main h3, main h4'))
        .filter(visible)
        .filter(
          (node) =>
            parseFloat(getComputedStyle(node).fontSize) >
            (node.tagName === 'H1' ? 32 : node.tagName === 'H2' ? 24 : 20),
        )
        .map((node) => node.textContent),
      controls: Array.from(
        document.querySelectorAll(
          'button, a.button, input:not([type=checkbox]):not([type=radio]), select, summary',
        ),
      )
        .filter(visible)
        .filter((node) => {
          const rect = node.getBoundingClientRect();
          return rect.height < 43.9 || rect.left < -1 || rect.right > innerWidth + 1;
        })
        .map((node) => ({
          tag: node.tagName,
          id: node.id,
          text: node.textContent?.slice(0, 32),
          height: node.getBoundingClientRect().height,
        })),
    };
  });
  expect(issues).toEqual({
    documentOverflow: false,
    containers: [],
    smallText: [],
    headings: [],
    controls: [],
  });
}

async function focusRing(page: Page, selector: string) {
  await page.locator(selector).focus();
  const ring = await page.locator(selector).evaluate((node) => {
    const style = getComputedStyle(node);
    return {
      style: style.outlineStyle,
      width: parseFloat(style.outlineWidth),
      color: style.outlineColor,
      focused: document.activeElement === node,
    };
  });
  expect(ring.focused).toBe(true);
  expect(ring.style).toBe('solid');
  expect(ring.width).toBeGreaterThanOrEqual(3);
  expect(ring.color).not.toBe('rgba(0, 0, 0, 0)');
}

for (const theme of themes)
  for (const width of widths) {
    for (const route of ['/', '/sources', '/tracker', '/missing-page']) {
      test(`${theme} ${width} ready ${route}`, async ({ page }, info) => {
        await setup(page, theme, width);
        await page.goto(route);
        await expect(page.locator('main h1').first()).toBeVisible();
        if (route === '/sources')
          await expect(page.locator('.source-catalog-card h3')).toBeVisible();
        if (route === '/tracker') await expect(page.locator('.direction-card')).toHaveCount(1);
        await page.evaluate(() => document.fonts.ready);
        await layout(page);
        await page.screenshot({ path: info.outputPath('page.png'), fullPage: true });
        if (route === '/') {
          await page.locator('#calculator').scrollIntoViewIfNeeded();
          await layout(page);
          await page.locator('#calculator').screenshot({
            path: info.outputPath('calculator.png'),
            style: '.skip-link:not(:focus) { visibility: hidden; }',
          });
        }
        if (route === '/tracker') {
          await page.getByRole('button', { name: 'История', exact: true }).click();
          await expect(page.locator('.history-scroll')).toBeVisible();
          await layout(page);
        }
      });
    }

    for (const editing of [false, true]) {
      test(`${theme} ${width} ${editing ? 'edit' : 'create'} form`, async ({ page }, info) => {
        const state = await setup(page, theme, width);
        if (!editing) state.watches = [];
        await page.goto('/tracker');
        if (editing)
          await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
        else
          await page
            .locator('.empty-state')
            .getByRole('button', { name: 'Добавить направление', exact: true })
            .click();
        const form = page.locator('.direction-form');
        await expect(form).toBeVisible();
        await layout(page);
        await form.screenshot({
          path: info.outputPath('form.png'),
          style: '.skip-link:not(:focus) { visibility: hidden; }',
        });
        await page.getByText('Как посчитать без ошибок', { exact: true }).click();
        await page.locator('#tracker-rank').fill('1000000');
        await page.locator('#tracker-seats').fill('1000000');
        await layout(page);
        expect(
          await form
            .locator('input')
            .evaluateAll((nodes) =>
              nodes.every((node) => getComputedStyle(node).fontSize === '16px'),
            ),
        ).toBe(true);
      });
    }

    test(`${theme} ${width} tracker loading empty and errors`, async ({ page }, info) => {
      const state = await setup(page, theme, width);
      state.watches = [];
      let release!: () => void;
      state.gate = new Promise<void>((resolve) => {
        release = resolve;
      });
      try {
        await page.goto('/tracker');
        await expect(page.getByRole('heading', { name: 'Загружаем направления…' })).toBeVisible();
        await expect(
          page.getByRole('heading', { name: 'Направлений пока нет', exact: true }),
        ).toHaveCount(0);
        await layout(page);
        release();
        await expect(
          page.getByRole('heading', { name: 'Направлений пока нет', exact: true }),
        ).toBeVisible();
        await page.screenshot({ path: info.outputPath('empty.png'), fullPage: true });
        state.failCore = true;
        await page.reload();
        await expect(
          page.getByRole('heading', { name: 'Не удалось загрузить направления' }),
        ).toBeVisible();
        await expect(page.getByRole('alert')).toHaveCount(1);
        await layout(page);
        await page.screenshot({ path: info.outputPath('error.png'), fullPage: true });
        state.failCore = false;
        await page.getByRole('button', { name: 'Повторить', exact: true }).click();
        await expect(
          page.getByRole('heading', { name: 'Направлений пока нет', exact: true }),
        ).toBeVisible();
        state.failOptional = true;
        await page.getByText('Изменения сохранённых списков', { exact: true }).click();
        await expect(page.locator('.change-feed .request-feedback')).toBeVisible();
        await page.getByText('Источники и охват вузов', { exact: true }).click();
        await expect(page.locator('.coverage-summary .request-feedback')).toBeVisible();
        await expect(page.getByRole('alert')).toHaveCount(0);
        await layout(page);
      } finally {
        release();
      }
    });

    test(`${theme} ${width} source loading empty and errors`, async ({ page }) => {
      const state = await setup(page, theme, width);
      state.groups = [];
      let release!: () => void;
      state.gate = new Promise<void>((resolve) => {
        release = resolve;
      });
      try {
        await page.goto('/sources');
        await expect(page.getByText('Загружаем конкурсные группы…', { exact: true })).toBeVisible();
        await expect(page.locator('.catalog-empty')).toHaveCount(0);
        await layout(page);
        release();
        await expect(page.locator('.catalog-empty')).toBeVisible();
        await layout(page);
        state.failGroups = true;
        await page.reload();
        await expect(page.getByRole('alert')).toBeVisible();
        await expect(page.locator('.catalog-empty')).toHaveCount(0);
        await layout(page);
        state.failGroups = false;
        await page.getByRole('button', { name: 'Повторить загрузку групп' }).click();
        await expect(page.locator('.catalog-empty')).toBeVisible();
        await layout(page);
      } finally {
        release();
      }
    });

    test(`${theme} ${width} keyboard focus and disclosures`, async ({ page }) => {
      await setup(page, theme, width);
      await page.goto('/');
      await expect(page.locator('#hero-title')).toBeFocused();
      await page.keyboard.press('Tab');
      await focusRing(page, '.hero-buttons .button-primary');
      await focusRing(page, '.theme-toggle');
      if (width <= 900) {
        await page.locator('.navigation-toggle').focus();
        await page.keyboard.press('Enter');
        await page.keyboard.press('Tab');
        await expect(page.locator('#site-navigation a').first()).toBeFocused();
        await focusRing(page, '#site-navigation a:first-child');
        await page.keyboard.press('Escape');
        await expect(page.locator('.navigation-toggle')).toBeFocused();
      }
      await focusRing(page, '#rank');
      await page.locator('#rank').fill('0');
      await expect(page.locator('#calculation-error')).toBeVisible();
      await page.locator('#rank').fill('120');
      await focusRing(page, '.scenario-explanation summary');
      await page.keyboard.press('Enter');
      await expect(page.locator('.scenario-explanation')).toHaveAttribute('open', '');
      await layout(page);
      await page.getByRole('link', { name: 'Перейти к содержимому' }).focus();
      await expect(page.getByRole('link', { name: 'Перейти к содержимому' })).toBeInViewport();
      await page.keyboard.press('Enter');
      await expect(page.locator('main')).toBeFocused();
    });
  }
