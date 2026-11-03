import { expect, test } from '@playwright/test';
for(const theme of ['light','dark'])test(`archive keyboard save/cancel/delete and text contrast ${theme}`,async({page})=>{
  test.skip(process.env.E2E_SOURCE_FIXTURE!=='1','Requires anonymized archive API');
  await page.addInitScript(value=>localStorage.setItem('abiturient-theme',value),theme);
  await page.setViewportSize({width:320,height:1100});await page.goto('/sources');
  const find=page.getByRole('button',{name:'Найти свою запись',exact:true});await find.focus();await page.keyboard.press('Enter');
  await expect(page.getByLabel('Код поступающего')).toBeFocused();await page.keyboard.type('FIXTURE-000001');await page.keyboard.press('Enter');
  await expect(page.getByRole('heading',{name:'Проверьте выбранную запись'})).toBeFocused();
  await page.getByLabel('Подтверждаю: выбраны нужные мне группа и запись').focus();await page.keyboard.press('Space');await page.keyboard.press('Tab');
  await expect(page.getByRole('button',{name:'Сохранить эту запись'})).toBeFocused();await page.keyboard.press('Enter');
  const saved=page.getByRole('link',{name:/Открыть мои направления/});await expect(saved).toBeFocused();await page.keyboard.press('Enter');
  await expect(page.getByRole('heading',{name:'Мои направления',exact:true})).toBeFocused();
  const remove=page.getByRole('button',{name:'Удалить архивную запись',exact:true});await remove.focus();await page.keyboard.press('Enter');
  await expect(page.getByRole('button',{name:'Отмена',exact:true})).toBeFocused();await page.keyboard.press('Escape');await expect(remove).toBeFocused();
  const ratios=await page.evaluate(()=>{
    const style=getComputedStyle(document.documentElement);
    const luminance=(name:string)=>{const hex=style.getPropertyValue(name).trim().slice(1);const full=hex.length===3?Array.from(hex,v=>v+v).join(''):hex;
      const rgb=[0,2,4].map(i=>parseInt(full.slice(i,i+2),16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);
      return .2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2];};
    return [['--text','--bg'],['--text','--surface'],['--muted','--bg'],['--muted','--surface'],['--primary','--surface'],['--cta-text','--primary'],['--error','--error-bg'],['--tag-text','--tag-bg']].map(([fg,bg])=>{const a=luminance(fg),b=luminance(bg);return{pair:`${fg}/${bg}`,ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)};});
  });
  for(const item of ratios)expect(item.ratio,item.pair).toBeGreaterThanOrEqual(4.5);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.keyboard.press('Enter');await expect(page.getByRole('button',{name:'Отмена',exact:true})).toBeFocused();await page.keyboard.press('Tab');
  await expect(page.getByRole('button',{name:'Да, удалить архивную запись',exact:true})).toBeFocused();await page.keyboard.press('Enter');
  await expect(page.locator('.archive-direction-card')).toHaveCount(0);
  await expect(page.getByRole('heading',{name:'Мои направления',exact:true})).toBeFocused();
});
