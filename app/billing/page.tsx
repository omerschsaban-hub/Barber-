'use client'

import { useEffect, useState } from 'react'
import {
  FABRINAT_PRO_ENTITLEMENT,
  getWebOffering,
  purchaseWebPackage,
} from '@/lib/revenuecat-web'

export default function BillingPage() {
  const [userId, setUserId] = useState<string | null>(null)
  const [packages, setPackages] = useState<any[]>([])
  const [selectedPackage, setSelectedPackage] = useState<any>(null)
  const [pro, setPro] = useState(false)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function getBackendAccess() {
    const response = await fetch('/api/revenuecat/access', { cache: 'no-store' })
    const body = await response.json() as { pro?: boolean; error?: string }
    if (!response.ok) throw new Error(body.error || 'Unable to verify subscription access')
    return Boolean(body.pro)
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
        const [offering, backendPro] = await Promise.all([
          getWebOffering(id),
          getBackendAccess(),
        ])
        if (cancelled) return
        const available = offering?.availablePackages ?? []
        setPackages(available)
        setSelectedPackage(available[0] ?? null)
        setPro(backendPro)
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
        if (await getBackendAccess()) {
          setPro(true)
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
      <h1 className="title">Fabrient Pro</h1>
      <p className="muted">One RevenueCat entitlement controls Pro access across the web app and MCP.</p>
      <section className="panel" style={{ marginTop: 24 }}>
        {loading ? <p className="muted">Loading subscription…</p> : pro ? (
          <>
            <div className="status ok">PRO ACTIVE</div>
            <p className="muted">Entitlement: {FABRINAT_PRO_ENTITLEMENT}</p>
          </>
        ) : (
          <>
            <h2>Unlock Pro</h2>
            <p className="muted">Advanced 3D risk analysis, manufacturing exports, inspection analytics, and extended MCP tools.</p>
            {packages.length > 0 ? (
              <>
                <div className="grid grid2" style={{ margin: '20px 0' }}>
                  {packages.map((item: any) => {
                    const selected = selectedPackage?.identifier === item.identifier
                    return <button key={item.identifier} type="button" className={`panel ${selected ? 'selected-plan' : ''}`} onClick={() => setSelectedPackage(item)} aria-pressed={selected} style={{ textAlign: 'left', cursor: 'pointer' }}>
                      <strong>{item.product.title}</strong>
                      <div className="title" style={{ fontSize: 28, margin: '8px 0' }}>{item.product.priceString}</div>
                      <span className="muted">Secure checkout · cancel anytime</span>
                    </button>
                  })}
                </div>
                <button className="button primary" onClick={() => void buy()} disabled={busy}>
                  {busy ? 'Opening secure checkout…' : `Choose ${selectedPackage?.product?.title ?? 'plan'}`}
                </button>
              </>
            ) : <p className="error">No RevenueCat offering is currently available.</p>}
          </>
        )}
        {error && <p className="error">{error}</p>}
      </section>
    </main>
  )
}
