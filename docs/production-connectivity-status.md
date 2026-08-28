# Production connectivity status

## Required acceptance path

Web: Browser -> Vercel -> shared backend client -> Render backend -> auth/database

MCP: MCP client -> OAuth -> MCP -> backend -> auth/database

## Current verified blocker

Render builds for the production backend and MCP services are currently blocked by the Render workspace build-pipeline-minute limit. Recent deploy attempts are reported as `build_failed` because Render cancels builds when the workspace has no build-pipeline minutes remaining. Therefore the latest Git commits cannot yet be deployed to the live Render services.

## Rule

Do not mark frontend/backend connectivity, OTP, or MCP OAuth as production-fixed until the deployed services pass real end-to-end acceptance tests for both paths.

## Required tests after Render builds are restored

1. Browser can reach the canonical backend health endpoint through the production frontend path.
2. Browser can request and verify OTP, then make an authenticated API request.
3. MCP client can complete OAuth discovery/authorization/token flow.
4. MCP can establish an authenticated session and call a real backend operation.
5. Web and MCP invoke the same authoritative backend operation and receive equivalent structured results.
6. Request IDs are visible across frontend, backend, and MCP logs for failed requests.
