import { spawn, spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { createServer } from 'node:net';
import { resolve } from 'node:path';
import { build, preview } from 'vite';
import { stopChild } from './stop-child.mjs';

// Own server lifetimes directly. Playwright's Windows webServer teardown can
// hang when WMI/taskkill are unavailable in managed environments.
const visual = process.argv.includes('--visual');
// Opt-in integration against the existing local PostgreSQL stack. The default
// ephemeral browser-contract runtime remains unchanged for regular CI.
const existingApi = process.env.QA_API_TARGET;
const apiTarget = existingApi ?? 'http://127.0.0.1:5303';
const backend = resolve('../backend');
const python = process.env.PYTHON ?? ['.venv/Scripts/python.exe', '.venv/bin/python']
  .map(path => resolve(backend, path)).find(path => existsSync(path)) ?? 'python';
let api;
const previews = [];

async function requireFreePort(port) {
  await new Promise((done, reject) => {
    const socket = createServer();
    socket.once('error', reject);
    socket.listen(port, '127.0.0.1', () => socket.close(done));
  });
}

try {
  const target = new URL(apiTarget);
  if (target.protocol !== 'http:' || !['127.0.0.1', 'localhost'].includes(target.hostname) || target.username || target.password || target.pathname !== '/' || target.search || target.hash) throw Error('QA_API_TARGET must be a local HTTP origin.');
  for (const port of [...(visual ? [5300, 5301] : [5301]), ...(existingApi ? [] : [5303])]) await requireFreePort(port);
  if (visual && !existsSync('../../admitflow-frontend-v3-main/src/App.tsx')) throw Error('Original sibling React project is required.');
  const typecheck = spawnSync(process.execPath, ['node_modules/typescript/bin/tsc', '-b'], { stdio: 'inherit' });
  if (typecheck.status !== 0) throw Error('TypeScript failed before browser tests.');
  await build({ configFile: false });
  if (!existingApi) api = spawn(python, ['tests/catalog_runtime.py'], {
      cwd: backend, env: { ...process.env, CATALOG_CONTROL_STDIN: '1' }, stdio: ['pipe', 'inherit', 'inherit'],
    });
  let startupError;
  api?.on('error', error => { startupError = error; });
  const deadline = Date.now() + 30_000;
  while (true) {
    if (startupError || (api && api.exitCode !== null)) throw startupError ?? Error('Catalog test API exited during startup.');
    try {
      const response = await fetch(apiTarget + '/api/live');
      if (response.ok) break;
    } catch { /* wait only for the owned API */ }
    if (Date.now() > deadline) throw Error('Catalog test API did not start in 30 seconds.');
    await new Promise(done => setTimeout(done, 100));
  }
  previews.push(await preview({ configFile: false, preview: {
    host: '127.0.0.1', port: 5301, strictPort: true,
    proxy: { '/api': { target: apiTarget } },
  } }));
  if (visual) {
    const { default: reference } = await import('../reference.vite.config.mjs');
    await build({ ...reference, configFile: false });
    previews.push(await preview({ ...reference, configFile: false }));
  }
  const test = spawn(process.execPath, ['node_modules/@playwright/test/cli.js', 'test'], {
    stdio: 'inherit', env: { ...process.env, QA_EXTERNAL_SERVERS: '1', COMPARE_REFERENCE: visual ? '1' : '0' },
  });
  process.exitCode = await new Promise((done, reject) => {
    test.once('error', reject);
    test.once('exit', code => done(code ?? 1));
  });
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
} finally {
  for (const server of previews) {
    server.httpServer.closeAllConnections();
    await new Promise(done => server.httpServer.close(done));
  }
  await stopChild(api);
}
