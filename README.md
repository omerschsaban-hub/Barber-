# Fabrient

Fabrient is an engineering system for turning bounded physical-product jobs into verified real-world outcomes.

**North star:** **Define → Analyze → Fix → Verify → Build → Release**.

The product is intentionally hybrid: language models coordinate intent and bounded agents, while deterministic engineering code, CAD kernels, real measurements and explicit evidence gates remain the authorities for engineering claims.

## What Fabrient does today

A user can describe an engineering job, provide dimensions/CAD and process context, and move through a single workspace that connects:

- natural-language engineering intent normalization;
- deterministic dimensional and manufacturing validation;
- parametric CAD generation through CadQuery/OCCT with STEP exchange validation;
- STEP ingestion and computed geometry summaries;
- DFM analysis and bounded deterministic self-fix workflows;
- physical build guidance and an auditable manufacturing package;
- inspection-record normalization plus CSV/PDF export;
- scale-gated computer vision measurement from real images;
- machine/process system identification from real observations;
- interpretable residual ML with held-out validation;
- combined uncertainty and refusal gates;
- bounded engineering-agent orchestration;
- provenance, audit state and consent-gated data collection;
- an engineering MCP surface exposing the same underlying capabilities to agents.

Fabrient is not a generic chatbot. The language layer can plan and explain, but it does not get to invent measurements, engineering numbers, confidence, calibration evidence or tolerance overrides.

## The engineering stack

### Deterministic layer

Engineering authority is implemented in explicit code rather than model output. The current stack includes:

- **CadQuery / OCCT** for deterministic parametric CAD and STEP exchange;
- explicit unit/range/tolerance validation;
- geometry and topology gates before manufacturing release;
- deterministic DFM analysis and bounded self-fix operations;
- Monte Carlo/domain-randomization workflows where parameters are explicitly declared and seeded;
- physical-build and release gates that fail closed when required evidence is missing.

### Machine learning layer

ML is used as a bounded correction and system-identification layer around engineering baselines.

- **Ridge regression** currently performs machine/process system identification from real observations using layer height, print speed, nozzle temperature, ambient temperature, humidity and axis.
- **Leave-one-out cross-validation** reports held-out mean absolute error before a fitted system model is treated as validated.
- **Residual modeling** estimates remaining error after the deterministic baseline rather than replacing it.
- **Combined uncertainty** accounts for physics, measurement, model and empirical residual components and reports a bounded 95% interval.
- Real-observation thresholds prevent unsupported calibration claims; insufficient evidence produces a limited/not-calibrated state instead of fabricated confidence.

### Computer vision

The current real-CV path uses OpenCV primitives with explicit physical scale:

- image decoding and quality gates for size, contrast and sharpness;
- **Canny edge detection + Hough line candidates**;
- user-selected reference and target geometry;
- explicit mm-per-pixel scale from a physical reference;
- measurement uncertainty propagated from pixel and reference uncertainty;
- provenance that distinguishes image-derived evidence from physical ground truth.

CV is evidence, not a final physical acceptance authority by itself.

## The bounded agent loop

The engineering agent graph currently separates responsibilities across context/evidence collection, physics, deterministic validation, measurement CV, system identification, residual ML, uncertainty/risk gating, experiment selection and a critic/falsification step.

The loop is:

**OBSERVE → UNDERSTAND → GENERATE OPTIONS → PRIORITIZE → ACT → MEASURE → EVALUATE → LEARN → UPDATE → REPEAT**

Consequential geometry/topology changes remain human-gated. The system explicitly prohibits fabricated measurements, fabricated confidence, automatic tolerance overrides and unbounded execution.

## Reality data flywheel

Fabrient's data model is designed around prediction versus reality rather than synthetic demonstrations. The current catalog covers design requirements, CAD/geometry, manufacturing conditions, measurements, fit/assembly outcomes, failures/rework, prediction deltas, engineer corrections, workflow outcomes and other provenance-bearing observations.

Observations are normalized, consent-gated and content-hashed for deduplication before ingestion. Synthetic data is never presented as calibration evidence.

## Manufacturing release

The manufacturing workflow requires a real validated STEP artifact before engineering release. The current flow can:

1. generate or attach STEP;
2. validate the STEP exchange artifact and geometry/topology state;
3. run DFM analysis;
4. apply bounded self-fixes where allowed;
5. generate a physical build guide;
6. produce a manufacturing package containing the validated CAD, release manifest, DFM report, build guide, manufacturing notes and inspection plan.

A release is a usable engineering artifact with evidence and blockers, not simply a green status badge.

## Routes

- `/` — technical product overview
- `/login` — passwordless Gmail OTP access
- `/workspace` — integrated engineering workspace
- `/manufacturing` — CAD/DFM/self-fix/build/release workflow
- `/geometry` — STEP geometry extraction and computed 3D view
- `/records` — auditable inspection records and exports
- `/graph` — bounded engineering agent graph
- `/projects` — project history and state

## Architecture

- Next.js + TypeScript frontend
- Supabase/Postgres + passwordless email OTP
- Python/FastAPI engineering service
- CadQuery/OCCT CAD kernel
- NumPy + scikit-learn engineering ML
- OpenCV real-image measurement primitives
- provenance/audit records and RLS
- authenticated MCP engineering tools
- GitHub Actions CI and browser acceptance tests

## Engineering honesty

LLMs may parse natural language, coordinate bounded agents and explain results. They do **not** generate engineering numbers, pass/fail decisions, confidence, measurements or calibration evidence.

Real observations are ground truth. Literature values retain their source and applicability context. Unsupported extrapolation is refused.

## Agent operating contract

All coding/automation agents must read `AGENTS.md` before execution. The product requirements and execution standards are in:

- `docs/PRODUCT_EXECUTION_PRINCIPLES.md`
- `docs/DEEP_EXECUTION_STANDARD.md`
- `docs/PRODUCT_SIMPLIFICATION.md`
- `docs/PRODUCT_SURFACE.md`
- `.claude/skills/playwright/SKILL.md`

Run `npm run agent:preflight` to verify the required operating contract.

## Testing

- `npm run test:unit` — frontend/domain unit tests
- `npm run test:e2e` — Playwright browser tests
- `npm run test:deep` — unit + browser tests
- `npm run test:all` — lint + build + unit + browser tests
- `pytest -q tests/mcp` — MCP registry/contract tests

For UI work, acceptance requires real-browser verification rather than static inspection alone.

## Local development

```bash
npm install
npm run agent:preflight
npm run dev
cd engineering
pip install -r requirements.txt
uvicorn app.composed:app --reload --port 8000
```

Set `NEXT_PUBLIC_ENGINEERING_API` when the engineering service is not on `http://localhost:8000`.

## Public URL

The intended public canonical hostname is **getfabrient.com**. The repository metadata now uses that hostname for canonical/Open Graph URLs; DNS/domain attachment still has to be completed in the hosting account before it becomes the live production hostname.
