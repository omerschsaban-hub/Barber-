# 20× implementation status

Implemented on `feat/sim2real-20x`:

- Shared 20-capability contract.
- Evidence types for CAD, deterministic, physics, CV, physical, ML and LLM sources.
- Prediction-vs-reality residual calculation with optional uncertainty normalization.
- Information-gain-per-cost/risk experiment selection.
- Cross-modal disagreement detection.
- Release gate that refuses without validated physical evidence and residual evidence.
- API adapter wired into the existing engineering composition.
- Regression tests for the evidence contract.

Not changed:

- No new product category.
- No new standalone UI workflow.
- No replacement of the existing deterministic engineering implementation.
- No fabricated measurements or calibration evidence.
- No autonomous physical release.
