import { expect, test, type BrowserContext, type Page } from '@playwright/test';

type Server = { user: string | null; expired: boolean; refreshes: number; posts: string[]; failure?: number; delay?: number };
async function mockAuth(context: BrowserContext) {
    const server: Server = { user: null, expired: false, refreshes: 0, posts: [] };
    const dto = () => ({ account: { id: server.user, email: `${server.user}@example.org`, emailVerified: true }, accessExpiresAt: '2026-11-13T12:15:00Z', absoluteExpiresAt: '2026-12-13T12:00:00Z' });
    await context.route('**/api/v1/auth/**', async route => {
        const path = new URL(route.request().url()).pathname.split('/auth/')[1];
        const post = route.request().method() === 'POST';
        if (post) server.posts.push(path);
        if (server.delay && post) await new Promise(done => setTimeout(done, server.delay));
        const reply = (status: number, json?: unknown) => route.fulfill({ status, ...(status !== 204 ? { json: json ?? {} } : {}) });
        if (post && route.request().headers()['x-csrf-token'] !== 'c'.repeat(43)) return reply(403, { code: 'csrf_invalid' });
        if (post && server.failure) return route.fulfill({ status: server.failure, json: { code: server.failure === 429 ? 'rate_limited' : 'auth_unavailable', detail: 'PRIVATE-SECRET' }, headers: { 'Retry-After': '23' } });
        if (path === 'csrf') return reply(200, { csrfToken: 'c'.repeat(43) });
        if (path === 'session') return server.user ? server.expired ? reply(401, { code: 'access_expired' }) : reply(200, dto()) : reply(401, { code: 'not_authenticated' });
        if (path === 'login') { server.user = route.request().postDataJSON().email.split('@')[0]; return reply(200, dto()); }
        if (path === 'logout') { server.user = null; return reply(204); }
        if (path === 'refresh') { server.expired = false; server.refreshes++; return reply(200, dto()); }
        if (path === 'verification/confirm' || path === 'recovery/confirm') return reply(204);
        return reply(202, { message: 'Accepted' });
    });
    return server;
}
async function signIn(page: Page, email = 'alice@example.org') {
    await page.goto('/auth/login');
    await page.getByLabel('EMAIL', { exact: true }).fill(email);
    await page.getByLabel('ПАРОЛЬ', { exact: true }).fill('a sufficiently long password');
    await page.getByRole('button', { name: 'Войти ↗', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Мой аккаунт', exact: true })).toBeVisible();
}
test('live login uses server proof, survives reload and server logout preserves guest storage', async ({ page, context }) => {
    const server = await mockAuth(context);
    await signIn(page);
    await page.evaluate(() => localStorage.setItem('admitflow-demo-tracked', '["guest-direction"]'));
    await page.reload();
    await expect(page.locator('#root')).toContainText('alice@example.org');
    await page.getByRole('button', { name: 'Выйти из аккаунта' }).click();
    await expect(page.getByRole('heading', { name: 'Войдите в аккаунт' })).toBeVisible();
    expect(server.posts).toEqual(['login', 'logout']);
    const storage = await page.evaluate(() => JSON.stringify({ ...localStorage, ...sessionStorage }));
    expect(storage).toContain('guest-direction');
    expect(storage).not.toContain('alice@example.org');
    expect(storage).not.toContain('sufficiently');
    expect(storage).not.toContain('csrf');
});
test('registration validates matching long passwords, pending button blocks duplicates and success needs 202', async ({ page, context }) => {
    const server = await mockAuth(context); server.delay = 250;
    await page.goto('/auth/register');
    await page.getByLabel('EMAIL', { exact: true }).fill('new@example.org');
    await page.getByLabel('ПАРОЛЬ', { exact: true }).fill('a sufficiently long password');
    await page.getByLabel('ПОДТВЕРЖДЕНИЕ ПАРОЛЯ').fill('another long phrase here');
    await page.getByRole('button', { name: 'Создать аккаунт ↗' }).click();
    await expect(page.getByRole('alert')).toContainText('не совпадают');
    expect(server.posts).toEqual([]);
    await page.getByLabel('ПОДТВЕРЖДЕНИЕ ПАРОЛЯ').fill('a sufficiently long password');
    await page.getByRole('button', { name: 'Создать аккаунт ↗' }).click();
    await expect(page.getByRole('button', { name: 'Отправляем…' })).toBeDisabled();
    await expect(page.getByRole('status')).toContainText('Запрос принят');
    await expect(page.getByLabel('ПАРОЛЬ', { exact: true })).toHaveValue('');
    expect(server.posts).toEqual(['register']);
});
for (const status of [403, 429, 503]) test(`recovery HTTP ${status} never reports email success or exposes detail`, async ({ page, context }) => {
    const server = await mockAuth(context); server.failure = status;
    await page.goto('/auth/recovery');
    await page.getByLabel('EMAIL', { exact: true }).fill('new@example.org');
    await page.getByRole('button', { name: 'Получить инструкцию ↗' }).click();
    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.locator('.af-inline-success')).toHaveCount(0);
    await expect(page.locator('#root')).not.toContainText('PRIVATE-SECRET');
    if (status === 429) await expect(page.getByRole('alert')).toContainText('23 сек.');
});
test('email fragment is erased before requests, explicit confirmation only, no persistence', async ({ page, context }) => {
    const server = await mockAuth(context);
    const token = 't'.repeat(43);
    await page.goto('/auth/verify#token=' + token);
    await expect(page).toHaveURL(/\/auth\/verify$/);
    expect(server.posts).toEqual([]);
    await expect(page.locator('input')).toHaveCount(0);
    expect(await page.evaluate(() => JSON.stringify({ ...localStorage, ...sessionStorage }))).not.toContain(token);
    await page.getByRole('button', { name: 'Подтвердить email ↗' }).click();
    await expect(page.getByRole('status')).toContainText('Email подтверждён');
    expect(server.posts).toEqual(['verification/confirm']);
    await page.reload(); await expect(page.getByRole('alert')).toContainText('Ссылка недействительна');
});
test('reset accepts a fragment and requires matching password before backend mutation', async ({ page, context }) => {
    const server = await mockAuth(context);
    await page.goto('/auth/reset#token=' + 'r'.repeat(43));
    await expect(page).toHaveURL(/\/auth\/reset$/);
    await page.getByLabel('ПАРОЛЬ', { exact: true }).fill('a new password phrase');
    await page.getByLabel('ПОДТВЕРЖДЕНИЕ ПАРОЛЯ').fill('a new password phrase');
    await page.getByRole('button', { name: 'Сохранить пароль ↗' }).click();
    await expect(page.getByRole('status')).toContainText('Пароль изменён');
    expect(server.posts).toEqual(['recovery/confirm']);
});
test('parallel tabs refresh once and reconcile logout and account switching', async ({ page, context }) => {
    const server = await mockAuth(context);
    await signIn(page);
    const other = await context.newPage();
    await other.goto('/app/profile'); await expect(other.locator('#root')).toContainText('alice@example.org');
    server.expired = true;
    await Promise.all([page.reload(), other.reload()]);
    await expect(page.locator('#root')).toContainText('alice@example.org');
    await expect(other.locator('#root')).toContainText('alice@example.org');
    expect(server.refreshes).toBe(1);
    await page.getByRole('button', { name: 'Выйти из аккаунта' }).click();
    await expect(other.getByRole('heading', { name: 'Войдите в аккаунт' })).toBeVisible();
    await signIn(page, 'bob@example.org');
    await expect(other.locator('#root')).toContainText('bob@example.org');
    await expect(other.locator('#root')).not.toContainText('alice@example.org');
});
test('unavailable session is distinct from anonymous and Demo sends no auth requests', async ({ page, context }) => {
    let calls = 0;
    await context.route('**/api/v1/auth/**', route => { calls++; return route.fulfill({ status: 503, json: { code: 'auth_unavailable' } }); });
    await page.goto('/app/profile');
    await expect(page.getByRole('heading', { name: 'Не удалось проверить аккаунт' })).toBeVisible();
    const before = calls;
    await page.goto('/auth/login?mode=demo');
    await expect(page.getByRole('heading', { name: 'С возвращением!' })).toBeVisible();
    await page.getByLabel('EMAIL', { exact: true }).fill('demo@example.org');
    await page.getByLabel('ПАРОЛЬ', { exact: true }).fill('demo-password');
    await page.getByRole('button', { name: 'Войти ↗' }).click();
    await expect(page.locator('.af-inline-success')).toContainText('вход пока не подключён');
    expect(calls).toBe(before);
});

test('invalid credentials never refresh, create guest access or show a successful login', async ({ page, context }) => {
    const server = await mockAuth(context);
    await context.route('**/api/v1/auth/login', route => route.fulfill({ status: 401, json: { code: 'not_authenticated', detail: 'private@example.org' } }));
    let guestWrites = 0;
    page.on('request', req => { if (req.url().endsWith('/api/v1/session') && req.method() !== 'GET') guestWrites++; });
    await page.goto('/auth/login');
    await page.getByLabel('EMAIL', { exact: true }).fill('invalid@example.org');
    await page.getByLabel('ПАРОЛЬ', { exact: true }).fill('wrong-password');
    await page.getByRole('button', { name: 'Войти ↗' }).click();
    await expect(page.getByRole('alert')).toContainText('Не удалось войти');
    await expect(page.getByLabel('ПАРОЛЬ', { exact: true })).toHaveValue('');
    expect(server.refreshes).toBe(0); expect(guestWrites).toBe(0);
    await expect(page).toHaveURL(/\/auth\/login$/);
});
test('login does not trust POST when subsequent server session belongs to another user', async ({ page, context }) => {
    await mockAuth(context);
    await context.route('**/api/v1/auth/login', route => route.fulfill({ status: 200, json: { account: { id: 'claimed', email: 'claimed@example.org', emailVerified: true }, accessExpiresAt: '2026-11-13T12:15:00Z', absoluteExpiresAt: '2026-12-13T12:00:00Z' } }));
    await page.goto('/auth/login');
    await page.getByLabel('EMAIL', { exact: true }).fill('claimed@example.org');
    await page.getByLabel('ПАРОЛЬ', { exact: true }).fill('wrong-password');
    await page.getByRole('button', { name: 'Войти ↗' }).click();
    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page).toHaveURL(/\/auth\/login$/);
    await expect(page.locator('#root')).not.toContainText('Мой аккаунт');
});
test('peer clears private content before a slow logout completes', async ({ page, context }) => {
    const server = await mockAuth(context);
    await signIn(page);
    const other = await context.newPage(); await other.goto('/app/profile');
    await expect(other.locator('#root')).toContainText('alice@example.org');
    server.delay = 800;
    await page.getByRole('button', { name: 'Выйти из аккаунта' }).click();
    await expect(other.locator('#root')).not.toContainText('alice@example.org');
    await expect(other.getByRole('heading', { name: 'Войдите в аккаунт' })).toBeVisible();
});
test('expired refresh is terminal, a failed refresh is never looped', async ({ page, context }) => {
    const server = await mockAuth(context); server.user = 'alice'; server.expired = true;
    let refreshes = 0;
    await context.route('**/api/v1/auth/refresh', route => { refreshes++; return route.fulfill({ status: 401, json: { code: 'not_authenticated' } }); });
    await page.goto('/app/profile');
    await expect(page.getByRole('heading', { name: 'Войдите в аккаунт' })).toBeVisible();
    expect(refreshes).toBe(1);
    await expect(page.locator('#root')).not.toContainText('alice@example.org');
});
test('without cross-tab locking expired access requires re-login rather than unsafe refresh', async ({ page, context }) => {
    const server = await mockAuth(context); server.user = 'alice'; server.expired = true;
    await page.addInitScript(() => Object.defineProperty(navigator, 'locks', { value: undefined, configurable: true }));
    await page.goto('/app/profile');
    await expect(page.getByRole('alert')).toContainText('Web Locks');
    expect(server.refreshes).toBe(0);
});
test('failed logout hides private state but does not claim server revocation', async ({ page, context }) => {
    const server = await mockAuth(context); await signIn(page); server.failure = 503;
    await page.getByRole('button', { name: 'Выйти из аккаунта' }).click();
    await expect(page.getByRole('heading', { name: 'Не удалось проверить аккаунт' })).toBeVisible();
    expect(server.user).toBe('alice');
    await expect(page.locator('#root')).not.toContainText('alice@example.org');
});
for (const url of ['/auth/verify?token=unsafe', '/auth/reset#token=short', '/auth/verify#token=' + 'x'.repeat(43) + '&token=' + 'y'.repeat(43)]) test(`malformed or query credential is removed and cannot submit: ${url.slice(0, 40)}`, async ({ page, context }) => {
    const server = await mockAuth(context);
    await page.goto(url);
    await expect(page).toHaveURL(/\/auth\/(verify|reset)$/);
    await expect(page.getByRole('alert')).toContainText('Ссылка недействительна');
    await expect(page.locator('form')).toHaveCount(0);
    expect(server.posts).toEqual([]);
});
test('route exit cancels a slow form without showing success on the next route', async ({ page, context }) => {
    const server = await mockAuth(context); server.delay = 600;
    await page.goto('/auth/recovery');
    await page.getByLabel('EMAIL', { exact: true }).fill('slow@example.org');
    await page.getByRole('button', { name: 'Получить инструкцию ↗' }).click();
    await page.getByRole('link', { name: 'Войти', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'С возвращением!' })).toBeVisible();
    await expect(page.locator('.af-inline-success')).toHaveCount(0);
    await expect(page.getByLabel('ПАРОЛЬ', { exact: true })).toHaveValue('');
});
