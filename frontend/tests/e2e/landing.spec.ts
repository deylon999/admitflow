import { expect, test } from '@playwright/test';

for (const width of [320, 390, 768, 1024, 1440]) {
  test(`лендинг: калькулятор, темы и ширина ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    const errors: string[] = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto('/');
    await expect(page.locator('#hero-title')).toBeVisible();
    await expect(page.locator('#how-it-works')).toContainText('повторно вычитать нельзя');
    await expect(page.locator('.features-grid .tag')).toHaveText([
      'Ручной режим',
      'Доступно',
      'В разработке',
    ]);
    await expect(page.locator('.faq-list')).toContainText('Они не считаются навсегда выбывшими');
    await expect(page.locator('#result-place')).toHaveText('74');
    const explanation = page.locator('.scenario-explanation');
    await explanation.locator('summary').click();
    await expect(explanation).toContainText('120 − 30 − 16 = 74');
    await page.getByLabel('Бюджетных мест', { exact: true }).fill('73');
    await expect(page.locator('#result-status')).toHaveAttribute('data-state', 'out');
    await page.getByLabel('Ваш номер в списке', { exact: true }).fill('');
    await expect(page.locator('#calculation-error')).toBeVisible();
    await expect(page.locator('#result-place')).toHaveText('—');
    await expect(page.locator('#result-status')).toHaveAttribute('data-state', 'insufficient_data');
    await expect(page.locator('.scenario-explanation')).toHaveCount(0);
    await page.getByLabel('Ваш номер в списке', { exact: true }).fill('120');
    for (const theme of ['dark', 'light']) {
      await page
        .getByRole('button', {
          name: theme === 'dark' ? 'Включить тёмную тему' : 'Включить светлую тему',
        })
        .click();
      await expect(page.locator('html')).toHaveAttribute('data-theme', theme);
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth > window.innerWidth,
      );
      expect(overflow).toBe(false);
    }
    const question = page.locator('.faq-list details').nth(1);
    await question.locator('summary').click();
    await expect(question).toHaveAttribute('open', '');
    expect(errors).toEqual([]);
  });
}
