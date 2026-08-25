import { NextRequest, NextResponse } from 'next/server'
import { createServerClient } from '@supabase/ssr'

function withSecurityHeaders(request: NextRequest) {
  const nonce = crypto.randomUUID().replace(/-/g, '')
  const csp = [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' https://*.supabase.co https://va.vercel-scripts.com`,
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
  ].join('; ')

  const requestHeaders = new Headers(request.headers)
  requestHeaders.set('x-nonce', nonce)
  requestHeaders.set('Content-Security-Policy', csp)

  const response = NextResponse.next({
    request: { headers: requestHeaders }
  })
  response.headers.set('Content-Security-Policy', csp)

  return { response, requestHeaders }
}

export async function middleware(request: NextRequest) {
  const security = withSecurityHeaders(request)
  let { response } = security
  const { requestHeaders } = security

  if (!request.nextUrl.pathname.startsWith('/projects')) {
    return response
  }

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookies) {
          cookies.forEach(({ name, value }) => request.cookies.set(name, value))
          response = NextResponse.next({ request: { headers: requestHeaders } })
          response.headers.set('Content-Security-Policy', requestHeaders.get('Content-Security-Policy')!)
          cookies.forEach(({ name, value, options }) => response.cookies.set(name, value, options))
        }
      }
    }
  )

  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    const redirect = NextResponse.redirect(new URL('/login', request.url))
    redirect.headers.set('Content-Security-Policy', requestHeaders.get('Content-Security-Policy')!)
    return redirect
  }

  return response
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)']
}
