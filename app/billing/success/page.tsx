'use client'

import { useSearchParams } from 'next/navigation'

export default function BillingSuccessPage() {
  const params = useSearchParams()
  const appUserId = params.get('app_user_id')
  const redeemUrl = params.get('redeem_url')

  return (
    <main className="page" style={{ maxWidth: 720 }}>
      <div className="eyebrow">FABRIENT / BILLING</div>
      <h1 className="title">Purchase complete</h1>
      <section className="panel" style={{ marginTop: 24 }}>
        <div className="status ok">SUBSCRIPTION RECEIVED</div>
        <p className="muted" style={{ marginTop: 12 }}>
          RevenueCat has received your purchase. Your Fabrient account will use the RevenueCat entitlement state as the subscription source of truth.
        </p>
        {appUserId && (
          <p className="muted">Account: {appUserId}</p>
        )}
        {redeemUrl && (
          <p className="muted">
            If RevenueCat provided a redemption link for this purchase, use it from the hosted purchase experience to associate the purchase with your account or app.
          </p>
        )}
        <a className="button primary" href="/billing" style={{ display: 'inline-block', marginTop: 12 }}>
          Return to billing
        </a>
      </section>
    </main>
  )
}
