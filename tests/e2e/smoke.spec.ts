import { test, expect, type Page } from '@playwright/test'

const publicRoutes = ['/', '/login']
const legacyRoutes = ['/manufacturing', '/engineering', '/geometry', '/records', '/calibration', '/experiments', '/graph', '/import', '/projects', '/risk-map']

function attachDiagnostics(page: Page) {
  const pageErrors: string[] = []
  const failedRequests: string[] = []
  const serverErrors: string[] = []
  page.on('pageerror', error => pageErrors.push(error.message))
  page.on('requestfailed', request => failedRequests.push(`${request.method()} ${request.url()} :: ${request.failure()?.errorText || 'failed'}`))
  page.on('response', response => {
    if (response.status() >= 500) serverErrors.push(`${response.status()} ${response.url()}`)
  })
  return { pageErrors, failedRequests, serverErrors }
}

test.describe('Fabrient browser health', () => {
  for (const route of publicRoutes) {
    test(`${route} renders real content without runtime failures`, async ({ page }) => {
      const diagnostics = attachDiagnostics(page)
      const response = await page.goto(route, { waitUntil: 'domcontentloaded' })
      expect(response?.ok(), `HTTP failure for ${route}`).toBeTruthy()
      await expect(page.locator('body')).toBeVisible()
      await expect(page.locator('body')).not.toBeEmpty()
      await expect(page.locator('body')).toContainText(/.+/)
      expect(diagnostics.pageErrors, `Browser errors on ${route}`).toEqual([])
      expect(diagnostics.serverErrors, `5xx responses on ${route}`).toEqual([])
      expect(diagnostics.failedRequests, `Failed requests on ${route}`).toEqual([])
    })
  }

  test('landing page has exactly two execution CTAs and neither executes work', async ({ page }) => {
    const diagnostics = attachDiagnostics(page)
    await page.goto('/')
    const ctas = page.locator('main .cad-actions a')
    await expect(ctas).toHaveCount(2)
    await expect(page.getByRole('link', { name: /GET STARTED/i })).toHaveAttribute('href', /\/login\?redirect=%2Fworkspace/)
    await expect(page.getByRole('link', { name: /^LOG IN$/i })).toHaveAttribute('href', /\/login\?redirect=%2Fworkspace/)
    await expect(page.getByText(/informational entry point only/i)).toBeVisible()
    await expect(page.getByAltText(/Real 3D printer mechanism/i)).toBeVisible()
    expect(diagnostics.pageErrors).toEqual([])
  })

  for (const route of legacyRoutes) {
    test(`${route} is no longer a disconnected product destination`, async ({ page }) => {
      const response = await page.goto(route, { waitUntil: 'domcontentloaded' })
      expect(response?.status()).toBeLessThan(400)
      await expect(page).toHaveURL(/\/login|\/workspace/)
    })
  }
})
