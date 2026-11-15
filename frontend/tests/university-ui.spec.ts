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

for (const width of widths) test(`real university cards preserve sourced API data with three-line titles and align at ${width}px`, async ({ page }, info) => {
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
        await expect(heading).toHaveText(item.displayName ?? item.legalName);
        await expect(heading.locator('a')).toHaveAttribute('title', item.legalName);
        const titleSize = await heading.locator('a').evaluate(node => ({ height: node.getBoundingClientRect().height, line: parseFloat(getComputedStyle(node).lineHeight) }));
        expect(titleSize.height).toBeLessThanOrEqual(titleSize.line * 3 + 1);
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

for (const width of [390, 1440]) for (const [id, kind] of [
    ['miccedu-1593', 'official'], ['miccedu-101', 'normalized'], ['miccedu-10006765', 'original'], ['miccedu-140143824', 'official'],
] as const) test(`sourced ${id} title, branch facts and complete detail at ${width}px`, async ({ page, request }, info) => {
    await page.setViewportSize({ width, height: 900 });
    const data = await (await request.get(`/api/v1/catalog/universities/${id}`)).json() as UniversityResults['items'][number];
    expect(data.displayNameSource?.kind).toBe(kind);
    await page.goto(`/universities?q=${id}`);
    const card = page.locator('.af-university-card').filter({ has: page.locator(`h3 a[href="/universities/${id}"]`) });
    await expect(card).toHaveCount(1);
    await expect(card.locator('h3')).toHaveText(data.displayName!);
    await expect(card.locator('h3 a')).toHaveAttribute('title', data.legalName);
    if (data.isBranch) {
        const description = card.locator('.af-program-card__main > p');
        if (data.branchInfo) {
            await expect(description).toContainText(data.branchInfo.parentUniversityName!);
            await expect(description).toContainText(data.branchInfo.city!);
        } else await expect(description).toHaveText('Филиал');
    }
    const size = await card.locator('h3 a').evaluate(node => ({ height: node.getBoundingClientRect().height, line: parseFloat(getComputedStyle(node).lineHeight) }));
    expect(size.height).toBeLessThanOrEqual(size.line * 3 + 1);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await card.getByRole('link', { name: 'Университет ↗', exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`/universities/${id}$`));
    await expect(page.locator('.af-profile-hero h1')).toHaveText(data.displayName!);
    await expect(page.locator('.af-profile-hero p').first()).toHaveText(data.legalName);
    const source = page.locator('.af-university-name-source a');
    await expect(source).toHaveAttribute('href', data.displayNameSource!.url);
    if (data.branchInfo) await expect(page.getByRole('link', { name: 'Сведения о филиале ↗' })).toHaveAttribute('href', data.branchInfo.url);
    const full = page.locator('.af-profile-hero p').first();
    expect(await full.evaluate(node => node.scrollHeight <= node.clientHeight + 1)).toBe(true);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await info.attach(`${id}-${width}`, { body: await page.screenshot({ fullPage: true, animations: 'disabled' }), contentType: 'image/png' });
});

test('older API without name projection safely falls back to the complete legal name', async ({ page }) => {
    let fullName = '';
    await page.route('**/api/v1/catalog/universities?**', async route => {
        const response = await route.fetch(), body = await response.json();
        for (const item of body.items) {
            fullName = item.legalName;
            for (const field of ['displayName', 'displayNameSource', 'nameAliases', 'branchInfo']) delete item[field];
        }
        await route.fulfill({ response, json: body });
    });
    await page.goto('/universities?q=miccedu-1593');
    await expect.poll(() => fullName).not.toBe('');
    await expect(page.locator('.af-university-card h3')).toHaveText(fullName);
    await expect(page.getByRole('alert')).toHaveCount(0);
});

for (const [name, damage] of [
    ['missing source', (p: Record<string, unknown>) => { p.displayNameSource = null; }],
    ['invalid checksum', (p: Record<string, unknown>) => { (p.displayNameSource as Record<string, unknown>).sha256 = 'wrong'; }],
    ['false original', (p: Record<string, unknown>) => { (p.displayNameSource as Record<string, unknown>).kind = 'original'; }],
    ['normalization without rule', (p: Record<string, unknown>) => { Object.assign(p.displayNameSource!, { kind: 'normalized', ruleVersion: null }); }],
    ['branch facts on head', (p: Record<string, unknown>) => { p.branchInfo = { parentUniversityName: 'invalid', city: null, ...(p.displayNameSource as object) }; }],
] as const) test(`invalid naming DTO is an error: ${name}`, async ({ page }) => {
    await page.route('**/api/v1/catalog/universities?**', async route => {
        const response = await route.fetch(), body = await response.json();
        damage(body.items[0]);
        await route.fulfill({ response, json: body });
    });
    await page.goto('/universities?q=miccedu-1593');
    await expect(page.getByRole('alert')).toContainText('Не удалось загрузить данные');
    await expect(page.locator('.af-university-card')).toHaveCount(0);
});
