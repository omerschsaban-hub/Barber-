# Production connectivity smoke contract

This is the minimum end-to-end contract for Fabrient. A feature is not considered healthy until the browser and MCP can reach the same authoritative backend and complete an authenticated request.

## Browser path
1. Frontend loads over HTTPS.
2. Frontend resolves exactly one production API origin.
3. Browser can reach backend health endpoint.
4. Browser can start authentication.
5. Authentication callback/session is accepted by the backend.
6. Browser can call an authenticated identity endpoint.
7. Browser can call one representative protected feature endpoint.
8. Request/response correlation IDs are visible in diagnostics.

## MCP path
1. MCP endpoint is reachable over HTTPS.
2. Protected-resource/authorization discovery is reachable.
3. OAuth authorization can complete in a browser.
4. Callback exchanges the code for a token.
5. MCP request with the access token reaches the same backend authority.
6. Tool discovery succeeds.
7. A representative authenticated tool call succeeds.
8. Backend failures are returned as structured errors, never fabricated success.

## Shared backend invariant
The web app and MCP must use the same authoritative business/engineering operation layer and database state. Authentication, authorization, request correlation, and error semantics must be consistent across both paths.

## Current acceptance rule
Do not debug individual feature behavior as the first step when the connectivity ladder is red. Fix the earliest failed hop, redeploy, and rerun the ladder before diagnosing downstream feature-specific failures.

## MCP OAuth note
Implement against the currently supported MCP authorization specification. The 2026-07-28 MCP specification hardens authorization and changes client registration guidance; clients validate the authorization-server issuer and the ecosystem is moving from Dynamic Client Registration toward Client ID Metadata Documents. See the official MCP specification/release notes before changing the implementation.
