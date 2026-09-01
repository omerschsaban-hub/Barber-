import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { engineeringOrigin } from '@/lib/engineering-origin'

const API = engineeringOrigin()
export async function POST() {
  const out = NextResponse.json({ ok: true })
  const token = (await cookies()).get('fabrient_session')?.value
  if (token) {
    await fetch(`${API}/auth/logout`, { method: 'POST', headers: { Authorization: `Bearer ${token}` }, cache: 'no-store' }).catch(() => undefined)
  }
  out.cookies.set('fabrient_session', '', { httpOnly: true, secure: process.env.NODE_ENV === 'production', sameSite: 'lax', path: '/', maxAge: 0 })
  return out
}
