import { test, expect, type Page } from '@playwright/test'

const publicRoutes = ['/']

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

  test('landing page exposes the real engineering narrative and demo entry point', async ({ page }) => {
    const diagnostics = attachDiagnostics(page)
    await page.goto('/', { waitUntil: 'domcontentloaded' })
    await expect(page.getByRole('heading', { name: /Design it\. Build it\. Learn from it\./i })).toBeVisible()
    await expect(page.getByText(/engineering work to what happens on the factory floor/i)).toBeVisible()
    await expect(page.getByRole('link', { name: /OPEN THE DEMO/i })).toHaveAttribute('href', '/api/demo-video')
    await expect(page.getByRole('link', { name: /EMAIL FABRIENT/i }).last()).toBeVisible()
    expect(diagnostics.pageErrors).toEqual([])
  })

  test('landing page demo endpoint is reachable without waiting for media network idle', async ({ request }) => {
    const response = await request.get('/api/demo-video', { headers: { Range: 'bytes=0-1023' } })
    expect([200, 206]).toContain(response.status())
    expect(response.headers()['content-type']).toMatch(/^video\/mp4/i)
    expect(response.headers()['accept-ranges']).toBe('bytes')
  })
})
