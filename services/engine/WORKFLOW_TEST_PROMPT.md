# Fabrient full workflow proof test

Run this as a synthetic test fixture only. Never represent synthetic data as physical acceptance.

## Required sequence
1. Accept a public/reference STEP fixture and record source + license/provenance.
2. Parse it with a real CAD/BREP kernel. Verify units, solids, watertightness, topology, bounding box, and feature inventory.
3. Run all available geometry/DFM/risk-map checks.
4. For every auto-fixable issue, create a versioned derived geometry, then re-run the CAD-kernel checks and all affected DFM checks.
5. Run physics/simulation checks and explicitly separate simulated evidence from physical evidence.
6. Run CV only when a calibrated physical reference is present; never infer millimetres from uncalibrated pixels.
7. Run sim-to-real only with supplied real observations. For this synthetic test, exercise the gate and report BLOCKED rather than inventing observations.
8. Generate a manufacturing package candidate containing revision, source provenance, geometry hash, DFM findings, fixes, verification results, process/material assumptions, inspection plan, traceability, and explicit release status.
9. Generate a physical build/acceptance guide with measurement points, assembly/fit checks, defect checks, recording procedure, and release gates.
10. Exercise every MCP operation that is advertised by the registry. Record PASS/FAIL/BLOCKED with evidence. Unsupported operations must fail loudly, not return a fake success.
11. The final report must distinguish: synthetic test passed, simulation passed, and physical acceptance pending.

## Hard gates
- No fabricated physical measurements.
- No claim of sim-to-real validation without real observations.
- No manufacturing release claim without physical acceptance.
- No arbitrary STEP rewrite without a CAD/BREP kernel and post-fix topology verification.
- Every generated artifact must contain provenance and revision identifiers.
