import { NextRequest, NextResponse } from 'next/server'
import { createServerClient } from '@supabase/ssr'

const FEATURE_ROUTES = ['/engineering','/manufacturing','/calibration','/geometry','/graph','/import','/integrations','/machine-health','/records','/risk-map','/sim2real','/experiments','/projects']

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
    "frame-ancestors 'none'"
  ].join('; '))
  return response
}

export async function middleware(request: NextRequest) {
  let response = securityHeaders(NextResponse.next({request: {headers: new Headers(request.headers)}}))
  const path = request.nextUrl.pathname
  const isWorkspace = path === '/workspace' || path.startsWith('/workspace/')
  const isFeatureRoute = FEATURE_ROUTES.some(route => path === route || path.startsWith(`${route}/`))

  if (!isWorkspace && !isFeatureRoute) return response

  const supabase = createServerClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!, {
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll(cookies) => {
        cookies.forEach(({name, value}) => request.cookies.set(name, value))
        response = securityHeaders(NextResponse.next({request: {headers: new Headers(request.headers)}}))
        cookies.forEach(({name, value, options}) => response.cookies.set(name, value, options))
      }
    }
  })

  const {data: {user}} = await supabase.auth.getUser()
  if (!user) {
    const login = new URL('/login', request.url)
    login.searchParams.set('redirect', '/workspace')
    return securityHeaders(NextResponse.redirect(login))
  }

  // The old feature routes remain in source for compatibility and backend/API
  // contracts, but the user-facing product is now one authenticated workspace.
  if (isFeatureRoute && !isWorkspace) return securityHeaders(NextResponse.redirect(new URL('/workspace', request.url)))
  return response
}

export const config = {matcher: ['/((?!_next/static|_next/image|favicon.ico).*)']}
