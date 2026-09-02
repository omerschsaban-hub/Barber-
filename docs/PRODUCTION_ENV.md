# Fabrient production environment

This document is the environment-variable contract for the current Render/Vercel architecture. Secret values are intentionally not stored in Git.

## Render: shared PostgreSQL

`DATABASE_URL` — **required** on Engineering and MCP. It must be the connection string for the existing shared Fabrient PostgreSQL database and must use TLS. Do not paste the value into source control.

## Render: Engineering

Required:

- `DATABASE_URL` — shared PostgreSQL connection string.
- `AUTH_SECRET` — required; at least 32 bytes of high-entropy secret material. The same value must be used by services that verify the same owned-session/API-key tokens.

Billing/integrations when those features are enabled:

- `PAYPAL_CLIENT_ID`
- `PAYPAL_CLIENT_SECRET`
- `PAYPAL_WEBHOOK_ID`
- `PAYPAL_ENVIRONMENT` (`sandbox` or `production`)
- `PAYPAL_HOBBY_PLAN_ID`
- `PAYPAL_STARTUP_PLAN_ID`
- `GMAIL_OAUTH_JSON`
- `DATA_FLYWHEEL_RUN_TOKEN`
- `DATA_FLYWHEEL_INGEST_SECRET`
- `OPENAI_API_KEY` or `OPENROUTER_API_KEY` for LLM enrichment
- `OPENAI_API_BASE` only when using a non-default OpenAI-compatible endpoint

Recommended operational values:

- `DB_POOL_MIN=1`
- `DB_POOL_MAX=4` on the current free Render service; increase only after measuring active connections and upgrading the database/service plan.
- `FLYWHEEL_INTERVAL_SECONDS=1800`
- `FLYWHEEL_ENABLE_PRODUCTION=true` only when production flywheel execution is intentionally enabled.
- `FLYWHEEL_SCHEDULER_ENABLED=true` only when the scheduler is actually deployed and desired.
- `FABRIENT_ALLOWED_ORIGINS=https://fabrinat-omega.vercel.app,https://getfabrient.com,https://www.getfabrient.com`

## Render: MCP

Required:

- `DATABASE_URL` — the same PostgreSQL database as Engineering.
- `AUTH_SECRET` — required by token hashing/verification.

Set explicitly:

- `FABRIENT_ENGINE_URL=https://fabrient-engineering.onrender.com`
- `FABRIENT_WEB_ORIGIN=https://fabrinat-omega.vercel.app` while the Vercel hostname is the active public product hostname.
- `FABRIENT_MCP_OAUTH_ISSUER=https://fabrient-mcp.onrender.com`
- `FABRIENT_MCP_RESOURCE_URL=https://fabrient-mcp.onrender.com/mcp`
- `DB_POOL_MIN=1`
- `DB_POOL_MAX=4`

Optional:

- `FABRIENT_MCP_AUTH_TOKEN` — only for the configured MCP smoke/service token. If used, it is stored hashed in PostgreSQL; never log the plaintext token.
- `FABRIENT_FREE_ENTITLEMENTS`
- `FABRIENT_HOBBYIST_ENTITLEMENTS`
- `FABRIENT_HOBBYIST_PRODUCT_IDS`
- `FABRIENT_STARTUP_ENTITLEMENTS`
- `FABRIENT_STARTUP_PRODUCT_IDS`
- `FABRIENT_ENTERPRISE_ENTITLEMENTS`
- `FABRIENT_ENTERPRISE_PRODUCT_IDS`

## Vercel: browser-visible variables

Only values safe to expose to browser JavaScript may use the `NEXT_PUBLIC_` prefix.

Current public-host configuration:

- `NEXT_PUBLIC_FABRIENT_WEB_URL=https://fabrinat-omega.vercel.app`
- `NEXT_PUBLIC_FABRIENT_ENGINEERING_API=https://fabrient-engineering.onrender.com` when the browser directly needs the Engineering API.

Never put these in `NEXT_PUBLIC_*`:

- `DATABASE_URL`
- `AUTH_SECRET`
- `OPENAI_API_KEY`
- `OPENROUTER_API_KEY`
- PayPal secrets
- Gmail OAuth credentials
- flywheel run/ingest secrets
- integration encryption keys
- MCP service tokens

## Important infrastructure warning

The live Render PostgreSQL instance is currently on the free plan and has an expiration date in the Render account. That is not an acceptable long-term production database posture. Before real customer data is trusted, upgrade/migrate to a persistent paid PostgreSQL plan and perform a tested restore.

Also note that `render.yaml` currently describes a different Docker/blueprint topology than the already-created live Render services. Do not apply that blueprint blindly: it can create a separate database instead of adopting the existing database. Infrastructure reconciliation must be performed deliberately before using the blueprint as the source of truth.
