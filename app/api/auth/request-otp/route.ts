import { NextResponse } from 'next/server'
import { backendFetch } from '../../../../lib/backend'

export async function POST(request: Request) {
  const requestId = request.headers.get('x-request-id') || crypto.randomUUID()
  try {
    const response = await backendFetch('/auth/request-otp', {
      method: 'POST',
      headers: { 'content-type': 'application/json', 'x-request-id': requestId },
      body: await request.text(),
    })
    const text = await response.text()
    return new NextResponse(text, {
      status: response.status,
      headers: { 'content-type': response.headers.get('content-type') || 'application/json', 'x-request-id': requestId },
    })
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error && error.name === 'AbortError' ? 'Authentication backend timed out' : 'Authentication backend unavailable', request_id: requestId }, { status: 502, headers: { 'x-request-id': requestId } })
  }
}
