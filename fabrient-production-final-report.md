# Fabrient Production Migration — Final Verification Report

**Date:** 30 August 2026
**Repository:** `omerschsaban-hub/Barber-`
**Final branch:** `main`

## Executive conclusion

The owned PostgreSQL/FastAPI engineering platform, plan catalog, owned MCP OAuth service, authenticated MCP contract, authentication path, and deployment/acceptance infrastructure are documented separately from payment-provider configuration.

**Payment provider decision:** Fabrient is switching from **RevenueCat to PayPal**. RevenueCat is no longer the intended billing provider.

The PayPal migration is an account/integration task and is **not claimed complete by this report**. The actual PayPal application, products/plans, checkout implementation, webhook endpoint, webhook verification, credentials, and live/sandbox payment round trip must be implemented and verified before billing can be marked production-ready.

No PayPal credentials should be invented, committed to source, or pasted into chat.

## Implemented product contract

| Area | Implemented result |
|---|---|
| Plans | Free, Hobby ($9 individual), Startup ($49 for teams of 1–29), Enterprise (contact) |
| Usage gating | Authoritative resolver in `engineering/app/plan_catalog.py`; paid-tier entitlements and limits remain backend-controlled |
| Landing pricing | Shared plan catalog drives the pricing UI |
| Engineering parity | Existing engineering compatibility and validation work remains unchanged |
| Billing authority | **PostgreSQL backend entitlement state, with PayPal as the intended external payment provider** |
| Auth | Owned PostgreSQL-backed auth/OAuth path and Gmail OTP routes |
| MCP | Owned OAuth metadata and authenticated MCP registry/call contract |
| Infrastructure | Render PostgreSQL and deployment configuration |
| Frontend | Responsive pricing UI and product routes in the Next.js app |

## PayPal billing contract

The target payment flow is:

1. A signed-in customer selects a Fabrient plan.
2. Fabrient creates or opens the corresponding PayPal checkout/subscription flow.
3. The customer completes the payment on PayPal.
4. PayPal sends the relevant server-side event/webhook.
5. Fabrient verifies the PayPal event according to PayPal's verification requirements.
6. The backend records the authoritative payment/entitlement state in PostgreSQL.
7. The frontend reads the entitlement from the backend.
8. Paid access is granted only from verified backend state.

A browser success redirect is never sufficient evidence of payment.

## PayPal configuration contract

The final implementation should use only the variables it actually consumes. Candidate server-side configuration includes:

| Variable | Purpose |
|---|---|
| `PAYPAL_CLIENT_ID` | PayPal application client identifier |
| `PAYPAL_CLIENT_SECRET` | PayPal application secret; server-side only |
| `PAYPAL_WEBHOOK_ID` | PayPal webhook identifier when required for verification |
| `PAYPAL_ENVIRONMENT` | `sandbox` during testing and `live` in production |
| `PAYPAL_PLAN_ID_*` | Recurring PayPal billing-plan identifiers, if subscriptions are implemented with PayPal plans |

Exact variable names must match the final implementation. Do not expose secrets through `NEXT_PUBLIC_*` variables.

## PayPal sandbox verification requirements

Before billing is marked PASS:

1. Configure a PayPal sandbox application.
2. Configure the required sandbox products/plans.
3. Configure the server-side webhook endpoint.
4. Verify webhook authenticity server-side.
5. Complete a real sandbox checkout using a sandbox test account.
6. Confirm the backend receives and validates the PayPal event.
7. Confirm PostgreSQL records the correct payment/entitlement state.
8. Confirm Fabrient reflects the paid plan using backend state.
9. Test cancellation, expiration, failed payment, duplicate events, and invalid/forged webhook data.

Mocks and client-only success states must not be used to claim billing PASS.

## Production verification requirements

After sandbox verification:

1. Configure the production PayPal application.
2. Configure production products/plans.
3. Configure the production webhook endpoint.
4. Store production secrets only in the server-side deployment environment.
5. Perform an appropriate controlled production payment if needed.
6. Verify the payment and webhook round trip.
7. Confirm PostgreSQL remains the authoritative entitlement source.

## Migration completion rule

The billing migration is complete only when all of these are true:

- no active production billing path depends on RevenueCat;
- PayPal checkout works;
- PayPal server-side verification works;
- the PayPal webhook is verified server-side;
- PostgreSQL is the authoritative entitlement/payment state;
- cancellation, expiration and failure behavior are handled;
- duplicate and forged webhook events are rejected or safely idempotent;
- no PayPal secret reaches browser JavaScript;
- a real sandbox payment has produced verified backend entitlement evidence.

## Existing non-billing verification

Existing CI, engineering, MCP, auth, browser, deployment and security checks should continue to be treated according to their own evidence. Payment-provider verification is now a separate PayPal gate.

## Remaining account-side actions

### 1. Configure PayPal

Create/use the appropriate PayPal developer application and configure the intended Fabrient products/plans.

### 2. Configure server-side environment

Add the exact PayPal variables required by the implementation to the appropriate Render/Vercel server-side environments. Never send the values in chat or commit them.

### 3. Implement checkout

Replace the existing billing checkout path with PayPal checkout/subscription creation as appropriate for the selected pricing model.

### 4. Implement webhook verification

Receive PayPal server-side events, verify authenticity, make processing idempotent, and update PostgreSQL entitlement state.

### 5. Remove RevenueCat dependency

Remove or disable active RevenueCat checkout, SDK, webhook, environment-variable, and entitlement dependencies once the PayPal path is verified. Do not remove working billing behavior before PayPal has passed its tests.

### 6. Run the final billing tests

Perform a real sandbox purchase and verify the full round trip:

**Customer → PayPal → verified webhook → PostgreSQL entitlement → Fabrient paid access**

## Security reminders

Use HTTPS. Keep PayPal client secrets and webhook credentials server-side. Never grant paid access solely from a browser redirect. Never disable webhook verification to make a test pass. Treat webhook processing as untrusted input and make entitlement updates idempotent.

## Final status

**Engineering/platform:** continue using the repository's existing verification evidence.

**Billing:** **NOT YET VERIFIED — migration target is PayPal.**

The repository documentation has been updated so PayPal is the intended payment provider. The actual provider replacement remains to be performed and tested by the account owner.
