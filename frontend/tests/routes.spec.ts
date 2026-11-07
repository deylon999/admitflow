import { test, expect } from '@playwright/test';
import { routes } from './routes';

test('the source inventory contains exactly 29 unique routes',()=>{
  expect(routes).toHaveLength(29);expect(new Set(routes).size).toBe(29);
});
const runtimeRoutes=routes.map(route=>route==='/universities/mtuci'?'/universities/sgu-saratov':route==='/programs/mtuci-se'?'/programs/sgu-2026-4588':route);
for(const route of runtimeRoutes)test(`route ${route}: React loads with the appropriate data boundary`,async({page})=>{
  const errors:string[]=[],backend:string[]=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
  page.on('request',request=>{if(new URL(request.url()).pathname.startsWith('/api/'))backend.push(request.url());});
  const response=await page.goto(route);expect(response?.status()).toBe(200);
  await expect(page.locator('#root h1, #root h2').first()).toBeVisible();
  await expect(page.locator('#root')).not.toBeEmpty();
  if(route.startsWith('/universities')||route.startsWith('/programs')) await expect(page.locator('.af-program-card, .af-catalog-detail h1').first()).toBeVisible();
  expect(errors).toEqual([]);if(!route.startsWith('/universities')&&!route.startsWith('/programs'))expect(backend).toEqual([]);else expect(backend.length).toBeGreaterThan(0);
});
