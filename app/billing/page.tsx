'use client'

import { useEffect, useState } from 'react'
import {
  FABRINAT_PRO_ENTITLEMENT,
  getWebCustomerInfo,
  getWebOffering,
  hasProEntitlement,
  purchaseWebPackage,
} from '@/lib/revenuecat-web'

export default function BillingPage() {
  const [userId, setUserId] = useState<string | null>(null)
  const [packageInfo, setPackageInfo] = useState<any>(null)
  const [pro, setPro] = useState(false)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

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
        const [offering, info] = await Promise.all([
          getWebOffering(id),
          getWebCustomerInfo(id),
        ])
        if (cancelled) return
        setPackageInfo(offering?.availablePackages?.[0] ?? null)
        setPro(hasProEntitlement(info))
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
    if (!userId || !packageInfo) return
    setBusy(true)
    setError('')
    try {
      const result = await purchaseWebPackage(userId, packageInfo)
      setPro(hasProEntitlement(result.customerInfo))
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
            {packageInfo ? (
              <button className="button primary" onClick={() => void buy()} disabled={busy}>
                {busy ? 'Opening secure checkout…' : `${packageInfo.product.title} · ${packageInfo.product.priceString}`}
              </button>
            ) : <p className="error">No RevenueCat offering is currently available.</p>}
          </>
        )}
        {error && <p className="error">{error}</p>}
      </section>
    </main>
  )
}
