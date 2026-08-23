# Fabrient Agent Operating Contract

**READ THIS FILE BEFORE EVERY EXECUTION.** This applies to every coding agent, automation agent, MCP implementation agent, reviewer, and maintenance agent working in this repository. Do not start by editing code. First read this file and `docs/PRODUCT_EXECUTION_PRINCIPLES.md`, `docs/DEEP_EXECUTION_STANDARD.md`, and `docs/PRODUCT_SIMPLIFICATION.md`.

## Non-negotiable behavior

1. **Own the outcome.** Do not stop at explanation, code review, or a partial implementation when the task can be executed.
2. **Understand before changing.** Inspect the existing implementation, tests, routes, MCP registry, data model, auth boundaries, and deployment assumptions relevant to the task. Do not rebuild systems that already exist.
3. **Human-first, agent-native.** Every important capability must be understandable and usable by a human and composable by an agent.
4. **Complete work.** A successful intermediate API response is not a completed job. Follow the workflow through verification, artifact generation, release, or a truthful actionable blocker.
5. **Evidence over claims.** Never invent measurements, confidence, validation, or completion. Preserve provenance and deterministic evidence.
6. **Test deeply.** Every execution that changes behavior must run the deepest practical test set: unit tests, MCP contract/registry tests, integration tests, and Playwright browser tests. Test happy paths, invalid inputs, permissions, failure/recovery paths, and important state transitions.
7. **Use the browser.** When UI behavior is involved, use Playwright against a real running app. Do not declare UI work complete from static code inspection alone.
8. **Simplify aggressively.** Remove duplicate concepts, unnecessary screens, unnecessary configuration, dead code, and features that do not move users toward a verified engineering outcome. Nice-to-haves should be simplified rather than automatically deleted.
9. **Optimize the whole system.** For meaningful changes inspect auth, authorization, DB queries/indexes/RLS, API/MCP latency and failure handling, security, scalability, accessibility, observability, and operational cost.
10. **Automate repeated work.** If an agent encounters the same manual diagnostic, validation, migration, test setup, or release step twice, look for a safe way to turn it into a script, test, tool, or CI check.
11. **Prefer one source of truth.** Do not create parallel registries, duplicate business rules, or separate MCP/UI implementations when a shared domain contract is possible.
12. **Leave the repository better.** Add regression coverage for bugs you fix and update the relevant documentation/skill when the workflow changes.

## Required execution order

**READ → INSPECT → PLAN → IMPLEMENT → TEST → BROWSER VERIFY → HARDEN → SIMPLIFY → AUTOMATE → REPORT**

A report must state what was actually changed, what was actually tested, what failed, and what remains blocked. Never imply deployment or runtime verification that was not performed.

## Required testing commands

- `npm run test:unit`
- `npm run test:e2e`
- `npm run test:deep`
- `npm run test:all` for a release-quality pass
- Python/MCP tests for changed engineering or MCP behavior

If an environment cannot run a required test, add/retain the test and state the exact environment blocker instead of pretending it passed.

## Product decision rule

When deciding whether to build or retain something, ask: **Does this materially increase the probability that a human or agent can complete a difficult physical-engineering job and prove the result?** If not, delete it or simplify it.
