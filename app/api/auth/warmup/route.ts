import { NextResponse } from 'next/server'
import { backendFetch } from '../../../../lib/backend'

export const dynamic = 'force-dynamic'

/**
 * Cheap, unauthenticated Render wake-up endpoint.
 * It deliberately calls only /health so a cold backend does not need a
 * database connection, Gmail, or an authenticated session to become ready.
 */
export async function GET(request: Request) {
  const requestId = request.headers.get('x-request-id') || crypto.randomUUID()
  try {
    const response = await backendFetch('/health', {
      method: 'GET',
      headers: { 'x-request-id': requestId },
    })
    return NextResponse.json({
      ok: response.ok,
      backend_status: response.status,
      request_id: response.headers.get('x-request-id') || requestId,
    }, {
      status: response.ok ? 200 : 503,
      headers: {
        'cache-control': 'no-store',
        'x-request-id': response.headers.get('x-request-id') || requestId,
      },
    })
  } catch (error) {
    return NextResponse.json({
      ok: false,
      error: error instanceof Error && error.name === 'AbortError' ? 'Backend is waking up' : 'Backend unavailable',
      request_id: requestId,
    }, { status: 503, headers: { 'cache-control': 'no-store', 'x-request-id': requestId } })
  }
}
