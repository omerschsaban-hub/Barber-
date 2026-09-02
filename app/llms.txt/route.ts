import { NextResponse } from 'next/server'

const SITE = process.env.NEXT_PUBLIC_FABRIENT_WEB_URL || 'https://fabrinat-omega.vercel.app'

export function GET() {
  const body = `# Fabrient\n\n> Fabrient connects physical-product intent, CAD, deterministic engineering, build preparation, measurement, learning, and release evidence.\n\n## Public pages\n- Home: ${SITE}/\n- Changelog: ${SITE}/changelog\n\n## Product principles\n- Engineering rules and measured evidence are kept separate from model suggestions.\n- Fabrient does not invent measurements or silently change tolerances.\n- Important geometry and physical-experiment actions require appropriate validation or human approval.\n- MCP and the web app use the same authenticated engineering backend.\n\n## Scope\nThe public website describes product capabilities and principles. Authenticated workspaces, projects, engineering APIs, billing, integrations, and private artifacts are not public documentation.\n`
  return new NextResponse(body, { headers: { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'public, max-age=3600' } })
}
