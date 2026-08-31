# Sim-to-real product cut/refine decisions

## North-star outcome
Reduce the number of physical experiments required to reach a model that passes independent validation inside a declared operating envelope.

## Keep and strengthen
- Prediction vs reality comparison
- Divergence detection
- Physics-based baseline
- System identification / parameter calibration
- Physics + residual ML
- Held-out validation
- Uncertainty and empirical fit reporting
- Active experiment selection
- Trust/validity envelope
- Provenance and model versions
- App + MCP parity

## Simplify
- One reality-loop workspace instead of a feature gallery
- Safe defaults instead of repeated configuration
- Evidence first; reports are generated from evidence
- One canonical engineering operation layer underneath UI and MCP
- Existing CAD/DFM capabilities remain available but are not the primary workflow

## Defer or retire from the primary product path
- Generic AI chat that does not advance a reality-loop job
- Generic CAD generation as a primary feature
- Broad manufacturing lifecycle automation
- Large MCP tool count as a product metric
- Decorative dashboards
- Duplicate engineering rules/operations
- Unrelated productivity workflows
- Autonomous claims without physical evidence

## Non-negotiable truth boundary
Fabrient may automate analysis, calibration, model training, validation, experiment selection, provenance and connected test execution. It cannot fabricate a physical measurement. If no robot/test executor is connected, physical execution remains an external dependency and the product must say so.

## App/MCP parity
The app and MCP must invoke the same reality-loop contracts. The canonical contracts are:
- `/v1/sim2real/run`
- `/v1/sim2real/compare`
- `/v1/sim2real/calibrate-and-run`
- `/v1/sim2real/next-experiment`
- `/v1/sim2real/autonomous`
- `/v1/sim2real/trust-envelope`

The first four are also covered by the existing MCP registry. New MCP tools must replace low-value capabilities rather than growing the registry indefinitely.

## Research grounding
The design follows the current research direction: the reality gap has multiple sources; system identification, real-to-sim, residual learning and active exploration are complementary; and simulator fidelity alone does not eliminate the gap. See the 2026 Annual Review survey and the 2025 CoRL SPI-Active work in the project research notes.
