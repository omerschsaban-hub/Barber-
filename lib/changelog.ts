export type ChangelogKind = 'added' | 'changed' | 'fixed' | 'security' | 'removed' | 'deprecated';

export type ChangelogItem = {
  kind: ChangelogKind;
  text: string;
};

export type ChangelogRelease = {
  version: string;
  date: string;
  title: string;
  items: ChangelogItem[];
};

/**
 * Public, release-oriented changelog data.
 * Keep this intentionally separate from raw Git history: users need outcomes,
 * not every implementation commit. CHANGELOG.md mirrors this public history.
 */
export const changelog: ChangelogRelease[] = [
  {
    version: '2026.08.31',
    date: '2026-08-31',
    title: 'LLM reliability and billing',
    items: [
      { kind: 'added', text: 'LLM-enhanced engineering copilot with a deterministic fallback when an LLM is unavailable.' },
      { kind: 'added', text: 'Best-effort LLM enrichment across data-flywheel agents.' },
      { kind: 'added', text: 'PayPal billing cutover and updated billing architecture.' },
      { kind: 'changed', text: 'Billing configuration and documentation now consistently use PayPal.' },
      { kind: 'fixed', text: 'Hardened the engineering copilot fallback path so it remains usable when an LLM call cannot complete.' },
    ],
  },
  {
    version: '2026.08.30',
    date: '2026-08-30',
    title: 'Billing migration cleanup',
    items: [
      { kind: 'changed', text: 'Updated the README and agent contract to match the PayPal billing direction.' },
      { kind: 'changed', text: 'Standardized payment-migration documentation.' },
      { kind: 'fixed', text: 'Replaced remaining RevenueCat environment placeholders with PayPal configuration.' },
    ],
  },
];

export const changelogKindLabel: Record<ChangelogKind, string> = {
  added: 'Added',
  changed: 'Changed',
  fixed: 'Fixed',
  security: 'Security',
  removed: 'Removed',
  deprecated: 'Deprecated',
};
