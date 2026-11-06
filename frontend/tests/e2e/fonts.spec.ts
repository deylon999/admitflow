import { expect, test } from '@playwright/test';

test('Inter and JetBrains Mono load Latin/Cyrillic locally with external requests blocked', async ({
  page,
  baseURL,
}) => {
  const external: string[] = [];
  await page.route('**/*', (route) => {
    if (new URL(route.request().url()).origin !== new URL(baseURL!).origin) {
      external.push(new URL(route.request().url()).hostname);
      return route.abort();
    }
    return route.continue();
  });
  await page.goto('/');
  const fonts = await page.evaluate(async () => {
    await document.fonts.ready;
    return Promise.all(
      ['Inter', 'JetBrains Mono'].map(async (family) => {
        const faces = await document.fonts.load(`600 16px "${family}"`, 'ABC абв');
        return {
          family,
          statuses: faces.map((face) => face.status),
          checked: document.fonts.check(`600 16px "${family}"`, 'ABC абв'),
        };
      }),
    );
  });
  for (const value of fonts) {
    expect(value.checked).toBe(true);
    expect(value.statuses.length).toBeGreaterThanOrEqual(2);
    expect(value.statuses.every((status) => status === 'loaded')).toBe(true);
  }
  expect(external).toEqual([]);
  const manifest = await (await page.request.get('/fonts/manifest.json')).json();
  for (const file of manifest.files)
    expect((await page.request.get('/fonts/' + file.path)).status()).toBe(200);
  expect((await page.request.get('/fonts/inter/OFL.txt')).status()).toBe(200);
  expect((await page.request.get('/fonts/jetbrains-mono/OFL.txt')).status()).toBe(200);
});
