import type { Page } from '@playwright/test';

// The only deliberate differences outside the catalog are visible demo labels.
// Normalize these four exact strings in the reference DOM before rendering a
// second baseline. No geometry, CSS, values or other content is normalized.
export async function labelReferenceDemos(page: Page) {
  return page.evaluate(() => {
    const changes: string[] = [];
    const replacements = [
      ['.forecast-heading div > span', 'МГУ · Прикладная математика', 'МГУ · Прикладная математика · демо'],
      ['.calc-caption', 'Ваш шанс поступить', 'Ваш шанс поступить · демо'],
      ['.af-program-card__stats > span', 'ОЦЕНКА ШАНСОВ', 'ШАНСЫ · ДЕМО'],
      ['.af-page-heading .af-eyebrow', 'РЕЗУЛЬТАТ ПРОГНОЗА', 'РЕЗУЛЬТАТ ПРОГНОЗА · ДЕМО'],
    ];
    for (const [selector, before, after] of replacements) {
      for (const element of document.querySelectorAll(selector)) {
        if (element.textContent === before) { element.textContent = after; changes.push(selector); }
      }
    }
    return changes;
  });
}
