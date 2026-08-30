# Fabrient Agent Operating Contract

**READ THIS FILE BEFORE EVERY EXECUTION.** This applies to every coding agent, automation agent, MCP implementation agent, reviewer, and maintenance agent working in this repository. Do not start by editing code. First read this file and `docs/PRODUCT_EXECUTION_PRINCIPLES.md`, `docs/DEEP_EXECUTION_STANDARD.md`, and `docs/PRODUCT_SIMPLIFICATION.md`.

## Non-negotiable behavior

1. **Own the outcome.** Do not stop at explanation, code review, or a partial implementation when the task can be executed.
2. **Understand before changing.** Inspect the existing implementation, tests, routes, MCP registry, data model, auth boundaries, payment flows, and deployment assumptions relevant to the task. Do not rebuild systems that already exist.
3. **Human-first, agent-native.** Every important capability must be understandable and usable by a human and composable by an agent.
4. **Complete work.** A successful intermediate API response is not a completed job. Follow the workflow through verification, artifact generation, release, or a truthful actionable blocker.
5. **Evidence over claims.** Never invent measurements, confidence, validation, payment state, or completion. Preserve provenance and deterministic evidence.
6. **Test deeply.** Every execution that changes behavior must run the deepest practical test set: unit tests, MCP contract/registry tests, integration tests, and Playwright browser tests. Test happy paths, invalid inputs, permissions, failure/recovery paths, and important state transitions.
7. **Use the browser.** When UI behavior is involved, use Playwright against a real running app. Do not declare UI work complete from static code inspection alone.
8. **Production browser acceptance is mandatory for release.** Once production is deployed, run the real deployed frontend through Playwright. Do not substitute local browser tests for production acceptance. The production gate must cover blank-page protection, uncaught errors, failed/5xx requests, backend routing, primary user journeys, payment states where applicable, and recovery states.
9. **Simplify aggressively.** Remove duplicate concepts, unnecessary screens, unnecessary configuration, dead code, and features that do not move users toward a verified engineering outcome. Nice-to-haves should be simplified rather than automatically deleted.
10. **Optimize the whole system.** For meaningful changes inspect auth, authorization, DB queries/indexes/RLS, API/MCP latency and failure handling, security, scalability, accessibility, observability, and operational cost.
11. **Automate repeated work.** If an agent encounters the same manual diagnostic, validation, migration, test setup, or release step twice, look for a safe way to turn it into a script, test, tool, or CI check.
12. **Prefer one source of truth.** Do not create parallel registries, duplicate business rules, or separate MCP/UI implementations when a shared domain contract is possible.
13. **Leave the repository better.** Add regression coverage for bugs you fix and update the relevant documentation/skill when the workflow changes.

## Payment provider: PayPal

**PayPal is the intended payment provider for Fabrient.** This instruction establishes the target architecture; it does not claim that the actual PayPal migration is complete.

Target authoritative flow:

**customer → PayPal checkout/subscription → verified server-side PayPal event/webhook → PostgreSQL payment/entitlement state → backend authorization → frontend access**

Payment rules:

- Never grant paid access solely because the browser reached a success/callback URL.
- Verify PayPal webhook/event authenticity server-side using the official verification mechanism used by the implementation.
- Make webhook processing idempotent because providers can retry events.
- Handle failed, cancelled, refunded, and expired states where supported by the chosen PayPal product.
- Keep PayPal secrets, access tokens, signing/webhook secrets, and other credentials server-side.
- Never place a PayPal secret in frontend code or `NEXT_PUBLIC_*` configuration.
- Never invent client IDs, client secrets, webhook IDs, plan IDs, transaction IDs, or payment state.
- PostgreSQL is the application's authoritative entitlement state; PayPal is the external payment source of truth for payment events.
- Do not delete or rename legacy RevenueCat code blindly. Trace every consumer and replace it safely as part of the actual migration.
- Do not mark PayPal integration complete until checkout, webhook verification, persistence, entitlement enforcement, cancellation/failure paths, and security boundaries have been tested.

## Required execution order

**READ → INSPECT → PLAN → IMPLEMENT → TEST → BROWSER VERIFY → HARDEN → SIMPLIFY → AUTOMATE → REPORT**

A report must state what was actually changed, what was actually tested, what failed, and what remains blocked. Never imply deployment or runtime verification that was not performed.

## Required testing commands

- `npm run test:unit`
- `npm run test:e2e`
- `npm run test:deep`
- `npm run test:all` for a release-quality pass
- Python/MCP tests for changed engineering or MCP behavior
- PayPal sandbox tests for changed payment behavior
- Production Playwright acceptance after deployment

If a named command does not exist, inspect the package scripts and use the repository's actual equivalent rather than inventing a passing result.

## Full production acceptance chain

For release-quality work, verify the actual deployed chain:

**human/browser → auth/session → DB → backend → MCP → agent execution → geometry/DFM → fix → verification → manufacturing package → release/acceptance → payment/integrations → error/recovery → browser verification**

Also verify all applicable MCP tools with representative valid/invalid inputs, unit/integration/E2E coverage, storage, realtime, payment/integrations, malformed input handling, security boundaries, performance/timeouts, production configuration, and actual deployed URLs/services.

**Acceptance rule: one critical failure means fix it, redeploy, and rerun the relevant gate and then the full acceptance suite. Green CI alone never means Fabrient works.**

If an environment cannot run a required test, add/retain the test and state the exact environment blocker instead of pretending it passed.

## Security baseline

Never commit secrets. Never weaken authentication or authorization to make a test pass. Never trust client-provided roles, prices, entitlements, or payment success. Never bypass authorization because a request came through MCP. Validate untrusted inputs at boundaries and fail closed on authorization/payment verification failures. Avoid logging tokens, passwords, secrets, or sensitive customer data.

## Database and scalability baseline

Use the repository's PostgreSQL architecture as the authoritative persisted application state. Use the established migration mechanism, add indexes for real query paths, use constraints for important invariants, avoid N+1 access patterns, use transactions for consistency-sensitive writes, and make asynchronous workers/event handlers idempotent. Prefer bounded queries, pagination, appropriate caching with explicit invalidation, connection pooling, timeouts, retries, and observability. Do not add infrastructure without a demonstrated need.

## Product decision rule

When deciding whether to build or retain something, ask: **Does this materially increase the probability that a human or agent can complete a difficult physical-engineering job and prove the result?** If not, delete it or simplify it.

## Git discipline

Make focused commits. Do not rewrite unrelated files. Review the diff before committing. Never commit secrets or local environment files. Do not claim tests, payment verification, or deployment succeeded unless actually verified.
