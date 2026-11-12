import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdir, readFile, symlink, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { build, preview } from 'vite';
import { chromium } from '@playwright/test';

// A fresh read-only Git reference, never an automatically accepted baseline.
// API responses are captured once from the local stack and shared by both
// previews to avoid timestamp drift. This is visual replay, not API evidence.
const ref = process.argv[2];
if (!ref || !/^[a-f0-9]{7,40}$/.test(ref)) throw Error('Usage: node scripts/compare-main.mjs <baseline commit SHA>');
const frontend = resolve(import.meta.dirname, '..');
const root = resolve(frontend, '..');
const sha = execFileSync('git', ['rev-parse', '--verify', `${ref}^{commit}`], { cwd: root, encoding: 'utf8' }).trim();
const directory = resolve(frontend, 'test-results', `compare-main-${Date.now()}`);
const reference = resolve(directory, 'source', 'frontend');
await mkdir(resolve(directory, 'source'), { recursive: true });
const archive = resolve(directory, 'reference.tar');
execFileSync('git', ['archive', '--format=tar', `--output=${archive}`, sha, 'frontend'], { cwd: root });
execFileSync('tar', ['-xf', archive, '-C', resolve(directory, 'source')]);
await symlink(resolve(frontend, 'node_modules'), resolve(reference, 'node_modules'), 'junction');
const routes = Array.from((await readFile(resolve(frontend, 'SCREEN_INVENTORY.md'), 'utf8')).matchAll(/^\|[^\n]*?\|\s*`(\/[^`]*)`\s*\|/gm), match => match[1]);
if (routes.length !== 29) throw Error('Expected exactly 29 inventory routes');
const api = process.env.QA_API_TARGET ?? 'http://127.0.0.1:8080';
const target = new URL(api);
if (target.protocol !== 'http:' || !['127.0.0.1', 'localhost'].includes(target.hostname) || target.username || target.password || target.pathname !== '/' || target.search || target.hash) throw Error('QA_API_TARGET must be a local HTTP origin');
const servers = [];
const results = [];
const snapshots = new Map();
let browser;
const hash = value => createHash('sha256').update(value).digest('hex');
try {
  await build({ root: reference, configFile: false, logLevel: 'error' });
  await build({ root: frontend, configFile: false, logLevel: 'error' });
  for (const [source, port] of [[reference, 5300], [frontend, 5301]]) {
    servers.push(await preview({ root: source, configFile: false, preview: { host: '127.0.0.1', port, strictPort: true } }));
  }
  browser = await chromium.launch();
  for (const width of [390, 1440]) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, deviceScaleFactor: 1, locale: 'ru-RU', timezoneId: 'Europe/Moscow', colorScheme: 'light', reducedMotion: 'reduce' });
    try {
      await context.route('**/api/**', async route => {
        if (route.request().method() !== 'GET') throw Error('Visual comparison must be read-only');
        const url = new URL(route.request().url());
        const path = url.pathname + url.search;
        if (!snapshots.has(path)) snapshots.set(path, (async () => {
          const response = await fetch(api + path);
          return { status: response.status, contentType: response.headers.get('content-type') ?? 'application/json', body: Buffer.from(await response.arrayBuffer()) };
        })());
        await route.fulfill(await snapshots.get(path));
      });
      for (const demo of [false, true]) for (const route of routes) {
        const pages = [await context.newPage(), await context.newPage()];
        const errors = [];
        try {
          const buffers = [], texts = [], overflow = [];
          const name = `${width}-${demo ? 'demo' : 'default'}-${route === '/' ? 'landing' : route.slice(1).replaceAll('/', '__')}`;
          for (const [index, page] of pages.entries()) {
            page.on('pageerror', error => errors.push(error.message));
            await page.goto(`http://127.0.0.1:${index ? 5301 : 5300}${route}${demo ? '?mode=demo' : ''}`);
            await page.locator('#root h1, #root h2').first().waitFor();
            await page.getByRole('status').filter({ hasText: /Загрузка данных|Обновляем данные/ }).waitFor({ state: 'hidden' });
            await page.evaluate(() => globalThis.document.fonts.ready);
            texts.push(await page.locator('#root').innerText());
            overflow.push(await page.evaluate(() => Math.max(0, globalThis.document.documentElement.scrollWidth - globalThis.innerWidth)));
            buffers.push(await page.screenshot({ path: resolve(directory, `${name}-${index ? 'current' : 'main'}.png`), fullPage: true, animations: 'disabled', caret: 'hide' }));
          }
          const equal = buffers[0].equals(buffers[1]);
          results.push({ route, demo, width, equal, textEqual: texts[0] === texts[1], overflow, errors, baselineSha256: hash(buffers[0]), currentSha256: hash(buffers[1]) });
          console.log(`${equal ? 'PASS' : 'DIFF'} ${name}`);
        } finally { for (const page of pages) await page.close(); }
      }
    } finally { await context.close(); }
  }
} finally {
  await browser?.close();
  for (const server of servers) { server.httpServer.closeAllConnections(); await new Promise(done => server.httpServer.close(done)); }
  await writeFile(resolve(directory, 'metrics.json'), JSON.stringify({ baseline: sha, responseMode: 'read-only local API visual replay', results }, null, 2) + '\n');
  console.log(`Evidence: ${directory}`);
}
if (results.length !== 116 || results.some(r => !r.equal || !r.textEqual || r.errors.length || r.overflow.some(v => v !== 0))) throw Error('Visual comparison failed; inspect evidence, do not update a baseline to hide differences.');
