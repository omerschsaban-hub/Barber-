# Uploaded video checklist — implementation record

This record maps the two uploaded videos to Fabrient. It separates things we can fix in code from things that require an external deployment decision.

## Video 1 — security

### Security bullets shown before the full checklist

1. **Keep keys and secrets on the server.** Fabrient uses server-side environment variables for private credentials; browser metadata is limited to intentionally public values.
2. **Keep secrets out of Git history.** `.env` files and variants are ignored. A committed secret is not made safe by deleting it later; any historical secret would need rotation.
3. **Turn on row-level security for every database table.** Fabrient's production architecture is owned PostgreSQL rather than Supabase. The equivalent control is enforced at the server boundary with authenticated identity, organization/project membership, and owner-scoped queries. We do not claim PostgreSQL RLS exists where it does not.
4. **Confirm each user can only reach their own records, not merely that they are logged in.** Artifact access is owner-scoped and workspace/project routes require membership/authorization.
5. **Rate-limit the API, especially login and anything that costs money per call.** Browser mutations, OTP requests/verifications, and paid LLM usage have server-side limits.
6. **Set billing caps and alerts on every paid service.** LLM runs have hard plan caps. Payment state is resolved server-side. Provider-wide monetary alerts still require the billing/provider console and its external configuration; the application must not claim those are configured without proof.
7. **Use parameterized queries so user input cannot become a command.** Core owned-auth, artifact, billing, and workspace SQL uses parameterized queries rather than string interpolation.

### Full-checklist items visibly shown in the clip

- Server-side secrets: implemented.
- Secrets out of Git history: repository hygiene is implemented; historical-secret scanning/rotation is an operational requirement.
- Sensitive-data encryption: implemented for persisted integration OAuth secrets with AES-256-GCM; transient bearer credentials are not persisted by the connection-test route.
- Server authentication: implemented with expiring, revocable sessions and server-side identity checks.

## Video 2 — SEO / production quality

Visible requirements and current treatment:

1. **Connect a custom domain** — code is domain-ready through `NEXT_PUBLIC_FABRIENT_WEB_URL`; DNS/domain ownership is external. We will not pretend a domain is connected before it is actually owned and configured.
2. **Meta descriptions** — implemented for public pages.
3. **Custom 404 page** — implemented in `app/not-found.tsx`.
4. **Proper page sources** — public homepage is server-rendered through the Next App Router; no Vite browser app is used.
5. **Unique page titles** — root and changelog use distinct titles with a shared title template.
6. **Canonical tags** — root and changelog declare canonical URLs based on the configured site origin.
7. **Unique headings per page** — public pages have a single primary H1.
8. **Structured data** — Organization and WebSite JSON-LD are emitted. LocalBusiness markup is deliberately not added because Fabrient is not a local business; fake schema would be misleading.
9. **robots.txt** — implemented with private-route exclusions.
10. **sitemap.xml** — implemented for public pages.
11. **Favicon** — existing `app/icon.svg` is explicitly wired into metadata.
12. **Internal links** — real Next links are used across the public surfaces and global navigation.
13. **Breadcrumbs** — accessible breadcrumbs added to the changelog secondary public page.
14. **Local business schema** — intentionally rejected as inapplicable.
15. **Social share images** — branded Open Graph and Twitter image routes added.
16. **Alt text on images** — landing-page image has descriptive alt text; the static audit checks visible landing imagery.
17. **Fix console errors** — Playwright now fails public-page tests on browser console errors and page errors.
18. **Remove production source maps** — explicitly disabled in `next.config.mjs`.
19. **llms.txt** — implemented as a public machine-readable route while excluding private application surfaces.
20. **Remove placeholder text** — obvious placeholder marketing text is rejected by the static audit.
21. **Reduce huge JS bundles** — the homepage remains server-rendered and does not import the heavy Three.js stack. Next route splitting keeps 3D code off the homepage bundle.
22. **Remove Vite + React from the browser** — the web product is already a Next.js/React application, so React is required. There is no root Vite browser application or Vite production dependency; Vite seen in the lockfile is a test-tool dependency of Vitest, not the browser app.

## Release gate

Run:

```bash
npm run audit:videos
npm run lint
npm run build
npm run test:e2e
```

A static pass is not proof of production behavior. Production URL checks still need to pass after deployment.
