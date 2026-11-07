import { test, expect } from '@playwright/test';

test('landing keeps exact heading, forecast values, calculator, tabs and FAQ',async({page})=>{
  await page.goto('/');
  await expect(page.locator('.hero h1')).toHaveText('Оцени шансына поступлениес точнымпрогнозом');
  await expect(page.locator('.chance-metric strong')).toHaveText('74%');
  await page.getByRole('button',{name:'Рассчитать прогноз',exact:false}).click();
  await expect(page.locator('.calc-message')).toContainText('Пример результата: 74%');
  await page.locator('.competitors-tabs').getByRole('button',{name:'Динамика',exact:true}).click();
  await expect(page.locator('.tab-placeholder')).toContainText('Позиция обновляется');
  const faq=page.locator('.faq-item').nth(1).getByRole('button');await faq.click();await expect(faq).toHaveAttribute('aria-expanded','true');await faq.click();await expect(faq).toHaveAttribute('aria-expanded','false');
});

test('tracking toggles persist in localStorage across page transitions and reload',async({page})=>{
  await page.goto('/app/watchlist');await expect(page.locator('.af-program-card')).toHaveCount(3);
  await page.locator('.af-track-button').first().click();await expect(page.locator('.af-program-card')).toHaveCount(2);await page.reload();await expect(page.locator('.af-program-card')).toHaveCount(2);
  await page.goto('/app/watchlist/add');await page.getByPlaceholder('МТУСИ, программная инженерия...').fill('МТУСИ');await page.getByRole('button',{name:'+ Следить',exact:true}).click();
  await page.locator('.af-sidebar').getByRole('link',{name:'Мои направления',exact:false}).click();await expect(page.locator('.af-program-card')).toHaveCount(3);
});

test('exam scores update sum and result navigation works',async({page})=>{
  await page.goto('/app/forecast');await page.getByLabel('Профильная математика',{exact:true}).fill('80');await expect(page.locator('.af-form-footer')).toContainText('267');
  await page.getByRole('link',{name:'Посмотреть прогноз',exact:false}).click();await expect(page).toHaveURL(/\/app\/forecast\/example$/);await expect(page.locator('.af-spotlight')).toContainText('74%');
});

test('competition table search and original tabs filter participants',async({page})=>{
  await page.goto('/app/competitions/mtuci-se');await expect(page.locator('tbody tr')).toHaveCount(13);
  await page.getByRole('button',{name:'Ваше заявление',exact:true}).click();await expect(page.locator('tbody tr')).toHaveCount(1);await expect(page.locator('tbody')).toContainText('ВЫ');
  await page.getByRole('button',{name:'Все',exact:true}).click();await page.getByLabel('Поиск кода абитуриента').fill('no-match');await expect(page.locator('tbody tr')).toHaveCount(0);
});

test('comparison permits four choices and exposes the original empty state',async({page})=>{
  await page.goto('/app/compare');const choices=page.locator('.af-choice-row input');
  await choices.nth(3).check();await choices.nth(4).click();await expect(page.locator('.af-compare-col')).toHaveCount(4);await expect(choices.nth(4)).not.toBeChecked();
  for(const input of await choices.all())if(await input.isChecked())await input.uncheck();await expect(page.locator('.af-empty')).toContainText('Выбери направления');
});

test('exam analytics switches subject without inventing new behavior',async({page})=>{
  await page.goto('/ege-analytics');const before=await page.locator('.af-distribution-layout').innerHTML();
  await page.getByRole('button',{name:'Математика',exact:true}).click();await expect(page.getByRole('button',{name:'Математика',exact:true})).toHaveClass(/is-active/);expect(await page.locator('.af-distribution-layout').innerHTML()).not.toBe(before);
});

test('profile form, theme selector, checkbox and confirmation preserve source interactions',async({page})=>{
  await page.goto('/app/profile');await page.getByLabel('ИМЯ',{exact:true}).fill('Тест');await page.getByRole('button',{name:'Сохранить изменения',exact:true}).click();await expect(page.locator('.af-inline-success')).toHaveText('Настройки изменены.');
  await page.goto('/app/settings');await page.locator('.af-field select').selectOption('Тёмная');await expect(page.locator('.af-field select')).toHaveValue('Тёмная');
  await page.locator('.af-check input').uncheck();await expect(page.locator('.af-check input')).not.toBeChecked();await page.getByRole('button',{name:'Очистить мои данные',exact:true}).click();await expect(page.getByRole('dialog')).toBeVisible();await page.getByRole('button',{name:'Отмена',exact:true}).click();await expect(page.getByRole('dialog')).toHaveCount(0);
});

for(const mode of ['login','register','recovery'])test(`auth ${mode}: original form shows its client-only response`,async({page})=>{
  await page.goto(`/auth/${mode}`);await page.getByLabel('EMAIL',{exact:true}).fill('test@example.org');for(const field of await page.locator('input[type=password]').all())await field.fill('password123');await page.locator('button[type=submit]').click();await expect(page.locator('.af-inline-success')).toContainText('вход пока не подключён');
});

test('SPA links, back/forward and source mobile navigation work',async({page})=>{
  await page.goto('/');await page.locator('.header-actions .button-primary').click();await expect(page).toHaveURL(/\/app\/forecast$/);await page.goBack();await expect(page.locator('.hero h1')).toBeVisible();await page.goForward();await expect(page.locator('.af-page-heading h1')).toContainText('Рассчитай прогноз');
  await page.setViewportSize({width:390,height:844});await expect(page.locator('.af-mobile-nav')).toBeVisible();await page.locator('.af-mobile-nav a[href="/universities"]').click();await expect(page).toHaveURL(/\/universities$/);
});
