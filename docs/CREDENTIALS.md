# Fabrient credential control plane

This document is the **single inventory and ownership map** for Fabrient runtime credentials. It deliberately contains **names, scope, and storage location only** — never secret values.

## Security rule

Do not put API keys, passwords, refresh tokens, private keys, database passwords, webhook signing secrets, or OAuth client secrets in Git, `.env` files committed to the repository, issues, PRs, logs, or screenshots.

The repository is the source of truth for **which credentials exist**. The runtime secret store is the source of truth for **their values**.

For Render, use an environment group as the shared runtime secret store and link only the services that need each variable. Render explicitly recommends environment variables/environment groups for secrets and warns not to commit secret values to `render.yaml`. urlRender environment variables and secrets docshttps://render.com/docs/configure-environment-variables

GitHub Actions should receive only the minimum secrets required by a workflow. Enable secret scanning and push protection so accidental commits are blocked. urlGitHub secret protection docshttps://docs.github.com/en/code-security/how-tos/secure-your-secrets/prevent-future-leaks

## Current deployment inventory

| Variable | Type | Required by | Storage | Notes |
|---|---|---|---|---|
| `DATABASE_URL` | secret | deployed backend / migration tooling | Render environment group | Render Postgres connection string; never expose to browser |
| `NEXT_PUBLIC_SUPABASE_URL` | public config | web + MCP auth compatibility | Render/Vercel env | Current Supabase project URL; safe to expose to the browser |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | public config | web + MCP auth compatibility | Render/Vercel env | Publishable/anon key; not a substitute for service-role credentials |
| `SUPABASE_SERVICE_ROLE_KEY` | secret | only where privileged Supabase compatibility remains | Render secret store / GitHub secret only if a workflow truly needs it | Do not expose client-side |
| `REVENUECAT_PROJECT_ID` | non-secret config | MCP billing checks | Render env | Current RevenueCat project: `projb138a8db` |
| `REVENUECAT_SECRET_API_KEY` | secret | web server + MCP | Render environment group | Server-side RevenueCat API key only |
| `REVENUECAT_WEBHOOK_AUTH` | secret | RevenueCat webhook receiver | Render environment group | Shared authorization value if webhook endpoint uses it |
| `REVENUECAT_WEBHOOK_SIGNING_SECRET` | secret | webhook verification where implemented | Render environment group | Keep separate from webhook authorization |
| `FABRIENT_PRO_ENTITLEMENT` | non-secret config | MCP/web entitlement gate | Render/Vercel env | Current identifier: `create_an_app_called_fabrinat_pro` |
| `FABRIENT_WEB_ORIGIN` | config | backend CORS/auth redirects | Render/Vercel env | Must match deployed frontend origin |
| `FABRIENT_ALLOWED_ORIGINS` | config | backend CORS | Render env | Comma-separated allowed origins |
| `FABRIENT_API_URL` | config | Next.js auth proxy | Vercel env | Backend URL used by `/api/auth/*` on the migration branch |
| `FABRIENT_MCP_URL` | config | clients/integration tests | Vercel/CI env as needed | MCP service URL |
| `FABRIENT_MCP_RESOURCE_URL` | config | MCP OAuth metadata | Render env | Canonical protected MCP resource URL |
| `FABRIENT_MCP_OAUTH_ISSUER` | config | MCP OAuth metadata | Render env | Canonical authorization-server issuer |
| `FABRIENT_ENTERPRISE_DOMAINS` | config | MCP account segmentation | Render env | Optional comma-separated domains |
| `FABRIENT_STARTUP_DOMAINS` | config | MCP account segmentation | Render env | Optional comma-separated domains |
| `FABRIENT_MCP_REQUESTS_PER_MINUTE` | config | MCP rate limiting | Render env | Defaults to 120 if omitted |
| `DB_POOL_MIN` | config | backend DB pool | Render env | Current migration default: 1 |
| `DB_POOL_MAX` | config | backend DB pool | Render env | Current migration default: 8 |
| `AUTH_SECRET` | secret | migration-branch auth/session code if still referenced | Render environment group | Rotate if exposed; must be long/random |
| `OPENAI_API_KEY` | secret | server-side AI integrations, only if enabled | Render environment group | Never prefix with `NEXT_PUBLIC_` |
| `OPENAI_MODEL` | config | AI integrations | Render env | Current default: `gpt-5.6` |
| `DATA_FLYWHEEL_RUN_TOKEN` | secret | flywheel cron/worker if enabled | Render environment group | Separate from user/session credentials |
| `FLYWHEEL_ENABLE_PRODUCTION` | config | flywheel worker | Render env | Keep `false` until production flywheel gate is explicitly passed |

## Credentials intentionally removed from the new canonical set

### Gmail OAuth inbox credentials

The product contract says Fabrient uses Gmail only as the user's email destination for OTP and **does not request Gmail inbox access**. Therefore these legacy variables are not part of the canonical credential set:

- `GMAIL_CLIENT_ID`
- `GMAIL_CLIENT_SECRET`
- `GMAIL_REFRESH_TOKEN`

The current OTP flow is through the authentication provider's email OTP endpoint. Do not reintroduce Gmail inbox OAuth just to send or read OTP mail.

`GMAIL_SENDER` is also not a secret. If an SMTP provider is configured for the auth service, its sender identity belongs in the provider/auth configuration, not as a Gmail OAuth credential bundle in the application.

## Public vs secret RevenueCat values

The mobile SDK public key and hosted purchase URLs may be client-visible. Server-side RevenueCat API keys and webhook secrets are not. The codebase already distinguishes the server-side `REVENUECAT_SECRET_API_KEY` from public purchase/SDK configuration.

## Environment separation

Use separate values for:

- **staging** — migration branch, staging Render services, preview frontend
- **production** — production Render services, production Vercel project

Never point staging at production credentials unless the test explicitly requires it and the blast radius is understood.

The Render deployment currently contains a dedicated `fabrient-migration-staging` service and a Render Postgres instance named `fabrient-postgres`; this is the intended migration validation boundary.

## Required GitHub Actions secrets

Only create these if the corresponding workflow is retained/enabled:

- `FABRIENT_WEB_URL` — production browser acceptance target
- `SUPABASE_ACCESS_TOKEN` — only for the legacy Supabase migration workflow while Supabase remains intentionally active
- `SUPABASE_DB_PASSWORD` — only for that legacy workflow

The migration is **not allowed to delete Supabase yet**. Before the legacy migration workflow is changed or removed, its project reference must be reconciled with the currently connected Supabase project.

## Rotation policy

If any secret may have been exposed, rotate it at the provider first, then update the runtime store, redeploy affected services, and rerun the relevant acceptance gate. Do not merely rename the environment variable.

## Verification policy

A credential is considered configured only when the application performs a real provider operation successfully. Presence of an environment variable, a green build, or a health endpoint is not enough.

For the migration DB gate, the required evidence remains:

**deployed service → authenticated DB connection → real write → read-back → cleanup/rollback evidence**

Until that chain is observed, the DB gate remains unpassed.
