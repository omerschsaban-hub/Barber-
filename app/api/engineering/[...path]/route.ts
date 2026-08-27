import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'

const API = process.env.FABRIENT_API_URL || process.env.NEXT_PUBLIC_ENGINEERING_API || 'https://fabrient-engineering.onrender.com'
const COOKIE = 'fabrient_session'

async function handler(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const token = (await cookies()).get(COOKIE)?.value
  if (!token) return NextResponse.json({ error: 'Sign in before running engineering actions' }, { status: 401 })
  const { path } = await context.params
  const target = `${API.replace(/\/$/, '')}/${path.map(encodeURIComponent).join('/')}${new URL(request.url).search}`
  try {
    const body = request.method === 'GET' || request.method === 'HEAD' ? undefined : await request.arrayBuffer()
    const response = await fetch(target, {
      method: request.method,
      headers: {
        Authorization: `Bearer ${token}`,
        'content-type': request.headers.get('content-type') || 'application/json',
        origin: request.headers.get('origin') || '',
      },
      body,
      cache: 'no-store',
    })
    return new NextResponse(response.body, {
      status: response.status,
      headers: { 'content-type': response.headers.get('content-type') || 'application/json' },
    })
  } catch {
    return NextResponse.json({ error: 'Engineering backend unavailable' }, { status: 502 })
  }
}

export const GET = handler
export const POST = handler
export const PUT = handler
export const PATCH = handler
export const DELETE = handler
