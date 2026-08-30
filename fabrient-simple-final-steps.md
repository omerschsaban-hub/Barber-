# Fabrient: simple final steps

## What is already done

The code is on `main` at the latest committed revision. The engineering, MCP, auth, acceptance, and deployment checks described by the repository remain separate from payment-provider configuration.

## Important: payment provider migration

Fabrient's intended payment provider is now **PayPal**. RevenueCat is no longer the intended billing provider for the product.

The actual PayPal integration, account configuration, credentials, products/plans, checkout links, webhooks, and live payment verification are **not claimed complete by this document**. The account owner will perform that replacement separately.

Do not invent PayPal credentials or paste secrets into source code or chat.

## Step 1: open the GitHub repository

1. Open the repository.
2. Click **Settings**.
3. Click **Secrets and variables**.
4. Click **Actions**.

## Step 2: configure deployment/account secrets

Create only the secrets actually required by the current implementation. Payment-provider secrets must remain server-side.

For PayPal, the eventual integration may require values such as:

| Secret/config | Purpose |
| --- | --- |
| `PAYPAL_CLIENT_ID` | PayPal application client identifier, if the chosen integration uses the PayPal API |
| `PAYPAL_CLIENT_SECRET` | PayPal application secret; server-side only |
| `PAYPAL_WEBHOOK_ID` | PayPal webhook identifier, if webhook verification uses the webhook ID |
| `PAYPAL_ENVIRONMENT` | `sandbox` during testing and `live` for production, according to the implementation |
| `PAYPAL_PLAN_ID_*` | PayPal billing-plan identifiers, if recurring subscriptions are implemented with PayPal plans |

Use the exact variable names implemented by the final PayPal integration. Do not add placeholder secrets that the application does not consume.

## Step 3: update Render environment variables

Open the relevant Render services and add the PayPal variables required by the implemented integration. Keep all PayPal secrets server-side. Never put a PayPal secret in a `NEXT_PUBLIC_*` variable.

The database, auth, MCP, and engineering-service variables remain unchanged unless the implementation requires otherwise.

## Step 4: PayPal checkout and billing flow

The intended production flow is:

1. A signed-in customer selects a Fabrient plan.
2. Fabrient creates or opens the appropriate PayPal checkout/subscription flow.
3. The customer completes payment on PayPal.
4. PayPal sends the relevant server-side event/webhook.
5. Fabrient verifies the event according to PayPal's webhook/API verification rules.
6. The backend records the authoritative entitlement/payment state in PostgreSQL.
7. The frontend reads the entitlement state from the backend.
8. Access is granted only from verified backend state.

A client-side success redirect is not sufficient proof of payment.

## Step 5: test PayPal in sandbox

Before production:

1. Configure a PayPal sandbox application.
2. Configure the required sandbox products/plans if recurring billing is used.
3. Configure the PayPal sandbox webhook endpoint.
4. Verify webhook authenticity server-side.
5. Complete a real sandbox checkout with a sandbox test account.
6. Confirm the backend receives and validates the PayPal event.
7. Confirm PostgreSQL records the correct customer/payment/entitlement state.
8. Refresh Fabrient and confirm the paid plan is reflected by backend state.
9. Test cancellation, expiration, duplicate webhook delivery, failed payment, and invalid/forged webhook data.

Do not mark billing as passing from a mocked request or a client-side success page.

## Step 6: verify production billing

Only after sandbox verification:

1. Configure the production PayPal application.
2. Configure production products/plans.
3. Configure the production webhook endpoint.
4. Store production secrets only in the server-side deployment environment.
5. Run a controlled production payment if appropriate.
6. Verify the payment and webhook round trip.
7. Confirm the backend entitlement is authoritative.

## Step 7: final checks

The payment migration is complete only when:

- no active production billing path depends on RevenueCat;
- PayPal checkout works;
- PayPal server-side verification works;
- the PayPal webhook is verified server-side;
- PostgreSQL is the authoritative entitlement/payment state;
- cancellation/expiration/failure behavior is tested;
- duplicate and forged webhook events are rejected or safely ignored;
- no PayPal secret is exposed to the browser.

## Security reminders

Use HTTPS. Keep `PAYPAL_CLIENT_SECRET` and any webhook/signing credentials out of browser JavaScript and out of chat. Never weaken webhook verification to make a test pass. Never grant paid access solely because a browser was redirected to a success URL.

## Done

When the PayPal integration has been implemented and the live/sandbox verification gates are green, update this document with the exact implemented variable names and evidence. Until then, this document intentionally describes the target PayPal architecture without claiming the account-side integration is complete.
