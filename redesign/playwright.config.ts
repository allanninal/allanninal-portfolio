import { defineConfig, devices } from '@playwright/test';

process.env.PUBLIC_BASE_PATH ??= '/';
process.env.PUBLIC_SITE_URL ??= 'http://localhost:4321';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL: 'http://localhost:4321',
    trace: 'retain-on-failure',
    colorScheme: 'light',
  },
  webServer: {
    command: 'npm run build && npm run preview -- --host 127.0.0.1 --port 4321',
    url: 'http://localhost:4321/',
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
    env: {
      PUBLIC_SITE_URL: 'http://localhost:4321',
      PUBLIC_BASE_PATH: '/',
      PUBLIC_TEMPLATE_HUB_URL: 'https://templates.allanninal.dev',
    },
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
