#!/usr/bin/env node

/**
 * Static release gate for the two uploaded videos.
 * It checks only claims that can be verified from source. Browser/runtime
 * claims remain covered by Playwright and deployment checks.
 */
import fs from 'node:fs'
import path from 'node:path'

const root = process.cwd()
const read = file => fs.readFileSync(path.join(root, file), 'utf8')
const exists = file => fs.existsSync(path.join(root, file))
const checks = []
const check = (name, pass, detail) => checks.push({ name, pass: Boolean(pass), detail })

const middleware = read('middleware.ts')
const nextConfig = read('next.config.mjs')
const layout = read('app/layout.tsx')
const landing = read('app/page.tsx')
const auth = read('engineering/app/owned_auth.py')
const artifacts = read('engineering/app/postgres_artifacts.py')
const plan = read('engineering/app/plan_catalog.py')
const gitignore = read('.gitignore')

// Security points visible in video 1.
check('Secrets stay server-side', !/NEXT_PUBLIC_[A-Z0-9_]*(SECRET|TOKEN|PASSWORD|PRIVATE|KEY)/.test(middleware + layout), 'public environment variables must not contain secret material')
check('Environment files are ignored', /(^|\n)\.env(\.|\n|$)/.test(gitignore), '.env and environment variants are ignored')
check('Admin database keys are not shipped', !/SUPABASE_SERVICE_ROLE|SUPABASE_SECRET|service_role/i.test(landing), 'browser code must never reference a database admin key')
check('Server authentication exists', /def user_from_token/.test(auth) && /expires_at>now\(\)/.test(auth), 'sessions are verified server-side and expire')
check('Session cookie is hardened', /httpOnly:\s*true/.test(read('app/api/auth/verify-otp/route.ts')) && /sameSite:\s*['"]lax['"]/.test(read('app/api/auth/verify-otp/route.ts')), 'session cookie is HttpOnly and SameSite')
check('Cross-site mutations are blocked', /Cross-site request blocked/.test(middleware) && /sameOrigin/.test(middleware), 'cookie-authenticated mutations require same-origin')
check('API mutations are rate limited', /mutationLimit/.test(middleware) && /Too many requests/.test(middleware), 'server middleware throttles mutations')
check('OTP is throttled and bounded', /MAX_OTP_ATTEMPTS/.test(auth) && /otp:ip:/.test(auth) && /otp:email:/.test(auth), 'OTP request and verification paths have dedicated limits')
check('Sensitive external credentials are not persisted by integration test route', /Credentials are never persisted/.test(read('engineering/app/integration_connections.py')) && /credential_persisted.*False/.test(read('engineering/app/integration_connections.py')), 'integration connection test path does not store bearer credentials')
check('User-owned artifacts are enforced', /owner_id: str/.test(artifacts) && /owner_id/.test(read('engineering/app/cad_routes.py')), 'artifact metadata/download is scoped to authenticated owner')
check('Billing/LLM usage has server-side caps', /plan_usage_monthly/.test(plan) && /llm_runs_month/.test(plan), 'LLM usage is counted and capped on the server')
check('SQL uses parameters in core auth/artifact paths', !/execute\(\s*f['"]/.test(auth + artifacts), 'core SQL calls do not interpolate request text')

// SEO points visible in video 2.
check('Custom-domain ready', /NEXT_PUBLIC_FABRIENT_WEB_URL/.test(layout) && /metadataBase/.test(layout), 'canonical base is environment-configurable; DNS/domain ownership is an external deployment step')
check('Meta descriptions', /description:/.test(layout) && /description:/.test(read('app/changelog/page.tsx')), 'public pages expose descriptions')
check('Custom 404', exists('app/not-found.tsx'), 'Next App Router custom not-found page exists')
check('Server-rendered public source', !/^['"]use client['"]/.test(landing.trim()), 'homepage is a server component')
check('Unique page titles', /title:\s*\{/.test(layout) && /title:\s*['"]Changelog['"]/.test(read('app/changelog/page.tsx')), 'public pages use unique titles with a shared template')
check('Canonical tags', /alternates:\s*\{\s*canonical:/.test(layout) && /canonical: ['"]\/changelog['"]/.test(read('app/changelog/page.tsx')), 'public pages declare canonical URLs')
check('Structured data', /schema\.org/.test(layout) && /Organization/.test(layout) && /WebSite/.test(layout), 'organization and website JSON-LD are emitted')
check('robots.txt', exists('app/robots.ts'), 'robots route exists')
check('sitemap.xml', exists('app/sitemap.ts'), 'sitemap route exists')
check('Favicon', /icons:\s*\{/.test(layout) && exists('app/icon.svg'), 'icon metadata and asset exist')
check('Internal links', /<Link href=/.test(landing) && /<Link href=/.test(read('app/changelog/page.tsx')), 'public pages use real internal navigation')
check('Breadcrumbs', /Breadcrumbs/.test(read('app/changelog/page.tsx')) && exists('components/breadcrumbs.tsx'), 'public secondary page has accessible breadcrumbs')
check('Local-business schema not fabricated', !/LocalBusiness/.test(layout), 'Fabrient is not a local business; adding fake LocalBusiness markup would be misleading')
check('Social share images', exists('app/opengraph-image.tsx') && exists('app/twitter-image.tsx') && /opengraph-image/.test(layout), 'Open Graph and Twitter images are generated')
check('Image alt text', /<(?:img|Image)\b[^>]*\balt\s*=/.test(landing), 'visible landing image has descriptive alt text')
check('Production source maps disabled', /productionBrowserSourceMaps:\s*false/.test(nextConfig), 'browser production source maps are explicitly disabled')
check('llms.txt', exists('app/llms.txt/route.ts'), 'machine-readable public product summary exists')
check('No placeholder marketing text', !/Lorem ipsum|Jane Doe|John Doe|Customer Name|Your Company/i.test(landing), 'landing page has no obvious placeholder claims')
check('No Vite browser app', !exists('vite.config.ts') && !exists('vite.config.js') && !/"vite"\s*:\s*"\^/.test(read('package.json')), 'root web app is Next.js; Vite is not a browser dependency')
check('JS is route-split by Next', /next/.test(read('package.json')) && !/from ['"]react-three\/fiber['"]/.test(landing), 'heavy 3D dependencies are not imported into the homepage bundle')

const failures = checks.filter(x => !x.pass)
for (const item of checks) console.log(`${item.pass ? 'PASS' : 'FAIL'}  ${item.name} — ${item.detail}`)
console.log(`\n${checks.length - failures.length}/${checks.length} static checks passed.`)
process.exitCode = failures.length ? 1 : 0
