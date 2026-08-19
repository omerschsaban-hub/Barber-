# Fabrient v1 engineering acceptance gates

## Ground truth
- Physical inspection measurements are authoritative.
- Synthetic simulation samples are never inserted as calibration observations.
- Literature numbers must carry source/material/method provenance.

## Calibration
- <3 real paired observations: `not_calibrated`.
- 3–9 observations: `limited` unless explicitly validated by a held-out protocol.
- A residual model may only become `validated` after held-out evaluation and sufficient real observations.

## Acceptance/refusal
- Refuse when the combined uncertainty interval crosses the engineering acceptance band.
- Refuse when measurement uncertainty consumes the available margin.
- Refuse unsupported materials/process ranges instead of extrapolating silently.

## Re-verification
- Interval requires an observed production drift rate.
- Production drift and service wear are separate clocks.
- The recommendation is a decision aid, not a certification or standards claim.

## Experiments
- Select experiments from measured uncertainty/information value.
- Physical execution is human-approved in v1.
- Every run records provenance, algorithm/model version and source measurements.

## Geometry
- STEP files are never assigned invented units or topology.
- Limited extraction is labelled limited.
- A CAD kernel is required for authoritative BREP/topology operations.

## Security
- Browser clients use Supabase user sessions and RLS.
- Service secrets never ship to the browser.
- Uploaded files are size-limited and content-validated.
- External actions require explicit approval.
