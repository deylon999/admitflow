import { test, expect } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { evidenceDirectory } from './routes';

const university = '/universities/sgu-saratov';
const program = '/programs/sgu-2026-4588';

for (const width of [390, 1440]) {
  test(`real catalog journey, stable IDs and reload at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    await page.goto('/universities?q=СГУ+Чернышевского');
    await expect(page.locator('.af-program-card')).toHaveCount(1);
    await page.locator('.af-program-card h3 a').click();
    await expect(page).toHaveURL(new RegExp(`${university}$`));
    await expect(page.locator('.af-profile-hero')).toContainText('СГУ имени');
    await expect(page.locator('.af-program-card')).toHaveCount(2);
    await page.locator(`a[href="${program}"]`).first().click();
    await expect(page).toHaveURL(new RegExp(`${program}$`));
    await expect(page.locator('.af-page-heading h1')).toContainText('Программная инженерия');
    await expect(page.locator('.af-info-row').filter({ hasText: 'Бюджетных мест' })).toContainText('16');
    await expect(page.locator('.af-info-row').filter({ hasText: 'Приёмная кампания' })).toContainText('2026');
    await expect(page.locator('.af-spotlight')).toContainText('Нет данных');
    await expect(page.locator('.af-catalog-source a')).toHaveAttribute('href', 'https://www.sgu.ru/svodka/4588');
    await expect(page.locator('.af-catalog-source')).toContainText('03.11.2026');
    await expect(page.locator('.af-main')).not.toContainText('74%');
    await page.reload();
    await expect(page.locator('.af-info-row').filter({ hasText: 'Бюджетных мест' })).toContainText('16');
    await page.getByRole('link', { name: 'Университет ↗', exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`${university}$`));
    await page.getByRole('link', { name: 'Программы университета', exact: false }).click();
    await expect(page).toHaveURL(/programs\?universityId=sgu-saratov$/);
    await expect(page.locator('.af-program-card')).toHaveCount(2);
    if (width === 1440) await expect(page.locator('.af-sidebar')).toBeVisible();
    else await expect(page.locator('.af-mobile-nav')).toBeVisible();
    expect(errors).toEqual([]);
  });
}

test('real search, region, sorting, pages and browser history', async ({ page }) => {
  await page.goto('/universities');
  await expect(page.locator('.af-program-card')).toHaveCount(12);
  const first = await page.locator('.af-program-card h3').allTextContents();
  await page.getByRole('button', { name: 'Далее', exact: true }).click();
  await expect(page).toHaveURL(/offset=12/);
  await expect(page.locator('.af-program-card')).toHaveCount(12);
  await expect.poll(()=>page.locator('.af-program-card h3').allTextContents()).not.toEqual(first);
  await page.goBack();
  await expect(page.locator('.af-program-card h3').first()).toHaveText(first[0]);
  await page.getByLabel('СОРТИРОВКА').selectOption('name-desc');
  await expect(page.locator('.af-program-card h3').first()).not.toHaveText(first[0]);
  await page.getByLabel('РЕГИОН', { exact: true }).selectOption('Саратовская область');
  await expect(page.locator('.af-program-card').first()).toContainText('Саратовская область');
  await page.locator('.af-search-panel input').fill('Программная');
  await expect(page.locator('.af-program-card')).toHaveCount(1);
  await expect(page.locator('.af-program-card')).toContainText('СГУ имени');
  await page.locator('.af-search-panel input').fill('no-such-university');
  await expect(page.locator('.af-empty')).toContainText('Ничего не нашлось');
});

test('program code search, campaign isolation and unsupported subject', async ({ page }) => {
  await page.goto('/programs');
  await expect(page.locator('.af-program-card')).toHaveCount(2);
  await page.getByPlaceholder('Поиск по названию или коду').fill('09.03.04');
  await expect(page.locator('.af-program-card')).toHaveCount(1);
  await expect(page.locator('.af-program-card')).toContainText('16 мест');
  await page.getByLabel('ГОД ПОСТУПЛЕНИЯ').selectOption('2026');
  await expect(page.locator('.af-program-card')).toHaveCount(1);
  await page.goto('/programs?year=2027');
  await expect(page.locator('.af-empty')).toContainText('Ничего не нашлось');
  await expect(page.getByLabel('ГОД ПОСТУПЛЕНИЯ')).toHaveValue('2027');
  await page.goto(university + '?year=2027');
  await expect(page.locator('.af-empty')).toContainText('Нет данных');
  await page.goto('/programs?subject=Информатика');
  await expect(page.locator('.af-empty')).toContainText('Ничего не нашлось');
  const directory = await page.request.get('/api/v1/catalog/universities?limit=12');
  const emptyUniversity = (await directory.json()).items.find((item: { knownProgramCount: number }) => item.knownProgramCount === 0);
  expect(emptyUniversity).toBeTruthy();
  await page.goto(`/universities/${emptyUniversity.id}`);
  await expect(page.locator('.af-profile-hero h1')).toBeVisible();
  await expect(page.locator('.af-empty')).toContainText('Нет данных');
  await expect(page.locator('.af-program-card')).toHaveCount(0);
});

test('loading, real HTTP errors, retry and detail 404', async ({ page }) => {
  let fail = true;
  await page.route('**/api/v1/catalog/programs?**', async route => {
    if (fail) await route.fulfill({ status: 503, contentType: 'application/json', body: '{"detail":"temporary"}' });
    else await route.continue();
  });
  await page.goto('/programs');
  await expect(page.getByRole('alert')).toContainText('Не удалось загрузить данные');
  await expect(page.locator('.af-program-card')).toHaveCount(0);
  fail = false;
  await page.getByRole('button', { name: 'Повторить', exact: true }).click();
  await expect(page.locator('.af-program-card')).toHaveCount(2);
  await page.goto('/programs/unknown-id');
  await expect(page.getByRole('alert')).toContainText('Запись не найдена');
  await expect(page.locator('.af-spotlight')).toHaveCount(0);
});

test('a late response cannot replace the current search', async ({ page }) => {
  let release: () => void = () => {};
  const blocked = new Promise<void>(resolve => { release = resolve; });
  await page.route('**/api/v1/catalog/programs?**', async route => {
    if (new URL(route.request().url()).searchParams.get('q') === 'old') {
      await blocked;
      try { await route.continue(); } catch { /* superseded request was aborted */ }
    } else await route.continue();
  });
  await page.goto('/programs');
  await expect(page.locator('.af-program-card')).toHaveCount(2);
  const oldRequest = page.waitForRequest(request => request.url().includes('q=old'));
  await page.getByPlaceholder('Поиск по названию или коду').fill('old');
  await oldRequest;
  await expect(page.getByRole('status')).toContainText('Загрузка данных');
  await page.getByPlaceholder('Поиск по названию или коду').fill('09.03.04');
  await expect(page.locator('.af-program-card')).toHaveCount(1);
  release();
  await expect(page.locator('.af-program-card')).toContainText('Программная инженерия');
});

test('an HTML fallback is an error, never demo catalog data', async ({ page }) => {
  await page.route('**/api/v1/catalog/universities?**', route => route.fulfill({ status: 200, contentType: 'text/html', body: '<div id="root"></div>' }));
  await page.goto('/universities');
  await expect(page.getByRole('alert')).toContainText('Не удалось загрузить данные');
  await expect(page.locator('.af-program-card')).toHaveCount(0);
});

for (const width of [390, 768, 1024, 1280, 1440]) {
  for (const [name, path] of [['universities', '/universities'], ['university', university], ['programs', '/programs'], ['program', program]]) {
    test(`catalog screenshot ${name} ${width}`, async ({ page }, info) => {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(path);
      await expect(page.locator('.af-program-card, .af-catalog-detail h1').first()).toBeVisible();
      await expect(page.getByRole('status')).toHaveCount(0);
      await page.evaluate(() => document.fonts.ready);
      expect(await page.evaluate(() => Math.max(0, document.documentElement.scrollWidth - innerWidth))).toBe(0);
      const directory = resolve(evidenceDirectory, String(width));
      await mkdir(directory, { recursive: true });
      const actual = await page.screenshot({ path: resolve(directory, `${name}.png`), fullPage: true, animations: 'disabled' });
      if (process.env.QA_BASELINE_REF) {
        const reference = execFileSync('git', ['cat-file', 'blob', `${process.env.QA_BASELINE_REF}:docs/evidence/catalog-vertical-slice/${width}/${name}.png`]);
        const snapshot = `catalog-${width}-${name}.png`;
        const baseline = info.snapshotPath(snapshot);
        await mkdir(resolve(baseline, '..'), { recursive: true });
        await writeFile(baseline, reference);
        expect(actual).toMatchSnapshot(snapshot, { threshold: 0, maxDiffPixels: 0 });
        const metrics = resolve('test-results/catalog-metrics');
        await mkdir(metrics, { recursive: true });
        await writeFile(resolve(metrics, `${width}-${name}.json`), JSON.stringify({ name, width, baselineRef: process.env.QA_BASELINE_REF, pixelDiff: 0 }));
      }
    });
  }
}

test('accreditation register: active status, source date and register-only organisations', async ({ page, request }) => {
  await page.goto('/universities/sgu-saratov');
  const block = page.locator('.af-accreditation');
  await expect(block).toContainText('Государственная аккредитация');
  await expect(block.locator('.af-info-row').filter({ hasText: 'Статус в реестре' })).toContainText('Действует');
  await expect(block.locator('a')).toHaveAttribute('href', 'https://isga.obrnadzor.gov.ru/accredreestr/opendata/');
  await expect(block).toContainText('10.11.2026');
  const found = await (await request.get('/api/v1/catalog/universities?q=СКОЛКОВО')).json();
  const only = found.items.find((item: { provenance: { kind: string } }) => item.provenance.kind === 'accreditation');
  expect(only).toBeTruthy();
  await page.goto(`/universities/${only.id}`);
  await expect(page.locator('.af-catalog-source').first()).toContainText('Реестр аккредитации Рособрнадзора');
  await expect(page.locator('.af-accreditation .af-info-row').filter({ hasText: 'ОГРН' })).toContainText(only.accreditation.ogrn);
  await expect(page.locator('.af-program-card')).toHaveCount(0);
});
