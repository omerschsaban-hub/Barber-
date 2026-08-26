# Fabrient Product Execution Principles

These are product requirements, not marketing claims. Every agent must read this document before executing work.

## 1. Human-first, agent-native

Fabrient must work exceptionally well for a human engineer while exposing the same engineering capabilities as composable, authenticated, machine-readable tools for agents.

Requirements:
- Every important engineering action has a UI path and an API/MCP path where technically appropriate.
- Tool inputs, outputs, units, assumptions, provenance, evidence, and failure states are structured.
- Agents can inspect state, choose the next bounded action, execute it, observe the result, and continue.
- Human approval is required for consequential geometry/topology changes and other explicitly gated operations.
- The UI explains why a result passed, failed, was refused, or requires human review.

## 2. Complete work, do not merely sell software

A Fabrient job is complete only when the requested engineering outcome has been produced and verified, or the system has reached a truthful, actionable blocker.

The canonical lifecycle is:

**Define → Analyze → Fix → Verify → Build → Release**

Completion requirements:
- No workflow may report success merely because an intermediate tool returned successfully.
- Each stage records state, evidence, artifacts, and the next required action.
- Failures are recoverable where possible; otherwise they become explicit blockers with evidence.
- Release requires the required verification gates to pass.
- Successful release produces usable manufacturing artifacts, not just analysis screens.
- The primary product metric should increasingly be verified end-to-end job completion, not clicks, seats, or tool calls.

## 3. Engineering authority hierarchy

Fabrient has an explicit authority boundary:

**real physical evidence > deterministic engineering computation > validated learned correction > language-model interpretation**.

- CAD geometry is owned by the deterministic CAD kernel, not generated as an unchecked model artifact.
- DFM and release gates are deterministic and explicit.
- ML learns machine/process effects or residual error only around a defined baseline and only when real observations support the claim.
- Computer vision can extract measurement evidence only when physical scale and image quality are established.
- Language models coordinate intent, planning and explanation but do not author engineering truth.

## 4. Evidence-backed intelligence

Current ML/measurement requirements are concrete:

- System identification uses Ridge regression over real observations including process and environment variables.
- Held-out evaluation uses leave-one-out cross-validation and reports MAE before a system model is called validated.
- Residual modeling stays separate from the deterministic baseline.
- Uncertainty combines physics, measurement, model and empirical residual components.
- Real-observation thresholds control whether a result is validated, limited or refused.
- Real CV uses quality gates plus explicit physical scale; pixel geometry alone is not ground truth.
- Synthetic data may support algorithm development but is never presented as calibration evidence.

## 5. Target hard-to-automate physical industries

Fabrient should deliberately prioritize engineering workflows that are difficult for generic AI systems because they require physical evidence, deterministic constraints, iterative verification, manufacturing knowledge, or scarce expertise.

Selection criteria:
- High cost of physical iteration or failure.
- Strong need for evidence and traceability.
- Mixed digital + physical workflow.
- Deterministic constraints that can be encoded and verified.
- Meaningful gap between what an AI agent can propose and what it can safely complete.
- A credible path from one narrow wedge to a larger physical-engineering workflow.

Avoid competing primarily on generic text generation, generic copilots, dashboards, or workflows where existing software already completes the hard part.

## 6. Relentless quality: test, simplify, harden, automate

Every meaningful change must be treated as a full-system change, not a code diff.

- Deeply test the affected feature and its dependencies every time.
- Use unit, integration, MCP contract, and Playwright browser tests where applicable.
- Test happy paths, invalid inputs, permissions, stale state, retries, upstream failures, recovery, and completion states.
- For UI changes, actually operate the app in a real browser; static inspection is not acceptance testing.
- After correctness, simplify the experience and remove unnecessary complexity.
- After simplification, harden auth, RLS, DB performance, scalability, security, observability, idempotency, and error handling.
- Automate repeated manual work discovered during implementation or testing.
- Add regression coverage for every important bug found.

See `docs/DEEP_EXECUTION_STANDARD.md` for the mandatory execution/testing standard and `docs/PRODUCT_SIMPLIFICATION.md` for product-level simplification rules.

## Product north star

**Fabrient turns bounded physical-engineering jobs from requests into verified real-world outcomes, for humans and increasingly autonomous agents.**

## Anti-slop acceptance test

Before shipping a feature, ask:
1. Does this help complete a real engineering job?
2. Can an agent use it as a reliable primitive or workflow?
3. Is the result backed by deterministic computation or real evidence where required?
4. If ML is involved, is it downstream of an explicit baseline and validated on held-out real observations?
5. Does it move the job closer to a verified physical outcome?
6. Does it remain simple enough for a human to understand and operate?
7. Has it been deeply tested, including failure and recovery paths?
8. If it cannot complete the job, does it fail honestly and identify the exact blocker?

If the answer is no to most of these, the feature is not core Fabrient work.
