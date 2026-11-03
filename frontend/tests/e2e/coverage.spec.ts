import { expect, test } from '@playwright/test';

test('справочник не выдаётся за автоматический охват', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Требуется API');
  await page.goto('/tracker');
  const section = page.getByRole('region', { name: 'Покрытие источников' });
  const coverage=await (await page.request.get('/api/v1/coverage')).json();
  await expect(section.locator('dd')).toHaveText(['catalogUniversities','automaticSources','publishedGroups','reviewedSources','importedGroups','importedUniversities','conditionalGroups'].map(key=>String(coverage[key])));
  await expect(section).toContainText('Последний импорт получен');
  await expect(section).toContainText('Это не полный охват');
});

test('ошибка проверки покрытия не заменяется ложным нулём', async ({ page }) => {
  await page.route('**/api/v1/coverage', route => route.fulfill({ status: 503, json: { detail: 'Unavailable' } }));
  await page.goto('/tracker');
  const section = page.getByRole('region', { name: 'Покрытие источников' });
  await expect(section.getByRole('alert')).toContainText('Не удалось проверить покрытие');
  await expect(section.locator('dd')).toHaveCount(0);
  await page.unroute('**/api/v1/coverage');
});
