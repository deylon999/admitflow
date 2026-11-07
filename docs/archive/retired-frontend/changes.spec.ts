import { expect, test } from '@playwright/test';
import { openTrackerPanel } from './helpers/tracker';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
test('actual private changefeed links immutable comparison and keeps seen state', async ({
  page,
  browser,
}) => {
  test.skip(process.env.E2E_CHANGES !== '1', 'Requires disposable two-source control');
  await page.goto('/sources');
  const card = page.locator('article.source-catalog-card').filter({ hasText: '09.03.04' });
  await card.getByRole('button', { name: 'Найти свою запись', exact: true }).click();
  await page.getByLabel('Код поступающего').fill('FIXTURE-000020');
  await page.getByRole('button', { name: 'Найти запись', exact: true }).click();
  await page.getByLabel('Подтверждаю: выбраны нужные мне группа и запись').check();
  await page.getByRole('button', { name: 'Сохранить эту запись' }).click();
  await page.getByRole('link', { name: /Открыть мои направления/ }).click();
  await openTrackerPanel(page, 'changes');
  const feed = page.getByRole('region', { name: 'Изменения в ваших списках' });
  await expect(feed).toContainText('Непрочитанных: 0');
  const other = await browser.newContext();
  const otherPage = await other.newPage();
  await otherPage.goto('/tracker');
  await openTrackerPanel(otherPage, 'changes');
  await expect(otherPage.getByRole('region', { name: 'Изменения в ваших списках' })).toContainText(
    'Непрочитанных: 0',
  );
  execFileSync(
    path.resolve('../backend/.venv/bin/python'),
    [path.resolve('../scripts/advance_source_e2e.py')],
    { stdio: 'pipe' },
  );
  await feed.getByRole('button', { name: 'Перечитать изменения', exact: true }).click();
  await expect(feed).toContainText('Непрочитанных: 1');
  const item = (await (await page.request.get('/api/v1/changes')).json()).items[0];
  await feed.getByRole('link', { name: 'Сравнить сохранённые версии' }).click();
  const comparison = page.getByRole('region', { name: 'Сравнение сохранённых сценариев' });
  await expect(comparison).toContainText('До изменения');
  await expect(comparison).toContainText(item.scenario.snapshotId);
  await expect(
    comparison.getByRole('heading', { name: 'Сравнение сохранённых версий' }),
  ).toBeFocused();
  await expect(feed).toContainText('Непрочитанных: 1');
  await feed.getByRole('button', { name: 'Отметить прочитанным' }).click();
  await expect(feed).toContainText('Непрочитанных: 0');
  await page.reload();
  await openTrackerPanel(page, 'changes');
  await expect(feed).toContainText('Прочитано:');
  await otherPage
    .getByRole('region', { name: 'Изменения в ваших списках' })
    .getByRole('button', { name: 'Перечитать изменения', exact: true })
    .click();
  await expect(otherPage.getByRole('region', { name: 'Изменения в ваших списках' })).toContainText(
    'всего: 0',
  );
  expect(
    (
      await otherPage.request.post(`/api/v1/changes/${item.id}/seen`, {
        headers: { 'X-Requested-With': 'abiturient' },
      })
    ).status(),
  ).toBe(404);
  await other.close();
});
