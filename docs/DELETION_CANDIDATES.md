# Deletion Candidates — Audit Before Removal

These are candidates, not blind-delete instructions. Each item must pass the dependency and production-use check before removal.

## High confidence if unused

- `film/` and associated video-production-only files/workflows.
- `mobile-ci.yml` if the retained application is web-only or only one mobile surface is retained.
- Duplicate production-connectivity documents when one canonical document is established.
- `repair-mcp-stateful.yml` after MCP state repair is no longer an operational requirement.
- Migration-only workflows/scripts after the relevant migration is complete and no rollback/forward migration depends on them.
- Decorative dashboard components whose metrics have no decision/release effect.
- Generic chat surfaces that do not create, advance, inspect, verify, or release an engineering job.

## High-value consolidation candidates

- MCP tools that are aliases for the same endpoint and have no distinct schema/authorization/evidence contract.
- Repeated calibration/system-identification wrappers.
- Repeated manufacturing package/release wrappers.
- Repeated acceptance/reverification wrappers.
- Repeated CAD review wrappers that merely expose one deterministic check each to the agent.
- MCP authentication/bootstrap/compatibility layers that can be reduced to one production auth boundary.

## Do not delete

- Deterministic engineering checks.
- Evidence/provenance.
- Release/acceptance gates.
- Human approval gates for consequential geometry/topology changes.
- Data-flywheel ingestion/provenance needed for the learning loop.
- The engineering graph itself.
- The shared backend operation layer.
- Authentication/security controls merely because they add complexity.

## Required removal test

Before deleting any candidate, search imports, route references, workflow references, deployment configuration, tests, and production callers. Then run the critical web and MCP paths against the real backend. A candidate is not considered dead merely because it is not linked from the main UI.
