import { NextRequest, NextResponse } from 'next/server'
import { createServerClient } from '@supabase/ssr'

const FEATURE_ROUTES = ['/engineering','/manufacturing','/calibration','/geometry','/graph','/import','/integrations','/machine-health','/records','/risk-map','/sim2real','/experiments','/projects']
const MUTATING_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])
const RATE_WINDOW_MS = 60_000
const RATE_LIMIT = 120
const requestBuckets = new Map<string, number[]>()

function securityHeaders(response: NextResponse) {
  response.headers.set('Content-Security-Policy', [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' https://*.supabase.co https://va.vercel-scripts.com",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob: https:",
    "font-src 'self' data: https:",
    "connect-src 'self' https://*.supabase.co https://api.openai.com https://va.vercel-scripts.com",
    "frame-src 'self' https://*.supabase.co",
    "worker-src 'self' blob:",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "upgrade-insecure-requests"
  ].join('; '))
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('X-Frame-Options', 'DENY')
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')
  response.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=(), payment=()')
  response.headers.set('Cross-Origin-Opener-Policy', 'same-origin')
  response.headers.set('Cross-Origin-Resource-Policy', 'same-origin')
  if (process.env.NODE_ENV === 'production') {
    response.headers.set('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
  }
  return response
}

function sameOrigin(request: NextRequest) {
  const origin = request.headers.get('origin')
  if (!origin) return true
  try {
    return new URL(origin).origin === request.nextUrl.origin
  } catch {
    return false
  }
}

function rateLimit(request: NextRequest) {
  const forwarded = request.headers.get('x-forwarded-for')?.split(',')[0]?.trim()
  const realIp = request.headers.get('x-real-ip')?.trim()
  const key = forwarded || realIp || 'unknown'
  const now = Date.now()
  const existing = requestBuckets.get(key) || []
  const recent = existing.filter(ts => now - ts < RATE_WINDOW_MS)
  if (recent.length >= RATE_LIMIT) {
    requestBuckets.set(key, recent)
    return false
  }
  recent.push(now)
  requestBuckets.set(key, recent)
  if (requestBuckets.size > 10_000) {
    for (const [bucketKey, timestamps] of requestBuckets) {
      if (!timestamps.some(ts => now - ts < RATE_WINDOW_MS)) requestBuckets.delete(bucketKey)
    }
  }
  return true
}

export async function middleware(request: NextRequest) {
  let response = securityHeaders(NextResponse.next({request: {headers: new Headers(request.headers)}}))
  const path = request.nextUrl.pathname
  const isWorkspace = path === '/workspace' || path.startsWith('/workspace/')
  const isFeatureRoute = FEATURE_ROUTES.some(route => path === route || path.startsWith(`${route}/`))

  if (MUTATING_METHODS.has(request.method) && request.cookies.has('fabrient_session') && !sameOrigin(request)) {
    return securityHeaders(NextResponse.json({ error: 'Cross-site request blocked' }, { status: 403 }))
  }

  if (MUTATING_METHODS.has(request.method) && path.startsWith('/api/') && !rateLimit(request)) {
    return securityHeaders(NextResponse.json({ error: 'Too many requests' }, { status: 429, headers: { 'Retry-After': '60' } }))
  }

  if (!isWorkspace && !isFeatureRoute) return response

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  if (!supabaseUrl || !supabaseAnonKey) {
    return securityHeaders(NextResponse.json({ error: 'Authentication configuration unavailable' }, { status: 503 }))
  }

  const supabase = createServerClient(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll: (cookies) => {
        cookies.forEach(({name, value}) => request.cookies.set(name, value))
        response = securityHeaders(NextResponse.next({request: {headers: new Headers(request.headers)}}))
        cookies.forEach(({name, value, options}) => response.cookies.set(name, value, options))
      }
    }
  })

  const {data: {user}} = await supabase.auth.getUser()
  if (!user) {
    const login = new URL('/login', request.url)
    login.searchParams.set('redirect', path)
    return securityHeaders(NextResponse.redirect(login))
  }

  if (isFeatureRoute && !isWorkspace) return securityHeaders(NextResponse.redirect(new URL('/workspace', request.url)))
  return response
}

export const config = {matcher: ['/((?!_next/static|_next/image|favicon.ico).*)']}
