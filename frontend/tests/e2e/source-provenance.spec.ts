import { expect, test } from '@playwright/test';
test('source failure preserves fetched/unknown times while showing its separate check', async ({
  page,
}) => {
  test.skip(process.env.E2E_SOURCE_FIXTURE !== '1', 'Requires anonymized fixture DTO');
  const result = await (await page.request.get('/api/v1/groups')).json();
  let state = 'archived',
    checked = result.items[0].lastCheckedAt;
  await page.route('**/api/v1/groups?*', (route) =>
    route.fulfill({
      json: {
        ...result,
        items: [{ ...result.items[0], sourceState: state, lastCheckedAt: checked }],
      },
    }),
  );
  await page.goto('/sources');
  await expect(page.locator('.source-provenance dd').first()).toHaveText(
    result.items[0].snapshotId,
  );
  const original = await page.locator('.source-provenance dd').allTextContents();
  state = 'quarantined';
  checked = '2026-11-03T20:00:00Z';
  await page.reload();
  await expect(page.locator('.source-provenance')).toContainText('Новый ответ источника отклонён');
  const current = await page.locator('.source-provenance dd').allTextContents();
  expect(current.slice(0, 3)).toEqual(original.slice(0, 3));
  expect(current[3]).toContain(checked);
  expect(current[2]).toBe('неизвестно');
  await expect(page.locator('.source-provenance a')).toHaveAttribute(
    'href',
    result.items[0].sourceUrl,
  );
  expect(current[0]).toBe(result.items[0].snapshotId);
});
