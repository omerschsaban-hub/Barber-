# Changelog

All notable product and engineering changes are recorded here.

The public changelog is intentionally release-oriented rather than a raw dump of Git commits. Internal implementation details, secrets, and noisy maintenance commits stay out of the customer-facing history.

## 2026-08-31

### Added
- LLM-enhanced engineering copilot with a deterministic fallback when an LLM is unavailable.
- Best-effort LLM enrichment across data-flywheel agents.
- PayPal billing cutover and updated billing architecture documentation.

### Changed
- Billing documentation and configuration now consistently use PayPal rather than the previous RevenueCat references.
- Agent contract documentation now reflects the PayPal architecture.

### Reliability
- Hardened the engineering copilot fallback path so the feature remains usable when an LLM call cannot be completed.

## 2026-08-30

### Documentation
- Updated the README and agent contract to match the PayPal billing direction.
- Standardized payment-migration documentation.

### Configuration
- Replaced remaining RevenueCat environment placeholders with PayPal configuration.

---

## How entries are published

1. Changes are implemented and tested.
2. A release owner groups user-visible changes into a release entry.
3. Internal-only implementation details are excluded from the public entry.
4. The release is added here and mirrored in the in-app `/changelog` page.

This file is the source of truth for the repository changelog. The in-app page uses the same release data so the two surfaces do not drift.
