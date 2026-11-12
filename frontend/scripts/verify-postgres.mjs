import { execFileSync } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { mkdir, writeFile } from 'node:fs/promises';
import { createServer } from 'node:net';
import { resolve } from 'node:path';
import { build, preview } from 'vite';
import { chromium, expect } from '@playwright/test';

// Requires the existing Compose db + admitflow-backend image. Only an owned,
// fresh test database is seeded. No sources in the user's DB are activated.
const frontend = resolve(import.meta.dirname, '..'), root = resolve(frontend, '..');
const suffix = randomUUID().replaceAll('-', '').slice(0, 12);
const database = `admitflow_test_kan212_${suffix}`, container = `admitflow-kan212-verification-${suffix}`;
if (!/^admitflow_test_kan212_[a-f0-9]{12}$/.test(database) || !/^admitflow-kan212-verification-[a-f0-9]{12}$/.test(container)) throw Error('Unsafe test cleanup target');
const run = args => execFileSync('docker', args, { cwd: root, encoding: 'utf8' }).trim();
for (const port of [5301, 5303]) await new Promise((done, reject) => {
  const socket = createServer(); socket.once('error', reject); socket.listen(port, '127.0.0.1', () => socket.close(done));
});
let created = false, started = false, server, browser, context;
const errors = [], requests = [], result = { fixture: 'derived archive SGU573 rows; isolated PostgreSQL DB; not production source capture', passed: false };
const output = resolve(frontend, 'test-results', 'postgres-flow.json');
try {
  await build({ root: frontend, configFile: false, logLevel: 'error' });
  run(['compose', 'exec', '-T', 'db', 'createdb', '-U', 'admitflow', database]); created = true;
  run(['run', '-d', '--name', container, '--network', 'admitflow_default', '-p', '127.0.0.1:5303:5303', '-e', `KAN212_DATABASE_NAME=${database}`,
    '--mount', `type=bind,source=${resolve(frontend, 'scripts/postgres-runtime.py')},target=/verification.py,readonly`,
    '--mount', `type=bind,source=${resolve(root, 'backend/tests/fixtures/sgu-2026/sgu-4588-derived.html')},target=/fixture.html,readonly`,
    'admitflow-backend', 'python', '/verification.py']); started = true;
  const deadline = Date.now() + 30000;
  while (true) {
    try { if ((await fetch('http://127.0.0.1:5303/api/live')).ok) break; } catch { /* owned runtime startup */ }
    if (Date.now() > deadline) throw Error('Owned PostgreSQL fixture runtime failed to start.');
    await new Promise(done => setTimeout(done, 100));
  }
  server = await preview({ root: frontend, configFile: false, preview: { host: '127.0.0.1', port: 5301, strictPort: true, proxy: { '/api': { target: 'http://127.0.0.1:5303' } } } });
  browser = await chromium.launch();
  context = await browser.newContext({ baseURL: 'http://127.0.0.1:5301', viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  page.on('pageerror', e => errors.push(e.message));
  page.on('response', response => {
    const path = new URL(response.url()).pathname;
    if (path.startsWith('/api/')) requests.push({ endpoint: path.replace(/subscriptions\/[^/]+/, 'subscriptions/{id}'), status: response.status() });
  });
  await page.goto('/app/watchlist');
  await page.getByRole('button', { name: 'Начать гостевую сессию' }).click();
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  await page.getByRole('link', { name: 'Добавить направление', exact: false }).click();
  await page.getByLabel('Поиск конкурса').fill('09.03.04');
  await expect(page.getByRole('button', { name: 'Выбрать', exact: true })).toHaveCount(1);
  await page.getByRole('button', { name: 'Выбрать', exact: true }).click();
  await page.getByLabel('Публичный код в списке').fill('FIXTURE-000003');
  await page.getByRole('button', { name: 'Найти запись', exact: true }).click();
  await expect(page.getByText(/Номер в официальном списке: 3/)).toBeVisible();
  await page.getByRole('button', { name: 'Подтвердить и сохранить' }).click();
  await expect(page.getByText('Сервер подтвердил сохранение подписки.')).toBeVisible();
  await page.getByRole('link', { name: 'Открыть направление', exact: false }).click();
  await expect(page).toHaveURL(/\/app\/watchlist\/[^/]+$/);
  await page.getByRole('link', { name: 'Конкурсный список ↗', exact: true }).click();
  await expect(page.locator('tbody tr')).toHaveCount(50);
  await expect(page.locator('tbody tr.is-me')).toHaveCount(1);
  await expect(page.locator('tbody tr.is-me td').first()).toContainText('3');
  await expect(page.locator('.af-competition-warnings')).toContainText('Архивный список');
  await page.getByRole('button', { name: 'Далее', exact: true }).click();
  await expect(page).toHaveURL(/offset=50/);
  await expect(page.locator('tbody tr').first().locator('td').first()).toHaveText('51');
  await page.reload();
  await expect(page.locator('tbody tr').first().locator('td').first()).toHaveText('51');
  await page.getByRole('link', { name: 'Анализ конкуренции', exact: false }).click();
  await expect(page.locator('.af-spotlight strong')).toHaveText('2');
  await expect(page.locator('.af-spotlight')).toContainText('Ваша позиция 3');
  expect(errors).toEqual([]);
  result.passed = true;
  result.flow = 'guest -> groups -> lookup rank3 -> confirm201 -> subscription detail -> real list50 -> next/reload51 -> summary above2';
} finally {
  if (context) await context.request.delete('/api/v1/session', { headers: { 'X-Requested-With': 'abiturient' } });
  await browser?.close();
  if (server) { server.httpServer.closeAllConnections(); await new Promise(done => server.httpServer.close(done)); }
  // Both names come only from this invocation. Never drop an existing/user DB.
  if (started) { run(['stop', container]); run(['rm', container]); }
  if (created) run(['compose', 'exec', '-T', 'db', 'dropdb', '-U', 'admitflow', database]);
  await mkdir(resolve(output, '..'), { recursive: true });
  await writeFile(output, JSON.stringify({ ...result, errors, requests, cleanup: 'only owned container and fresh test database removed' }, null, 2) + '\n');
}
console.log(`PASS: PostgreSQL guest/lookup/confirm/detail/list/pagination/summary. Evidence: ${output}`);
