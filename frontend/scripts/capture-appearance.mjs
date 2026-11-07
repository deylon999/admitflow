import { chromium } from '@playwright/test';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';

// Deterministic browser snapshots for architecture migrations without production data.
const phase = process.argv[2];
assert(['baseline', 'after'].includes(phase), 'Use baseline or after');
const baseURL = process.env.E2E_BASE_URL ?? 'http://127.0.0.1:5284';
const directory = resolve('test-results/fsd-appearance');
const watch = JSON.parse(await readFile('../shared/manual-watch.json', 'utf8'));
await mkdir(directory, { recursive: true });

const browser = await chromium.launch();
const snapshots = [];
try {
  for (const theme of ['light', 'dark']) {
    for (const width of [390, 1440]) {
      const context = await browser.newContext({ viewport: { width, height: 900 } });
      await context.addInitScript(
        (value) => localStorage.setItem('abiturient-theme', value),
        theme,
      );
      const page = await context.newPage();
      await page.clock.setFixedTime(new Date('2026-11-06T12:00:00Z'));
      await page.route('**/api/v1/**', async (route) => {
        const path = new URL(route.request().url()).pathname.replace('/api/v1', '');
        let body;
        if (path === '/session') {
          if (route.request().method() === 'POST') return route.fulfill({ status: 204 });
          body = { expiresAt: '2030-12-01T00:00:00Z', draftScope: 'a'.repeat(64) };
        } else if (path === '/watches') body = [watch];
        else if (path === '/subscriptions') body = [];
        else if (path === '/direction-budget') {
          body = { limit: 20, total: 1, manualCount: 1, archiveCount: 0 };
        } else if (path === '/changes') {
          body = { items: [], total: 0, unreadCount: 0, nextCursor: null };
        } else if (path === '/universities') body = { items: [], total: 0, nextOffset: null };
        else if (path === '/groups') {
          body = { items: [], total: 0, nextCursor: null, facets: { branches: [], years: [] } };
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
            generatedAt: '2026-11-06T12:00:00Z',
          });
        } else throw new Error(`Unexpected appearance fixture route: ${path}`);
        return route.fulfill({ json: body });
      });
      for (const route of ['/', '/sources', '/tracker']) {
        await page.goto(new URL(route, baseURL).href);
        await page.locator('main h1').first().waitFor();
        await page.waitForLoadState('networkidle');
        await page.evaluate(() => document.fonts.ready);
        if (route === '/tracker') await page.locator('.direction-card').waitFor();
        if (route === '/sources') await page.locator('.notice').waitFor();
        const name = `${theme}-${width}-${route.slice(1) || 'landing'}`;
        const screenshot = await page.screenshot({
          fullPage: true,
          animations: 'disabled',
          caret: 'hide',
        });
        const path = resolve(directory, `${name}-${phase}.png`);
        await writeFile(path, screenshot);
        if (phase === 'after') {
          const baseline = await readFile(resolve(directory, `${name}-baseline.png`));
          assert(screenshot.equals(baseline), `Appearance changed: ${name}`);
        }
        snapshots.push(name);
      }
      await context.close();
    }
  }
} finally {
  await browser.close();
}
await writeFile(
  resolve(directory, `${phase}.json`),
  JSON.stringify(
    { phase, snapshots, count: snapshots.length, exactPixelMatch: phase === 'after' },
    null,
    2,
  ),
);
process.stdout.write(`${phase}: ${snapshots.length} appearance snapshots verified\n`);
