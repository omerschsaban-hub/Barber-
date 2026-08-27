'use client'

import { useEffect, useState } from 'react'
import {
  getWebOffering,
  purchaseWebPackage,
} from '@/lib/revenuecat-web'
import { ENTERPRISE_CONTACT, FABRINAT_PLANS } from '@/lib/fabrinat-plans'

const PLAN_ORDER = ['free', 'hobbyist', 'startup', 'enterprise'] as const

export default function BillingPage() {
  const [userId, setUserId] = useState<string | null>(null)
  const [packages, setPackages] = useState<any[]>([])
  const [selectedPackage, setSelectedPackage] = useState<any>(null)
  const [selectedPlan, setSelectedPlan] = useState<'hobbyist' | 'startup'>('hobbyist')
  const [plan, setPlan] = useState<string>('free')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function getBackendAccess() {
    const response = await fetch('/api/revenuecat/access', { cache: 'no-store' })
    const body = await response.json() as { pro?: boolean; plan?: string; error?: string }
    if (!response.ok) throw new Error(body.error || 'Unable to verify subscription access')
    return body
  }

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const auth = await fetch('/api/auth/me', { cache: 'no-store' })
        if (!auth.ok) throw new Error('Sign in before purchasing Fabrient Pro')
        const body = await auth.json() as { user?: { id?: string } }
        const id = body.user?.id
        if (!id) throw new Error('Sign in before purchasing Fabrient Pro')
        if (cancelled) return
        setUserId(id)
        const [offering, backendAccess] = await Promise.all([
          getWebOffering(id),
          getBackendAccess(),
        ])
        if (cancelled) return
        const available = offering?.availablePackages ?? []
        setPackages(available)
        const requested = new URLSearchParams(window.location.search).get('plan')
        const initialPlan = requested === 'startup' ? 'startup' : 'hobbyist'
        setSelectedPlan(initialPlan)
        const initialPackage = available.find((item: any) => {
          const text = `${item.identifier} ${item.product?.identifier ?? ''} ${item.product?.title ?? ''}`.toLowerCase()
          return initialPlan === 'startup' ? text.includes('startup') : text.includes('hobby') || text.includes('personal') || text.includes('pro')
        }) ?? available[0] ?? null
        setSelectedPackage(initialPackage)
        setPlan(backendAccess.plan ?? 'free')
      } catch (e: any) {
        if (!cancelled) setError(e?.message ?? 'Unable to load billing')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => { cancelled = true }
  }, [])

  async function buy() {
    if (!userId || !selectedPackage) return
    setBusy(true)
    setError('')
    try {
      await purchaseWebPackage(userId, selectedPackage)
      // RevenueCat delivers the entitlement asynchronously through the signed webhook.
      // Never grant Pro from client-side customer info alone.
      setError('Purchase completed. Waiting for entitlement confirmation…')
      for (let attempt = 0; attempt < 5; attempt += 1) {
        await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)))
        const access = await fetch('/api/revenuecat/access', { cache: 'no-store' })
        const accessBody = await access.json() as { plan?: string }
        if (access.ok && accessBody.plan && accessBody.plan !== 'free') {
          setPlan(accessBody.plan)
          setError('')
          break
        }
      }
    } catch (e: any) {
      if (!e?.userCancelled) setError(e?.message ?? 'Purchase failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="page" style={{ maxWidth: 720 }}>
      <div className="eyebrow">FABRIENT / BILLING</div>
      <h1 className="title">Choose your Fabrient plan</h1>
      <p className="muted">Free is useful on purpose. Hobby is for one builder. Startup is for teams of 1–29. Enterprise is for 30+ people and custom governance.</p>
      <section className="panel" style={{ marginTop: 24 }}>
        {loading ? <p className="muted">Loading plans…</p> : (
          <>
            <div className="grid grid2" style={{ marginBottom: 24 }}>
              {PLAN_ORDER.map((key) => {
                const item = FABRINAT_PLANS[key]
                const active = plan === key
                return <button key={key} type="button" className={`panel ${active ? 'selected-plan' : ''}`} onClick={() => { if (key === 'hobbyist' || key === 'startup') setSelectedPlan(key) }} aria-pressed={active} style={{ textAlign: 'left', cursor: key === 'enterprise' || key === 'free' ? 'default' : 'pointer' }}>
                  <strong>{item.name}</strong><div className="title" style={{ fontSize: 28, margin: '8px 0' }}>{item.billingLabel}</div><span className="muted">{item.audience}</span>
                </button>
              })}
            </div>
            {plan !== 'free' ? <div className="status ok">{plan.toUpperCase()} ACTIVE</div> : <p className="muted">Current access: Free. Choose a paid plan below to unlock more features.</p>}
            <p className="muted">Selected: {FABRINAT_PLANS[selectedPlan].name}. {FABRINAT_PLANS[selectedPlan].tagline}</p>
            {packages.length > 0 ? (
              <>
                <div className="grid grid2" style={{ margin: '20px 0' }}>
                  {packages.map((item: any) => {
                    const selected = selectedPackage?.identifier === item.identifier
                    return <button key={item.identifier} type="button" className={`panel ${selected ? 'selected-plan' : ''}`} onClick={() => setSelectedPackage(item)} aria-pressed={selected} style={{ textAlign: 'left', cursor: 'pointer' }}>
                      <strong>{item.product.title}</strong><div className="title" style={{ fontSize: 28, margin: '8px 0' }}>{item.product.priceString}</div><span className="muted">Secure checkout · signed entitlement confirmation</span>
                    </button>
                  })}
                </div>
                <button className="button primary" onClick={() => void buy()} disabled={busy || !selectedPackage}>{busy ? 'Opening secure checkout…' : `Choose ${FABRINAT_PLANS[selectedPlan].name}`}</button>
              </>
            ) : <p className="error">No paid RevenueCat package is currently available. Add the Hobby and Startup products to the current offering before accepting purchases.</p>}
            <div style={{ marginTop: 24 }}><strong>Enterprise</strong><p className="muted">30+ people, private deployment, governance, SSO and dedicated support.</p><a href={`mailto:${ENTERPRISE_CONTACT.email}?subject=Fabrient%20Enterprise%20plan`}>Email {ENTERPRISE_CONTACT.email}</a> · <a href={`tel:${ENTERPRISE_CONTACT.phone}`}>Call {ENTERPRISE_CONTACT.phone}</a></div>
          </>
        )}
        {error && <p className="error">{error}</p>}
      </section>
    </main>
  )
}
