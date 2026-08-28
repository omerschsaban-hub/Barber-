import { NextResponse } from 'next/server'
import { backendFetch } from '../../../../lib/backend'

const COOKIE = 'fabrient_session'

export async function POST(request: Request) {
  const requestId = request.headers.get('x-request-id') || crypto.randomUUID()
  try {
    const response = await backendFetch('/auth/verify-otp', {
      method: 'POST',
      headers: { 'content-type': 'application/json', 'x-request-id': requestId },
      body: await request.text(),
    })
    const text = await response.text()
    if (!response.ok) return new NextResponse(text, { status: response.status, headers: { 'content-type': response.headers.get('content-type') || 'application/json', 'x-request-id': requestId } })
    const data = JSON.parse(text) as { session_token?: string; expires_in?: number; user?: unknown }
    if (!data.session_token) return NextResponse.json({ error: 'Authentication backend returned no session', request_id: requestId }, { status: 502, headers: { 'x-request-id': requestId } })
    const out = NextResponse.json({ user: data.user }, { headers: { 'x-request-id': requestId } })
    out.cookies.set(COOKIE, data.session_token, {
      httpOnly: true, secure: process.env.NODE_ENV === 'production', sameSite: 'lax', path: '/',
      maxAge: Math.max(60, Math.min(data.expires_in ?? 2592000, 2592000)),
    })
    return out
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error && error.name === 'AbortError' ? 'Authentication backend timed out' : 'Authentication backend unavailable', request_id: requestId }, { status: 502, headers: { 'x-request-id': requestId } })
  }
}
