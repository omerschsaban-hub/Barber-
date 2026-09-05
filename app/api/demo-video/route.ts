import { NextRequest, NextResponse } from 'next/server'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

const VIDEO_URL = 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663321590917/uilhFdzHJgyMSihq.mp4'

export async function GET(request: NextRequest) {
  const range = request.headers.get('range')
  const headers: HeadersInit = {
    Accept: 'video/mp4,application/octet-stream;q=0.9,*/*;q=0.8',
  }
  if (range) headers.Range = range

  try {
    const upstream = await fetch(VIDEO_URL, {
      headers,
      redirect: 'follow',
      cache: 'no-store',
    })

    if (!upstream.ok && upstream.status !== 206) {
      return NextResponse.json({ error: 'Demo video unavailable' }, { status: 502 })
    }

    const contentType = upstream.headers.get('content-type') || ''
    if (!/^video\/mp4(?:\s*;|$)/i.test(contentType)) {
      return NextResponse.json({ error: 'Demo video returned an invalid media type' }, { status: 502 })
    }

    const responseHeaders = new Headers()
    responseHeaders.set('Content-Type', 'video/mp4')
    responseHeaders.set('Accept-Ranges', 'bytes')
    responseHeaders.set('Cache-Control', 'public, max-age=3600, s-maxage=86400, stale-while-revalidate=3600')
    responseHeaders.set('X-Content-Type-Options', 'nosniff')
    responseHeaders.set('Content-Disposition', 'inline; filename="fabrient-launch-demo.mp4"')

    for (const name of ['content-length', 'content-range']) {
      const value = upstream.headers.get(name)
      if (value) responseHeaders.set(name, value)
    }

    return new NextResponse(upstream.body, {
      status: upstream.status,
      headers: responseHeaders,
    })
  } catch {
    return NextResponse.json({ error: 'Demo video unavailable' }, { status: 502 })
  }
}
