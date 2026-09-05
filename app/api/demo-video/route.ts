import { createReadStream, existsSync, statSync } from 'node:fs'
import { Readable } from 'node:stream'
import path from 'node:path'
import { NextRequest, NextResponse } from 'next/server'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

const VIDEO_PATH = path.join(process.cwd(), 'public', 'demo', 'fabrient-launch-demo.mp4')
const MIN_VIDEO_BYTES = 1024

function parseRange(value: string | null, size: number) {
  if (!value?.startsWith('bytes=')) return null
  const [startText, endText] = value.slice(6).split('-', 2)
  const start = startText ? Number(startText) : Math.max(0, size - Number(endText || 0))
  const end = endText ? Number(endText) : size - 1
  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end < start || start >= size) return null
  return { start, end: Math.min(end, size - 1) }
}

export async function GET(request: NextRequest) {
  if (!existsSync(VIDEO_PATH)) {
    return NextResponse.json({ error: 'Demo video unavailable' }, { status: 503 })
  }

  const size = statSync(VIDEO_PATH).size
  if (size <= MIN_VIDEO_BYTES) {
    return NextResponse.json({ error: 'Demo video asset is not installed' }, { status: 503 })
  }

  const range = parseRange(request.headers.get('range'), size)
  const start = range?.start ?? 0
  const end = range?.end ?? size - 1
  const contentLength = end - start + 1
  const stream = Readable.toWeb(createReadStream(VIDEO_PATH, { start, end })) as ReadableStream
  const headers = new Headers({
    'Content-Type': 'video/mp4',
    'Accept-Ranges': 'bytes',
    'Cache-Control': 'public, max-age=3600, s-maxage=86400, stale-while-revalidate=3600',
    'Content-Disposition': 'inline; filename="fabrient-launch-demo.mp4"',
    'X-Content-Type-Options': 'nosniff',
    'Content-Length': String(contentLength),
  })

  if (range) headers.set('Content-Range', `bytes ${start}-${end}/${size}`)

  return new NextResponse(stream, { status: range ? 206 : 200, headers })
}
