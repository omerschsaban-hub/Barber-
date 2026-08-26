import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'

const API = process.env.FABRIENT_API_URL

export async function GET() {
  if (!API) return NextResponse.json({ error: 'Billing backend is not configured' }, { status: 503 })
  const token = (await cookies()).get('fabrient_session')?.value
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  try {
    const response = await fetch(`${API.replace(/\/$/, '')}/billing/access`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: 'no-store',
    })
    return new NextResponse(await response.text(), {
      status: response.status,
      headers: { 'content-type': 'application/json' },
    })
  } catch {
    return NextResponse.json({ error: 'Billing backend unavailable' }, { status: 502 })
  }
}
