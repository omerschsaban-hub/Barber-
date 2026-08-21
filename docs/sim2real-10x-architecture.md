# Fabrinat 10x Sim-to-Real Architecture

The 20 engineering layers are one evidence loop, not 20 disconnected features.

1. STEP/B-Rep ingestion
2. Deterministic topology extraction
3. Feature recognition
4. 3D geometric measurement
5. CV physical-part inspection
6. Physics-property extraction
7. Mesh/solver preparation
8. Multi-physics simulation orchestration
9. Boundary-condition/test-spec generation
10. Simulation uncertainty and sensitivity analysis
11. Physical measurement ingestion
12. CV measurement extraction from photos/video/scans
13. Prediction-vs-reality residual calculation
14. ML residual/error models
15. Calibration/model-update loop
16. Active-learning experiment selection
17. Deterministic DFM + auto-fix/revalidation
18. Evidence-constrained LLM engineering copilot
19. Cross-modal disagreement engine
20. Evidence-backed manufacturing release

## Loop

CAD -> B-Rep -> features -> DFM -> repair -> revalidation -> physics simulation -> uncertainty -> physical test -> CV/sensor measurement -> residual -> ML error model -> calibration -> next experiment -> repeat -> independent evidence -> release.

## Evidence policy

LLMs may interpret requirements, propose hypotheses, explain failures, and orchestrate tools, but cannot be the authority for engineering release. Physical measurements remain ground truth. Synthetic observations cannot silently become calibration evidence. Disagreement between deterministic geometry, physics, CV, ML, and LLM outputs blocks release until resolved.
