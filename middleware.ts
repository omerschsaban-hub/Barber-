import { NextRequest, NextResponse } from 'next/server'

function withSecurityHeaders(request: NextRequest) {
  const nonce = crypto.randomUUID().replace(/-/g, '')
  const csp = [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' https://va.vercel-scripts.com`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob: https:",
    "font-src 'self' data: https:",
    "connect-src 'self' https://api.openai.com https://va.vercel-scripts.com",
    "frame-src 'self'",
    "worker-src 'self' blob:",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'"
  ].join('; ')
  const requestHeaders = new Headers(request.headers)
  requestHeaders.set('x-nonce', nonce)
  requestHeaders.set('Content-Security-Policy', csp)
  const response = NextResponse.next({ request: { headers: requestHeaders } })
  response.headers.set('Content-Security-Policy', csp)
  return { response, requestHeaders }
}

export async function middleware(request: NextRequest) {
  const { response, requestHeaders } = withSecurityHeaders(request)
  if (!request.nextUrl.pathname.startsWith('/projects')) return response

  const token = request.cookies.get('fabrient_session')?.value
  const api = process.env.FABRIENT_API_URL
  if (!token || !api) {
    const redirect = NextResponse.redirect(new URL('/login', request.url))
    redirect.headers.set('Content-Security-Policy', requestHeaders.get('Content-Security-Policy')!)
    return redirect
  }

  try {
    const check = await fetch(`${api.replace(/\/$/, '')}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: 'no-store',
    })
    if (!check.ok) {
      const redirect = NextResponse.redirect(new URL('/login', request.url))
      redirect.headers.set('Content-Security-Policy', requestHeaders.get('Content-Security-Policy')!)
      return redirect
    }
  } catch {
    const redirect = NextResponse.redirect(new URL('/login?error=auth_unavailable', request.url))
    redirect.headers.set('Content-Security-Policy', requestHeaders.get('Content-Security-Policy')!)
    return redirect
  }
  return response
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)']
}
