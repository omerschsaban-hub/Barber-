import type { MetadataRoute } from 'next'

const SITE = (process.env.NEXT_PUBLIC_FABRIENT_WEB_URL || 'https://fabrinat-omega.vercel.app').replace(/\/$/, '')

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [{ userAgent: '*', allow: '/', disallow: ['/api/', '/workspace', '/projects', '/engineering', '/geometry', '/calibration', '/import', '/records', '/risk-map', '/sim2real', '/machine-health', '/manufacturing', '/billing', '/oauth', '/login', '/integrations'] }],
    sitemap: `${SITE}/sitemap.xml`,
    host: SITE,
  }
}
