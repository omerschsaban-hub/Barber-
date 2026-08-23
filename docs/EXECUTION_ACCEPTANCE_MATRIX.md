# Fabrient Execution Acceptance Matrix

This is the release gate, not a marketing checklist. A row is **accepted** only when its evidence exists in CI, a real integration test, or deployed browser/runtime verification.

| Area | Required outcome | Evidence required | Current gate |
|---|---|---|---|
| Human UX | A human can state a physical-engineering goal without understanding internal tools | Browser test + usability flow | Required |
| Agent UX | An agent can perform the same job through structured MCP/API state | MCP integration test | Required |
| Completion | Jobs end in verified deliverables or a truthful actionable blocker | Completion-state tests | Required |
| Engineering truth | No invented engineering numbers; deterministic checks have provenance | Unit/integration tests | Required |
| MCP | Every exposed tool has schema, callable path, predictable error behavior | Registry + representative real calls | Required |
| Browser | No blank screen, console crash, fatal request, or dead-end navigation | Playwright | Required |
| Auth | Login/session/unauthorized behavior is correct | Auth integration + browser tests | Required |
| Database | Reads/writes, constraints, failure handling, and migrations behave correctly | Integration tests | Required |
| Security | Secrets stay server-side; authorization is enforced; unsafe inputs fail safely | Security tests/review | Required |
| Performance | Hot paths have bounded latency and do not create obvious unbounded work | Runtime/metrics tests | Required |
| Manufacturing | A successful job produces a usable package and inspection/build evidence | End-to-end acceptance fixture | Required |
| Simplification | Non-core complexity is hidden, defaulted, or removed | Product review + browser assertions | Required |
| Automation | Repeated verification/manual setup is encoded as scripts or CI | `agent:loop` + CI | Required |
| Deployment | Main-branch deployments finish successfully and the deployed runtime passes smoke/e2e checks | Render/Vercel deployment + browser/runtime evidence | **Not accepted until verified** |

## Deletion policy

Delete a feature when it is decorative, duplicates another capability, exists mainly to demonstrate autonomy, generates unsupported engineering claims, or adds setup without changing correctness. Do not delete a feature merely because it is advanced; hide and simplify valuable advanced capability first.

## Four required product outcomes

1. **Human-first, agent-native:** one underlying execution model, two interfaces.
2. **Completed work:** optimize for verified physical outcomes, not clicks or tool calls.
3. **Hard/impossible industries:** prioritize jobs with real physical constraints, expensive iteration, verification burden, or expert scarcity.
4. **Deeply tested and continuously improved:** every feature gets unit/integration/MCP/browser/failure-path coverage where applicable, followed by simplification, hardening, and automation.

## Acceptance rule

Never mark the whole product green because one layer is green. Production acceptance requires all applicable rows above to have evidence. If a gate cannot be executed in the current environment, report it as unverified rather than claiming success.
