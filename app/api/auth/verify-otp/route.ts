import { NextResponse } from 'next/server'

const API = process.env.FABRIENT_API_URL
const COOKIE = 'fabrient_session'

export async function POST(request: Request) {
  if (!API) return NextResponse.json({ error: 'Authentication backend is not configured' }, { status: 503 })
  try {
    const response = await fetch(`${API.replace(/\/$/, '')}/auth/verify-otp`, {
      method: 'POST', headers: { 'content-type': 'application/json', origin: request.headers.get('origin') ?? '' },
      body: await request.text(), cache: 'no-store',
    })
    const text = await response.text()
    if (!response.ok) return new NextResponse(text, { status: response.status, headers: { 'content-type': 'application/json' } })
    const data = JSON.parse(text) as { session_token?: string; expires_in?: number; user?: unknown }
    if (!data.session_token) return NextResponse.json({ error: 'Authentication backend returned no session' }, { status: 502 })
    const out = NextResponse.json({ user: data.user })
    out.cookies.set(COOKIE, data.session_token, {
      httpOnly: true, secure: process.env.NODE_ENV === 'production', sameSite: 'lax', path: '/',
      maxAge: Math.max(60, Math.min(data.expires_in ?? 2592000, 2592000)),
    })
    return out
  } catch { return NextResponse.json({ error: 'Authentication backend unavailable' }, { status: 502 }) }
}
