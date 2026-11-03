import { expect, test } from '@playwright/test';
import fixture from '../../../shared/manual-watch.json' with { type: 'json' };
import { calculatePlace } from '../../src/lib/calculator';

test.beforeEach(async ({ page }) => {
  await page.route('**/api/v1/subscriptions', route => route.fulfill({ json: [] }));
  await page.route('**/api/v1/direction-budget', route => route.fulfill({ json: { limit: 20, total: 0, manualCount: 0, archiveCount: 0 } }));
  await page.route('**/api/v1/session', route => route.request().method() === 'GET' ? route.fulfill({ json: { expiresAt: '2026-12-01T00:00:00Z' } }) : route.fulfill({ status: 204 }));
});

test('можно сравнить любые два загруженных сохранения', async ({ page }) => {
  const items = [120,130,150].map((rank,index) => {
    const values = { ...fixture.latest.values, rank };
    return { ...fixture.latest, id: `snapshot-${3-index}`, values, calculation: calculatePlace(values) };
  });
  await page.route('**/api/v1/watches', route => route.fulfill({ json: [fixture] }));
  await page.route('**/api/v1/watches/*/history*', route => route.fulfill({ json: { items, nextCursor: null, total: 3 } }));
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'История', exact: true }).click();
  await expect(page.getByText('Сохранено 3 из 500. Осталось обновлений: 497.')).toBeVisible();
  await expect(page.locator('.direction-history tbody tr').first().locator('td')).toHaveCount(8);
  await expect(page.locator('.direction-history tbody tr').first()).toContainText('manual-v1');
  await expect(page.locator('.direction-history time').first()).toContainText(fixture.latest.capturedAt);
  await expect(page.locator('.history-comparison strong')).toHaveText('Место: 84 → 74');
  await page.getByLabel('Более раннее сохранение', { exact: true }).selectOption('snapshot-1');
  await expect(page.locator('.history-comparison strong')).toHaveText('Место: 104 → 74');
  await page.getByLabel('Новое сохранение', { exact: true }).selectOption('snapshot-2');
  await expect(page.locator('.history-comparison strong')).toHaveText('Место: 104 → 84');
});

test('поиск, фильтр и порядок не удаляют направления', async ({ page }) => {
  await page.route('**/api/v1/watches', route => route.fulfill({ json: [fixture, { ...fixture, id: 'second', university: 'Другой вуз' }] }));
  await page.goto('/tracker');
  await expect(page.locator('.direction-card')).toHaveCount(2);
  await page.locator('#watch-search').fill('другой');
  await expect(page.locator('.direction-card')).toHaveCount(1);
  await page.locator('#watch-state').selectOption('out');
  await expect(page.getByRole('heading', { name: 'Поиск не дал результатов' })).toBeVisible();
  await page.getByRole('button', { name: 'Сбросить поиск и фильтры' }).click();
  await expect(page.locator('.direction-card')).toHaveCount(2);
  await page.locator('#watch-order').selectOption('university');
  await expect(page.locator('.direction-top .eyebrow').first()).toHaveText('Другой вуз');
});

test('печатный отчёт содержит источник и допущения, без кнопок', async ({ page }) => {
  await page.route('**/api/v1/watches', route => route.fulfill({ json: [fixture] }));
  await page.goto('/tracker');
  await page.evaluate(() => { window.print = () => {}; });
  await page.getByRole('button', { name: /Распечатать выбранный/ }).click();
  await page.emulateMedia({ media: 'print' });
  await expect(page.locator('.print-report')).toBeVisible();
  await expect(page.locator('.print-report')).toContainText(fixture.sourceUrl);
  await expect(page.locator('.print-report')).toContainText('не гарантирует зачисление');
  await expect(page.locator('.print-report')).toContainText('manual-v1');
  await expect(page.locator('.tracker-page-heading')).toBeHidden();
});

test('удаление редактируемого направления требует подтвердить потерю черновика', async ({ page }) => {
  let deleted = 0;
  await page.route('**/api/v1/watches', route => route.fulfill({ json: deleted ? [] : [fixture] }));
  await page.route('**/api/v1/watches/watch-1', route => { deleted++; return route.fulfill({ status: 204 }); });
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
  await page.locator('#tracker-rank').fill('125');
  await page.getByRole('button', { name: 'Удалить', exact: true }).click();
  page.once('dialog', dialog => dialog.dismiss());
  await page.getByRole('button', { name: 'Да, удалить', exact: true }).click();
  expect(deleted).toBe(0);
  await expect(page.locator('#tracker-rank')).toHaveValue('125');
  page.once('dialog', dialog => dialog.accept());
  await page.getByRole('button', { name: 'Да, удалить', exact: true }).click();
  await expect(page.locator('.direction-card')).toHaveCount(0);
  await expect(page.locator('.direction-form')).toHaveCount(0);
  expect(deleted).toBe(1);
});

test('подтверждение удаления получает фокус и закрывается Escape', async ({ page }) => {
  await page.route('**/api/v1/watches', route => route.fulfill({ json: [fixture] }));
  await page.goto('/tracker');
  const trigger = page.getByRole('button', { name: 'Удалить', exact: true });
  await trigger.click();
  await expect(page.getByRole('button', { name: 'Отмена', exact: true })).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(trigger).toBeFocused();
  await page.getByRole('button', { name: 'Удалить все мои данные' }).click();
  await expect(page.getByRole('button', { name: 'Отмена', exact: true })).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('button', { name: 'Удалить все мои данные' })).toBeFocused();
});

test('фоновая ошибка сохраняет карточки и открытый черновик', async ({ page }) => {
  let failed = false;
  await page.route('**/api/v1/watches', route => route.fulfill(failed ? { status: 503, json: { detail: 'Временный отказ' } } : { json: [fixture] }));
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
  await page.locator('#tracker-rank').fill('125');
  failed = true;
  await page.evaluate(() => window.dispatchEvent(new Event('visibilitychange')));
  await expect(page.locator('.stale-warning')).toBeVisible();
  await expect(page.locator('.direction-card')).toHaveCount(1);
  await expect(page.locator('#tracker-rank')).toHaveValue('125');
  failed = false;
  await page.getByRole('button', { name: 'Повторить обновление' }).click();
  await expect(page.locator('.stale-warning')).toHaveCount(0);
});

test('срок доступа берётся с сервера и не продлевается после reload', async ({ page }) => {
  let starts = 0;
  await page.route('**/api/v1/session', route => {
    if (route.request().method() === 'POST') { starts++; return route.fulfill({ status: 204 }); }
    return route.fulfill({ json: { expiresAt: '2026-12-01T00:00:00Z' } });
  });
  await page.route('**/api/v1/watches', route => route.fulfill({ json: [] }));
  await page.goto('/tracker');
  await expect(page.locator('.session-deadline time')).toHaveAttribute('datetime', '2026-12-01T00:00:00Z');
  await page.reload();
  await expect(page.locator('.session-deadline time')).toHaveAttribute('datetime', '2026-12-01T00:00:00Z');
  expect(starts).toBe(1);
});

test('переход по сайту и пропуск навигации управляют фокусом', async ({ page }) => {
  await page.goto('/missing-page');
  await expect(page.getByRole('heading', { name: 'Страница не найдена' })).toBeFocused();
  await expect(page).toHaveTitle('Страница не найдена — Абитуриент');
  await page.getByRole('link', { name: 'На главную', exact: true }).click();
  await expect(page.locator('main h1').first()).toBeFocused();
  const skip = page.getByRole('link', { name: 'Перейти к содержимому' });
  await expect(skip).not.toBeInViewport();
  await skip.focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('main')).toBeFocused();
});

test('историю на телефоне можно прокрутить с клавиатуры', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route('**/api/v1/watches', route => route.fulfill({ json: [fixture] }));
  await page.route('**/api/v1/watches/*/history*', route => route.fulfill({ json: { items: [fixture.latest], nextCursor: null, total: 1 } }));
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'История', exact: true }).click();
  const region = page.getByRole('region', { name: `История ${fixture.title}`, exact: true });
  await region.focus();
  await expect(region).toBeFocused();
  await expect(region.locator('th[scope=col]')).toHaveCount(8);
  await page.keyboard.press('ArrowRight');
  await expect.poll(() => region.evaluate(element => element.scrollLeft)).toBeGreaterThan(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
});

test('ручное обновление списка сохраняет ввод формы и не создаёт сессию', async ({ page }) => {
  let rank = 120;
  let starts = 0;
  page.on('request', request => { if (request.url().endsWith('/api/v1/session') && request.method() === 'POST') starts++; });
  await page.route('**/api/v1/watches', route => {
    const values = { ...fixture.latest.values, rank };
    return route.fulfill({ json: [{ ...fixture, latest: { ...fixture.latest, values, calculation: calculatePlace(values) } }] });
  });
  await page.goto('/tracker');
  await page.getByRole('button', { name: 'Обновить цифры', exact: true }).click();
  await page.locator('#tracker-rank').fill('125');
  rank = 130;
  const before = starts;
  await page.getByRole('button', { name: 'Обновить направления', exact: true }).click();
  await expect(page.locator('.direction-result strong')).toHaveText('84');
  await expect(page.locator('#tracker-rank')).toHaveValue('125');
  expect(starts).toBe(before);
});

test('предпросмотр файла показывает названия безопасным текстом до импорта', async ({ page }) => {
  let imports = 0;
  page.on('request', request => { if (request.url().endsWith('/api/v1/import')) imports++; });
  await page.route('**/api/v1/watches', route => route.fulfill({ json: [] }));
  await page.goto('/tracker');
  await page.getByText('Восстановить из JSON', { exact: true }).click();
  const bundle = { formatVersion: 'manual-export-v1', exportedAt: '2026-11-01T01:00:00Z', watches: [{ ...fixture, title: '<img src=x onerror=alert(1)>', history: [fixture.latest] }] };
  await page.getByLabel('Файл выгрузки, до 8 МБ').setInputFiles({ name: 'bundle.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(bundle)) });
  await expect(page.locator('.import-preview')).toContainText('<img src=x onerror=alert(1)>');
  await expect(page.locator('.import-preview img')).toHaveCount(0);
  await expect(page.locator('.import-preview')).toContainText(fixture.sourceUrl);
  await page.getByRole('button', { name: 'Отменить импорт' }).click();
  await expect(page.locator('.import-preview')).toHaveCount(0);
  expect(imports).toBe(0);
});

test('ошибка загрузки страницы показывает восстановление без автоповтора', async ({ page }) => {
  let failed = true;
  let starts = 0;
  page.on('request', request => { if (request.url().endsWith('/api/v1/session') && request.method() === 'POST') starts++; });
  await page.route(/\/(?:src\/pages\/TrackerPage\.tsx|assets\/TrackerPage-[^/?]+\.js)(?:\?.*)?$/, route => failed ? route.abort('failed') : route.continue());
  await page.route('**/api/v1/watches', route => route.fulfill({ json: [] }));
  await page.goto('/tracker');
  await expect(page.getByRole('heading', { name: 'Не удалось открыть страницу' })).toBeFocused();
  expect(starts).toBe(0);
  failed = false;
  await page.getByRole('button', { name: 'Обновить страницу', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Направлений пока нет' })).toBeVisible();
  expect(starts).toBe(1);
});
