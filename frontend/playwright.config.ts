import { defineConfig } from '@playwright/test';

const live = process.env.COMPARE_REFERENCE === '1';
export default defineConfig({
  testDir: './tests',
  testMatch: live ? '**/*.spec.ts' : ['**/routes.spec.ts','**/interactions.spec.ts'],
  fullyParallel: true,
  workers: 2,
  retries: 0,
  timeout: 30_000,
  reporter: [['line'], ['json',{outputFile:'test-results/results.json'}]],
  expect: {toMatchSnapshot: {threshold:0,maxDiffPixels:0}},
  use: {baseURL:process.env.COPY_URL ?? 'http://127.0.0.1:5301',browserName:'chromium',deviceScaleFactor:1,locale:'ru-RU',timezoneId:'Europe/Moscow',colorScheme:'light',reducedMotion:'reduce',trace:'retain-on-failure'},
  webServer: process.env.QA_EXTERNAL_SERVERS === '1' ? undefined : [
    {command:'npm run build && npm run preview -- --host 127.0.0.1 --port 5301 --strictPort',url:'http://127.0.0.1:5301',reuseExistingServer:false,timeout:60_000},
    ...(live ? [{command:'node node_modules/vite/bin/vite.js build --config reference.vite.config.mjs --configLoader native && node node_modules/vite/bin/vite.js preview --config reference.vite.config.mjs --configLoader native',url:'http://127.0.0.1:5300',reuseExistingServer:false,timeout:60_000}] : []),
  ],
});
