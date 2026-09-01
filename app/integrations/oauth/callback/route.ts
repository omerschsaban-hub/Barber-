import { NextRequest, NextResponse } from 'next/server'

const API = (process.env.FABRIENT_ENGINEERING_API || process.env.NEXT_PUBLIC_FABRIENT_ENGINEERING_API || 'http://localhost:8000').replace(/\/$/, '')

export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get('code')
  const state = request.nextUrl.searchParams.get('state')
  const error = request.nextUrl.searchParams.get('error')
  if (error) return NextResponse.redirect(new URL(`/integrations?oauth_error=${encodeURIComponent(error)}`, request.url))
  if (!code || !state) return NextResponse.redirect(new URL('/integrations?oauth_error=missing_callback_parameters', request.url))
  try {
    const response = await fetch(`${API}/integrations/auth/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, state }),
      cache: 'no-store',
    })
    const body = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(body.detail || 'OAuth completion failed')
    return NextResponse.redirect(new URL(`/integrations?connected=${encodeURIComponent(body.provider || '')}`, request.url))
  } catch (e) {
    return NextResponse.redirect(new URL(`/integrations?oauth_error=${encodeURIComponent(e instanceof Error ? e.message : 'OAuth completion failed')}`, request.url))
  }
}
