import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { backendFetch } from '../../../../lib/backend'

const COOKIE = 'fabrient_session'

async function handler(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const token = (await cookies()).get(COOKIE)?.value
  const requestId = request.headers.get('x-request-id') || crypto.randomUUID()
  if (!token) return NextResponse.json({ error: 'Sign in before running engineering actions', request_id: requestId }, { status: 401, headers: { 'x-request-id': requestId } })
  const { path } = await context.params
  const targetPath = path.map(encodeURIComponent).join('/') + new URL(request.url).search
  try {
    const body = request.method === 'GET' || request.method === 'HEAD' ? undefined : await request.arrayBuffer()
    const response = await backendFetch(targetPath, {
      method: request.method,
      headers: {
        Authorization: `Bearer ${token}`,
        'content-type': request.headers.get('content-type') || 'application/json',
        'x-request-id': requestId,
      },
      body,
    })
    return new NextResponse(response.body, {
      status: response.status,
      headers: {
        'content-type': response.headers.get('content-type') || 'application/json',
        'x-request-id': response.headers.get('x-request-id') || requestId,
      },
    })
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error && error.name === 'AbortError' ? 'Engineering backend timed out' : 'Engineering backend unavailable', request_id: requestId }, { status: 502, headers: { 'x-request-id': requestId } })
  }
}

export const GET = handler
export const POST = handler
export const PUT = handler
export const PATCH = handler
export const DELETE = handler
