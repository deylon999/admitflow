import { expect, test } from '@playwright/test';

test.beforeEach(() => test.skip(process.env.E2E_NGINX !== '1', 'Requires the actual nginx image'));

test('missing build resources return404 without the SPA document', async ({ request }) => {
  for (const path of ['/assets/missing-build-chunk.js', '/assets/missing-build-style.css']) {
    const response = await request.get(path);
    expect(response.status()).toBe(404);
    expect(await response.text()).not.toContain('<div id="root">');
    expect(response.headers()['cache-control'] ?? '').not.toContain('immutable');
    expect(response.headers()['x-content-type-options']).toBe('nosniff');
  }
});

test('HTML revalidates, hashed JS and CSS cache immutably, API stays private', async ({ request }) => {
  for (const path of ['/', '/index.html', '/tracker', '/unknown-deep-link']) {
    const response = await request.get(path);
    expect(response.status()).toBe(200);
    expect(response.headers()['cache-control']).toBe('no-cache');
    expect(await response.text()).toContain('<div id="root">');
  }
  const html = await (await request.get('/')).text();
  const assets = [...html.matchAll(/(?:src|href)="(\/assets\/[^" ]+\.(?:js|css))"/g)].map(match => match[1]);
  expect(assets.some(path => path.endsWith('.js'))).toBe(true);
  expect(assets.some(path => path.endsWith('.css'))).toBe(true);
  for (const path of assets) {
    const response = await request.get(path);
    expect(response.status()).toBe(200);
    expect(response.headers()['cache-control']).toBe('public, max-age=31536000, immutable');
    expect(response.headers()['x-content-type-options']).toBe('nosniff');
    expect(response.headers()['content-type']).toMatch(path.endsWith('.js') ? /javascript/ : /text\/css/);
    expect(await response.text()).not.toContain('<div id="root">');
  }
  const health = await request.get('/api/health');
  expect(health.status()).toBe(200);
  expect(health.headers()['cache-control']).toBe('no-store');
});
