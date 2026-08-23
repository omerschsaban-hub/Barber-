# Product Simplification Pass

Fabrient should feel simple without becoming shallow.

## Keep — core

- One clear project/request entry point.
- Define → Analyze → Fix → Verify → Build → Release.
- Evidence, provenance, deterministic checks, refusal gates.
- Human approval for consequential geometry/topology changes.
- Agent/MCP access to the same underlying capabilities.
- Manufacturing package, physical build guide, inspection evidence.

## Simplify — valuable but too complex

- Advanced engineering configuration: expose sensible defaults first; reveal expert controls only when needed.
- Agent graph: show the current job, next action, evidence, and blocker instead of exposing internal orchestration complexity by default.
- Reports: lead with the decision and required action; keep detailed evidence one level deeper.
- Geometry/DFM: use one coherent workflow instead of making users understand individual tool names.
- MCP: provide clear tool descriptions, consistent schemas, predictable errors, and high-level workflow tools on top of primitives.
- Project history: default to the current release state; keep full audit history available without dominating the UI.

## Remove / do not build

- Generic AI chat that does not advance an engineering job.
- Decorative dashboards whose metrics do not change a decision.
- Duplicate tool registries or duplicate implementations of the same engineering rule.
- Features whose only purpose is demonstrating AI autonomy.
- Unsupported engineering-number generation or confidence theater.
- Extra setup steps that can be safely inferred or defaulted.

## Product interaction rule

A new user should be able to express an engineering goal in plain language and quickly see:

1. what Fabrient understood;
2. what it can do now;
3. what evidence it needs;
4. what it is doing;
5. what is finished;
6. what is blocked and exactly why;
7. what the human must approve, if anything.

An agent should receive the same state as structured data rather than scraping UI text.

## Request normalization

Natural-language requests should be normalized into a compact job contract before execution:

- objective
- inputs/assets
- constraints
- required evidence
- allowed actions
- approval gates
- expected deliverables
- completion criteria

Do not make users fill forms for information the system can safely derive. Do not silently invent missing engineering constraints; ask only when the missing information changes safety or correctness.
