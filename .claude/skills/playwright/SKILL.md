# Playwright Browser Testing Skill

Use this skill whenever a task changes or depends on Fabrient UI behavior.

## Rule

Do not claim a UI feature works from code inspection. Start the app and exercise it in a real browser with Playwright.

## Workflow

1. Read `AGENTS.md` and `docs/DEEP_EXECUTION_STANDARD.md`.
2. Install dependencies with `npm ci` or `npm install` and install browser binaries with `npx playwright install --with-deps chromium` in CI/Linux when needed.
3. Start the app with the required safe test environment.
4. Exercise the primary user journey, not only a single selector.
5. Assert visible outcomes, URL/state transitions, network/API failures, and critical accessibility properties.
6. Test at least one invalid/error path for important workflows.
7. Save a trace/screenshot on failure.
8. Fix root causes and rerun.

## Test design

Prefer stable role/name/label selectors. Avoid brittle CSS selectors and arbitrary sleeps. Keep tests deterministic and isolated. Use fixtures and test-only accounts/data rather than real production credentials.

## Minimum Fabrient smoke coverage

- landing page renders
- start-project CTA reaches the intended workflow
- primary workspace route is reachable
- manufacturing route is reachable
- engineering/geometry/records routes are reachable when their prerequisites are satisfied
- no uncaught page errors in the smoke journey
- authenticated flows are covered in an environment with test credentials

## Safety

Never put production secrets in tests, fixtures, traces, screenshots, or committed files. Never weaken auth/RLS merely to make a browser test pass.
