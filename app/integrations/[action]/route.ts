import { NextRequest, NextResponse } from 'next/server'

const API = (process.env.FABRIENT_ENGINEERING_API || process.env.NEXT_PUBLIC_FABRIENT_ENGINEERING_API || 'http://localhost:8000').replace(/\/$/, '')
const PUBLIC_WEB_URL = process.env.NEXT_PUBLIC_FABRIENT_WEB_URL || 'https://fabrinat-omega.vercel.app'

const FALLBACK_PROVIDERS = [
  { id: 'fabrient-mcp', name: 'Fabrient MCP', description: 'Authenticated engineering tools for geometry, evidence, manufacturing, and release workflows.', auth: 'oauth', endpoint: 'https://fabrient-mcp.onrender.com/mcp', docs: `${PUBLIC_WEB_URL}/integrations`, configured: true, kind: 'mcp_server' },
  { id: 'cad-import', name: 'CAD / STEP import', description: 'Bring existing STEP and CAD artifacts into a Fabrient engineering job.', auth: 'none', endpoint: '/import', docs: `${PUBLIC_WEB_URL}/import`, configured: true, kind: 'engineering_artifact' },
  { id: 'measurement-evidence', name: 'Measurement evidence', description: 'Attach inspection records, images, units, provenance, and physical observations to a project.', auth: 'none', endpoint: '/records', docs: `${PUBLIC_WEB_URL}/records`, configured: true, kind: 'evidence' },
  { id: 'manufacturing-release', name: 'Manufacturing release', description: 'Prepare build guidance, manufacturing notes, inspection planning, and validated release packages.', auth: 'none', endpoint: '/records', docs: `${PUBLIC_WEB_URL}/records`, configured: true, kind: 'manufacturing' },
]

const FALLBACK_TOOLS = [
  { provider: 'Fabrient MCP', name: 'inspect_geometry', description: 'Inspect CAD geometry, dimensions, openings, bosses, and topology.' },
  { provider: 'Fabrient MCP', name: 'analyze_clearance', description: 'Check fit and clearance against a board, assembly, or requirement.' },
  { provider: 'Fabrient MCP', name: 'run_dfm_check', description: 'Run deterministic design-for-manufacture checks and return findings.' },
  { provider: 'Fabrient MCP', name: 'modify_within_bounds', description: 'Apply a bounded engineering change without silently changing protected intent.' },
  { provider: 'Fabrient MCP', name: 'verify_geometry', description: 'Re-run geometry and tolerance checks after a proposed or approved change.' },
]

export async function GET(req: NextRequest, { params }: { params: Promise<{ action: string }> }) {
  const { action } = await params
  const url = new URL(`${API}/integrations/${action}`)
  req.nextUrl.searchParams.forEach((value, key) => url.searchParams.set(key, value))
  return forward(url, { method: 'GET' }, action, req.nextUrl.searchParams.get('query') || '', req)
}

export async function POST(req: NextRequest, { params }: { params: Promise<{ action: string }> }) {
  const { action } = await params
  const body = await req.text()
  return forward(new URL(`${API}/integrations/${action}`), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body }, action, '', req)
}

async function forward(url: URL, init: RequestInit, action: string, query: string, req: NextRequest) {
  try {
    const headers = new Headers(init.headers)
    const cookie = req.headers.get('cookie')
    const authorization = req.headers.get('authorization')
    if (cookie) headers.set('cookie', cookie)
    if (authorization) headers.set('authorization', authorization)
    const response = await fetch(url, { ...init, headers, cache: 'no-store' })
    const text = await response.text()
    return new NextResponse(text, { status: response.status, headers: { 'Content-Type': response.headers.get('content-type') || 'application/json' } })
  } catch {
    if (init.method === 'GET' && action === 'search') {
      const needle = query.trim().toLowerCase()
      const results = needle ? FALLBACK_PROVIDERS.filter((item) => `${item.name} ${item.description} ${item.kind}`.toLowerCase().includes(needle)) : FALLBACK_PROVIDERS
      return NextResponse.json({ results, source: 'local-fallback' })
    }
    if (init.method === 'GET' && action === 'search-tools') {
      const needle = query.trim().toLowerCase()
      const tools = needle ? FALLBACK_TOOLS.filter((item) => `${item.name} ${item.description}`.toLowerCase().includes(needle)) : FALLBACK_TOOLS
      return NextResponse.json({ tools, source: 'local-fallback' })
    }
    return NextResponse.json({ detail: 'Fabrient engineering API is unavailable' }, { status: 503 })
  }
}
