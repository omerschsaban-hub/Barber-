# Fabrient

Fabrient is engineering software for measuring and learning FDM dimensional drift from real inspection data.

## v1 scope

- Import existing inspection records (CSV/table) rather than inventing a new measurement ritual.
- Track serialized gauge instances and machine/process provenance.
- Deterministic dimensional calculations and acceptance checks.
- Separate production drift from in-service wear.
- Machine-specific calibration from real observations only.
- Prediction uncertainty and explicit calibration status.
- Defensible re-verification interval recommendations.
- Auditable inspection records and provenance.

LLMs may parse and explain engineering inputs, but they do not generate engineering numbers, pass/fail decisions, confidence values, or fake measurements.

## Architecture

`Next.js` frontend → `Python/FastAPI` engineering service → `Supabase/Postgres`.

The repository is intentionally starting clean; the previous Barber archives were unrelated to Fabrient and were removed.
