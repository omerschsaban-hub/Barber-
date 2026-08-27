import { NextResponse } from 'next/server'

const API = process.env.FABRIENT_API_URL || process.env.NEXT_PUBLIC_ENGINEERING_API || 'https://fabrient-engineering.onrender.com'

export async function POST(request: Request) {
  try {
    const response = await fetch(`${API.replace(/\/$/, '')}/auth/request-otp`, {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: await request.text(), cache: 'no-store', signal: AbortSignal.timeout(20_000),
    })
    return new NextResponse(await response.text(), { status: response.status, headers: { 'content-type': 'application/json' } })
  } catch { return NextResponse.json({ error: 'Authentication backend unavailable' }, { status: 502 }) }
}
