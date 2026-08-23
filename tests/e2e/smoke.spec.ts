import { test, expect } from '@playwright/test'

const publicRoutes = ['/', '/manufacturing', '/engineering', '/geometry', '/records']

test.describe('Fabrient public product surface', () => {
  for (const route of publicRoutes) {
    test(`${route} loads without a browser-level failure`, async ({ page }) => {
      const pageErrors: string[] = []
      page.on('pageerror', error => pageErrors.push(error.message))
      const response = await page.goto(route, { waitUntil: 'domcontentloaded' })
      expect(response?.ok()).toBeTruthy()
      await expect(page.locator('body')).toBeVisible()
      expect(pageErrors).toEqual([])
    })
  }

  test('landing page exposes the real product loop and project entry point', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('From idea', { exact: false })).toBeVisible()
    await expect(page.getByRole('link', { name: /START A PROJECT/i })).toBeVisible()
    await expect(page.getByText(/DESIGN|BUILD|REAL WORLD/i).first()).toBeVisible()
  })

  test('manufacturing workflow can execute a bounded self-fix and show evidence', async ({ page }) => {
    await page.route('**/v1/dfm/self-fix', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          changes: [{ issue: 'Wall too thin', field: 'wall_thickness_mm', before: 1, after: 1.2, reason: 'Within deterministic scalar fix bound' }],
          refused: [],
          after: { status: 'PASS', blocker_count: 0 },
        }),
      })
    })

    await page.goto('/manufacturing')
    await page.getByRole('button', { name: /Self-fix \+ verify/i }).click()
    await expect(page.getByText('Wall too thin')).toBeVisible()
    await expect(page.getByText(/Verification: PASS/i)).toBeVisible()
  })
})
