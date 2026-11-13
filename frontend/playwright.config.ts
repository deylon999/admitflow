import { defineConfig } from '@playwright/test';

const auth = process.env.AUTH_BROWSER_E2E === '1';
const live = process.env.COMPARE_REFERENCE === '1';
export default defineConfig({
  testDir: './tests',
  outputDir: './test-results/playwright',
  testMatch: auth ? '**/auth-live.spec.ts' : live ? '**/*.spec.ts' : ['**/routes.spec.ts','**/interactions.spec.ts','**/catalog.spec.ts','**/api.spec.ts','**/api-unit.spec.ts','**/auth-unit.spec.ts','**/auth.spec.ts'],
  testIgnore: auth ? [] : ['**/auth-live.spec.ts'],
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  workers: 2,
  retries: 0,
  timeout: 30_000,
  reporter: [['line'], ['json',{outputFile:'test-results/results.json'}], ['junit', {outputFile:'test-results/frontend.xml'}]],
  expect: {toMatchSnapshot: {threshold:0,maxDiffPixels:0}},
  use: {baseURL:process.env.COPY_URL ?? 'http://127.0.0.1:5301',browserName:'chromium',deviceScaleFactor:1,locale:'ru-RU',timezoneId:'Europe/Moscow',colorScheme:'light',reducedMotion:'reduce',trace:'retain-on-failure',screenshot:'only-on-failure'},
  // npm test / npm run test:visual own the real API and preview servers in
  // scripts/test.mjs. Direct Playwright calls require already running previews.
});
