
The new MCP deployment no longer fails on missing DATABASE_URL. It reaches the owned PostgreSQL host at `10.192.222.62:5432`, but the current copied credential is rejected with `FATAL: password authentication failed for user fabrient_postgres_cdcb_user`. The safe next step is to refresh/copy the current Internal Database URL again; credential rotation is not being performed automatically.

The refreshed database page confirms the same available owned database and the current connection section. No credential rotation has been initiated; only a fresh copy of the current Internal Database URL is being attempted before considering any destructive credential change.

The refreshed PostgreSQL page still shows the owned database as available. The connection section is now in view; the next step is to reveal Username/Password/Internal Database URL and copy the current URL again without rotating credentials.

After the second redeploy, the MCP service still returns 500 on authenticated `/mcp` requests. Current Render logs at `https://dashboard.render.com/web/srv-da2qfue7bikc73bi2ccg/logs?t=app&r=1h` show `FATAL: password authentication failed for user "fabrient_postgres_cdcb_user"` while connecting to the owned PostgreSQL host. Health and OAuth discovery remain live. The next required account action is to create/rotate a valid PostgreSQL credential in Render, copy the resulting Internal Database URL into MCP, redeploy, and rerun the smoke test. This is not a source-code defect.

Credential rotation is confirmed by the user. The refreshed Render database page shows the database is available and the credential-rotation section is present; no rotation has yet been submitted.

The Render database page remains available and the credential-rotation controls are further below the connection section. User has explicitly confirmed rotating the default credential; the database itself will remain intact.


## Latest verification evidence (2026-08-27)

Source: `https://fabrient-mcp.onrender.com/health`

- Live health is HTTP 200 and advertises `tool_count: 100`.
- The live service identifies as `fabrient-mcp-auth-wrapper`.

Source: `https://dashboard.render.com/web/srv-da2qfue7bikc73bi2ccg/logs?t=app&r=1h`

- The owned PostgreSQL schema bootstrap now logs `owned PostgreSQL schema migration applied` during startup.
- The current authenticated request reaches the MCP SDK, so the prior database, missing-table, and 401 failures are no longer the active blocker.
- The remaining failure is HTTP 500 on `POST /mcp`: `RuntimeError: Task group is not initialized. Make sure to use run().` from MCP SDK 1.13.1 `streamable_http_manager.py`.

Recent main commits involved in this repair: `b6dedef`, `bfd7f01`, `5a35fd7`, `974c91b`, `8f8377d`, `0c5652e`, `a54212d`, `fa29136`. The latest package-local import fix is pushed to `main` as `fa29136` after rebasing onto remote commit `55b7a3c`.

## Vercel production finding — Aug 27, 2026

The connected Vercel project `fabrinat` had framework preset `Services`, while the repository is a Next.js application. The current production deployment `fabrinat-omega.vercel.app` was READY but returned an empty document. The project dashboard showed source commit `21cc1f1`; project ID `prj_LIY1jgw08lNkn26vQTEcVbwezinG`. I changed the Project Settings framework preset to `Next.js`; the remaining action is to persist the framework settings and redeploy/verify the live URL. The latest GitHub main commit is `21cc1f1` or newer, with CI, MCP 100-tool acceptance, backend tests, and full acceptance passing; browser/release failures were tied to stale/misconfigured production rendering and duplicate CTA selectors.

Sources: Vercel project dashboard and Build and Deployment settings viewed in the connected browser; GitHub Actions runs 33064407878, 33064407933, 33064407931, and 33064408029.

## Pricing and owned-stack requirements

The product implementation includes Free, Hobby ($9 individual), Startup ($49 for 1–29 people), and Enterprise (contact via 0509220082 and omerschsaban@gmail.com), with plan and LLM usage gating in engineering/app/plan_catalog.py and billing authority in engineering/app/billing.py.

## Live MCP state

Render MCP health is passing, owned PostgreSQL schema bootstrap executes, OAuth metadata is owned, and the authenticated 100-tool surface acceptance workflow passes. Historical live failures were repaired through database credential correction, AUTH_SECRET provisioning, token seeding, and MCP lifespan/app-wrapper fixes.
