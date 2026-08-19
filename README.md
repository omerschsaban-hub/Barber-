# Fabrient

Fabrient is engineering software for machine-specific dimensional drift in FDM production.

## Authentication

Fabrient uses passwordless Gmail OTP authentication. Users enter a Gmail address, receive a one-time six-digit code, can open Gmail with one tap, paste/type the code, and are sent directly to the Workspace. Fabrient does not request Gmail inbox access.

### Supabase OTP configuration

1. Enable Email/OTP authentication in Supabase.
2. Configure SMTP (Resend can be used as the SMTP provider).
3. In Authentication → Email Templates → Magic Link, send the numeric OTP with `{{ .Token }}` rather than `{{ .ConfirmationURL }}`.
4. Keep the production Site URL and redirect configuration aligned with the Fabrient deployment.

The app uses `signInWithOtp()` followed by `verifyOtp({ email, token, type: 'email' })`. The repository never stores or handles SMTP credentials.

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

## Architecture

- Next.js + TypeScript frontend
- Supabase/Postgres + passwordless email OTP
- Python/FastAPI engineering service
- deterministic FDM physics and validation
- Monte Carlo/domain randomization with explicit seeds
- OpenCV measurement primitives with scale refusal
- scikit-learn residual/system-identification models
- bounded engineering agent graph
- provenance/audit records and RLS
- GitHub Actions CI
- MCP engineering tools with the same authenticated workspace model

## Manufacturing lifecycle

The primary user journey is deliberately short:

**Define → Analyze → Fix → Verify → Build → Release**

A successful release produces a manufacturing package and a simple physical build guide. Deterministic fixes are shown to the user; geometry/topology changes remain human-gated.

## Engineering honesty

LLMs may parse natural language, coordinate bounded agents, and explain results. They do not generate engineering numbers, pass/fail decisions, confidence, measurements, or calibration evidence.

Real observations are ground truth. Synthetic data is never stored or presented as calibration evidence. Literature values retain their source and applicability context. Unsupported extrapolation is refused.

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

- `/login` — passwordless Gmail OTP access
- `/workspace` — integrated engineering workspace
- `/manufacturing` — DFM, self-fix, physical build guide and manufacturing package
- `/geometry` — STEP geometry extraction and computed 3D view
- `/records` — auditable inspection-record export
- `/graph` — engineering agent graph
- `/projects` — Supabase-backed projects

No Gmail inbox access, passwords, payments, purchasing, fulfillment, spam, or generic autonomous-business engine are part of Fabrient v1.
