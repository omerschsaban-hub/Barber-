# Fabrient Native Mobile Clients

This directory contains native API client layers for Android/Kotlin and iOS/Swift. Both clients use the owned Fabrient FastAPI service and intentionally keep session tokens in platform secure storage supplied by the host application. No production credentials, PayPal secrets, webhook secrets, database URLs, or Gmail OAuth values belong in these sources.

## Shared API contract

The clients cover OTP request and verification, authenticated billing access, engineering health, and logout. The default API origin is `https://fabrient-engineering.onrender.com`; applications may inject a staging or local origin at construction time. Requests use bounded timeouts and report non-2xx responses as errors. Paid-plan checkout opens the authenticated Fabrient web billing page, where PayPal handles approval.

## Android/Kotlin

The Kotlin source is under `android/src/main/kotlin`. The Gradle descriptor is ready for a JVM contract-test run with `gradle test`. A production Android app should wrap the client with Jetpack Compose or the existing product UI, store the session token in Android Keystore-backed storage, and open the Fabrient web checkout for paid plans.

## iOS/Swift

The Swift package is under `ios`. Run `swift test` on macOS with Xcode/Swift installed. A production iOS app should store the session token in Keychain and open the Fabrient web checkout for paid plans. Never ship PayPal client secrets or webhook credentials in the app.

## Verification

The Expo app is validated with `npm run typecheck` and `CI=1 npx expo export --platform web`. Native source contracts are checked in GitHub Actions, and native package tests run automatically when Gradle or Swift is present on the runner. This sandbox does not contain `gradle`, `swiftc`, or `xcodebuild`, so native compilation must be completed on an Android/macOS runner before store submission.
