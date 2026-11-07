import { chromium } from '@playwright/test';
import assert from 'node:assert/strict';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

// Short visual review of the actual application, with deterministic synthetic data.
// No backend, applicant data, or persistent session is used.
const baseURL = process.env.E2E_BASE_URL ?? 'http://127.0.0.1:5285';
const directory = resolve('test-results/design-system');
await mkdir(directory, { recursive: true });
const original = JSON.parse(await readFile('../shared/manual-watch.json', 'utf8'));
const watch = {
  ...original,
  latest: {
    ...original.latest,
    values: { rank: 1_000_000, seats: 1_000_000, excluded: 0, noConsent: 0 },
    calculation: {
      place: 1_000_000,
      worstPlace: 1_000_000,
      seats: 1_000_000,
      state: 'safe',
      status: 'Synthetic manual scenario',
    },
  },
};
const group = {
  id: 'design-group',
  universityId: 'design-university',
  universityName: 'Вуз для визуальной проверки',
  parentUniversityId: null,
  year: 2026,
  level: 'bachelor',
  title: 'Прикладная информатика',
  studyForm: 'full-time',
  funding: 'budget',
  category: 'general',
  seats: 20,
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
const results = [];
const browser = await chromium.launch();
try {
  for (const theme of ['light', 'dark']) {
    for (const width of [320, 1440]) {
      const context = await browser.newContext({
        viewport: { width, height: 960 },
        reducedMotion: 'reduce',
      });
      await context.addInitScript(
        (value) => localStorage.setItem('abiturient-theme', value),
        theme,
      );
      const page = await context.newPage();
      let unavailable = false;
      await page.route('**/api/v1/**', async (route) => {
        const path = new URL(route.request().url()).pathname.replace('/api/v1', '');
        let body;
        if (path === '/session') {
          if (route.request().method() === 'POST') return route.fulfill({ status: 204 });
          body = { expiresAt: '2030-12-01T00:00:00Z', draftScope: 'a'.repeat(64) };
        } else if (path === '/watches') body = [watch];
        else if (path === '/subscriptions') body = [];
        else if (path === '/direction-budget')
          body = { limit: 20, total: 1, manualCount: 1, archiveCount: 0 };
        else if (path === '/changes')
          body = { items: [], total: 0, unreadCount: 0, nextCursor: null };
        else if (path === '/universities') body = { items: [], total: 0, nextOffset: null };
        else if (path === '/groups') {
          if (unavailable)
            return route.fulfill({ status: 503, json: { detail: 'Synthetic outage' } });
          body = {
            items: [group],
            total: 1,
            nextCursor: null,
            facets: { branches: [], years: [2026] },
          };
        } else if (path === '/coverage') {
          body = Object.fromEntries(
            [
              'registeredSources',
              'reviewedSources',
              'importedSources',
              'importedGroups',
              'importedUniversities',
              'importedRows',
              'archiveImportedGroups',
              'conditionalGroups',
              'catalogUniversities',
              'automaticSources',
              'publishedGroups',
              'freshGroups',
              'archiveGroups',
            ].map((key) => [key, 0]),
          );
          Object.assign(body, {
            lastImportedAt: null,
            nationalTotal: null,
            generatedAt: '2026-11-07T12:00:00Z',
          });
        } else throw new Error(`Unexpected design fixture route: ${path}`);
        return route.fulfill({ json: body });
      });
      for (const route of ['/', '/sources', '/tracker']) {
        await page.goto(new URL(route, baseURL).href);
        await page.locator('main h1').first().waitFor();
        await page.waitForLoadState('networkidle');
        await page.evaluate(() => document.fonts.ready);
        const headingSize = await page
          .locator('main h1')
          .first()
          .evaluate((node) => getComputedStyle(node).fontSize);
        assert.equal(headingSize, width === 320 ? '28px' : '32px', `${theme} ${route} h1`);
        const metrics = await page.evaluate(() => ({
          overflow: document.documentElement.scrollWidth > innerWidth + 1,
          buttons: Array.from(document.querySelectorAll('button, a.button'))
            .filter((node) => node.getClientRects().length)
            .map((node) => ({
              styled: node.classList.contains('button'),
              height: node.getBoundingClientRect().height,
              font: getComputedStyle(node).fontSize,
            })),
          headings: Array.from(document.querySelectorAll('main h2, main h3'))
            .filter((node) => node.getClientRects().length)
            .map((node) => ({
              tag: node.tagName,
              size: getComputedStyle(node).fontSize,
            })),
        }));
        assert.equal(metrics.overflow, false, `Overflow: ${theme}/${width}${route}`);
        assert.equal(
          await page.locator('.header-cta').evaluate((node) => node.getBoundingClientRect().height),
          44,
          'Header CTA stays on one line',
        );
        assert(
          metrics.buttons.every((button) => button.styled && button.height >= 43.9),
          `Unstyled/small button: ${route}`,
        );
        assert(
          metrics.headings.every(
            (heading) => heading.size === (heading.tag === 'H2' ? '24px' : '20px'),
          ),
          `Heading scale: ${route}`,
        );
        results.push({ theme, width, route, headingSize, buttons: metrics.buttons.length });
        if (route === '/' && width === 1440) {
          await page.screenshot({ path: resolve(directory, `${theme}-landing-viewport.png`) });
        }
        await page.screenshot({
          path: resolve(directory, `${theme}-${width}-${route.slice(1) || 'landing'}.png`),
          fullPage: true,
        });
        if (route === '/sources') {
          unavailable = true;
          await page.reload();
          const retry = page.getByRole('button', { name: 'Повторить загрузку групп', exact: true });
          await retry.waitFor();
          assert.equal(
            await retry.evaluate((node) => node.classList.contains('button-secondary')),
            true,
          );
          assert.equal(
            await page
              .locator('[role="alert"]')
              .evaluate((node) => node.classList.contains('alert')),
            true,
          );
          await page.screenshot({
            path: resolve(directory, `${theme}-${width}-outage.png`),
            fullPage: true,
          });
          unavailable = false;
          await retry.click();
          await page.locator('article.source-catalog-card').waitFor();
        }
      }
      await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
      await page.locator('.direction-form').waitFor();
      const rank = page.getByLabel('Ваш номер в списке');
      await rank.fill('0');
      const inputMetrics = await rank.evaluate((node) => {
        const style = getComputedStyle(node);
        return {
          height: node.getBoundingClientRect().height,
          size: style.fontSize,
          radius: style.borderRadius,
        };
      });
      assert.equal(inputMetrics.height, 44);
      assert.equal(inputMetrics.size, '16px');
      assert.equal(inputMetrics.radius, '8px');
      const action = page.getByRole('button', { name: 'Сохранить обновление', exact: true });
      await action.hover();
      const hover = await action.evaluate((node) => {
        const reference = document.createElement('span');
        reference.style.color = getComputedStyle(document.documentElement).getPropertyValue(
          '--primary-hover',
        );
        document.body.append(reference);
        const expected = getComputedStyle(reference).color;
        reference.remove();
        const style = getComputedStyle(node);
        return { background: style.backgroundColor, color: style.color, expected };
      });
      assert.equal(hover.background, hover.expected, 'Primary hover retains its accent color');
      const luminance = (color) => {
        const linear = color
          .match(/[\d.]+/g)
          .slice(0, 3)
          .map((value) => {
            const channel = Number(value) / 255;
            return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
          });
        return linear[0] * 0.2126 + linear[1] * 0.7152 + linear[2] * 0.0722;
      };
      const contrast =
        (Math.max(luminance(hover.background), luminance(hover.color)) + 0.05) /
        (Math.min(luminance(hover.background), luminance(hover.color)) + 0.05);
      assert(contrast >= 4.5, `Primary hover contrast: ${contrast}`);
      await action.focus();
      assert.equal(await action.evaluate((node) => getComputedStyle(node).outlineWidth), '3px');
      const opacity = await action.evaluate((node) => {
        node.disabled = true;
        const value = getComputedStyle(node).opacity;
        node.disabled = false;
        return value;
      });
      assert.equal(opacity, '0.5');
      assert.equal(
        await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1),
        false,
        'Editor overflow',
      );
      await page.evaluate(() => {
        if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
        window.scrollTo(0, 0);
      });
      await page.screenshot({
        path: resolve(directory, `${theme}-${width}-editor.png`),
        fullPage: true,
      });
      await context.close();
    }
  }
} finally {
  await browser.close();
}
await writeFile(
  resolve(directory, 'verification.json'),
  JSON.stringify({ pages: results, assertions: 'passed' }, null, 2),
);
process.stdout.write(
  `Design system: ${results.length} page/theme/viewport checks and 4 editor/state checks passed\n`,
);
