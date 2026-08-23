import { test, expect } from '@playwright/test'

const publicRoutes = ['/', '/manufacturing', '/engineering', '/geometry', '/records']

async function assertHealthyPage(page: Parameters<typeof test>[0] extends never ? never : any) {
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
      const diagnostics = await assertHealthyPage(page)
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

  test('landing page is a simple entry point into the real product loop', async ({ page }) => {
    const diagnostics = await assertHealthyPage(page)
    await page.goto('/')
    await expect(page.getByRole('link', { name: /START A PROJECT/i })).toBeVisible()
    await expect(page.getByText(/From idea/i)).toBeVisible()
    await expect(page.getByText(/real product/i)).toBeVisible()
    await page.getByRole('link', { name: /START A PROJECT/i }).click()
    await expect(page).toHaveURL(/\/manufacturing$/)
    expect(diagnostics.pageErrors).toEqual([])
  })

  test('manufacturing surface has a low-friction default path and an explicit advanced path', async ({ page }) => {
    await page.goto('/manufacturing')
    await expect(page.getByRole('heading', { name: /Fix it\. Verify it\. Build it\./i })).toBeVisible()
    await expect(page.getByLabel(/Part name/i)).toHaveValue(/.+/)
    await expect(page.getByLabel(/Material/i)).toHaveValue(/.+/)
    await expect(page.getByLabel(/Machine/i)).toHaveValue(/.+/)
    await expect(page.getByRole('button', { name: /Self-fix \+ verify/i })).toBeVisible()
  })

  test('manufacturing workflow recovers from an engineering API failure', async ({ page }) => {
    await page.route('**/v1/dfm/self-fix', async route => {
      await route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'temporary upstream failure' }) })
    })
    await page.goto('/manufacturing')
    await page.getByRole('button', { name: /Self-fix \+ verify/i }).click()
    await expect(page.getByText(/temporary upstream failure/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /Self-fix \+ verify/i })).toBeEnabled()
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
