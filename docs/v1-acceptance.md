# Fabrient v1 engineering acceptance gates

## Ground truth
- Physical inspection measurements are authoritative.
- Synthetic simulation samples are not physical acceptance evidence.
- PostgreSQL is the target production database.
- Database acceptance must be proven against the actual PostgreSQL deployment, not an old or deprecated database service.

## Authentication and authorization
- Browser clients use the application's authenticated user sessions.
- Database authorization must be enforced by the production PostgreSQL authorization model and application/API boundaries.
- Privileged database credentials remain server-side only.

## Release evidence
- Every engineering release requires the applicable deterministic, measurement, uncertainty, provenance and manufacturing evidence gates.
- A green status is valid only when the underlying evidence exists and can be reproduced.
