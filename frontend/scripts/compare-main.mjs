import { execFileSync, spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync } from 'node:fs';
import { mkdir, readFile, symlink, writeFile } from 'node:fs/promises';
import { createServer } from 'node:net';
import { resolve } from 'node:path';
import { build, preview } from 'vite';
import { chromium } from '@playwright/test';
import { stopChild } from './stop-child.mjs';

// A fresh read-only Git reference, never an automatically accepted baseline.
// API responses are captured once from the local stack and shared by both
// previews to avoid timestamp drift. This is visual replay, not API evidence.
const ref = process.argv[2];
const matrix = process.argv[3] === '--layout-matrix';
if (!ref || !/^[a-f0-9]{7,40}$/.test(ref) || process.argv.length > (matrix ? 4 : 3)) {
  throw Error('Usage: node scripts/compare-main.mjs <baseline commit SHA> [--layout-matrix]');
}
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
if (matrix) routes.push('/app/competitions', '/app/competitions/sgu-2026-4588',
  '/app/competitions/sgu-2026-4588/competitors', '/app/coverage', '/auth/verify', '/auth/reset');
const widths = matrix ? [320, 375, 390, 768, 1024, 1440, 1920] : [390, 1440];
const ownsApi = matrix && !process.env.QA_API_TARGET;
const apiPort = ownsApi ? await findLoopbackPort() : 8080;
const api = process.env.QA_API_TARGET ?? `http://127.0.0.1:${apiPort}`;
const target = new URL(api);
if (target.protocol !== 'http:' || !['127.0.0.1', 'localhost'].includes(target.hostname) || target.username || target.password || target.pathname !== '/' || target.search || target.hash) throw Error('QA_API_TARGET must be a local HTTP origin');
const servers = [];
const results = [];
const snapshots = new Map();
let browser, apiProcess;
const hash = value => createHash('sha256').update(value).digest('hex');

async function findLoopbackPort() {
  const socket = createServer();
  await new Promise((done, reject) => {
    socket.once('error', reject);
    socket.listen(0, '127.0.0.1', done);
  });
  const { port } = socket.address();
  await new Promise(done => socket.close(done));
  return port;
}

async function startIsolatedApi() {
  const backend = resolve(root, 'backend');
  const python = process.env.PYTHON ?? ['.venv/Scripts/python.exe', '.venv/bin/python']
    .map(path => resolve(backend, path)).find(existsSync) ?? 'python';
  apiProcess = spawn(python, ['tests/catalog_runtime.py'], {
    cwd: backend, env: { ...process.env, CATALOG_CONTROL_STDIN: '1', CATALOG_RUNTIME_PORT: String(apiPort) },
    stdio: ['pipe', 'ignore', 'inherit'],
  });
  let startupError;
  apiProcess.on('error', error => { startupError = error; });
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    if (startupError || apiProcess.exitCode !== null) throw startupError ?? Error('Visual API exited on startup');
    try {
      if ((await fetch(api + '/api/live')).ok) return;
    } catch { /* Only retry while starting the owned test process. */ }
    await new Promise(done => setTimeout(done, 100));
  }
  throw Error('Visual API did not start within 30 seconds');
}

function relativeUrl(raw) {
  const url = new URL(raw);
  return url.pathname + url.search + url.hash;
}

async function settle(page, route, demo, port, errors) {
  const httpErrors = [], requests = [], responses = [];
  page.on('pageerror', error => errors.push(error.message));
  if (matrix) {
    page.on('request', request => {
      const url = relativeUrl(request.url());
      if (url.startsWith('/api/')) requests.push(`${request.method()} ${url}`);
    });
    page.on('response', response => {
      const url = relativeUrl(response.url());
      if (url.startsWith('/api/')) responses.push(`${response.status()} ${url}`);
    });
    page.on('console', message => {
      if (message.type() !== 'error') return;
      const location = message.location().url;
      if (location && relativeUrl(location).startsWith('/api/') && message.text().startsWith('Failed to load resource:')) {
        httpErrors.push(relativeUrl(location) + ' ' + message.text());
      } else errors.push(message.text());
    });
  }
  const navigation = await page.goto(`http://127.0.0.1:${port}${route}${demo ? '?mode=demo' : ''}`);
  await page.locator('#root h1, #root h2').first().waitFor();
  await page.getByRole('status').filter({ hasText: /Загрузка данных|Обновляем данные/ }).waitFor({ state: 'hidden' });
  if (matrix) await page.waitForLoadState('networkidle');
  await page.evaluate(() => globalThis.document.fonts.ready);
  return {
    text: await page.locator('#root').innerText(),
    overflow: await page.evaluate(() => Math.max(0, globalThis.document.documentElement.scrollWidth - globalThis.innerWidth)),
    status: navigation?.status(), url: relativeUrl(page.url()),
    requests: requests.sort(), responses: responses.sort(), httpErrors: httpErrors.sort(),
  };
}

try {
  if (ownsApi) await startIsolatedApi();
  for (const [source, port, label] of [[reference, 5300, 'main'], [frontend, 5301, 'current']]) {
    const config = { root: source, configFile: false };
    if (matrix) config.build = { outDir: resolve(directory, `dist-${label}`) };
    await build({ ...config, logLevel: 'error' });
    servers.push(await preview({ ...config,
      preview: { host: '127.0.0.1', port: matrix ? 0 : port, strictPort: true } }));
  }
  const ports = servers.map(server => server.httpServer.address().port);
  browser = await chromium.launch();
  for (const width of widths) {
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
          const name = `${width}-${demo ? 'demo' : 'default'}-${route === '/' ? 'landing' : route.slice(1).replaceAll('/', '__')}`;
          const navigate = (page, index) => settle(page, route, demo, ports[index], errors);
          const screenshot = (index, label) => pages[index].screenshot({
            path: resolve(directory, `${name}-${label}.png`),
            fullPage: true, animations: 'disabled', caret: 'hide',
          });
          // Page loads can overlap. Serialize raster capture to avoid concurrent
          // Chromium screenshots of two open surfaces on the same renderer.
          const settled = matrix ? await Promise.all(pages.map(navigate)) : undefined;
          const before = settled?.[0] ?? await navigate(pages[0], 0);
          const beforePng = await screenshot(0, 'main');
          const after = settled?.[1] ?? await navigate(pages[1], 1);
          const afterPng = await screenshot(1, 'current');
          const equal = beforePng.equals(afterPng);
          const item = { route, demo, width, equal, textEqual: before.text === after.text,
            overflow: [before.overflow, after.overflow], errors,
            baselineSha256: hash(beforePng), currentSha256: hash(afterPng) };
          if (matrix) {
            item.routeEqual = before.status === 200 && after.status === 200 && before.url === after.url;
            item.apiEqual = ['requests','responses','httpErrors'].every(key => JSON.stringify(before[key]) === JSON.stringify(after[key]));
            item.httpErrors = before.httpErrors;
          }
          results.push(item);
          console.log(`${equal ? 'PASS' : 'DIFF'} ${name}`);
        } finally { for (const page of pages) await page.close(); }
      }
    } finally { await context.close(); }
  }
} finally {
  await browser?.close();
  for (const server of servers) { server.httpServer.closeAllConnections(); await new Promise(done => server.httpServer.close(done)); }
  await stopChild(apiProcess);
  await writeFile(resolve(directory, 'metrics.json'), JSON.stringify({ baseline: sha, widths, responseMode: 'read-only local API visual replay', results }, null, 2) + '\n');
  console.log(`Evidence: ${directory}`);
}
if (results.length !== routes.length * widths.length * 2 || results.some(r => !r.equal || !r.textEqual || r.errors.length ||
  (matrix ? !r.routeEqual || !r.apiEqual || r.overflow[0] !== r.overflow[1] : r.overflow.some(v => v !== 0)))) {
  throw Error('Visual comparison failed; inspect evidence, do not update a baseline to hide differences.');
}
if (matrix) console.log(`${results.length} identical pairs; inherited page overflow in ${results.filter(r => r.overflow[0]).length} pairs.`);
