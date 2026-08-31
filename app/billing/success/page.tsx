'use client'

import { Suspense } from 'react'
import { useSearchParams } from 'next/navigation'

function BillingSuccessContent() {
  const params = useSearchParams()
  const plan = params.get('plan')

  return (
    <main className="page" style={{ maxWidth: 720 }}>
      <div className="eyebrow">FABRIENT / BILLING</div>
      <h1 className="title">PayPal approval received</h1>
      <section className="panel" style={{ marginTop: 24 }}>
        <div className="status">PAYPAL VERIFICATION PENDING</div>
        <p className="muted" style={{ marginTop: 12 }}>
          PayPal approved the subscription{plan ? ` for the ${plan} plan` : ''}. Fabrient will unlock access only after the signed PayPal webhook is verified by the backend.
        </p>
        <p className="muted">If access does not change shortly, refresh Billing or contact support. Do not purchase again while verification is pending.</p>
        <a className="button primary" href="/billing" style={{ display: 'inline-block', marginTop: 12 }}>
          Return to billing
        </a>
      </section>
    </main>
  )
}

export default function BillingSuccessPage() {
  return <Suspense fallback={<main className="page" style={{ maxWidth: 720 }}><div className="eyebrow">FABRIENT / BILLING</div><h1 className="title">Loading payment status…</h1></main>}><BillingSuccessContent /></Suspense>
}
