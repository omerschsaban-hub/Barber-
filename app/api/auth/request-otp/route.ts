import { NextResponse } from 'next/server'

const API = process.env.FABRIENT_API_URL || process.env.NEXT_PUBLIC_ENGINEERING_API

export async function POST(request: Request) {
  if (!API) return NextResponse.json({ error: 'Authentication backend is not configured' }, { status: 503 })
  try {
    const response = await fetch(`${API.replace(/\/$/, '')}/auth/request-otp`, {
      method: 'POST', headers: { 'content-type': 'application/json', origin: request.headers.get('origin') ?? '' },
      body: await request.text(), cache: 'no-store',
    })
    return new NextResponse(await response.text(), { status: response.status, headers: { 'content-type': 'application/json' } })
  } catch { return NextResponse.json({ error: 'Authentication backend unavailable' }, { status: 502 }) }
}
