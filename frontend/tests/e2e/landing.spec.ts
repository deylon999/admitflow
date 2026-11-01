import { expect, test } from '@playwright/test';

for (const width of [320, 390, 768, 1440]) {
  test(`лендинг: калькулятор, темы и ширина ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('/');
    await expect(page.locator('#hero-title')).toBeVisible();
    await expect(page.locator('#result-place')).toHaveText('74');
    await page.getByLabel('Бюджетных мест', { exact: true }).fill('73');
    await expect(page.locator('#result-status')).toHaveAttribute('data-state', 'out');
    await page.getByLabel('Ваш номер в списке', { exact: true }).fill('');
    await expect(page.locator('#calculation-error')).toBeVisible();
    await expect(page.locator('#result-place')).toHaveText('—');
    await expect(page.locator('#result-status')).toHaveAttribute('data-state', 'insufficient_data');
    await page.getByLabel('Ваш номер в списке', { exact: true }).fill('120');
    for (const theme of ['dark', 'light']) {
      await page.getByRole('button', { name: theme === 'dark' ? 'Включить тёмную тему' : 'Включить светлую тему' }).click();
      await expect(page.locator('html')).toHaveAttribute('data-theme', theme);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      expect(overflow).toBe(false);
    }
    const question = page.locator('details').nth(1);
    await question.locator('summary').click();
    await expect(question).toHaveAttribute('open', '');
    expect(errors).toEqual([]);
  });
}
