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
        <h1 className="title">Your engineering workspace.</h1>
        <p className="muted">Bring the file, problem, or goal you already have. Fabrient handles technical details and only asks when a real engineering decision cannot be inferred safely.</p>
      </div>
      <div className={`status ${service === 'ready' ? 'ok' : 'warn'}`} role="status" aria-live="polite">
        {service === 'checking' ? 'ENGINE CONNECTING…' : service === 'ready' ? 'ENGINE READY' : 'ENGINE ACTION NEEDED'}
      </div>
    </div>

    {service === 'blocked' && <section className="panel" style={{marginTop:16}} role="alert">
      <strong>The engineering service is not reachable.</strong>
      <p className="error">{error}</p>
      <p className="muted">No fabricated result is shown.</p>
      <button className="button" onClick={refreshHealth}>Retry connection</button>
    </section>}

    <section className="panel" style={{marginTop:16}}>
      <div className="eyebrow">START WITH WHAT YOU HAVE</div>
      <h2>Bring the real design or describe the job.</h2>
      <p className="muted">You do not need to calculate dimensions, tolerances, temperatures, shrinkage, dates, or other engineering inputs just to get started. Fabrient uses the supplied artifact, project context, saved machine/material information, and deterministic defaults where appropriate.</p>
      <div className="row" style={{marginTop:14, flexWrap:'wrap'}}>
        <Link className="button primary" href="/geometry">Add STEP file</Link>
        <Link className="button" href="/engineering">Engineering</Link>
        <Link className="button" href="/calibration">Monitoring & calibration</Link>
        <Link className="button" href="/manufacturing">Manufacturing</Link>
        <Link className="button" href="/records">Inspection records</Link>
        <Link className="button" href="/projects">Projects</Link>
      </div>
    </section>

    <EngineeringCopilot />

    <section className="panel" style={{marginTop:16}}>
      <div className="eyebrow">THE SIMPLE RULE</div>
      <h2>You provide the evidence. Fabrient handles the machinery.</h2>
      <div className="workspace-grid" style={{marginTop:12}}>
        <div><strong>Bring</strong><p className="muted">STEP files, existing project data, measurements, inspection records, or a plain-language goal.</p></div>
        <div><strong>We decide</strong><p className="muted">Applicable checks, calculations, simulations, evidence collection, and the next graph step are selected automatically.</p></div>
        <div><strong>We ask only when necessary</strong><p className="muted">If a fact can safely be inferred, it is inferred. If choosing wrong could change the engineering result, Fabrient asks.</p></div>
      </div>
    </section>
  </main>
}
