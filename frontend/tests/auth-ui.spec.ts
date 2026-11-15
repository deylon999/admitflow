import { expect, test } from '@playwright/test';
import { authCases, authWidths, openAuthCase } from './auth-ui-cases';

for (const width of authWidths) {
    for (const state of authCases) test(`auth layout ${state} at ${width}px`, async ({ page }, info) => {
        await page.setViewportSize({ width, height: 900 });
        const release = await openAuthCase(page, state);
        try {
            const panel = page.getByRole('main');
            await expect(panel.locator('.af-page-heading h1')).toBeVisible();
            await expect(panel.getByRole('link', { name: 'Продолжить без входа ↗' })).toBeVisible();
            expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
            const bounds = await panel.boundingBox();
            expect(bounds!.width).toBeLessThanOrEqual(width <= 650 ? width - 32 : 448);
            // Check actual control bounds, including wrapped secondary actions.
            for (const element of await panel.locator('input, button, a').all()) {
                const box = await element.boundingBox();
                if (!box) continue;
                expect(box.x).toBeGreaterThanOrEqual(bounds!.x - 1);
                expect(box.x + box.width).toBeLessThanOrEqual(bounds!.x + bounds!.width + 1);
            }
            if (state.endsWith('-success')) {
                const reset = state.startsWith('reset');
                const title = reset ? 'Пароль успешно изменён' : 'Email подтверждён';
                await expect(panel.getByRole('heading', { name: title, exact: true })).toBeVisible();
                await expect(panel.getByRole('status')).toContainText(reset ? 'Войдите с новым паролем' : 'Теперь можно войти');
                await expect(panel.getByRole('status')).not.toContainText(title);
                await expect(panel.locator('form')).toHaveCount(0);
                await expect(panel.getByRole('alert')).toHaveCount(0);
                const login = panel.getByRole('link', { name: 'Войти в аккаунт', exact: true });
                await expect(login).toHaveAttribute('href', '/auth/login');
                await expect(login).toHaveCSS('background-color', 'rgb(33, 71, 255)');
                expect((await login.boundingBox())!.height).toBeGreaterThanOrEqual(48);
            }
            if (state === 'login-loading') {
                await expect(panel.locator('form')).toHaveAttribute('aria-busy', 'true');
                await expect(panel.locator('input').first()).toBeDisabled();
                await expect(panel.getByRole('status')).toHaveCount(0);
            }
            if (state === 'registration-accepted') {
                await expect(panel.getByRole('button', { name: 'Отправить письмо повторно' })).toBeDisabled();
                await expect(panel.locator('.af-auth-resend__hint')).toContainText('сек.');
            }
            if (state === 'registration-suppressed') {
                await expect(panel.locator('.af-inline-success')).toHaveCount(0);
                await expect(panel.getByRole('button', { name: 'Отправить письмо повторно' })).toHaveCount(0);
            }
            const image = info.outputPath(`${state}-${width}.png`);
            await page.screenshot({ path: image, fullPage: true, animations: 'disabled' });
            await info.attach(`${state}-${width}`, { path: image, contentType: 'image/png' });
        } finally { release(); }
    });
}

for (const width of [320, 1440]) test(`auth keyboard focus and long email remain usable at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 600 });
    await openAuthCase(page, 'login');
    await page.getByLabel('EMAIL', { exact: true }).fill('a'.repeat(64) + '@' + 'sub.'.repeat(40) + 'example.org');
    await page.getByLabel('EMAIL', { exact: true }).focus();
    await page.keyboard.press('Tab');
    await expect(page.getByLabel('ПАРОЛЬ', { exact: true })).toBeFocused();
    await page.keyboard.press('Tab');
    const submit = page.getByRole('button', { name: 'Войти ↗' });
    await expect(submit).toBeFocused();
    await expect(submit).toHaveCSS('outline-style', 'solid');
    await expect(submit).toHaveCSS('outline-color', 'rgb(33, 71, 255)');
    await expect(submit).toHaveCSS('outline-width', '3px');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

for (const reset of [false, true]) test(`completion presentation requires backend acknowledgement: ${reset ? 'reset' : 'verify'}`, async ({ page }) => {
    await openAuthCase(page, reset ? 'reset' : 'verify');
    await page.route('**/api/v1/auth/**/confirm', route => route.fulfill({ status: 202, json: { message: 'Accepted' } }));
    if (reset) {
        await page.getByLabel('ПАРОЛЬ', { exact: true }).fill('a sufficiently long password');
        await page.getByLabel('ПОДТВЕРЖДЕНИЕ ПАРОЛЯ').fill('a sufficiently long password');
    }
    await page.locator('button[type="submit"]').click();
    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.locator('form')).toHaveCount(1);
    await expect(page.getByRole('link', { name: 'Войти в аккаунт', exact: true })).toHaveCount(0);
    await expect(page.getByRole('heading', { name: reset ? 'Пароль успешно изменён' : 'Email подтверждён', exact: true })).toHaveCount(0);
});
