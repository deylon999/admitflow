import { expect, test, type Page } from '@playwright/test';
import type { UniversityResults } from '../src/catalog/types';

const widths = [320, 375, 390, 768, 1024, 1440, 1920];
async function universities(page: Page) {
    const response = page.waitForResponse(r => r.url().includes('/api/v1/catalog/universities?') && r.status() === 200);
    await page.goto('/universities');
    const data = await (await response).json() as UniversityResults;
    await expect(page.locator('.af-university-card')).toHaveCount(data.items.length);
    return data;
}

for (const width of widths) test(`real university cards preserve full API data and align at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 900 });
    const data = await universities(page);
    const catalog = page.locator('.af-university-catalog');
    await expect(catalog.getByRole('heading', { name: 'Университеты по твоему запросу', exact: true })).toBeVisible();
    await expect(catalog.locator('.af-university-count')).toHaveText(`${data.total} вузов`);
    await expect(catalog.getByRole('link', { name: /Посмотреть демо интерфейса|Реальный каталог/ })).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const columns = await catalog.locator('.af-university-grid').evaluate(node => getComputedStyle(node).gridTemplateColumns.split(' ').length);
    expect(columns).toBe(width > 930 ? 2 : 1);
    // The reviewed real API fixture contains both short and long legal names.
    expect(Math.min(...data.items.map(item => item.name.length))).toBeLessThan(50);
    expect(Math.max(...data.items.map(item => item.name.length))).toBeGreaterThan(150);
    const geometry: { top: number; height: number; linkTop: number; titleTop: number; infoTop: number }[] = [];
    for (const [index, item] of data.items.entries()) {
        const card = catalog.locator('.af-university-card').nth(index);
        const heading = card.locator('h3');
        await expect(heading).toHaveText(item.name);
        await expect(card.locator('.af-program-card__university')).toContainText(item.region);
        await expect(card.locator('.af-program-card__stats strong')).toHaveText(item.provenance.kind === 'accreditation' ? 'Реестр' : String(item.provenance.edition));
        expect(await card.locator('.af-program-card__stats strong').evaluate(node => node.scrollWidth <= node.clientWidth + 1)).toBe(true);
        await expect(card.locator('.af-program-card__stats small')).toHaveText(item.accreditation ? 'Аккредитация действует' : 'Мониторинг');
        expect(await heading.evaluate(node => node.scrollHeight <= node.clientHeight + 1)).toBe(true);
        const link = card.getByRole('link', { name: 'Университет ↗', exact: true });
        await expect(link).toHaveAttribute('href', `/universities/${encodeURIComponent(item.id)}`);
        const bounds = await card.boundingBox(), action = await link.boundingBox();
        expect(bounds!.x).toBeGreaterThanOrEqual(0);
        expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(width);
        expect(action!.height).toBeGreaterThanOrEqual(44);
        geometry.push({ top: bounds!.y, height: bounds!.height, linkTop: action!.y, titleTop: (await heading.boundingBox())!.y, infoTop: (await card.locator('.af-program-card__main > p').boundingBox())!.y });
    }
    if (columns === 2) for (let i = 0; i + 1 < geometry.length; i += 2) {
        expect(Math.abs(geometry[i].top - geometry[i + 1].top)).toBeLessThan(1);
        expect(Math.abs(geometry[i].height - geometry[i + 1].height)).toBeLessThan(1);
        expect(Math.abs(geometry[i].linkTop - geometry[i + 1].linkTop)).toBeLessThan(1);
        expect(Math.abs(geometry[i].titleTop - geometry[i + 1].titleTop)).toBeLessThan(1);
        expect(Math.abs(geometry[i].infoTop - geometry[i + 1].infoTop)).toBeLessThan(1);
    }
    await page.evaluate(() => document.fonts.ready);
    const screenshot = info.outputPath(`universities-${width}.png`);
    await page.screenshot({ path: screenshot, fullPage: true, animations: 'disabled' });
    await info.attach(`universities-${width}`, { path: screenshot, contentType: 'image/png' });
});

test('university empty results and pagination still use the real API', async ({ page }) => {
    const first = await universities(page);
    await page.getByRole('button', { name: 'Далее', exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`offset=${first.nextOffset}`));
    await expect(page.locator('.af-university-card h3').first()).not.toHaveText(first.items[0].name);
    await page.locator('.af-search-panel input').fill('no-such-university-layout-check');
    await expect(page.locator('.af-empty')).toContainText('Ничего не нашлось');
    await expect(page.locator('.af-university-count')).toHaveText('0 вузов');
    await expect(page.locator('.af-university-card')).toHaveCount(0);
    await expect(page.getByRole('navigation', { name: 'Страницы каталога' })).toHaveCount(0);
});

for (const failure of ['503', 'network']) test(`university ${failure} error keeps retry and never shows fake cards`, async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 700 });
    await page.route('**/api/v1/catalog/universities?**', route => failure === 'network' ? route.abort('failed') : route.fulfill({ status: 503, json: {} }));
    await page.goto('/universities');
    await expect(page.getByRole('alert')).toContainText('Не удалось загрузить данные');
    await expect(page.locator('.af-university-card, .af-university-count')).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.unroute('**/api/v1/catalog/universities?**');
    await page.getByRole('button', { name: 'Повторить', exact: true }).click();
    await expect(page.locator('.af-university-card')).toHaveCount(12);
});

test('university loading does not invent a count; card links support keyboard and hover', async ({ page }) => {
    let release!: () => void;
    const gate = new Promise<void>(done => { release = done; });
    await page.route('**/api/v1/catalog/universities?**', async route => { await gate; await route.continue(); });
    await page.goto('/universities');
    await expect(page.getByRole('status')).toContainText('Загрузка данных');
    await expect(page.locator('.af-university-count')).toHaveCount(0);
    release();
    await expect(page.getByRole('status')).toHaveCount(0);
    const card = page.locator('.af-university-card').first();
    const title = card.locator('h3 a'), footer = card.getByRole('link', { name: 'Университет ↗', exact: true });
    await title.focus();
    await expect(title).toBeFocused();
    await page.keyboard.press('Tab');
    await expect(footer).toBeFocused();
    await expect(footer).toHaveCSS('outline-width', '3px');
    await footer.hover();
    await expect(footer).toHaveCSS('color', 'rgb(10, 53, 232)');
    const destination = await footer.getAttribute('href');
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(new RegExp(destination + '$'));
    await expect(page.locator('.af-catalog-detail h1')).toBeVisible();
});
