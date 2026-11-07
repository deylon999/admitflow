import { test, expect } from '@playwright/test';
import { routes } from './routes';

test('the source inventory contains exactly 29 unique routes',()=>{
  expect(routes).toHaveLength(29);expect(new Set(routes).size).toBe(29);
});
for(const route of routes)test(`route ${route}: React loads and makes no backend requests`,async({page})=>{
  const errors:string[]=[],backend:string[]=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
  page.on('request',request=>{if(new URL(request.url()).pathname.startsWith('/api/'))backend.push(request.url());});
  const response=await page.goto(route);expect(response?.status()).toBe(200);
  await expect(page.locator('#root h1, #root h2').first()).toBeVisible();
  await expect(page.locator('#root')).not.toBeEmpty();
  expect(errors).toEqual([]);expect(backend).toEqual([]);
});
