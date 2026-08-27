# Video hardening implementation

This is the implementation record for the two uploaded 20-point videos. It is deliberately written as a release gate, not a marketing checklist.

## Video A — remove the visible signs of a generic/vibe-coded website

The product surface is now governed by these 20 checks:

1. No default AI-purple gradient unless the brand has a deliberate reason.
2. No gradient hero text used as decoration.
3. No sparkles or emoji used as fake product/UI icons.
4. No generic centered-hero + three-identical-card template as the primary composition.
5. No glassmorphism/glow effects that do not communicate state.
6. No generic AI-generated people/faces as fake product proof.
7. No fake testimonials or invented customer quotes.
8. No invented counters, customer totals, savings claims or vanity metrics.
9. No placeholder company/person names presented as real customers.
10. No dead social icons or buttons that do nothing.
11. No non-functional toggles, tabs, carousels or interactive decoration.
12. No excessive scroll-triggered animation; motion must communicate state or hierarchy.
13. Loading states exist for asynchronous product actions.
14. Action buttons communicate progress and prevent accidental duplicate submission.
15. Data-heavy surfaces use intentional empty/loading/error states.
16. Typography uses a deliberate hierarchy rather than random sizes/weights.
17. Spacing and border radii use a small consistent design system.
18. Icons remain proportional to their labels and surrounding controls.
19. Copy avoids generic AI marketing filler and excessive em-dash/"not X, but Y" patterns.
20. Every public claim has a source, a real product behavior behind it, or is clearly framed as a goal.

Current implementation notes:
- The landing page was rewritten around a real engineering workflow and no longer uses fake social proof, fake counters, emoji icons, or a template-style testimonial section.
- The page uses a real manufacturing photograph rather than generated people as product proof.
- The product flow is expressed as a single job lifecycle rather than a feature dump.
- Public claims are limited to behavior represented in the repository.
- The remaining UI audit is enforced by the scanner below rather than by subjective visual claims.

## Video B — launch/security hardening

1. HSTS is enabled in production.
2. CSRF protection rejects cross-site cookie-authenticated mutations.
3. Session cookies remain HttpOnly/Secure/SameSite where issued.
4. Authentication state is refreshed server-side for protected routes.
5. Reset/OTP links and codes expire and are single-use where implemented.
6. Authentication responses avoid revealing whether an account exists.
7. Uploads have server-side size and type/parse validation.
8. Server-side request validation is required; client validation is not trusted.
9. Payment/entitlement decisions are server-side only.
10. Webhook endpoints authenticate/verify their event source before changing entitlement state.
11. AI/API request rate limits are enforced server-side.
12. Request body size limits are enforced server-side.
13. Password/OTP reset endpoints have dedicated throttling and attempt limits.
14. Untrusted text is sanitized/validated before being persisted or rendered in privileged contexts.
15. CORS is allowlisted at the production engineering boundary.
16. Directory listing is not exposed by the application/runtime.
17. Security headers include CSP, MIME sniffing protection, clickjacking protection, referrer policy and Permissions Policy.
18. Privileged/admin routes require authenticated authorization rather than UI-only hiding.
19. Failed authentication/authorization paths fail closed and do not leak secrets or internal stack traces.
20. Database access is parameterized and production migration/rollback remains gated until an actual operation succeeds.

Current implementation notes:
- The Next middleware already applies the main browser security headers, same-origin mutation protection, and API rate limiting.
- OTP request/verification limits and generic auth responses are already part of the auth surface.
- Engineering JSON and file upload limits are enforced server-side.
- The engineering service has an origin allowlist and request-size gate.
- RevenueCat/entitlement changes are required to be server-side; production verification remains a deployment gate.
- The current repository still contains a legacy internal FastAPI app with a wildcard CORS middleware. The production wrapper blocks disallowed origins, but the legacy middleware should be removed when that file is next refactored; do not mark this item green until the deployed response is tested.

## Release rule

A checklist item is green only after:

**source change → build → deployment → deployed behavior test.**

A static code match is not sufficient for a production claim.
