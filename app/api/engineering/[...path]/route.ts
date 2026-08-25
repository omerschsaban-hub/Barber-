import {NextRequest, NextResponse} from 'next/server'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

const ENGINE = process.env.ENGINEERING_API_INTERNAL || process.env.NEXT_PUBLIC_ENGINEERING_API || 'https://fabrient-engineering.onrender.com'

async function proxy(request: NextRequest, {params}: {params: Promise<{path: string[]}>}) {
  const {path} = await params
  const target = `${ENGINE.replace(/\/$/, '')}/${path.join('/')}${request.nextUrl.search}`
  const headers = new Headers(request.headers)
  headers.delete('host')
  headers.delete('content-length')
  headers.set('x-fabrient-proxy', 'nextjs')
  const body = request.method === 'GET' || request.method === 'HEAD' ? undefined : await request.arrayBuffer()
  try {
    const upstream = await fetch(target, {method: request.method, headers, body, cache: 'no-store', signal: AbortSignal.timeout(130_000)})
    return new NextResponse(upstream.body, {status: upstream.status, headers: {'content-type': upstream.headers.get('content-type') || 'application/json'}})
  } catch (error: any) {
    return NextResponse.json({ok: false, error: 'Engineering service unreachable', detail: error?.message || 'upstream connection failed', upstream: ENGINE}, {status: 503})
  }
}

export const GET = proxy
export const POST = proxy
export const PUT = proxy
export const PATCH = proxy
export const DELETE = proxy
