# Production connectivity smoke test

This is the acceptance checklist for the shared backend boundary.

## Web

- [ ] Production browser loads the app.
- [ ] Browser request reaches the canonical backend through the shared client.
- [ ] Health/diagnostic request returns success.
- [ ] OTP request reaches backend.
- [ ] OTP verification establishes the authenticated session.
- [ ] Authenticated `/me` (or canonical identity endpoint) succeeds.
- [ ] One real engineering/business operation succeeds.
- [ ] The response contains the expected request ID.

## MCP

- [ ] OAuth metadata/discovery is reachable.
- [ ] Authorization and callback complete.
- [ ] Token/session is accepted by MCP.
- [ ] MCP can discover the expected capability.
- [ ] One real backend operation succeeds through MCP.
- [ ] MCP result is backed by the same backend operation used by the web app.
- [ ] Request/trace ID is preserved.

## Deployment gate

A path is not considered fixed until the deployed service passes the relevant checks. A successful local test or source-code inspection is insufficient.
