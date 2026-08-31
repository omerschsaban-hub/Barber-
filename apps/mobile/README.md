# Fabrient Mobile

Fabrient Mobile is the native Android and iOS client built with React Native, Expo Router, and TypeScript. It uses the owned Fabrient API for authentication, workspace data, engineering operations, and authoritative billing state. The app never connects directly to PostgreSQL and never contains PayPal secrets, MCP bearer tokens, or other privileged credentials.

## Local development

From `apps/mobile`:

```bash
npm install --legacy-peer-deps
npm run typecheck
npx expo start
```

For a web smoke build:

```bash
npx expo export --platform web
```

For native development, use `npm run android` or `npm run ios` on a machine with the corresponding Android or Xcode toolchain.

## Configuration

Set `EXPO_PUBLIC_FABRIENT_API_URL` to the deployed engineering API URL and `EXPO_PUBLIC_FABRIENT_WEB_URL` to the Vercel web URL. The mobile paywall opens the authenticated Fabrient web checkout, where PayPal handles approval. PayPal client secrets and webhook credentials remain server-side.

The mobile auth flow calls `/auth/request-otp`, `/auth/verify-otp`, `/auth/me`, and `/auth/logout`. The verification response supplies a session token that is stored on-device and sent as a bearer token to the owned API. Subscription access is read from the backend entitlement state after verified PayPal webhook processing.

## Product screens

The app provides an owned-auth login flow, authenticated overview, plan and entitlement state, projects, release evidence, settings, PayPal web-checkout handoff, loading states, error states, and logout. Native Kotlin/Swift modules should be added only for platform-specific capabilities such as secure storage, push registration, and deep links; shared feature logic remains in TypeScript.

## Verification

The mobile CI workflow runs install, TypeScript validation, Expo web export, and a production dependency audit. The current Expo 57 toolchain still reports moderate advisories in its transitive build tooling; `npm audit fix --force` would request a breaking Expo downgrade and is intentionally not applied without a compatibility upgrade plan.

The production backend remains the authority for Gmail OTP delivery and PayPal entitlements. A successful browser approval screen alone is not proof of a completed purchase; the verified PayPal webhook and backend entitlement record are required.
