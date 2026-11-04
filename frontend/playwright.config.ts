import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.E2E_BASE_URL ?? 'http://127.0.0.1:5173';
const serverMode = process.env.E2E_SERVER ?? 'dev';
if (!['dev', 'preview', 'external'].includes(serverMode)) {
  throw new Error('E2E_SERVER must be dev, preview or external');
}

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  workers: process.env.CI ? 2 : 1,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL,
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'mobile-chromium', use: { ...devices['Pixel 7'] } },
    { name: 'mobile-webkit', use: { ...devices['iPhone 14'] } },
  ],
  webServer: serverMode === 'external' ? undefined : {
    command: serverMode === 'preview'
      ? `npm run build && npm run preview -- --port ${new URL(baseURL).port || '5173'}`
      : `npm run dev -- --port ${new URL(baseURL).port || '5173'}`,
    url: baseURL,
    reuseExistingServer: serverMode === 'dev' && !process.env.CI,
  },
});
