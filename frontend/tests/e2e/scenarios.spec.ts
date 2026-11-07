import { expect, test } from '@playwright/test';
import { openTrackerPanel } from './helpers/tracker';
import type { Page } from '@playwright/test';
test.beforeEach(() =>
  test.skip(process.env.E2E_SCENARIOS !== '1', 'Requires two-source scenario fixtureAPI'),
);
async function save(page: Page, code = 'FIXTURE-000020', group = '09.03.04') {
  await page.goto('/sources');
  const card = page.locator('article.source-catalog-card').filter({ hasText: group });
  await card.getByRole('button', { name: 'Найти свою запись', exact: true }).click();
  await page.getByLabel('Код поступающего').fill(code);
  await page.getByRole('button', { name: 'Найти запись', exact: true }).click();
  await page.getByLabel('Подтверждаю: выбраны нужные мне группа и запись').check();
  await page.getByRole('button', { name: 'Сохранить эту запись' }).click();
  await page.getByRole('link', { name: /Открыть мои направления/ }).click();
  await openTrackerPanel(page, 'archive-history');
  await openTrackerPanel(page, 'archive-facts');
}
for (const theme of ['light', 'dark'])
  test(`stored archive scenario explains conditional numbers at320px ${theme}`, async ({
    page,
  }) => {
    await page.addInitScript((v) => localStorage.setItem('abiturient-theme', v), theme);
    await page.setViewportSize({ width: 320, height: 1100 });
    await save(page);
    const scenario = page.getByRole('region', { name: 'Условный сценарий по списку' });
    await expect(scenario.locator('.scenario-numbers')).toBeVisible();
    const records = await (await page.request.get('/api/v1/subscriptions')).json();
    const actual = await (
      await page.request.get(`/api/v1/subscriptions/${records[0].id}/scenario`)
    ).json();
    await expect(scenario.locator('.scenario-summary')).toHaveText(actual.explanation.summary);
    await expect(scenario).toContainText('ваше согласие');
    await expect(scenario).toContainText('Приоритеты между группами не учтены');
    await expect(scenario).toContainText(actual.snapshotId);
    await expect(scenario).toContainText('архив 2026');
    await scenario.getByText('Основания и ограничения сценария', { exact: true }).click();
    await expect(scenario).toContainText('listed-consent-v1');
    await scenario.getByRole('button', { name: 'История условных сценариев' }).click();
    await expect(scenario.locator('.scenario-history li')).toHaveCount(1);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
  });
test('paid zero-capacity source retains explicit refusal and unknown consent', async ({ page }) => {
  await save(page, 'FIXTURE-000001', '01.03.02');
  const card = page.locator('.archive-direction-card');
  await expect(card.getByRole('region', { name: 'Условный сценарий по списку' })).toContainText(
    'Для этого платного конкурса',
  );
  await expect(card.locator('.scenario-numbers')).toHaveCount(0);
  await expect(card).toContainText('Согласие в источнике: неизвестно');
  await expect(card).toContainText('Договор и оплата не считаются согласием');
});
