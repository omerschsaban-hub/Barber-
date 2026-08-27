import { defineConfig, devices } from '@playwright/test'

const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:3000'
const isProductionURL = /^https?:\/\/(?!127\.0\.0\.1|localhost)/.test(baseURL)

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: process.env.CI ? [['html', { open: 'never' }], ['line']] : 'list',
  timeout: 30_000,
  expect: { timeout: 8_000 },
  outputDir: 'test-results',
  use: {
    baseURL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    ...devices['Desktop Chrome'],
    navigationTimeout: 15_000,
    actionTimeout: 10_000,
  },
  webServer: isProductionURL ? undefined : {
    command: 'npm run dev -- --hostname 127.0.0.1',
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: {
      NEXT_TELEMETRY_DISABLED: '1',
      NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://example.supabase.co',
      NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'test-anon-key',
      NEXT_PUBLIC_ENGINEERING_API: process.env.NEXT_PUBLIC_ENGINEERING_API || 'https://fabrient-engineering.onrender.com',
      NEXT_PUBLIC_ENGINEERING_URL: process.env.NEXT_PUBLIC_ENGINEERING_URL || 'https://fabrient-engineering.onrender.com',
      FABRIENT_WEB_ORIGIN: process.env.FABRIENT_WEB_ORIGIN || baseURL,
    },
  },
})
