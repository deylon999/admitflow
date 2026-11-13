import { defineConfig } from '@playwright/test';

const auth = process.env.AUTH_BROWSER_E2E === '1';
const selectedBrowser = process.env.AUTH_TEST_BROWSER ?? 'chromium';
if (auth && !['chromium', 'firefox', 'webkit'].includes(selectedBrowser)) throw Error('Unsupported auth acceptance browser.');
const browserName = auth && selectedBrowser === 'firefox' ? 'firefox' : auth && selectedBrowser === 'webkit' ? 'webkit' : 'chromium';
const evidence = auth ? process.env.AUTH_TEST_RESULTS_DIR ?? `test-results/auth-${browserName}` : 'test-results';
const live = process.env.COMPARE_REFERENCE === '1';
export default defineConfig({
  testDir: './tests',
  outputDir: `${evidence}/playwright`,
  testMatch: auth ? '**/auth-live.spec.ts' : live ? '**/*.spec.ts' : ['**/routes.spec.ts','**/interactions.spec.ts','**/catalog.spec.ts','**/api.spec.ts','**/api-unit.spec.ts','**/auth-unit.spec.ts','**/auth.spec.ts'],
  testIgnore: auth ? [] : ['**/auth-live.spec.ts'],
  fullyParallel: !auth,
  forbidOnly: !!process.env.CI,
  workers: auth ? 1 : 2,
  retries: 0,
  timeout: 30_000,
  reporter: [['line'], ['json',{outputFile:`${evidence}/results.json`}], ['junit', {outputFile:`${evidence}/frontend.xml`}]],
  expect: {toMatchSnapshot: {threshold:0,maxDiffPixels:0}},
  use: {baseURL:process.env.COPY_URL ?? 'http://127.0.0.1:5301',browserName,deviceScaleFactor:1,locale:'ru-RU',timezoneId:'Europe/Moscow',colorScheme:'light',reducedMotion:'reduce',trace:'retain-on-failure',screenshot:'only-on-failure'},
  // npm test / npm run test:visual own the real API and preview servers in
  // scripts/test.mjs. Direct Playwright calls require already running previews.
});
