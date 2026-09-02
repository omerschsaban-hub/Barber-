import { NextRequest, NextResponse } from 'next/server'
import { engineeringOrigin } from '@/lib/engineering-origin'

const mutationWindowMs = 60_000
const mutationLimit = 60
const mutationCounts = new Map<string, { count: number; resetAt: number }>()
const PRIVATE_PREFIXES = ['/api/', '/workspace', '/projects', '/engineering', '/geometry', '/calibration', '/import', '/records', '/risk-map', '/sim2real', '/machine-health', '/manufacturing', '/billing', '/oauth', '/login', '/integrations']

function withSecurityHeaders(request: NextRequest) {
  const csp = [
    "default-src 'self'",
    `script-src 'self' 'unsafe-inline'${process.env.NODE_ENV !== 'production' ? " 'unsafe-eval'" : ''} https://va.vercel-scripts.com`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob: https:",
    "font-src 'self' data: https:",
    "connect-src 'self' https://api.openai.com https://va.vercel-scripts.com https://fabrient-engineering.onrender.com https://fabrient-mcp.onrender.com",
    "frame-src 'self'",
    "worker-src 'self' blob:",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ].join('; ')
  const requestHeaders = new Headers(request.headers)
  requestHeaders.set('Content-Security-Policy', csp)
  const response = NextResponse.next({ request: { headers: requestHeaders } })
  response.headers.set('Content-Security-Policy', csp)
  response.headers.set('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('X-Frame-Options', 'DENY')
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')
  response.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
  if (PRIVATE_PREFIXES.some((prefix) => request.nextUrl.pathname === prefix || request.nextUrl.pathname.startsWith(`${prefix}/`))) {
    const robots = 'noindex, nofollow, noarchive'
    response.headers.set('X-Robots-Tag', robots)
    requestHeaders.set('X-Robots-Tag', robots)
  }
  return { response, requestHeaders }
}

function withHeaders(response: NextResponse, requestHeaders: Headers) {
  response.headers.set('Content-Security-Policy', requestHeaders.get('Content-Security-Policy')!)
  response.headers.set('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('X-Frame-Options', 'DENY')
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')
  response.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
  const robots = requestHeaders.get('X-Robots-Tag')
  if (robots) response.headers.set('X-Robots-Tag', robots)
  return response
}

function sameOrigin(request: NextRequest) {
  const origin = request.headers.get('origin')
  if (!origin) return true
  return origin === request.nextUrl.origin
}

function allowedMutation(request: NextRequest) {
  const key = request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || 'unknown'
  const now = Date.now()
  const previous = mutationCounts.get(key)
  const current = !previous || previous.resetAt <= now ? { count: 0, resetAt: now + mutationWindowMs } : previous
  current.count += 1
  mutationCounts.set(key, current)
  if (mutationCounts.size > 10_000) {
    for (const [address, item] of mutationCounts) if (item.resetAt <= now) mutationCounts.delete(address)
  }
  return current.count <= mutationLimit
}

export async function middleware(request: NextRequest) {
  const { response, requestHeaders } = withSecurityHeaders(request)
  const methodMutates = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(request.method)
  const hasSession = Boolean(request.cookies.get('fabrient_session')?.value)

  if (methodMutates && hasSession && !sameOrigin(request)) {
    return withHeaders(NextResponse.json({ error: 'Cross-site request blocked' }, { status: 403 }), requestHeaders)
  }
  if (methodMutates && !allowedMutation(request)) {
    return withHeaders(NextResponse.json({ error: 'Too many requests' }, { status: 429 }), requestHeaders)
  }

  if (!request.nextUrl.pathname.startsWith('/projects')) return response

  const token = request.cookies.get('fabrient_session')?.value
  const api = engineeringOrigin()
  if (!token) {
    return withHeaders(NextResponse.redirect(new URL('/login', request.url)), requestHeaders)
  }

  try {
    const check = await fetch(`${api}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: 'no-store',
    })
    if (!check.ok) return withHeaders(NextResponse.redirect(new URL('/login', request.url)), requestHeaders)
  } catch {
    return withHeaders(NextResponse.redirect(new URL('/login?error=auth_unavailable', request.url)), requestHeaders)
  }
  return response
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
