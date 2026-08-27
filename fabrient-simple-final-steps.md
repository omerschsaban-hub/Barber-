# Fabrient: simple final steps

## What is already done

The code is on `main` at commit `5ee86c0481a0a9a45473ebceca5e4b08ba226661`.

The following checks passed on the latest commit: Render backend validation, engineering smoke tests, MCP 100-tool surface acceptance, MCP production auth-wrapper check, acceptance artifacts, and video hardening. Local owned-auth tests passed, and the owned MCP registry has exactly 100 unique tools. Supabase has not been deleted.

The live engineering health URL is `https://fabrient-engineering.onrender.com/health` and currently returns HTTP 200. The live MCP wrapper health URL is `https://fabrient-mcp.onrender.com/health` and currently reports `tool_count: 100` and HTTP 200. The live MCP endpoint correctly requires authorization: its current anonymous request returns HTTP 401.

## Important: do not delete Supabase yet

Leave the Supabase project running. The live MCP service is still advertising old Supabase OAuth metadata. This means the new Render image or its environment variables have not finished switching to owned OAuth. Do not call the migration complete until the issuer no longer contains `supabase.co`.

## Step 1: open the GitHub repository

1. Open `https://github.com/omerschsaban-hub/Barber-`.
2. Click **Settings**.
3. Click **Secrets and variables**.
4. Click **Actions**.

## Step 2: add the two GitHub Actions secrets

Create these two repository secrets. Do not paste them into source code.

| Secret name | What to put there |
| --- | --- |
| `FABRIENT_WEB_URL` | The real deployed Fabrient web URL, including `https://`, with no trailing slash. Use the Vercel production URL or the attached `getfabrient.com` domain only after opening it in a browser and confirming it is the real app. |
| `FABRIENT_MCP_AUTH_TOKEN` | A valid bearer token accepted by the live MCP wrapper, with the required `mcp:use` scope. |

The browser acceptance job is currently blocked only because `FABRIENT_WEB_URL` is empty. The deployed MCP smoke test is currently blocked by HTTP 401 because `FABRIENT_MCP_AUTH_TOKEN` is empty or not accepted.

## Step 3: update Render environment variables

1. Open the Render dashboard.
2. Open the **fabrient-mcp** service.
3. Open **Environment**.
4. Set `FABRIENT_MCP_OAUTH_ISSUER` to the final owned MCP OAuth issuer URL.
5. Set `FABRIENT_MCP_RESOURCE_URL` to `https://fabrient-mcp.onrender.com/mcp`.
6. Confirm the service is using the Dockerfile at `services/mcp/Dockerfile` and the owned auth wrapper entrypoint.
7. Click **Save changes**.
8. Click **Manual Deploy** and choose the latest commit from `main`: `5ee86c0`.
9. Wait until Render says **Live**.

Keep these variables server-side. Never put them in a `NEXT_PUBLIC_*` variable.

## Step 4: update the engineering service variables

Open the **fabrient-engineering** Render service and confirm these variables exist:

| Variable | Required value |
| --- | --- |
| `DATABASE_URL` | Owned PostgreSQL connection string with TLS enabled. |
| `AUTH_SECRET` | At least 32 random bytes. Do not use the example text. |
| `GMAIL_SENDER` | The Gmail address that sends OTP messages. |
| `GMAIL_CLIENT_ID` | Gmail OAuth client ID. |
| `GMAIL_CLIENT_SECRET` | Gmail OAuth client secret. |
| `GMAIL_REFRESH_TOKEN` | Gmail OAuth refresh token for the sender. |
| `REVENUECAT_SECRET_API_KEY` | RevenueCat server secret API key. |
| `REVENUECAT_WEBHOOK_AUTH` | The exact authorization value configured in RevenueCat. |
| `REVENUECAT_WEBHOOK_SIGNING_SECRET` | RevenueCat webhook signing secret. |
| `FABRIENT_ALLOWED_ORIGINS` | The real web URL from Step 2, comma-separated if there is more than one. |
| `FABRIENT_MCP_OAUTH_ISSUER` | The same owned issuer URL used by the MCP service. |
| `FABRIENT_MCP_RESOURCE_URL` | `https://fabrient-mcp.onrender.com/mcp`. |

Save the changes and manually deploy commit `5ee86c0` if Render does not auto-deploy it.

## Step 5: verify the old Supabase OAuth metadata is gone

After the MCP service is Live, open:

`https://fabrient-mcp.onrender.com/.well-known/oauth-authorization-server`

The JSON field named `issuer` must not contain `supabase.co`. If it still contains `supabase.co`, repeat Step 3 and check the Render deploy log for the actual image and environment values.

## Step 6: test Gmail OTP in the browser

1. Open the real URL stored in `FABRIENT_WEB_URL`.
2. Sign out first.
3. Enter a real Gmail address that you control.
4. Click **Send code**.
5. Open Gmail and find the new Fabrient OTP email.
6. Enter the newest six-digit code.
7. Confirm the app shows the signed-in workspace.
8. Sign out.
9. Try the old code again. It must fail.
10. Try an invalid email. It must be rejected.

If no email arrives, check `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`, `GMAIL_SENDER`, Gmail API permission, and Render logs. Do not mark authentication as passing from a mock email.

## Step 7: test RevenueCat sandbox billing

1. Open the RevenueCat dashboard.
2. Confirm the current offering is active.
3. Confirm the monthly and yearly products are attached to that offering.
4. Confirm the Pro entitlement identifier exactly matches the backend configuration.
5. Open the Fabrient app while signed in with the Gmail OTP account.
6. Open Billing.
7. Start a sandbox purchase using a test-store account.
8. Confirm the purchase completes.
9. Wait for the RevenueCat webhook.
10. Refresh Fabrient Billing.
11. Confirm Pro access comes from the backend entitlement state.
12. Test restore, cancellation, expiration, duplicate webhook delivery, and a forged webhook signature.

Do not mark payments as passing from catalog inspection alone. A real sandbox purchase and a signed webhook are required.

## Step 8: run the final checks

From the repository root, run:

```bash
curl -fsS --max-time 30 https://fabrient-engineering.onrender.com/health
curl -fsS --max-time 30 https://fabrient-mcp.onrender.com/health
MCP_URL=https://fabrient-mcp.onrender.com/mcp FABRIENT_MCP_AUTH_TOKEN='PASTE_VALID_TOKEN_ONLY_IN_YOUR_TERMINAL' python services/mcp/smoke_test.py
```

Then open GitHub Actions and confirm the workflows for commit `5ee86c0` are green. The production browser test must use the real `FABRIENT_WEB_URL`; the deployed MCP test must use a valid token with `mcp:use`.

## Completion rule

The migration is complete only when all of these are true: the MCP issuer no longer references Supabase, real Gmail OTP delivery works, a real RevenueCat sandbox purchase produces a signed webhook and backend entitlement, the 100-tool MCP smoke test passes with authorization, and the production browser acceptance test passes.

Keep Supabase available until all five conditions are green. After that, take a separate backup and decommissioning decision; do not delete it as part of this handoff.
## Reusable skill

The reusable verifier is available at `/home/ubuntu/skills/fabrient-migration-verifier/SKILL.md`. It records the migration workflow, auth and billing evidence rules, MCP contract checks, deployment probes, and the rule that provider-dependent gates must never be called PASS from mocks.

## Latest remaining blockers

At the latest check, `FABRIENT_WEB_URL` was missing from GitHub Actions, the deployed MCP endpoint returned HTTP 401 because the authenticated smoke token was not configured, and the live MCP discovery issuer still returned the legacy Supabase URL. These are deployment/account configuration items, not claims of successful Gmail or payment execution.

The GitHub and Render dashboards are the only places where these secret values should be entered. Never send the secret values in chat.

## Done

When Steps 1–8 are complete, send back only: `DONE — all green`.
Use `NOT DONE` if any step is still red or blocked.

Do not delete Supabase until the completion rule is satisfied.

---

## Exact commands used for the last local proof

```bash
PYTHONPATH=. python -c "import mcp_server; assert len(mcp_server.CAPABILITY_NAMES)==100; assert len(set(mcp_server.CAPABILITY_NAMES))==100"
PYTHONPATH=engineering:. python -m pytest -q engineering/tests/test_owned_auth.py tests/unit tests/mcp tests/owned-platform
ruff check engineering services/mcp tests
```

Latest local result: `9 passed, 100 skipped` for the focused contract set, with Ruff clean. Provider-dependent Gmail and RevenueCat purchase tests remain intentionally unclaimed until run against the configured live services.

Supabase remains intact by design.

---

## Exact production URLs

| Purpose | URL |
| --- | --- |
| Engineering health | `https://fabrient-engineering.onrender.com/health` |
| MCP health | `https://fabrient-mcp.onrender.com/health` |
| MCP endpoint | `https://fabrient-mcp.onrender.com/mcp` |
| MCP OAuth discovery | `https://fabrient-mcp.onrender.com/.well-known/oauth-authorization-server` |
| GitHub repository | `https://github.com/omerschsaban-hub/Barber-` |
| Intended canonical web hostname | `https://getfabrient.com` — verify that hosting is attached before using it as the production URL |

Do not assume the intended canonical hostname is live just because it appears in application metadata.

---

## Security reminders

Use HTTPS. Keep `DATABASE_URL`, `AUTH_SECRET`, Gmail credentials, RevenueCat credentials, OAuth issuer settings, and the MCP bearer token out of browser JavaScript and out of chat. Keep session tokens in HttpOnly cookies. Do not disable authorization to make a test pass. A 401 from the protected MCP endpoint proves enforcement and reachability; it does not prove that authenticated execution works.

The migration verifier has already been created as a reusable skill, and this document is the child-simple final checklist for the remaining account-side actions.
