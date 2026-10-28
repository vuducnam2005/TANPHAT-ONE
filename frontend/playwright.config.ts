import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  workers: 1,
  timeout: 45000,
  expect: { timeout: 15000 },
  outputDir: '../.local/frontend-test-results',
  reporter: [['list']],
  use: {
    baseURL: 'http://127.0.0.1:4173',
    ...devices['Desktop Chrome'],
    // Session cookies and login form data must not end up in a saved trace.
    trace: 'off',
    video: 'off',
    screenshot: 'off',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://127.0.0.1:4173/work/',
    reuseExistingServer: !process.env.CI,
    timeout: 30000,
  },
});
