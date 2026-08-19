# Fabrient

Fabrient is engineering software for machine-specific dimensional drift in FDM production.

## v1 product loop

Engineering input / STEP context
→ deterministic physics baseline
→ domain randomization around explicitly declared parameters
→ existing inspection records + real measurements
→ CV only when physical scale is evidenced
→ machine/process system identification
→ interpretable residual ML with held-out validation
→ combined uncertainty
→ tolerance/refusal gate
→ defensible re-verification interval
→ next physical experiment
→ new evidence.

## Walt/Jaegertech changes

- Existing inspection records are the primary onboarding path.
- Serialized gauge/fixture instances are first-class records.
- Production drift and service wear are separate data domains.
- Re-verification interval is an output, not a user-entered magic number.
- Outputs are expressed as acceptance consequences with dimensional values underneath.
- Every value carries provenance.
- Tight tolerances are refused when measured variation cannot support them.
- Inspection records export to auditable CSV/PDF.

## Architecture

- Next.js + TypeScript frontend
- Supabase/Postgres + Google OAuth
- Python/FastAPI engineering service
- deterministic FDM physics and validation
- Monte Carlo/domain randomization with explicit seeds
- OpenCV measurement primitives with scale refusal
- scikit-learn residual/system-identification models
- bounded engineering agent graph
- provenance/audit records and RLS
- GitHub Actions CI

## Engineering honesty

LLMs may parse natural language, coordinate bounded agents, and explain results. They do not generate engineering numbers, pass/fail decisions, confidence, measurements, or calibration evidence.

Real observations are ground truth. Synthetic data is never stored or presented as calibration evidence. Literature values must retain their source and applicability context. Unsupported extrapolation is refused.

## Important geometry limitation

STEP input currently extracts Cartesian-point geometry and a bounding box without pretending to have a full CAD-kernel BREP/topology interpretation. The API labels this state `extracted_limited`. A CAD-kernel adapter can be added without changing the provenance contract.

## Run locally

```bash
npm install
npm run dev
cd engineering
pip install -r requirements.txt
uvicorn app.composed:app --reload --port 8000
```

Set `NEXT_PUBLIC_ENGINEERING_API` when the engineering service is not on `http://localhost:8000`.

## Key routes

- `/workspace` — integrated prediction/import/re-verification workspace
- `/geometry` — STEP geometry extraction and computed 3D view
- `/records` — auditable inspection-record export
- `/graph` — engineering agent graph
- `/projects` — Supabase-backed projects

No payments, purchasing, fulfillment, spam, or generic autonomous-business engine are part of Fabrient v1.
