'use client'

import Link from 'next/link'
import EngineeringCopilot from '@/app/engineering/EngineeringCopilot'
import {useEffect, useState} from 'react'

const ENGINE = '/api/engineering'
const REQUEST_TIMEOUT_MS = 20_000

type Health = 'checking' | 'ready' | 'blocked'

async function checkHealth() {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)
  try {
    const response = await fetch(`${ENGINE}/health`, {method: 'GET', signal: controller.signal})
    if (!response.ok) throw new Error(`Engineering service returned ${response.status}`)
    return true
  } finally {
    window.clearTimeout(timer)
  }
}

export default function Workspace() {
  const [service, setService] = useState<Health>('checking')
  const [error, setError] = useState('')

  async function refreshHealth() {
    setService('checking')
    setError('')
    try {
      await checkHealth()
      setService('ready')
    } catch (e: any) {
      setService('blocked')
      setError(e?.message || 'Engineering service unavailable')
    }
  }

  useEffect(() => { refreshHealth() }, [])

  return <main className="page wide">
    <div className="workspace-head">
      <div>
        <div className="eyebrow">FABRIENT / WORKSPACE</div>
        <h1 className="title">What are you working on?</h1>
        <p className="muted">Bring what you already have. Fabrient works out the next steps and only asks when it truly needs you.</p>
      </div>
      <div className={`status ${service === 'ready' ? 'ok' : 'warn'}`} role="status" aria-live="polite">
        {service === 'checking' ? 'CONNECTING…' : service === 'ready' ? 'READY' : 'CONNECTION NEEDED'}
      </div>
    </div>

    {service === 'blocked' && <section className="panel" style={{marginTop:16}} role="alert">
      <strong>Fabrient cannot reach the engineering service.</strong>
      <p className="error">{error}</p>
      <p className="muted">No result is shown until the service responds.</p>
      <button className="button" onClick={refreshHealth}>Try again</button>
    </section>}

    <section className="panel" style={{marginTop:16}}>
      <div className="eyebrow">START HERE</div>
      <h2>Bring a file, a problem, or a goal.</h2>
      <p className="muted">You don't need to fill in a long form. Upload your design or tell Fabrient what you want to get done. We'll reuse project information and saved settings instead of asking you for the same details again.</p>
      <div className="row" style={{marginTop:14, flexWrap:'wrap'}}>
        <Link className="button primary" href="/geometry">Add a STEP file</Link>
        <Link className="button" href="/engineering">Engineering</Link>
        <Link className="button" href="/calibration">Monitoring</Link>
        <Link className="button" href="/manufacturing">Manufacturing</Link>
        <Link className="button" href="/records">Inspection</Link>
        <Link className="button" href="/projects">Projects</Link>
      </div>
    </section>

    <EngineeringCopilot />

    <section className="panel" style={{marginTop:16}}>
      <div className="eyebrow">HOW IT WORKS</div>
      <h2>You give Fabrient the goal. It handles the busywork.</h2>
      <div className="workspace-grid" style={{marginTop:12}}>
        <div><strong>Bring what you have</strong><p className="muted">STEP files, measurements, inspection records, project data, or just a plain-language goal.</p></div>
        <div><strong>Fabrient fills in the gaps</strong><p className="muted">It reads available information, reuses saved context, chooses the checks that apply, and runs the next safe step automatically.</p></div>
        <div><strong>You step in when it matters</strong><p className="muted">If the answer can be safely known, Fabrient handles it. If a real engineering choice is missing, it asks one clear question.</p></div>
      </div>
      <details style={{marginTop:16}}>
        <summary>Show technical details</summary>
        <p className="muted">Engineering checks, measurements, simulations, evidence and release gates remain available. They are kept out of the main path so the product stays simple without hiding useful engineering capability.</p>
      </details>
    </section>
  </main>
}
