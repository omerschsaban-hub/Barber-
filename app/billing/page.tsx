'use client'

import { useEffect, useMemo, useState } from 'react'
import { createBrowserSupabase } from '@/lib/supabase-browser'

type Tier = {
  key: string
  name: string
  description: string
  url: string
}

const tierDefinitions = [
  {
    key: 'tier1',
    name: 'Tier 1',
    description: 'Core Fabrient capabilities.',
    env: 'NEXT_PUBLIC_REVENUECAT_WEB_PURCHASE_URL_TIER1',
  },
  {
    key: 'tier2',
    name: 'Tier 2',
    description: 'Expanded Fabrient capabilities.',
    env: 'NEXT_PUBLIC_REVENUECAT_WEB_PURCHASE_URL_TIER2',
  },
  {
    key: 'tier3',
    name: 'Tier 3',
    description: 'Full Fabrient capabilities.',
    env: 'NEXT_PUBLIC_REVENUECAT_WEB_PURCHASE_URL_TIER3',
  },
] as const

function buildPurchaseUrl(baseUrl: string, userId: string) {
  const trimmed = baseUrl.trim()
  if (!trimmed) return ''
  const url = new URL(trimmed)
  const path = url.pathname.replace(/\/$/, '')
  if (!path.split('/').pop() || path.split('/').pop() === url.hostname) {
    return ''
  }
  url.pathname = `${path}/${encodeURIComponent(userId)}`
  return url.toString()
}

export default function BillingPage() {
  const [userId, setUserId] = useState<string | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function loadUser() {
      const supabase = createBrowserSupabase()
      if (!supabase) {
        setError('Authentication is not configured')
        return
      }
      const { data, error: authError } = await supabase.auth.getUser()
      if (cancelled) return
      if (authError || !data.user) {
        setError('Sign in before purchasing a subscription.')
        return
      }
      setUserId(data.user.id)
    }
    void loadUser()
    return () => { cancelled = true }
  }, [])

  const tiers = useMemo<Tier[]>(() => tierDefinitions.map((tier) => {
    const baseUrl = process.env[tier.env] ?? ''
    return {
      key: tier.key,
      name: tier.name,
      description: tier.description,
      url: userId ? buildPurchaseUrl(baseUrl, userId) : '',
    }
  }), [userId])

  return (
    <main className="page" style={{ maxWidth: 900 }}>
      <div className="eyebrow">FABRIENT / BILLING</div>
      <h1 className="title">Choose your Fabrient plan</h1>
      <p className="muted">
        Checkout is hosted by RevenueCat. No Stripe UI or RevenueCat Web SDK runs in this app.
      </p>

      {error && <p className="error">{error}</p>}

      <section className="panel" style={{ marginTop: 24 }}>
        <div style={{ display: 'grid', gap: 16 }}>
          {tiers.map((tier) => (
            <div key={tier.key} className="panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
              <div>
                <h2 style={{ marginBottom: 6 }}>{tier.name}</h2>
                <p className="muted" style={{ margin: 0 }}>{tier.description}</p>
              </div>
              {tier.url ? (
                <a
                  className="button primary"
                  href={tier.url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Subscribe
                </a>
              ) : (
                <span className="muted">Checkout not configured</span>
              )}
            </div>
          ))}
        </div>
      </section>
    </main>
  )
}
