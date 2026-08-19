# Fabrient

Fabrient is engineering software for machine-specific dimensional drift in FDM production.

## v1 loop

Plain-English engineering input / STEP context
→ structured engineering problem
→ deterministic physics baseline
→ uncertainty/domain perturbations
→ existing inspection records + real measurements
→ CV when an image contains a usable reference
→ machine/process system identification
→ residual ML
→ calibrated uncertainty
→ next physical experiment
→ new evidence.

## Product boundaries

LLMs may parse, orchestrate and explain. They do not generate engineering numbers, pass/fail decisions, confidence, or measurements. Real observations are ground truth. Unsupported extrapolation is refused.

Production drift and in-service wear are separate clocks. Every imported or displayed number keeps provenance. When the observed variation cannot support a requested tolerance, Fabrient should refuse a confident recommendation.

## Stack

- Next.js + TypeScript frontend
- Supabase/Postgres + Google OAuth
- Python/FastAPI engineering service
- deterministic physics and validation
- scikit-learn residual models
- OpenCV measurement primitives
- GitHub Actions CI

## Run locally

1. Configure `.env` from `.env.example`.
2. Enable **Google** as the only sign-in provider in Supabase Auth and set the callback URL to `/auth/callback` for the deployed site.
3. `npm install && npm run dev`
4. `cd engineering && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000`

## Engineering honesty

No fake calibration data. No fake confidence. No synthetic observations presented as measurements. Prediction records must carry algorithm/physics/model provenance and validation state.

## Current vertical slice

Projects + Google sign-in, inspection-record evidence import, deterministic shrinkage baseline, explicit uncertainty, residual calibration endpoint, CV feature detection with scale refusal, conservative next-experiment selection, graph/agent view, Supabase provenance, RLS ownership, and CI.

Future v1 increments: STEP geometry extraction/visualization, full inspection-column mapping into serialized gauges/features, production/service-wear separation, interval recommendation, auditable inspection-record PDF/CSV export, calibrated residual model evaluation, and deployment.
