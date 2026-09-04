import { test, expect } from '@playwright/test'

const RETIRED_UI_ROUTES = [
  '/workspace',
  '/projects',
  '/manufacturing',
  '/import',
  '/geometry',
  '/calibration',
  '/records',
  '/integrations',
  '/changelog',
  '/engineering',
  '/risk-map',
  '/sim2real',
  '/machine-health',
  '/billing',
  '/login',
]

test.describe('retired product UI surface', () => {
  test('landing page exposes no navigation into retired product routes', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' })

    const hrefs = await page.locator('a[href]').evaluateAll((links) =>
      links.map((link) => (link as HTMLAnchorElement).getAttribute('href') || ''),
    )

    for (const route of RETIRED_UI_ROUTES) {
      expect(hrefs.some((href) => href === route || href.startsWith(`${route}/`))).toBeFalsy()
    }
  })

  test('retired product routes redirect to the public landing page instead of 404', async ({ page }) => {
    for (const route of RETIRED_UI_ROUTES) {
      const response = await page.goto(route, { waitUntil: 'domcontentloaded' })
      expect(response).not.toBeNull()
      expect(response!.status()).toBe(200)
      expect(new URL(page.url()).pathname).toBe('/')
      await expect(page.locator('main')).not.toBeEmpty()
    }
  })
})
