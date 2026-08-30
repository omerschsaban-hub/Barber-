'use client'

import { useEffect, useState } from 'react'
import { ENTERPRISE_CONTACT, FABRINAT_PLANS, planUsageLabel } from '@/lib/fabrinat-plans'
import PlanFeatureMatrix from '@/components/plan-feature-matrix'

const PLAN_ORDER = ['free', 'hobbyist', 'startup', 'enterprise'] as const

type PaypalConfig = { configured: boolean; environment: string; plans?: Record<string, string | null> }
type PaypalStatus = { subscription?: { plan?: string; status?: string; environment?: string } | null }

export default function BillingPage() {
  const [config, setConfig] = useState<PaypalConfig | null>(null)
  const [plan, setPlan] = useState('free')
  const [selectedPlan, setSelectedPlan] = useState<'hobbyist' | 'startup'>('hobbyist')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function loadBilling() {
    const [configResponse, statusResponse] = await Promise.all([
      fetch('/api/engineering/billing/paypal/config', { cache: 'no-store' }),
      fetch('/api/engineering/billing/paypal/status', { cache: 'no-store' }),
    ])
    const configBody = await configResponse.json() as PaypalConfig & { error?: string }
    const statusBody = await statusResponse.json() as PaypalStatus & { error?: string }
    if (!configResponse.ok) throw new Error(configBody.error || 'Unable to load PayPal configuration')
    if (!statusResponse.ok) throw new Error(statusBody.error || 'Unable to load billing status')
    setConfig(configBody)
    const activePlan = statusBody.subscription?.status === 'ACTIVE' ? statusBody.subscription.plan : 'free'
    setPlan(activePlan || 'free')
  }

  useEffect(() => {
    const requested = new URLSearchParams(window.location.search).get('plan')
    if (requested === 'startup') setSelectedPlan('startup')
    void loadBilling().catch((e: any) => setError(e?.message || 'Unable to load billing')).finally(() => setLoading(false))
  }, [])

  async function startPaypalCheckout() {
    setBusy(true)
    setError('')
    try {
      const response = await fetch('/api/engineering/billing/paypal/create-subscription', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ plan: selectedPlan }),
      })
      const body = await response.json() as { approval_url?: string; error?: string }
      if (!response.ok || !body.approval_url) throw new Error(body.error || 'PayPal checkout is unavailable')
      window.location.assign(body.approval_url)
    } catch (e: any) {
      setError(e?.message || 'Unable to start PayPal checkout')
      setBusy(false)
    }
  }

  return (
    <main className="page" style={{ maxWidth: 720 }}>
      <div className="eyebrow">FABRIENT / BILLING</div>
      <h1 className="title">Choose your Fabrient plan</h1>
      <p className="muted">Secure web checkout is handled by PayPal. Access is granted only after a verified PayPal webhook reaches the backend.</p>
      <section className="panel" style={{ marginTop: 24 }}>
        {loading ? <p className="muted">Loading plans…</p> : <>
          <div className="grid grid2" style={{ marginBottom: 24 }}>
            {PLAN_ORDER.map((key) => {
              const item = FABRINAT_PLANS[key]
              const active = plan === key
              const selectable = key === 'hobbyist' || key === 'startup'
              return <button key={key} type="button" className={`panel ${active ? 'selected-plan' : ''}`} onClick={() => { if (selectable) setSelectedPlan(key) }} aria-pressed={active} style={{ textAlign: 'left', cursor: selectable ? 'pointer' : 'default' }}>
                <strong>{item.name}</strong><div className="title" style={{ fontSize: 28, margin: '8px 0' }}>{item.billingLabel}</div><span className="muted">{item.audience}</span><small className="muted" style={{ display: 'block', marginTop: 8 }}>{planUsageLabel(key)}</small>
              </button>
            })}
          </div>
          {plan !== 'free' ? <div className="status ok">{plan.toUpperCase()} ACTIVE</div> : <p className="muted">Current access: Free. Choose a paid plan below.</p>}
          <p className="muted">Selected: {FABRINAT_PLANS[selectedPlan].name}. {FABRINAT_PLANS[selectedPlan].tagline}</p>
          {config?.configured ? <>
            <p className="muted">PayPal environment: <strong>{config.environment}</strong>. Your browser will open PayPal’s secure approval page.</p>
            <button className="button primary" onClick={() => void startPaypalCheckout()} disabled={busy}>{busy ? 'Opening PayPal…' : `Continue with PayPal — ${FABRINAT_PLANS[selectedPlan].name}`}</button>
          </> : <p className="error">PayPal sandbox is not configured yet. Add the PayPal client credentials and plan IDs on the engineering service before accepting payments.</p>}
          {new URLSearchParams(typeof window === 'undefined' ? '' : window.location.search).get('paypal') === 'approved' && <p className="status">PayPal approved. Waiting for verified subscription webhook confirmation…</p>}
          {new URLSearchParams(typeof window === 'undefined' ? '' : window.location.search).get('paypal') === 'cancelled' && <p className="muted">PayPal checkout was cancelled. No access was changed.</p>}
          <div style={{ marginTop: 24 }}><strong>Enterprise</strong><p className="muted">30+ people, private deployment, governance, SSO and dedicated support.</p><a href={`mailto:${ENTERPRISE_CONTACT.email}?subject=Fabrient%20Enterprise%20plan`}>Email {ENTERPRISE_CONTACT.email}</a> · <a href={`tel:${ENTERPRISE_CONTACT.phone}`}>Call {ENTERPRISE_CONTACT.phone}</a></div>
          <PlanFeatureMatrix />
        </>}
        {error && <p className="error">{error}</p>}
      </section>
    </main>
  )
}
