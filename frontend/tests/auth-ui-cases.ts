import { expect, type Page } from '@playwright/test';

export const authWidths = [320, 375, 390, 768, 1024, 1440, 1920];
export const authCases = [
    'login', 'register', 'recovery', 'verify', 'reset',
    'verify-invalid', 'reset-invalid', 'login-error', 'login-network', 'registration-validation',
    'registration-accepted', 'registration-suppressed', 'recovery-accepted', 'recovery-error',
    'verify-expired', 'reset-expired', 'verify-success', 'reset-success', 'login-loading',
    'demo-login', 'demo-register', 'demo-recovery',
] as const;
export type AuthCase = typeof authCases[number];

// UI fixtures only: never evidence of real SMTP/inbox delivery.
export async function openAuthCase(page: Page, state: AuthCase) {
    let release = () => {};
    const pending = new Promise<void>(done => { release = done; });
    await page.route('**/api/**', async route => {
        const path = new URL(route.request().url()).pathname;
        const reply = (status: number, json?: unknown) => route.fulfill({ status, ...(status === 204 ? {} : { json: json ?? {} }) });
        if (path.endsWith('/csrf')) return reply(200, { csrfToken: 'c'.repeat(43) });
        if (path.endsWith('/session')) return reply(401, { code: 'not_authenticated' });
        if (state === 'login-loading') { await pending; return reply(503, { code: 'auth_unavailable' }); }
        if (state === 'login-network') return route.abort('failed');
        if (state.endsWith('-error')) return reply(503, { code: 'auth_unavailable' });
        if (state.endsWith('-expired')) return reply(400, { code: 'invalid_token' });
        if (path.endsWith('/confirm')) return reply(204);
        return reply(202, { message: 'Accepted', dispatch: state === 'registration-suppressed' ? 'suppressed' : 'accepted', retryAfterSeconds: state === 'registration-suppressed' ? 3600 : 60 });
    });
    const mode = state.includes('registration') ? 'register' : state.replace('demo-', '').split('-')[0];
    const emailAction = mode === 'verify' || mode === 'reset';
    await page.goto(`/auth/${mode}${state.startsWith('demo-') ? '?mode=demo' : emailAction && !state.endsWith('-invalid') ? '#token=' + 't'.repeat(43) : ''}`);
    await expect(page.locator('.af-auth-form-wrap')).toBeVisible();
    if (state.endsWith('-invalid')) await expect(page.getByRole('alert')).toBeVisible();
    const submit = state.includes('registration') || /-(error|network|accepted|expired|success|loading)$/.test(state);
    if (submit) {
        if (!emailAction) await page.getByLabel('EMAIL', { exact: true }).fill('controlled@example.org');
        if (mode !== 'recovery' && mode !== 'verify') await page.getByLabel('ПАРОЛЬ', { exact: true }).fill(state === 'registration-validation' ? 'short' : 'a sufficiently long password');
        if (mode === 'register' || mode === 'reset') await page.getByLabel('ПОДТВЕРЖДЕНИЕ ПАРОЛЯ').fill(state === 'registration-validation' ? 'short' : 'a sufficiently long password');
        await page.locator('button[type="submit"]').click();
        if (state === 'login-loading') await expect(page.locator('button[type="submit"]')).toBeDisabled();
        else if (state === 'registration-validation' || /-(error|network|expired)$/.test(state)) await expect(page.getByRole('alert')).toBeVisible();
        else await expect(page.getByRole('status')).toBeVisible();
    }
    await page.evaluate(() => document.fonts.ready);
    return release;
}
