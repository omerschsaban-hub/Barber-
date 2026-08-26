import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const url = new URL(request.url)
  return NextResponse.redirect(new URL('/login?error=legacy_oauth_disabled', url.origin))
}
