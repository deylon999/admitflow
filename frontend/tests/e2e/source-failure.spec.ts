import { expect, test } from '@playwright/test';
test('recovered archive still exposes earlier failed check without changing snapshot time', async ({
  page,
}) => {
  test.skip(process.env.E2E_SOURCE_FIXTURE !== '1', 'Requires anonymized source DTO');
  const catalog = await (await page.request.get('/api/v1/groups')).json(),
    group = catalog.items[0];
  await page.route('**/api/v1/sources/*/checks', (route) =>
    route.fulfill({
      json: [
        {
          id: 'recovered',
          checkedAt: '2026-11-03T12:00:00Z',
          outcome: 'success',
          errorCode: null,
          snapshotId: group.snapshotId,
        },
        {
          id: 'failed',
          checkedAt: '2026-11-03T11:00:00Z',
          outcome: 'failed',
          errorCode: 'invalid_format',
          snapshotId: group.snapshotId,
        },
      ],
    }),
  );
  let posts = 0;
  page.on('request', (request) => {
    if (request.method() === 'POST') posts++;
  });
  await page.goto('/sources');
  await page.getByRole('button', { name: 'Последние проверки источника', exact: true }).click();
  await expect(page.locator('.source-provenance ol li')).toHaveCount(2);
  await expect(page.locator('.source-provenance ol li').first()).toContainText('проверка прошла');
  await expect(page.locator('.source-provenance ol li').last()).toContainText(
    'проверка не прошла; прежний снимок сохранён',
  );
  expect(posts).toBe(0);
  await expect(page.locator('.source-provenance dd').nth(1)).toContainText(group.fetchedAt);
});
