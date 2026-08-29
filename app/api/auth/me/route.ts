import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { backendFetch } from '../../../../lib/backend'

export const dynamic = 'force-dynamic'

export async function GET(request: Request) {
  const token = (await cookies()).get('fabrient_session')?.value
  const requestId = request.headers.get('x-request-id') || crypto.randomUUID()
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized', request_id: requestId }, {
      status: 401,
      headers: { 'x-request-id': requestId },
    })
  }

  try {
    const response = await backendFetch('/auth/me', {
      headers: {
        Authorization: `Bearer ${token}`,
        'x-request-id': requestId,
      },
    })
    return new NextResponse(response.body, {
      status: response.status,
      headers: {
        'content-type': response.headers.get('content-type') || 'application/json',
        'cache-control': 'private, no-store',
        'x-request-id': response.headers.get('x-request-id') || requestId,
      },
    })
  } catch (error) {
    return NextResponse.json({
      error: error instanceof Error && error.name === 'AbortError' ? 'Authentication backend timed out' : 'Authentication backend unavailable',
      request_id: requestId,
    }, { status: 502, headers: { 'x-request-id': requestId } })
  }
}
