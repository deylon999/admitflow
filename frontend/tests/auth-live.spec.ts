import { expect, test, type Page } from '@playwright/test';
import { readFileSync, renameSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
// Test credentials never enter trace/video/screenshots or published reports.
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
test.describe.configure({ mode: 'serial' });
test.beforeEach(({ browser, browserName }, info) => {
    expect(browser.browserType().name()).toBe(browserName);
    info.annotations.push({ type: 'browser-engine', description: browserName });
});
const password = 'a safe isolated original phrase';
const replacement = 'a different isolated new phrase';
function clock(seconds: number) {
    const file = join(process.env.AUTH_TEST_DIRECTORY!, 'clock.json');
    writeFileSync(file + '.next', String(seconds)); renameSync(file + '.next', file);
}
function token(email: string, purpose: string): string {
    const rows: { email: string; purpose: string; token: string | null }[] = readFileSync(join(process.env.AUTH_TEST_DIRECTORY!, 'mailbox.jsonl'), 'utf8').trim().split('\n').filter(Boolean).map(line => JSON.parse(line));
    const found = rows.filter(row => row.email === email && row.purpose === purpose && row.token).at(-1);
    if (!found?.token) throw Error('Expected test mail was not delivered.');
    return found.token;
}
async function openEmailAction(page: Page, purpose: 'verify' | 'reset', value: string) {
    try { await page.goto(`/auth/${purpose}#token=${value}`); }
    catch { throw Error('Email action navigation failed.'); }
}
async function login(page: Page, email: string, secret = password) {
    await page.goto('/auth/login');
    await page.getByLabel('EMAIL', { exact: true }).fill(email);
    await page.getByLabel('ПАРОЛЬ', { exact: true }).fill(secret);
    await page.getByRole('button', { name: 'Войти ↗', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Мой аккаунт', exact: true })).toBeVisible();
}
async function register(page: Page, email: string) {
    await page.goto('/auth/register');
    await page.getByLabel('EMAIL', { exact: true }).fill(email);
    await page.getByLabel('ПАРОЛЬ', { exact: true }).fill(password);
    await page.getByLabel('ПОДТВЕРЖДЕНИЕ ПАРОЛЯ').fill(password);
    await page.getByRole('button', { name: 'Создать аккаунт ↗' }).click();
    await expect(page.getByRole('status')).toContainText('Запрос принят');
    await openEmailAction(page, 'verify', token(email, 'verify'));
    await expect.poll(() => new URL(page.url()).hash.length).toBe(0);
    await page.getByRole('button', { name: 'Подтвердить email ↗' }).click();
    await expect(page.getByRole('status')).toContainText('Email подтверждён');
}
test('PostgreSQL account lifecycle, strict refresh across tabs, guest preservation and recovery revocation', async ({ page, context }) => {
    test.setTimeout(90000); clock(0);
    const email = 'pg-browser@example.org';
    await page.goto('/app');
    await Promise.all([
        page.waitForResponse(response => new URL(response.url()).pathname === '/api/v1/session' && response.request().method() === 'POST' && response.status() === 204),
        page.getByRole('button', { name: 'Начать гостевую сессию' }).click(),
    ]);
    await expect.poll(async () => (await context.cookies()).some(cookie => cookie.name === 'abiturient_session')).toBe(true);
    const guest = (await context.cookies()).find(cookie => cookie.name === 'abiturient_session');
    if (!guest) throw Error('Guest cookie missing.');
    await register(page, email);
    await login(page, email);
    const oldCookies = (await context.cookies()).filter(cookie => cookie.name.startsWith('admitflow_'));
    await page.reload(); await expect(page.locator('#root')).toContainText(email);
    const other = await context.newPage(); await other.goto('/app/profile');
    await expect(other.locator('#root')).toContainText(email);
    let rotations = 0;
    context.on('request', req => { if (req.url().endsWith('/auth/refresh') && req.method() === 'POST') rotations++; });
    clock(901);
    await Promise.all([page.reload(), other.reload()]);
    await expect(page.locator('#root')).toContainText(email); await expect(other.locator('#root')).toContainText(email);
    expect(rotations).toBe(1);
    await page.getByRole('button', { name: 'Выйти из аккаунта' }).click();
    await expect(other.getByRole('heading', { name: 'Войдите в аккаунт' })).toBeVisible();
    expect((await context.cookies()).find(cookie => cookie.name === 'abiturient_session')?.value === guest.value).toBe(true);
    // Replaying old credentials must fail against the real backend.
    const replay = await context.browser()!.newContext();
    await replay.addCookies(oldCookies);
    const denied = await replay.request.get('http://127.0.0.1:5301/api/v1/auth/session', { headers: { 'X-Requested-With': 'abiturient' } });
    expect(denied.status()).toBe(401); await replay.close();
    await login(page, email);
    const activeCookies = (await context.cookies()).filter(cookie => cookie.name.startsWith('admitflow_'));
    await page.goto('/auth/recovery'); await page.getByLabel('EMAIL', { exact: true }).fill(email);
    await page.getByRole('button', { name: 'Получить инструкцию ↗' }).click();
    await expect(page.getByRole('status')).toContainText('Запрос принят');
    const reset = token(email, 'reset');
    await openEmailAction(page, 'reset', reset);
    await page.getByLabel('ПАРОЛЬ', { exact: true }).fill(replacement);
    await page.getByLabel('ПОДТВЕРЖДЕНИЕ ПАРОЛЯ').fill(replacement);
    await page.getByRole('button', { name: 'Сохранить пароль ↗' }).click();
    await expect(page.getByRole('status')).toContainText('Пароль изменён');
    await expect(other.getByRole('heading', { name: 'Войдите в аккаунт' })).toBeVisible();
    const revoked = await context.browser()!.newContext(); await revoked.addCookies(activeCookies);
    expect((await revoked.request.get('http://127.0.0.1:5301/api/v1/auth/session', { headers: { 'X-Requested-With': 'abiturient' } })).status()).toBe(401); await revoked.close();
    await login(page, email, replacement);
    await openEmailAction(page, 'reset', reset);
    await page.getByLabel('ПАРОЛЬ', { exact: true }).fill(password);
    await page.getByLabel('ПОДТВЕРЖДЕНИЕ ПАРОЛЯ').fill(password);
    await page.getByRole('button', { name: 'Сохранить пароль ↗' }).click();
    await expect(page.getByRole('alert')).toContainText('Ссылка недействительна');
    await page.goto('/app');
    await expect(page.getByRole('button', { name: 'Начать гостевую сессию' })).toHaveCount(0);
    expect((await context.cookies()).find(cookie => cookie.name === 'abiturient_session')?.value === guest.value).toBe(true);
    clock(31 * 86400);
    await other.reload(); await expect(other.getByRole('heading', { name: 'Войдите в аккаунт' })).toBeVisible();
    clock(0);
});

test('PostgreSQL account switch, other-account recovery isolation, wrong password and CSRF', async ({ page, context }) => {
    clock(0);
    const alice = 'switch-alice@example.org', bob = 'switch-bob@example.org';
    await register(page, alice); await register(page, bob);
    await login(page, alice);
    const other = await context.newPage(); await other.goto('/app/profile');
    await expect(other.locator('#root')).toContainText(alice);
    await login(page, bob);
    await expect(other.locator('#root')).toContainText(bob);
    await expect(other.locator('#root')).not.toContainText(alice);
    const csrfDenied = await context.request.post('http://127.0.0.1:5301/api/v1/auth/logout', { headers: { 'X-Requested-With': 'abiturient', Origin: 'http://127.0.0.1:5301' }, data: {} });
    expect(csrfDenied.status()).toBe(403);
    await page.reload(); await expect(page.locator('#root')).toContainText(bob);
    // Resetting Alice must not revoke the browser's independent Bob session.
    await page.goto('/auth/recovery');
    await page.getByLabel('EMAIL', { exact: true }).fill(alice);
    await page.getByRole('button', { name: 'Получить инструкцию ↗' }).click();
    await expect(page.getByRole('status')).toContainText('Запрос принят');
    await openEmailAction(page, 'reset', token(alice, 'reset'));
    await page.getByLabel('ПАРОЛЬ', { exact: true }).fill(replacement);
    await page.getByLabel('ПОДТВЕРЖДЕНИЕ ПАРОЛЯ').fill(replacement);
    await page.getByRole('button', { name: 'Сохранить пароль ↗' }).click();
    await expect(page.getByRole('status')).toContainText('Пароль изменён');
    await expect(other.locator('#root')).toContainText(bob);
    await page.goto('/app/profile'); await expect(page.locator('#root')).toContainText(bob);
    await page.goto('/auth/login');
    await page.getByLabel('EMAIL', { exact: true }).fill(bob);
    await page.getByLabel('ПАРОЛЬ', { exact: true }).fill('incorrect long password');
    await page.getByRole('button', { name: 'Войти ↗' }).click();
    await expect(page.getByRole('alert')).toContainText('Не удалось войти');
});

function mailMode(value: 'available' | 'fail') {
    const file = join(process.env.AUTH_TEST_DIRECTORY!, 'mail-mode.json');
    writeFileSync(file + '.next', value); renameSync(file + '.next', file);
}
test.afterEach(() => { clock(0); mailMode('available'); });

test('PostgreSQL unverified login, resend, token purpose separation and expired verification', async ({ page, context }) => {
    const email = 'unverified-browser@example.org';
    await page.goto('/auth/register');
    await page.getByLabel('EMAIL', { exact: true }).fill(email);
    await page.getByLabel('ПАРОЛЬ', { exact: true }).fill(password);
    await page.getByLabel('ПОДТВЕРЖДЕНИЕ ПАРОЛЯ').fill(password);
    await page.getByRole('button', { name: 'Создать аккаунт ↗' }).click();
    await expect(page.getByRole('status')).toContainText('Запрос принят');
    const original = token(email, 'verify');
    await page.goto('/auth/login');
    await page.getByLabel('EMAIL', { exact: true }).fill(email);
    await page.getByLabel('ПАРОЛЬ', { exact: true }).fill(password);
    await page.getByRole('button', { name: 'Войти ↗' }).click();
    await expect(page.getByRole('alert')).toContainText('Не удалось войти');
    await page.getByRole('button', { name: 'Повторить письмо подтверждения' }).click();
    await expect(page.getByRole('status')).toContainText('Запрос принят');
    const current = token(email, 'verify');
    expect(current !== original).toBe(true);
    await openEmailAction(page, 'verify', original);
    await page.getByRole('button', { name: 'Подтвердить email ↗' }).click();
    await expect(page.getByRole('alert')).toContainText('Ссылка недействительна');
    await openEmailAction(page, 'reset', current);
    await page.getByLabel('ПАРОЛЬ', { exact: true }).fill(replacement);
    await page.getByLabel('ПОДТВЕРЖДЕНИЕ ПАРОЛЯ').fill(replacement);
    await page.getByRole('button', { name: 'Сохранить пароль ↗' }).click();
    await expect(page.getByRole('alert')).toContainText('Ссылка недействительна');
    await openEmailAction(page, 'verify', current);
    await page.getByRole('button', { name: 'Подтвердить email ↗' }).click();
    await expect(page.getByRole('status')).toContainText('Email подтверждён');
    expect((await context.cookies()).some(cookie => cookie.name === 'admitflow_access')).toBe(false);
    await login(page, email);
    // A separately registered unverified account gets an actually expired link.
    const expiredEmail = 'expired-verify-browser@example.org';
    await page.goto('/auth/register');
    await page.getByLabel('EMAIL', { exact: true }).fill(expiredEmail);
    await page.getByLabel('ПАРОЛЬ', { exact: true }).fill(password);
    await page.getByLabel('ПОДТВЕРЖДЕНИЕ ПАРОЛЯ').fill(password);
    await page.getByRole('button', { name: 'Создать аккаунт ↗' }).click();
    await expect(page.getByRole('status')).toContainText('Запрос принят');
    clock(86401);
    await openEmailAction(page, 'verify', token(expiredEmail, 'verify'));
    await page.getByRole('button', { name: 'Подтвердить email ↗' }).click();
    await expect(page.getByRole('alert')).toContainText('Ссылка недействительна');
});

test('PostgreSQL CSRF and cookie isolation, refresh replay revocation and no browser secrets', async ({ page, context }) => {
    const email = 'replay-browser@example.org';
    await register(page, email); await login(page, email);
    const origin = 'http://127.0.0.1:5301', api = origin + '/api/v1/';
    const base = { 'X-Requested-With': 'abiturient', Origin: origin };
    const proof = (await (await context.request.get(api + 'auth/csrf', { headers: base })).json()).csrfToken as string;
    const headers = { ...base, 'X-CSRF-Token': proof };
    const before = (await context.cookies()).filter(cookie => cookie.name.startsWith('admitflow_'));
    for (const cookie of before) {
        expect(cookie.httpOnly).toBe(true); expect(cookie.sameSite).toBe('Lax');
        expect(cookie.path).toBe(cookie.name === 'admitflow_refresh' ? '/api/v1/auth' : '/api/v1');
    }
    const visible = await page.evaluate(() => ({ cookies: document.cookie, storage: JSON.stringify({ ...localStorage, ...sessionStorage }) }));
    expect(before.every(cookie => !visible.cookies.includes(cookie.value) && !visible.storage.includes(cookie.value))).toBe(true);
    expect(visible.storage.includes(password) || visible.storage.includes(email)).toBe(false);
    for (const unsafe of [base, { ...headers, 'X-CSRF-Token': 'x'.repeat(43) }, { ...headers, Origin: 'https://evil.invalid' }, { ...headers, 'Sec-Fetch-Site': 'cross-site' }, { Origin: origin, 'X-CSRF-Token': proof }]) {
        expect((await context.request.post(api + 'auth/logout', { headers: unsafe, data: {} })).status()).toBe(403);
    }
    const foreign = await context.browser()!.newContext();
    try {
        const foreignProof = (await (await foreign.request.get(api + 'auth/csrf', { headers: base })).json()).csrfToken as string;
        expect((await context.request.post(api + 'auth/logout', { headers: { ...base, 'X-CSRF-Token': foreignProof }, data: {} })).status()).toBe(403);
    } finally { await foreign.close(); }
    expect((await context.request.get(api + 'auth/session')).status()).toBe(200);
    expect((await context.request.post(api + 'auth/refresh', { headers, data: {} })).status()).toBe(200);
    const replay = await context.browser()!.newContext();
    try {
        await replay.addCookies(before);
        expect((await replay.request.post(api + 'auth/refresh', { headers, data: {} })).status()).toBe(401);
        expect((await context.request.get(api + 'auth/session')).status()).toBe(401);
    } finally { await replay.close(); }
    await page.reload(); await expect(page.getByRole('heading', { name: 'Войдите в аккаунт' })).toBeVisible();
    expect((await context.request.post(api + 'session', { headers: base })).status()).toBe(204);
    const guest = (await context.cookies()).find(cookie => cookie.name === 'abiturient_session');
    if (!guest) throw Error('Guest cookie missing.');
    const forged = await context.browser()!.newContext();
    try {
        await forged.addCookies([{ ...guest, name: 'admitflow_access', path: '/api/v1' }, { ...guest, name: 'admitflow_refresh', path: '/api/v1/auth' }]);
        expect((await forged.request.get(api + 'auth/session')).status()).toBe(401);
    } finally { await forged.close(); }
});

test('PostgreSQL recovery enumeration privacy, expired reset and actual test-transport failure', async ({ page, context }) => {
    const email = 'recovery-negative-browser@example.org';
    await register(page, email); await login(page, email);
    const origin = 'http://127.0.0.1:5301', api = origin + '/api/v1/auth/';
    const base = { 'X-Requested-With': 'abiturient', Origin: origin };
    const proof = (await (await context.request.get(api + 'csrf', { headers: base })).json()).csrfToken as string;
    const headers = { ...base, 'X-CSRF-Token': proof };
    const missing = await context.request.post(api + 'recovery/request', { headers, data: { email: 'missing-browser@example.org' } });
    const existing = await context.request.post(api + 'recovery/request', { headers, data: { email } });
    expect(missing.status()).toBe(202); expect(existing.status()).toBe(202);
    expect((await missing.text()) === (await existing.text())).toBe(true);
    const expired = token(email, 'reset'); clock(1801);
    await openEmailAction(page, 'reset', expired);
    await page.getByLabel('ПАРОЛЬ', { exact: true }).fill(replacement);
    await page.getByLabel('ПОДТВЕРЖДЕНИЕ ПАРОЛЯ').fill(replacement);
    await page.getByRole('button', { name: 'Сохранить пароль ↗' }).click();
    await expect(page.getByRole('alert')).toContainText('Ссылка недействительна');
    clock(0);
    await login(page, email); // Expired recovery never changed the old password.
    mailMode('fail');
    await page.goto('/auth/recovery');
    await page.getByLabel('EMAIL', { exact: true }).fill(email);
    await page.getByRole('button', { name: 'Получить инструкцию ↗' }).click();
    await expect(page.getByRole('alert')).toContainText('недоступна');
    await expect(page.locator('.af-inline-success')).toHaveCount(0);
    await page.goto('/app/profile'); await expect(page.locator('#root')).toContainText(email);
});
