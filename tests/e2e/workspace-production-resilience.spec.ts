import { test, expect } from '@playwright/test'

const productionEngine = 'https://fabrient-engineering.onrender.com'

test.describe('workspace production resilience', () => {
  test('never renders a blank workspace and always exposes a next action', async ({ page }) => {
    const consoleErrors: string[] = []
    page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()) })
    page.on('pageerror', error => consoleErrors.push(error.message))

    await page.goto('/workspace', { waitUntil: 'domcontentloaded' })
    await expect(page.locator('h1')).toContainText('Your engineering command center.')
    await expect(page.getByText('TODAY / NEXT BEST ACTION')).toBeVisible()
    await expect(page.getByRole('button', { name: /deterministic prediction/i })).toBeVisible()
    await expect(page.getByText(/NO-BLANK RULE/i)).toBeVisible()
    await expect(page.locator('main')).not.toBeEmpty()
    expect(consoleErrors.filter(message => !message.includes('favicon'))).toEqual([])
  })

  test('does not silently route production browser requests to localhost', async ({ page }) => {
    const requests: string[] = []
    page.on('request', request => {
      if (request.url().includes('/v1/') || request.url().includes('/health')) requests.push(request.url())
    })
    await page.goto('/workspace', { waitUntil: 'domcontentloaded' })
    await expect(page.getByText(/ENGINE (READY|ACTION NEEDED|CONNECTING)/i)).toBeVisible()
    await page.getByRole('button', { name: /retry connection/i }).click().catch(() => {})
    expect(requests.every(url => !url.startsWith('http://localhost:8000'))).toBeTruthy()
    expect(requests.every(url => !url.startsWith('http://127.0.0.1:8000'))).toBeTruthy()
  })

  test('production engineering health endpoint is reachable', async ({ request }) => {
    const response = await request.get(`${productionEngine}/health`)
    expect(response.ok()).toBeTruthy()
    expect(response.status()).toBe(200)
  })

  test('invalid engineering response becomes an explicit failure, never a blank page', async ({ page }) => {
    await page.route('**/v1/predict', route => route.fulfill({ status: 502, contentType: 'application/json', body: JSON.stringify({ detail: 'upstream unavailable' }) }))
    await page.goto('/workspace', { waitUntil: 'domcontentloaded' })
    await expect(page.getByText(/Run your first deterministic check|Review the verified prediction/i)).toBeVisible()
    await expect(page.locator('main')).not.toBeEmpty()
  })
})
