import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'

const API = process.env.FABRIENT_API_URL || process.env.NEXT_PUBLIC_ENGINEERING_API || 'https://fabrient-engineering.onrender.com'
export async function GET() {
  const token = (await cookies()).get('fabrient_session')?.value
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const response = await fetch(`${API.replace(/\/$/, '')}/auth/me`, { headers: { Authorization: `Bearer ${token}` }, cache: 'no-store' })
  return new NextResponse(await response.text(), { status: response.status, headers: { 'content-type': 'application/json' } })
}
