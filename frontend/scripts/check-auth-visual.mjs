// Compare against the reviewed main source, never rewrite historical baselines.
import { execFileSync, spawn } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { chromium } from '@playwright/test';
import { build, preview } from 'vite';
import { stopChild } from './stop-child.mjs';

const baseline = '3035f5e0bd2ba1cbeb3c13c1a002e136d16661d2';
const temporary = mkdtempSync(resolve(tmpdir(), 'admitflow-auth-visual-'));
const evidence = resolve('test-results/pr5-visual'); rmSync(evidence, { recursive: true, force: true }); mkdirSync(evidence, { recursive: true });
const servers = [];
let api, browser;
try {
    const archive = execFileSync('git', ['archive', baseline, 'frontend'], { cwd: '..', maxBuffer: 32 * 1024 * 1024 });
    execFileSync('tar', ['-x', '-C', temporary], { input: archive });
    const original = resolve(temporary, 'frontend');
    symlinkSync(resolve('node_modules'), resolve(original, 'node_modules'), 'dir');
    await build({ root: original, configFile: false, logLevel: 'warn' });
    await build({ configFile: false, logLevel: 'warn' });
    const python = ['../backend/.venv/bin/python', '../backend/.venv/Scripts/python.exe'].find(existsSync) ?? 'python';
    api = spawn(resolve(python), ['tests/catalog_runtime.py'], { cwd: '../backend', env: { ...process.env, CATALOG_CONTROL_STDIN: '1' }, stdio: ['pipe', 'ignore', 'inherit'] });
    const until = Date.now() + 30000;
    while (true) {
        try { if ((await fetch('http://127.0.0.1:5303/api/live')).ok) break; } catch { /* owned runtime starting */ }
        if (Date.now() > until || api.exitCode !== null) throw Error('Visual API failed to start.');
        await new Promise(done => setTimeout(done, 100));
    }
    for (const [root, port] of [[original, 5300], [process.cwd(), 5301]]) servers.push(await preview({ root, configFile: false, logLevel: 'warn', preview: { host: '127.0.0.1', port, strictPort: true, proxy: { '/api': { target: 'http://127.0.0.1:5303' } } } }));
    browser = await chromium.launch();
    const routes = [...readFileSync('SCREEN_INVENTORY.md', 'utf8').matchAll(/^\|[^\n]*?\|\s*`(\/[^`]*)`\s*\|/gm)].map(match => match[1]);
    const changed = ['/auth/login', '/auth/register', '/auth/recovery', '/app/profile'];
    const results = [];
    const hash = bytes => createHash('sha256').update(bytes).digest('hex');
    for (const width of [390, 1440]) {
        const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce', locale: 'ru-RU', timezoneId: 'Europe/Moscow' });
        // Coverage exposes request-time generatedAt. Freeze that one fixture field
        // equally for both builds; all other API fields and pixels remain compared.
        await context.route('**/api/v1/coverage', async route => {
            const response = await route.fetch();
            const json = await response.json();
            await route.fulfill({ response, json: { ...json, generatedAt: '2026-11-13T12:00:00Z' } });
        });
        const before = await context.newPage(), after = await context.newPage();
        const screenshot = async (page, port, route) => {
            const pending = new Set();
            const started = req => pending.add(req.url());
            const finished = req => pending.delete(req.url());
            page.on('request', started); page.on('requestfinished', finished); page.on('requestfailed', finished);
            try { await page.goto(`http://127.0.0.1:${port}${route}`, { waitUntil: 'domcontentloaded' }); }
            catch (error) { console.error(JSON.stringify({ port, route, pending: [...pending] })); throw error; }
            finally { page.off('request', started); page.off('requestfinished', finished); page.off('requestfailed', finished); }
            await page.locator('#root h1, #root h2').first().waitFor();
            await page.waitForFunction("!Array.from(document.querySelectorAll('[role=status]')).some(el => /Загрузка данных|Получаем сведения/.test(el.textContent))");
            await page.evaluate('document.fonts.ready');
            await page.evaluate('new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done)))');
            return page.screenshot({ fullPage: true, animations: 'disabled' });
        };
        for (const mode of ['live', 'demo']) for (const route of routes) {
            if (mode === 'live' && changed.includes(route)) continue;
            const target = route + (mode === 'demo' ? '?mode=demo' : '');
            const a = await screenshot(before, 5300, target), b = await screenshot(after, 5301, target);
            const equal = a.equals(b), name = `${mode}-${width}-${route.replaceAll('/', '_') || 'root'}`;
            if (!equal) { writeFileSync(resolve(evidence, name + '-before.png'), a); writeFileSync(resolve(evidence, name + '-after.png'), b); }
            results.push({ route, mode, width, equal, before: hash(a), after: hash(b) });
        }
        for (const route of [...changed, '/auth/verify', '/auth/reset']) writeFileSync(resolve(evidence, `${width}-${route.replaceAll('/', '_')}.png`), await screenshot(after, 5301, route));
        await context.close();
    }
    writeFileSync(resolve(evidence, 'comparison.json'), JSON.stringify({ baseline, normalizedFixtureField: 'coverage.generatedAt', results }, null, 2));
    console.log(`Visual comparison: ${results.filter(item => item.equal).length}/${results.length} identical; 12 changed/technical screen captures.`);
    if (results.some(item => !item.equal)) process.exitCode = 1;
} catch (error) { console.error(error.message); process.exitCode = 1; }
finally {
    await browser?.close();
    for (const server of servers) { server.httpServer.closeAllConnections(); await new Promise(done => server.httpServer.close(done)); }
    await stopChild(api); rmSync(temporary, { recursive: true, force: true });
}
