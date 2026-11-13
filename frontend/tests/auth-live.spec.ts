import { expect, test, type Page } from '@playwright/test';
import { readFileSync, renameSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
// Test credentials never enter trace/video/screenshots or published reports.
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
test.describe.configure({ mode: 'serial' });
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
    await page.goto('/auth/verify#token=' + token(email, 'verify'));
    await expect.poll(() => new URL(page.url()).hash.length).toBe(0);
    await page.getByRole('button', { name: 'Подтвердить email ↗' }).click();
    await expect(page.getByRole('status')).toContainText('Email подтверждён');
}
test('PostgreSQL account lifecycle, strict refresh across tabs, guest preservation and recovery revocation', async ({ page, context }) => {
    test.setTimeout(90000); clock(0);
    const email = 'pg-browser@example.org';
    await page.goto('/app');
    await page.getByRole('button', { name: 'Начать гостевую сессию' }).click();
    await expect(page.getByRole('button', { name: 'Начать гостевую сессию' })).toHaveCount(0);
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
    await page.goto('/auth/reset#token=' + reset);
    await page.getByLabel('ПАРОЛЬ', { exact: true }).fill(replacement);
    await page.getByLabel('ПОДТВЕРЖДЕНИЕ ПАРОЛЯ').fill(replacement);
    await page.getByRole('button', { name: 'Сохранить пароль ↗' }).click();
    await expect(page.getByRole('status')).toContainText('Пароль изменён');
    await expect(other.getByRole('heading', { name: 'Войдите в аккаунт' })).toBeVisible();
    const revoked = await context.browser()!.newContext(); await revoked.addCookies(activeCookies);
    expect((await revoked.request.get('http://127.0.0.1:5301/api/v1/auth/session', { headers: { 'X-Requested-With': 'abiturient' } })).status()).toBe(401); await revoked.close();
    await login(page, email, replacement);
    await page.goto('/auth/reset#token=' + reset);
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
    await page.goto('/auth/reset#token=' + token(alice, 'reset'));
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
