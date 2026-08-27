import {NextRequest, NextResponse} from 'next/server'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

const ENGINE = (process.env.ENGINEERING_API_INTERNAL || process.env.NEXT_PUBLIC_ENGINEERING_API || 'https://fabrient-engineering.onrender.com').replace(/\/$/, '')
const MAX_AUTH_BODY_BYTES = 32 * 1024

export async function POST(request: NextRequest, {params}: {params: Promise<{action: string}>}) {
  const {action} = await params
  if (!['request-code', 'verify-code', 'logout'].includes(action)) return NextResponse.json({error: 'Not found'}, {status: 404})
  const contentLength = Number(request.headers.get('content-length') || 0)
  if (Number.isFinite(contentLength) && contentLength > MAX_AUTH_BODY_BYTES) {
    return NextResponse.json({error: 'Request body is too large'}, {status: 413})
  }
  const body = await request.arrayBuffer()
  if (body.byteLength > MAX_AUTH_BODY_BYTES) {
    return NextResponse.json({error: 'Request body is too large'}, {status: 413})
  }
  return proxy(request, `/auth/${action}`, body)
}

export async function GET(request: NextRequest, {params}: {params: Promise<{action: string}>}) {
  const {action} = await params
  if (action !== 'me') return NextResponse.json({error: 'Not found'}, {status: 404})
  return proxy(request, '/auth/me')
}

async function proxy(request: NextRequest, path: string, body?: ArrayBuffer) {
  try {
    const headers = new Headers()
    const contentType = request.headers.get('content-type')
    if (contentType) headers.set('content-type', contentType)
    const cookie = request.headers.get('cookie')
    if (cookie) headers.set('cookie', cookie)
    const authorization = request.headers.get('authorization')
    if (authorization) headers.set('authorization', authorization)
    const upstream = await fetch(`${ENGINE}${path}`, {
      method: request.method,
      headers,
      body: request.method === 'GET' ? undefined : body,
      cache: 'no-store',
      signal: AbortSignal.timeout(20_000),
    })
    const response = new NextResponse(upstream.body, {status: upstream.status})
    const type = upstream.headers.get('content-type')
    if (type) response.headers.set('content-type', type)
    const setCookie = upstream.headers.get('set-cookie')
    if (setCookie) response.headers.set('set-cookie', setCookie.replace(/;\s*Domain=[^;]+/ig, ''))
    return response
  } catch {
    return NextResponse.json({error: 'Authentication service unavailable'}, {status: 503})
  }
}
