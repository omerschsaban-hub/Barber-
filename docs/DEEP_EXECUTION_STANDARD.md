# Deep Execution Standard

This is the minimum bar for substantial Fabrient work. It is intentionally stricter than ordinary SaaS development because Fabrient claims to help complete physical-engineering work.

## 1. Inspect the whole affected path

Trace the request from user/agent input through UI or MCP, auth, API, engineering logic, database/storage, artifacts, and final state. Inspect adjacent code for duplicated rules and hidden failure modes.

## 2. Define completion before coding

Write down the real outcome and the evidence that proves it. Intermediate success is not completion.

## 3. Implement the smallest coherent vertical slice

Prefer one end-to-end path that genuinely works over many disconnected features. Keep deterministic engineering decisions outside the LLM.

## 4. Test every layer

### Unit
- deterministic calculations
- validation/refusal boundaries
- parsers and normalization
- error mapping
- state transitions
- authorization helpers

### Integration
- authenticated API calls
- database reads/writes and RLS
- storage flows
- engineering-service calls
- artifact generation
- MCP-to-engine contracts

### MCP
- registry count and uniqueness
- every tool's schema and dispatch
- valid and invalid inputs
- auth/tenant isolation
- timeouts and upstream failures
- evidence/provenance preservation
- representative end-to-end tool chains

### Browser / Playwright
- landing → request/project start
- auth states where testable
- primary workspace flows
- engineering lifecycle transitions
- error/recovery states
- artifact/download paths
- responsive/accessibility-critical interactions
- no console/page errors in critical flows

### Release / resilience
- build
- lint/type checks
- migrations where applicable
- security-sensitive paths
- performance regressions
- retry/idempotency behavior

## 5. Browser verification is mandatory for UI changes

Static inspection is not enough. Run the application and interact with it in a real browser using Playwright. Capture useful diagnostics on failure (trace, screenshot, console/network information) and fix the underlying cause.

## 6. Deep means adversarial too

For important workflows, test malformed payloads, missing fields, stale state, duplicate submissions, unauthorized access, expired sessions, upstream timeout/error, oversized uploads, and partial completion. The expected behavior should be safe, deterministic, and explainable.

## 7. Simplify after correctness

After functionality passes, remove accidental complexity. Keep capabilities that are strategically useful but make them easier to understand and operate. Kill only features that fail the product decision rule.

## 8. Harden after simplification

Review auth, RLS, secrets, input validation, SSR/server boundaries, dependency risk, DB indexes/query shape, connection behavior, caching, rate limits, observability, idempotency, and failure recovery.

## 9. Automate the friction

Every repeated manual step is a candidate for a command, fixture, test helper, CI check, MCP tool, or internal automation. Automation must be deterministic, observable, and safe to rerun.

## Definition of done

A substantial change is done only when:

- the real user/agent outcome works;
- tests cover the changed behavior and important regressions;
- browser behavior was verified when applicable;
- security/data/auth boundaries were considered;
- unnecessary complexity was removed or simplified;
- repeated manual work discovered during execution has an automation candidate;
- documentation and agent instructions remain accurate.
