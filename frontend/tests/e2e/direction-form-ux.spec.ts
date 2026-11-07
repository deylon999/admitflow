import { expect, test } from '@playwright/test';
import type { Page } from '@playwright/test';
import { calculatePlace, parseWatch } from '@/entities/manual-direction';
import type { Watch, CalculationValues } from '@/entities/manual-direction';
import fixture from '../../../shared/manual-watch.json' with { type: 'json' };

async function install(page: Page, editing = false) {
  const state = {
    watches: editing ? [parseWatch(fixture)] : ([] as Watch[]),
    failure: '' as '' | 'server' | 'network' | 'conflict',
    pending: Promise.resolve(),
    catalogFails: false,
    writes: [] as { body: Record<string, unknown>; key: string; expected?: string }[],
  };
  await page.route('**/api/v1/**', async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname.replace('/api/v1', '');
    if (path === '/session')
      return route.fulfill(
        request.method() === 'POST'
          ? { status: 204 }
          : { json: { expiresAt: '2030-12-01T00:00:00Z', draftScope: 'a'.repeat(64) } },
      );
    if (request.method() === 'POST' && (path === '/watches' || path.endsWith('/snapshots'))) {
      const body = request.postDataJSON() as Record<string, unknown>;
      state.writes.push({
        body,
        key: request.headers()['idempotency-key'],
        expected: request.headers()['x-expected-snapshot'],
      });
      await state.pending;
      if (state.failure === 'server')
        return route.fulfill({ status: 503, json: { detail: 'private_debug database error' } });
      if (state.failure === 'conflict')
        return route.fulfill({
          status: 409,
          json: {
            detail:
              'В списке уже есть более новые данные. Проверьте направление перед сохранением.',
          },
        });
      const values = (path === '/watches' ? body.values : body) as CalculationValues;
      const next = parseWatch({
        ...fixture,
        ...(path === '/watches'
          ? { university: body.university, title: body.title, sourceUrl: body.sourceUrl }
          : {}),
        latest: {
          ...fixture.latest,
          id: 'snapshot-saved',
          capturedAt: '2026-11-07T10:00:00Z',
          values,
          calculation: calculatePlace(values),
        },
      });
      state.watches = [next];
      if (state.failure === 'network') return route.abort('failed');
      return route.fulfill({ status: 201, json: path === '/watches' ? next : next.latest });
    }
    if (path === '/watches') return route.fulfill({ json: state.watches });
    if (path === '/subscriptions') return route.fulfill({ json: [] });
    if (path === '/direction-budget')
      return route.fulfill({
        json: {
          limit: 20,
          total: state.watches.length,
          manualCount: state.watches.length,
          archiveCount: 0,
        },
      });
    if (path.endsWith('/history'))
      return route.fulfill({
        json: { items: [state.watches[0]?.latest ?? fixture.latest], total: 1, nextCursor: null },
      });
    if (path === '/universities')
      return route.fulfill(
        state.catalogFails
          ? { status: 503, json: { detail: 'Unavailable' } }
          : {
              json: {
                items: [
                  {
                    id: 'synthetic-university',
                    name: 'Вуз из подсказки',
                    officialUrl: 'https://example.org',
                    provenanceUrl: 'https://example.org/list',
                    verifiedAt: '2026-11-01T00:00:00Z',
                    coverage: 'manual',
                    catalogOrigin: 'operator',
                    region: 'Тестовый регион',
                  },
                ],
                total: 1,
                nextOffset: null,
              },
            },
      );
    return route.fulfill({ status: 503, json: { detail: 'Unexpected synthetic route' } });
  });
  return state;
}

async function openNew(page: Page) {
  await page.goto('/tracker');
  await page
    .locator('.empty-state')
    .getByRole('button', { name: 'Добавить направление', exact: true })
    .click();
}

async function fill(page: Page) {
  await page.getByLabel('Вуз', { exact: true }).fill('Тестовый вуз');
  await page.getByLabel('Направление', { exact: true }).fill('Информатика, очно, общий конкурс');
  await page.getByLabel('Ссылка на конкурсный список').fill('https://example.org/list');
  for (const [id, value] of Object.entries({
    rank: '120',
    seats: '90',
    excluded: '30',
    'no-consent': '16',
  })) {
    await page.locator(`#tracker-${id}`).fill(value);
  }
}

test('one form explains required fields, groups and sources of numbers', async ({ page }) => {
  await install(page);
  await openNew(page);
  const form = page.locator('.direction-form');
  await expect(form.locator('fieldset.direction-section > legend')).toHaveText([
    'Вуз и направление',
    'Данные из конкурсного списка',
    'Кто находится выше вас',
  ]);
  await expect(form.locator('input[required]')).toHaveCount(7);
  expect(await form.locator('input').evaluateAll((nodes) => nodes.map((node) => node.id))).toEqual([
    'university',
    'direction-title',
    'source-url',
    'tracker-rank',
    'tracker-seats',
    'tracker-excluded',
    'tracker-no-consent',
  ]);
  await expect(form).toContainText('Выбор вуза из подсказок можно пропустить');
  await expect(form).toContainText('Если число неизвестно');
  await expect(page.locator('#tracker-rank')).toHaveValue('');
  await expect(page.locator('#tracker-excluded')).toHaveValue('0');
  await expect(page.locator('#source-url-hint')).toContainText('автоматически не загружаются');
  await expect(page.locator('.tracker-preview')).toHaveCount(0);
  const help = page.getByText('Как посчитать без ошибок', { exact: true });
  await help.focus();
  await page.keyboard.press('Enter');
  await expect(form.getByText('Расчётное место будет 74.', { exact: false })).toBeVisible();
});

test('validation stays next to the affected fields with correct descriptions and focus', async ({
  page,
}) => {
  const state = await install(page);
  await openNew(page);
  await fill(page);
  await page.locator('#tracker-rank').fill('');
  await page.getByRole('button', { name: 'Сохранить направление', exact: true }).click();
  await expect(page.locator('#tracker-rank')).toBeFocused();
  await expect(page.locator('#tracker-rank')).toHaveAttribute(
    'aria-describedby',
    'tracker-rank-hint tracker-calculation-error',
  );
  await expect(page.locator('#tracker-seats')).toHaveAttribute(
    'aria-describedby',
    'tracker-seats-hint',
  );
  await expect(page.locator('#tracker-calculation-error').locator('..')).toHaveClass('field');
  await expect(page.locator('#tracker-calculation-error')).toContainText('целые числа');
  await page.locator('#tracker-rank').fill('120');
  await page.locator('#tracker-no-consent').fill('90');
  await page.getByRole('button', { name: 'Сохранить направление', exact: true }).click();
  await expect(page.locator('#tracker-excluded')).toBeFocused();
  await expect(page.locator('#tracker-excluded')).toHaveAttribute('aria-invalid', 'true');
  await expect(page.locator('#tracker-no-consent')).toHaveAttribute('aria-invalid', 'true');
  await expect(page.locator('#tracker-calculation-error')).toHaveCount(1);
  await expect(page.locator('.tracker-preview')).toHaveCount(0);
  expect(state.writes).toHaveLength(0);
  await page.locator('#tracker-no-consent').fill('16');
  await expect(page.locator('.tracker-preview strong')).toHaveText('74 из 90');
  await expect(page.locator('#tracker-calculation-error')).toHaveCount(0);
});

for (const failure of ['server', 'network'] as const) {
  test(`${failure} save failure preserves values and retry identity`, async ({ page }) => {
    const state = await install(page);
    state.failure = failure;
    await openNew(page);
    await fill(page);
    await page.getByRole('button', { name: 'Сохранить направление', exact: true }).click();
    await expect(page.locator('.direction-save-error')).toContainText(
      'Не удалось подтвердить сохранение',
    );
    await expect(page.locator('.direction-save-error')).not.toContainText('private_debug');
    await expect(page.getByLabel('Направление', { exact: true })).toHaveValue(
      'Информатика, очно, общий конкурс',
    );
    await expect(page.locator('#tracker-no-consent')).toHaveValue('16');
    await expect(page.locator('.tracker-notice')).toBeEmpty();
    const draft = await page.evaluate(() =>
      JSON.parse(sessionStorage.getItem('admitflow-draft-v1')!),
    );
    expect(draft.intent.key).toBe(state.writes[0].key);
    state.failure = '';
    await page.getByRole('button', { name: 'Сохранить направление', exact: true }).click();
    await expect(page.locator('.direction-form')).toHaveCount(0);
    await expect(page.locator('.direction-result strong')).toHaveText('74');
    await expect(page.locator('.tracker-notice')).toContainText('Данные сохранены');
    expect(state.writes).toHaveLength(2);
    expect(state.writes[0]).toEqual(state.writes[1]);
    expect(state.watches).toHaveLength(1);
  });
}

test('pending edit disables changes and preserves the expected snapshot header', async ({
  page,
}) => {
  const state = await install(page, true);
  let release!: () => void;
  state.pending = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
  const form = page.locator('.direction-form');
  await expect(form.locator('.direction-context')).toContainText(fixture.university);
  await expect(form.getByRole('link', { name: 'Открыть список вуза' })).toHaveAttribute(
    'href',
    fixture.sourceUrl,
  );
  await expect(form.locator('input')).toHaveCount(4);
  await page.locator('#tracker-rank').fill('125');
  await page.getByRole('button', { name: 'Сохранить обновление' }).click();
  try {
    await expect(form).toHaveAttribute('aria-busy', 'true');
    await expect(
      form.getByRole('status').filter({ hasText: 'Сохраняем направление' }),
    ).toBeVisible();
    await expect(page.locator('#tracker-rank')).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Закрыть форму' })).toBeDisabled();
    await expect(form.getByRole('button', { name: 'Отмена', exact: true })).toBeDisabled();
    await form.dispatchEvent('submit');
    expect(state.writes).toHaveLength(1);
    expect(state.writes[0].expected).toBe(fixture.latest.id);
    expect(state.writes[0].body).toEqual({ rank: 125, seats: 90, excluded: 30, noConsent: 16 });
  } finally {
    release();
  }
  await expect(form).toHaveCount(0);
  await expect(page.locator('.direction-result strong')).toHaveText('79');
  await expect(page.getByRole('button', { name: 'Обновить цифры', exact: true })).toBeFocused();
});

test('a conflicting edit retains the draft and does not silently replace newer data', async ({
  page,
}) => {
  const state = await install(page, true);
  state.failure = 'conflict';
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
  await page.locator('#tracker-rank').fill('125');
  await page.getByRole('button', { name: 'Сохранить обновление' }).click();
  await expect(page.locator('.direction-save-error')).toContainText('более новые данные');
  await expect(page.locator('#tracker-rank')).toHaveValue('125');
  await expect(page.locator('.direction-result strong')).toHaveText('74');
  expect(state.writes[0].expected).toBe(fixture.latest.id);
});

test('an interrupted attempt can restore its fields and retry key after reload', async ({
  page,
}) => {
  const state = await install(page);
  state.failure = 'server';
  await openNew(page);
  await fill(page);
  await page.getByRole('button', { name: 'Сохранить направление', exact: true }).click();
  await expect(page.locator('.direction-save-error')).toBeVisible();
  page.once('dialog', (dialog) => dialog.accept());
  await page.reload();
  await expect(page.locator('.draft-recovery')).toBeVisible();
  await expect(page.locator('.draft-recovery')).not.toContainText('ключ операции');
  await page.getByRole('button', { name: 'Восстановить черновик', exact: true }).click();
  await expect(page.getByLabel('Вуз', { exact: true })).toHaveValue('Тестовый вуз');
  await expect(page.locator('#tracker-rank')).toHaveValue('120');
  state.failure = '';
  await page.getByRole('button', { name: 'Сохранить направление', exact: true }).click();
  await expect(page.locator('.direction-form')).toHaveCount(0);
  expect(state.writes[0].key).toBe(state.writes[1].key);
});

test('bottom cancel preserves input when the user declines discarding', async ({ page }) => {
  await install(page);
  await openNew(page);
  await fill(page);
  page.once('dialog', (dialog) => dialog.dismiss());
  await page
    .locator('.direction-form')
    .getByRole('button', { name: 'Отмена', exact: true })
    .click();
  await expect(page.locator('#tracker-rank')).toHaveValue('120');
  page.once('dialog', (dialog) => dialog.accept());
  await page
    .locator('.direction-form')
    .getByRole('button', { name: 'Отмена', exact: true })
    .click();
  await expect(page.locator('.direction-form')).toHaveCount(0);
});

test('catalog keyboard selection is optional and does not change save requirements', async ({
  page,
}) => {
  await install(page);
  await openNew(page);
  const university = page.getByLabel('Вуз', { exact: true });
  await university.fill('Вуз');
  await expect(page.locator('.catalog-option')).toHaveCount(1);
  await university.press('ArrowDown');
  await expect(page.locator('.catalog-option')).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(university).toHaveValue('Вуз из подсказки');
  await expect(university).toBeFocused();
  await expect(page.locator('#source-url')).toHaveValue('https://example.org/list');
});

test('an unavailable catalog still allows manual entry and a successful save', async ({ page }) => {
  const state = await install(page);
  state.catalogFails = true;
  await openNew(page);
  await page.getByLabel('Вуз', { exact: true }).fill('Тестовый вуз');
  await expect(page.locator('.catalog-results')).toContainText('Название можно ввести вручную');
  await fill(page);
  await page.getByRole('button', { name: 'Сохранить направление', exact: true }).click();
  await expect(page.locator('.direction-form')).toHaveCount(0);
  await expect(page.locator('.direction-result strong')).toHaveText('74');
});

for (const theme of ['light', 'dark'])
  for (const editing of [false, true]) {
    test(`${theme} ${editing ? 'edit' : 'new'} form is usable at 320px`, async ({ page }, info) => {
      await page.setViewportSize({ width: 320, height: 900 });
      await page.addInitScript((value) => localStorage.setItem('abiturient-theme', value), theme);
      await install(page, editing);
      if (editing) {
        await page.goto('/tracker');
        await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
      } else {
        await openNew(page);
        await fill(page);
      }
      const form = page.locator('.direction-form');
      await page.getByText('Как посчитать без ошибок', { exact: true }).click();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
        true,
      );
      expect(
        await form
          .locator('input, button')
          .evaluateAll((nodes) => nodes.every((node) => node.getBoundingClientRect().height >= 44)),
      ).toBe(true);
      expect(
        await form
          .locator('input')
          .evaluateAll((nodes) =>
            nodes.every((node) => getComputedStyle(node).fontSize === '16px'),
          ),
      ).toBe(true);
      expect(
        await form.locator('input[aria-describedby]').evaluateAll((nodes) =>
          nodes.every((node) =>
            node
              .getAttribute('aria-describedby')!
              .split(' ')
              .every((id) => document.getElementById(id)),
          ),
        ),
      ).toBe(true);
      await expect(page.getByRole('link', { name: 'Перейти к содержимому' })).not.toBeInViewport();
      // A tall element capture can include fixed elements outside the viewport.
      await form.screenshot({
        path: info.outputPath('form.png'),
        style: '.skip-link:not(:focus) { visibility: hidden; }',
      });
      await page.locator('#tracker-seats').fill('1000000');
      await expect(page.locator('#tracker-seats')).toHaveValue('1000000');
    });
  }
