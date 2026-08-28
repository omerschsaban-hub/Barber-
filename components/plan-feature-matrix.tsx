'use client'

import { FABRINAT_PLANS, FEATURE_COPY, planHasFeature, type FabrinatPlan } from '@/lib/fabrinat-plans'

const PLAN_ORDER: FabrinatPlan[] = ['free', 'hobbyist', 'startup', 'enterprise']

export default function PlanFeatureMatrix() {
  const rows = Object.entries(FEATURE_COPY)
  return (
    <div className="pricing-comparison">
      <h3>Complete feature access</h3>
      <p className="muted">This table is generated from the same entitlement rules the app uses. “Included” means the tier is allowed to use that capability; engineering gates can still require evidence or human approval.</p>
      <div className="pricing-table" role="table" aria-label="Complete feature access by plan">
        <div className="pricing-row pricing-row-head" role="row"><strong>Capability</strong>{PLAN_ORDER.map((key) => <strong key={key}>{FABRINAT_PLANS[key].name}</strong>)}</div>
        {rows.map(([feature, copy]) => <div className="pricing-row" role="row" key={feature}><span>{copy.title}</span>{PLAN_ORDER.map((key) => <span key={key} aria-label={`${FABRINAT_PLANS[key].name}: ${planHasFeature(key, feature) ? 'included' : 'not included'}`}>{planHasFeature(key, feature) ? 'Included' : '—'}</span>)}</div>)}
      </div>
    </div>
  )
}
