import type { Page } from '@playwright/test';

export async function openTrackerPanel(
  page: Page,
  panel:
    | 'export'
    | 'access'
    | 'filters'
    | 'archive'
    | 'archive-history'
    | 'archive-facts'
    | 'sources'
    | 'changes',
) {
  const labels = {
    export: 'Скачать данные и распечатать',
    access: 'Доступ и удаление данных',
    filters: 'Поиск и фильтры',
    archive: 'Инструменты архива',
    'archive-history': 'Расчёт и история архива',
    'archive-facts': 'Данные списка и источник',
    sources: 'Источники и охват вузов',
    changes: 'Изменения сохранённых списков',
  };
  const summaries = page.locator('summary').filter({ hasText: labels[panel] });
  await summaries.first().waitFor({ state: 'visible' });
  for (const summary of await summaries.all()) {
    if (
      !(await summary.evaluate((element) => (element.parentElement as HTMLDetailsElement).open))
    ) {
      await summary.click();
    }
  }
}
