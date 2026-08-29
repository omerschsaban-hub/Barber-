'use client'

import Link from 'next/link'
import EngineeringCopilot from './EngineeringCopilot'

const areas = [
  ['Geometry', 'Bring a real STEP file and inspect the verified CAD geometry.', '/geometry'],
  ['Engineering', 'Run engineering work from a plain-language goal. Technical calculations stay underneath.', '/engineering'],
  ['Monitoring & calibration', 'Bring real observations and monitor machine/process behavior without manually entering synthetic numbers.', '/calibration'],
  ['Simulation', 'Compare predictions with real evidence and keep simulation separate from physical measurements.', '/sim2real'],
  ['Inspection', 'Import inspection records and keep measurements attached to their source.', '/records'],
  ['Manufacturing', 'Move a verified design into build guidance, inspection, and release.', '/manufacturing'],
] as const

export default function EngineeringCenter() {
  return <main className="page wide">
    <div className="eyebrow">FABRIENT / ENGINEERING</div>
    <div className="workspace-head">
      <div>
        <h1 className="title">Engineering, without the busywork.</h1>
        <p className="muted" style={{maxWidth:900}}>Use the engineering tools you need. You do not have to type dimensions, uncertainty values, temperatures, drift rates, sample counts, or other technical numbers when Fabrient can obtain them from the project, uploaded evidence, saved profiles, or deterministic defaults.</p>
      </div>
      <Link className="button" href="/workspace">Back to workspace</Link>
    </div>

    <EngineeringCopilot />

    <section className="workspace-grid" style={{marginTop:20}}>
      {areas.map(([title, description, href]) => <Link key={href} href={href} className="panel" style={{textDecoration:'none'}}>
        <div className="eyebrow">ENGINEERING TOOL</div>
        <h2>{title}</h2>
        <p className="muted">{description}</p>
        <span className="button">Open →</span>
      </Link>)}
    </section>

    <section className="panel" style={{marginTop:20}}>
      <div className="eyebrow">WHAT CHANGED</div>
      <h2>Technical capability stays. Technical data entry goes.</h2>
      <p className="muted">Advanced evidence and detailed engineering results remain available inside the individual tools. The main engineering screen no longer makes users operate the underlying math manually or type placeholder measurements.</p>
    </section>
  </main>
}
