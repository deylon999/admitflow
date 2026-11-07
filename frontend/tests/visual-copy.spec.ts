import { test, expect } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { routes, widths, slug } from './routes';

for(const width of widths)for(const route of routes)test(`exact ${width} ${route}`,async({browser},info)=>{
  const context=await browser.newContext({viewport:{width,height:900},deviceScaleFactor:1,locale:'ru-RU',timezoneId:'Europe/Moscow',colorScheme:'light',reducedMotion:'reduce'});
  try {
    const original=await context.newPage(),copy=await context.newPage();
    const errors:string[]=[];
    for(const page of [original,copy]) {page.on('pageerror',error=>errors.push(error.message));page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});}
    await original.goto((process.env.REFERENCE_URL ?? 'http://127.0.0.1:5300')+route);
    await copy.goto((process.env.COPY_URL ?? 'http://127.0.0.1:5301')+route);
    for(const page of [original,copy]) {await page.locator('#root h1, #root h2').first().waitFor();await page.evaluate(()=>document.fonts.ready);}
    const options={fullPage:true,animations:'disabled' as const,caret:'hide' as const};
    const reference=await original.screenshot(options),actual=await copy.screenshot(options);
    const snapshotName=`${width}-${slug(route)}.png`;
    const baseline=info.snapshotPath(snapshotName);
    await mkdir(resolve(baseline,'..'),{recursive:true});await writeFile(baseline,reference);
    expect(actual).toMatchSnapshot(snapshotName,{threshold:0,maxDiffPixels:0});
    const originalText=await original.locator('#root').innerText(),copyText=await copy.locator('#root').innerText();
    expect(copyText).toBe(originalText);
    const overflow=await copy.evaluate(()=>Math.max(0,document.documentElement.scrollWidth-innerWidth));
    const referenceOverflow=await original.evaluate(()=>Math.max(0,document.documentElement.scrollWidth-innerWidth));
    expect(overflow).toBe(referenceOverflow);expect(overflow).toBe(0);expect(errors).toEqual([]);
    const directory=resolve('../docs/evidence/frontend-v3-exact',String(width));
    await mkdir(directory,{recursive:true});
    await writeFile(resolve(directory,`${slug(route)}-original.png`),reference);
    await writeFile(resolve(directory,`${slug(route)}-copy.png`),actual);
    const metrics=resolve('test-results/exact-metrics');await mkdir(metrics,{recursive:true});
    await writeFile(resolve(metrics,`${width}-${slug(route)}.json`),JSON.stringify({route,width,pixelDiff:0,threshold:0,textEqual:true,overflow,referenceOverflow,originalSHA256:createHash('sha256').update(reference).digest('hex'),copySHA256:createHash('sha256').update(actual).digest('hex')},null,2));
  } finally {await context.close();}
});
