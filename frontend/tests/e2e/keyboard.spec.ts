import { expect, test } from '@playwright/test';

test('saving the twentieth direction returns focus to the page heading when add is disabled', async ({
  page,
}) => {
  test.skip(process.env.E2E_API !== '1', 'Requires API');
  await page.goto('/tracker');
  await expect(page.getByRole('button', { name: 'Добавить первое направление' })).toBeVisible();
  const body = {
    university: 'Keyboard limit example',
    title: 'Manual example',
    sourceUrl: 'https://example.org/list',
    values: { rank: 10, seats: 20, excluded: 0, noConsent: 0 },
  };
  for (let i = 0; i < 19; i++) {
    expect(
      (
        await page.request.post('/api/v1/watches', {
          data: body,
          headers: { 'X-Requested-With': 'abiturient' },
        })
      ).status(),
    ).toBe(201);
  }
  await page.reload();
  await page.getByRole('button', { name: 'Добавить направление', exact: true }).click();
  await page.getByLabel('Вуз', { exact: true }).fill(body.university);
  await page.getByLabel('Направление и конкурсная группа').fill(body.title);
  await page.getByLabel('Ссылка на конкурсный список').fill(body.sourceUrl);
  await page.getByLabel('Ваш номер в списке').fill('10');
  await page.getByLabel('Бюджетных мест', { exact: true }).fill('20');
  await page.getByRole('button', { name: 'Сохранить направление' }).click();
  await expect(
    page.getByRole('button', { name: 'Добавить направление', exact: true }),
  ).toBeDisabled();
  await expect(page.getByRole('heading', { name: 'Мои направления', exact: true })).toBeFocused();
});

for (const width of [390, 1440]) {
  test(`клавиатура: форма, справочник, сохранение и возврат фокуса (${width})`, async ({
    page,
  }) => {
    test.skip(process.env.E2E_API !== '1', 'Требуется настоящий API');
    await page.setViewportSize({ width, height: 900 });
    await page.goto('/tracker');
    const first = page.getByRole('button', { name: 'Добавить первое направление' });
    await first.focus();
    await page.keyboard.press('Enter');
    const heading = page.getByRole('heading', { name: 'Добавить направление', exact: true });
    await expect(heading).toBeFocused();
    await page.keyboard.press('Escape');
    await expect(first).toBeFocused();
    await expect(page.getByRole('form')).toHaveCount(0);

    await page.keyboard.press('Enter');
    await expect(heading).toBeFocused();
    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', { name: 'Закрыть форму' })).toBeFocused();
    await page.keyboard.press('Tab');
    const university = page.getByLabel('Вуз', { exact: true });
    await expect(university).toBeFocused();
    await expect(page.locator('.catalog-option').first()).toBeVisible();
    await page.keyboard.press('Tab');
    await expect(page.locator('.catalog-option').first()).toBeFocused();
    await page.keyboard.press('Escape');
    await expect(university).toBeFocused();
    await expect(page.locator('.catalog-results')).toHaveCount(0);
    await expect(heading).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(first).toBeFocused();

    await page.keyboard.press('Enter');
    await expect(heading).toBeFocused();
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await expect(university).toBeFocused();
    await page.keyboard.type('Keyboard University');
    await page.keyboard.press('Tab');
    await expect(page.getByLabel('Направление и конкурсная группа')).toBeFocused();
    await page.keyboard.type('Keyboard admission group');
    await page.keyboard.press('Tab');
    await page.keyboard.type('https://example.org/list');
    await page.keyboard.press('Tab');
    await page.keyboard.type('120');
    await page.keyboard.press('Tab');
    await page.keyboard.type('90');
    await page.keyboard.press('Tab');
    await page.keyboard.press('ControlOrMeta+A');
    await page.keyboard.type('30');
    await page.keyboard.press('Tab');
    await page.keyboard.press('ControlOrMeta+A');
    await page.keyboard.type('16');
    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', { name: 'Сохранить направление' })).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(page.locator('.direction-result strong')).toHaveText('74');
    await expect(
      page.getByRole('button', { name: 'Добавить направление', exact: true }),
    ).toBeFocused();

    const edit = page.getByRole('button', { name: 'Обновить цифры', exact: true });
    await edit.focus();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('heading', { name: 'Обновить цифры' })).toBeFocused();
    await page.keyboard.press('Escape');
    await expect(edit).toBeFocused();
  });
}

test('Escape и закрытие не теряют форму при сохранении', async ({ page }) => {
  test.skip(process.env.E2E_API !== '1', 'Требуется настоящий API');
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route('**/api/v1/watches', async (route) => {
    if (route.request().method() === 'POST') await gate;
    await route.continue();
  });
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Добавить первое направление' }).click();
  await page.getByLabel('Вуз', { exact: true }).fill('Pending University');
  await page.getByLabel('Направление и конкурсная группа').fill('Pending group');
  await page.getByLabel('Ссылка на конкурсный список').fill('https://example.org/list');
  await page.getByLabel('Ваш номер в списке').fill('10');
  await page.getByLabel('Бюджетных мест').fill('20');
  await page.getByRole('button', { name: 'Сохранить направление' }).click();
  try {
    await expect(page.getByRole('button', { name: 'Закрыть форму' })).toBeDisabled();
    await page.keyboard.press('Escape');
    await expect(page.getByRole('form', { name: 'Добавить направление' })).toBeVisible();
  } finally {
    release();
  }
  await expect(page.locator('.direction-result strong')).toHaveText('10');
});
