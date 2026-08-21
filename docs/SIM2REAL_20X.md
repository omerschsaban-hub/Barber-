# Fabrient 20× Sim-to-Real Architecture

The 20 items are the existing product contract. They are **not** 20 new products, screens, or MCP tools. The implementation underneath them is one evidence engine.

## The loop

CAD → deterministic geometry → feature extraction → DFM → deterministic fix → revalidation → physics simulation → uncertainty/sensitivity → physical test → CV/sensor measurement → prediction-vs-reality residual → residual ML/system identification → calibration → active experiment selection → repeat → cross-modal evidence check → release.

## Twenty layers

1. STEP/B-Rep ingestion
2. Deterministic topology extraction
3. Feature recognition
4. 3D geometric measurement
5. CV physical-part inspection
6. Physics-property extraction
7. Mesh/solver preparation
8. Multi-physics simulation orchestration
9. Boundary-condition/test-spec generation
10. Simulation uncertainty and sensitivity
11. Physical measurement ingestion
12. CV measurement extraction with scale validation
13. Prediction-vs-reality residuals
14. Interpretable residual/system-identification ML
15. Calibration and model update
16. Active-learning experiment selection
17. Deterministic DFM/fix/revalidation
18. Evidence-constrained LLM orchestration
19. Cross-modal evidence disagreement checks
20. Evidence-backed manufacturing release

## Evidence rules

- Real observations are ground truth.
- Synthetic simulation samples can quantify model behavior but cannot become physical calibration evidence.
- CV measurements require defensible scale/alignment; otherwise the system refuses the measurement.
- ML residual models require held-out validation before they can support a calibrated claim.
- LLMs can parse requirements, coordinate bounded tools, form hypotheses, and explain evidence. They cannot create engineering numbers, measurements, confidence, calibration evidence, or release decisions.
- Conflicting CAD/physics/CV/physical/ML evidence is surfaced as a disagreement rather than silently reconciled.
- Physical execution and final manufacturing release remain human-gated.

## Shared implementation contract

`engineering/app/sim2real_20x.py` contains the dependency-light evidence primitives shared by adapters. Existing UI and MCP surfaces should call these primitives rather than implementing independent versions of residual calculation, experiment selection, or release gating.

`engineering/app/sim2real_20x_routes.py` exposes the internal contract for the existing sim-to-real API without creating a new product surface.
