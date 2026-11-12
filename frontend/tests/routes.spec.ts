import { test, expect } from '@playwright/test';
import { routes } from './routes';

test('the source inventory contains exactly 29 unique routes',()=>{
  expect(routes).toHaveLength(29);expect(new Set(routes).size).toBe(29);
});
const runtimeRoutes=routes;
for(const route of runtimeRoutes)test(`route ${route}: React loads with the appropriate data boundary`,async({page})=>{
  const errors:string[]=[],backend:string[]=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('console',message=>{if(message.type()==='error' && !message.text().includes('Failed to load resource'))errors.push(message.text());});
  page.on('request',request=>{if(new URL(request.url()).pathname.startsWith('/api/'))backend.push(request.url());});
  const response=await page.goto(route);expect(response?.status()).toBe(200);
  await expect(page.locator('#root h1, #root h2').first()).toBeVisible();
  await expect(page.locator('#root')).not.toBeEmpty();
  if(route.startsWith('/universities')||route.startsWith('/programs')) await expect(page.locator('.af-program-card, .af-catalog-detail h1').first()).toBeVisible();
  expect(errors).toEqual([]);if(route.startsWith('/universities')||route.startsWith('/programs')||['/app','/app/watchlist','/app/watchlist/add','/app/history','/app/notifications','/app/sources','/app/competitions/mtuci-se'].includes(route))expect(backend.length).toBeGreaterThan(0);else expect(backend).toEqual([]);
  await page.reload();
  await expect(page.locator('#root h1, #root h2').first()).toBeVisible();
  await page.evaluate(() => {
    const link = document.createElement('a'); link.href = '/not-found?from=route-smoke'; link.textContent = 'Route smoke link'; link.style.cssText = 'position:fixed;top:0;left:0;z-index:10000'; document.body.append(link);
  });
  await page.getByRole('link', { name: 'Route smoke link', exact: true }).click();
  await expect(page).toHaveURL(/\/not-found\?from=route-smoke$/);
  await expect(page.getByRole('heading', { name: 'Такой страницы нет' })).toBeVisible();
  await page.goBack();
  await expect(page).toHaveURL(new RegExp(route.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '$'));
  await expect(page.locator('#root h1, #root h2').first()).toBeVisible();
  await page.goForward();
  await expect(page.getByRole('heading', { name: 'Такой страницы нет' })).toBeVisible();
  expect(errors).toEqual([]);
});

for (const route of ['/auth/missing?mode=demo', '/auth/nested/register', '/application', '/app/competitions/%E0%A4%A', '/app/competitions/bad%2Fid', '/app/competitions/%/competitors', '/app/watchlist/%', '/universities/%', '/programs/bad%3Fid']) {
  test(`unknown or malformed route is a 404 boundary: ${route}`, async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    // Vite preview rejects malformed percent encodings before serving the SPA.
    // Exercise those URLs through the actual client router; production HTTP
    // rejection is checked separately against nginx/PostgreSQL.
    let malformed = false;
    try { decodeURIComponent(route); } catch { malformed = true; }
    if (malformed) {
      await page.goto('/faq');
      await page.evaluate(href => {
        const link = document.createElement('a'); link.href = href; link.textContent = 'Malformed route'; link.style.cssText = 'position:fixed;top:0;left:0;z-index:10000'; document.body.append(link);
      }, route);
      await page.getByRole('link', { name: 'Malformed route' }).click();
    } else await page.goto(route);
    await expect(page.getByRole('heading', { name: /Такой страницы нет|Страница не найдена/ })).toBeVisible();
    await expect(page.locator('form')).toHaveCount(0);
    expect(errors).toEqual([]);
  });
}

test('encoded public IDs decode exactly once and unknown live IDs never show demo records', async ({ page }) => {
  await page.goto('/universities/%73gu-saratov');
  await expect(page.locator('.af-profile-hero')).toContainText('СГУ имени');
  await page.goto('/programs/%73gu-2026-4588');
  await expect(page.locator('h1')).toContainText('Программная инженерия');
  await page.goto('/app/competitions/does-not-exist?mode=demo');
  await expect(page.getByRole('heading', { name: 'Запись не найдена' })).toBeVisible();
  await expect(page.locator('tbody tr')).toHaveCount(0);
});

test('query plus hash links preserve history and prevented/download/target links stay native', async ({ page }) => {
  await page.goto('/faq?from=first');
  await page.evaluate(() => {
    const target = document.createElement('div'); target.id = 'test-section'; document.body.append(target);
    const link = document.createElement('a'); link.href = '/faq?from=second#test-section'; link.textContent = 'Query hash'; link.style.cssText = 'position:fixed;top:0;left:0;z-index:10000'; document.body.append(link);
  });
  await page.getByRole('link', { name: 'Query hash' }).click();
  await expect(page).toHaveURL(/\/faq\?from=second#test-section$/);
  await page.goBack(); await expect(page).toHaveURL(/\/faq\?from=first$/);
  await page.goForward(); await expect(page).toHaveURL(/\/faq\?from=second#test-section$/);
  const intercepted = await page.evaluate(() => {
    return ['prevented', 'download', 'target', 'foreign-origin'].map(kind => {
      const link = document.createElement('a');
      const foreign = new URL(location.href); foreign.hostname += '.example.invalid';
      link.href = kind === 'foreign-origin' ? foreign.origin + '/native' : '/faq?native';
      if (kind === 'download') link.setAttribute('download', '');
      if (kind === 'target') link.target = 'named-window';
      if (kind === 'prevented') link.addEventListener('click', event => event.preventDefault());
      document.body.append(link);
      let prevented = false;
      window.addEventListener('click', event => { prevented = event.defaultPrevented; event.preventDefault(); }, { once: true });
      link.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true })); link.remove();
      return prevented;
    });
  });
  expect(intercepted).toEqual([true, false, false, false]);
  await expect(page).toHaveURL(/\/faq\?from=second#test-section$/);
});
