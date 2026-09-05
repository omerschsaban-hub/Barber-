#!/usr/bin/env node

import fs from 'node:fs'
import path from 'node:path'

const root = process.cwd()
const read = (p) => fs.readFileSync(path.join(root, p), 'utf8')
const exists = (p) => fs.existsSync(path.join(root, p))

const checks = []
function check(name, pass, detail) {
  checks.push({ name, pass: Boolean(pass), detail })
}

const middleware = exists('middleware.ts') ? read('middleware.ts') : ''
const engine = exists('services/engine/main.py') ? read('services/engine/main.py') : ''
const landing = exists('app/page.tsx') ? read('app/page.tsx') : ''
const videoRoute = exists('app/api/demo-video/route.ts') ? read('app/api/demo-video/route.ts') : ''

check('HSTS', /Strict-Transport-Security/.test(middleware), 'production middleware must emit HSTS')
check('MIME sniffing protection', /X-Content-Type-Options/.test(middleware), 'nosniff header must exist')
check('Clickjacking protection', /X-Frame-Options/.test(middleware) && /frame-ancestors/.test(middleware), 'frame protections must exist')
check('CSRF same-origin gate', /Cross-site request blocked/.test(middleware) && /sameOrigin/.test(middleware), 'cookie-authenticated mutations need an origin check')
check('API rate limiting', /(RATE_LIMIT|mutationLimit)/.test(middleware) && /Too many requests/.test(middleware), 'mutating API calls need a server-side throttle')
check('Request size gate', /MAX_JSON_BODY_BYTES/.test(engine), 'engineering JSON requests need a hard limit')
check('Engineering CORS allowlist', /FABRIENT_ALLOWED_ORIGINS/.test(engine) && !/allow_origins=\["\*"\]/.test(engine), 'production wrapper must not expose wildcard CORS')
check('Auth-protected product routes', (/createServerClient/.test(middleware) && /getUser/.test(middleware)) || (/fabrient_session/.test(middleware) && /auth\/me/.test(middleware)) || /ARCHIVED_UI_PREFIXES/.test(middleware), 'active protected routes must verify the server-side user; archived UI routes may be explicitly redirected')
check('No fake testimonials', !/testimonial|customer quote|"Sarah Chen"/i.test(landing), 'public landing page must not invent social proof')
check('No vanity counters', !/\b[0-9][0-9,]+\s*(customers|users|projects|teams)\b/i.test(landing), 'public claims must not invent usage numbers')
check('No emoji-as-icons', !/✨|🚀|🔥|💡|⭐/.test(landing), 'avoid generic emoji decoration')
check('Human copy', !/in conclusion|leverage|delve into|unlock the power of/i.test(landing), 'avoid generic assistant phrasing')
check('First-party video URL', /DEMO_VIDEO_URL\s*=\s*['"]\/api\/demo-video['"]/.test(landing), 'landing page must use the server video endpoint')
check('Native video element', /<video[\s\S]*<source src=\{DEMO_VIDEO_URL\} type="video\/mp4"/.test(landing) && !/<iframe[\s\S]*DEMO_VIDEO_URL/.test(landing), 'use the browser video element rather than embedding an external player')
check('Manus CDN configured', /files\.manuscdn\.com/i.test(videoRoute), 'demo video endpoint must proxy the configured Manus CDN source')
check('Manus CDN range forwarding', /headers\.Range\s*=\s*range/.test(videoRoute) && /content-range/.test(videoRoute), 'video seeking must forward and return byte-range headers')
check('Upstream media validation', /video\/mp4/.test(videoRoute) && /invalid media type/.test(videoRoute), 'reject upstream responses that are not MP4 media')
check('Video response hardening', /X-Content-Type-Options/.test(videoRoute) && /Accept-Ranges/.test(videoRoute), 'proxied video must retain response hardening headers')

const failures = checks.filter((x) => !x.pass)
for (const item of checks) console.log(`${item.pass ? 'PASS' : 'FAIL'}  ${item.name} — ${item.detail}`)
console.log(`\n${checks.length - failures.length}/${checks.length} static checks passed.`)

process.exitCode = failures.length ? 1 : 0
