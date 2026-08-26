# Fabrient Current Product Surface

This document is the canonical product-facing description of the Fabrient implementation on `main`. It should be updated when the product surface changes so the README, landing page and technical documentation stay aligned.

## Product definition

Fabrient turns bounded physical-engineering jobs into verified real-world outcomes. It connects language-level intent with deterministic engineering, real physical evidence, bounded machine learning and manufacturing release.

The canonical lifecycle is:

**Define → Analyze → Fix → Verify → Build → Release**

## Intelligence architecture

### Language and agents

The language layer is responsible for intent, planning, explanation and bounded orchestration. The agent graph separates evidence collection, physics, deterministic validation, measurement, system identification, residual ML, uncertainty/risk gating, experiment selection and criticism.

The language layer is not an engineering authority.

### Deterministic engineering

The deterministic layer owns reproducible engineering decisions. Current implementation includes:

- explicit input/unit/range/tolerance validation;
- deterministic parametric CAD through CadQuery/OCCT;
- STEP exchange-format checks;
- geometry/topology validation before release;
- deterministic DFM analysis and bounded self-fix workflows;
- seeded Monte Carlo/domain randomization where explicitly applicable;
- release gates that fail closed when required evidence is missing.

### Machine learning

ML is deliberately downstream of the engineering baseline.

**System identification:** Ridge regression estimates machine/process effects from real observations across layer height, print speed, nozzle temperature, ambient temperature, humidity and axis. Leave-one-out predictions provide held-out MAE and residual spread.

**Residual modeling:** a correction layer models remaining error after deterministic prediction. The goal is interpretable improvement, not replacing the physical baseline with an opaque prediction.

**Uncertainty:** physics, measurement, model and empirical residual components are combined into a bounded uncertainty interval. Calibration is limited or refused when real observations are insufficient.

### Computer vision

Real-image measurement uses OpenCV primitives with physical scale established by an explicit reference. The current path includes image quality gates, Canny edge detection, Hough line candidates, explicit mm-per-pixel conversion and propagated measurement uncertainty.

CV evidence is not silently promoted to physical ground truth.

## Geometry and manufacturing

Fabrient can generate a deterministic parametric enclosure, export STEP, validate the exchange artifact and expose the remaining topology/release gates. Existing STEP files can also be ingested for geometry summaries.

The manufacturing workflow connects DFM analysis, bounded self-fix, physical build guidance and a release package. The package can include the validated CAD, release manifest, DFM report, build guide, manufacturing notes and inspection plan.

## Inspection and evidence

Inspection workflows normalize pasted/uploaded CSV or TSV records, reconcile supported units and preserve notes/provenance. Inspection records can be exported as CSV and PDF.

Re-verification interval logic uses tolerance, usage frequency, environment, observed drift and consequence of incorrect acceptance. It refuses a confident interval when evidence is insufficient.

## Data flywheel

The flywheel is designed around prediction versus reality. Its catalog includes requirements, geometry, revisions, validation outcomes, measurements, fit/assembly results, manufacturing outcomes, defects, rework, engineer corrections, prediction deltas, workflow failures and closed-loop learning signals.

Ingestion is consent-gated, normalized, provenance-bearing and content-hashed for deduplication. Synthetic observations are not calibration evidence.

## Agent-native interface

The same underlying engineering capabilities are exposed through authenticated UI/API/MCP surfaces. Structured outputs preserve units, assumptions, provenance, validation state and blockers so an agent can reason over engineering state without scraping presentation text.

## Safety and honesty boundaries

Fabrient must not:

- fabricate measurements;
- fabricate confidence or calibration evidence;
- silently override tolerances;
- claim a release from an intermediate success;
- perform consequential geometry/topology changes without the required human gate;
- treat unsupported extrapolation as engineering evidence.

## Public narrative

The landing page should explain the system as an engineering architecture rather than a feature checklist: language coordinates the work, deterministic computation establishes the baseline, ML learns residual behavior from real observations, measurement closes the loop, and release happens only when the evidence gates pass.

## Canonical public hostname

`https://getfabrient.com` is the intended public hostname. It is referenced by application metadata as the canonical/Open Graph URL. The domain must still be attached/configured in the hosting account before it is the live production hostname.
