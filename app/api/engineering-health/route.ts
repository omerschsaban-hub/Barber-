import { NextResponse } from 'next/server'
import { backendFetch } from '../../../lib/backend'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET(request: Request) {
  const requestId = request.headers.get('x-request-id') || crypto.randomUUID()
  const started = Date.now()
  try {
    const response = await backendFetch('/ready', {
      method: 'GET',
      headers: { 'x-request-id': requestId },
    })
    const body = await response.text()
    return new NextResponse(body || JSON.stringify({ ok: response.ok }), {
      status: response.status,
      headers: {
        'content-type': response.headers.get('content-type') || 'application/json',
        'cache-control': 'no-store',
        'x-request-id': response.headers.get('x-request-id') || requestId,
        'x-backend-latency-ms': String(Date.now() - started),
      },
    })
  } catch (error) {
    return NextResponse.json({
      ok: false,
      error: error instanceof Error && error.name === 'AbortError' ? 'Engineering backend timed out' : 'Engineering backend unavailable',
      request_id: requestId,
      latency_ms: Date.now() - started,
    }, {
      status: 502,
      headers: { 'cache-control': 'no-store', 'x-request-id': requestId },
    })
  }
}
