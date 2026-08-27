# Render live findings — 27 August 2026

Source: https://dashboard.render.com/web/srv-da2prmjl550s73cct8k0/deploys/dep-da86evuk1f9s73ceb21g

The authenticated Render dashboard shows service `fabrient-engineering` at https://fabrient-engineering.onrender.com. The environment editor accepted a managed same-region datastore URL reference for `DATABASE_URL` using the existing `fabrient-postgres` database, without exposing the credential in this file. Render reported that environment variables were updated and a deploy was triggered.

The resulting deployment for commit `273592700bf1b20327b1b8fbbfd38e2afaf489bb` (`fix: enforce database readiness in production`) is marked failed because Render cancelled the build: `your workspace has run out of build pipeline minutes for the current billing period`. Render explicitly directs the owner to upgrade the workspace plan or increase the build spend limit at https://dashboard.render.com/w/tea-d6ptbvnafjfc73al64q0/settings#build-pipeline. This is an account/billing limitation, not an application build diagnostic.

Before the environment update, the live Vercel OTP request returned HTTP 500 with detail indicating missing `DATABASE_URL` in the engineering route. The Vercel production release workflow was green on commit `5b724d9`; the production browser, CI, full acceptance, MCP 100-tool, and Render backend workflows were also green. A bounded OTP proxy timeout was committed as `d94939e` and rebased/pushed as `5b724d9`.

Do not mark real OTP delivery complete until a successful Render deploy after the datastore binding and a real code delivery/verification are observed.
