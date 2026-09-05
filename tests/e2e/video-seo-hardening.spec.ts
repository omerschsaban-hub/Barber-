import { test, expect } from '@playwright/test'

const publicPages = ['/']

test.describe('video SEO hardening', () => {
  for (const path of publicPages) {
    test(`${path} has no browser console errors and has SEO essentials`, async ({ page }) => {
      const errors: string[] = []
      page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })
      page.on('pageerror', error => errors.push(error.message))
      await page.goto(path, { waitUntil: 'domcontentloaded' })
      await expect(page.locator('h1')).toHaveCount(1)
      await expect(page.locator('meta[name="description"]')).toHaveCount(1)
      await expect(page.locator('link[rel="canonical"]')).toHaveCount(1)
      expect(errors, `console/page errors on ${path}`).toEqual([])
    })
  }

  test('404 is real and not a silent redirect', async ({ page }) => {
    const response = await page.goto('/this-route-should-not-exist', { waitUntil: 'domcontentloaded' })
    expect(response?.status()).toBe(404)
    await expect(page.getByRole('heading', { name: 'That page does not exist.' })).toBeVisible()
  })

  test('robots and sitemap are reachable', async ({ request }) => {
    const robots = await request.get('/robots.txt')
    expect(robots.ok()).toBeTruthy()
    expect(await robots.text()).toContain('/sitemap.xml')
    const sitemap = await request.get('/sitemap.xml')
    expect(sitemap.ok()).toBeTruthy()
    expect(await sitemap.text()).toContain('<urlset')
  })

  test('llms.txt is reachable and does not expose private routes', async ({ request }) => {
    const response = await request.get('/llms.txt')
    expect(response.ok()).toBeTruthy()
    const text = await response.text()
    expect(text).toContain('# Fabrient')
    expect(text).not.toContain('/api/')
    expect(text).not.toContain('/workspace')
  })
})
