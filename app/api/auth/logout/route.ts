import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'

const API = process.env.FABRIENT_API_URL
export async function POST() {
  const out = NextResponse.json({ ok: true })
  const token = (await cookies()).get('fabrient_session')?.value
  if (API && token) {
    await fetch(`${API.replace(/\/$/, '')}/auth/logout`, { method: 'POST', headers: { Authorization: `Bearer ${token}` }, cache: 'no-store' }).catch(() => undefined)
  }
  out.cookies.set('fabrient_session', '', { httpOnly: true, secure: process.env.NODE_ENV === 'production', sameSite: 'lax', path: '/', maxAge: 0 })
  return out
}
