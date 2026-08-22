import Link from 'next/link'

const stages = [
  ['01', 'INPUT', 'Measured geometry'],
  ['02', 'CHECK', 'DFM constraints'],
  ['03', 'PROVE', 'Physical evidence'],
  ['04', 'RELEASE', 'Build package'],
]

export default function Home() {
  return (
    <main className="cad-home">
      <section className="cad-hero">
        <div className="cad-intro">
          <div className="cad-kicker"><span className="live-dot" /> FABRIENT / ENGINEERING SYSTEM</div>
          <h1>Build it.<br /><em>Prove it.</em></h1>
          <p>Engineering software for physical products. Define geometry, run deterministic checks, attach real evidence, then release what is actually ready to manufacture.</p>
          <div className="cad-actions">
            <Link href="/manufacturing" className="cad-button cad-button-main">NEW BUILD <span>→</span></Link>
            <Link href="/workspace" className="cad-button">OPEN WORKSPACE</Link>
          </div>
          <div className="cad-meta"><span>SYS / READY</span><span>DFM ENGINE / ONLINE</span><span>REV 0.9</span></div>
        </div>

        <div className="cad-stage" aria-label="3D exploded enclosure preview">
          <div className="cad-axis axis-x">X</div><div className="cad-axis axis-y">Y</div><div className="cad-axis axis-z">Z</div>
          <div className="cad-floor" />
          <div className="part part-top"><span>TOP / A</span></div>
          <div className="part part-board"><span>PCB / 01</span><i /></div>
          <div className="part part-bottom"><span>BASE / A</span></div>
          <div className="part-part part-side side-a" /><div className="part-part part-side side-b" />
          <div className="dimension dim-x"><b>68.4</b><span>mm</span></div>
          <div className="dimension dim-y"><b>42.0</b><span>mm</span></div>
          <div className="cad-tag tag-pass">DFM PASS</div>
          <div className="cad-tag tag-rev">REV A / 003</div>
        </div>
      </section>

      <section className="cad-pipeline">
        {stages.map(([num, name, detail], i) => <div className="cad-stage-row" key={name}>
          <span className="stage-num">{num}</span><strong>{name}</strong><small>{detail}</small>{i < stages.length - 1 && <span className="stage-line" />}
        </div>)}
      </section>

      <section className="cad-work">
        <div className="cad-section-head"><div><span>WORKSPACE</span><h2>Current engineering state</h2></div><Link href="/engineering">VIEW ENGINEERING →</Link></div>
        <div className="cad-grid">
          <article className="cad-card large"><header><span>01 / GEOMETRY</span><b>LOCKED</b></header><div className="card-value">68.4 × 42.0 × 16.2 <small>mm</small></div><p>Measured enclosure envelope · 12 features · 0 unresolved dimensions</p><div className="mini-wire"><i /><i /><i /><i /></div></article>
          <article className="cad-card"><header><span>02 / DFM</span><b>PASS</b></header><div className="card-value">18 / 18</div><p>Deterministic checks satisfied</p><div className="checkline"><span /> wall thickness <b>2.0</b></div><div className="checkline"><span /> clearances <b>1.5</b></div><div className="checkline"><span /> overhangs <b>0</b></div></article>
          <article className="cad-card"><header><span>03 / EVIDENCE</span><b>3 ATTACHED</b></header><div className="card-value">READY</div><p>Inspection record, measured fit and simulation result linked to revision.</p><Link href="/records" className="card-link">OPEN RECORDS →</Link></article>
          <article className="cad-card wide-card"><header><span>04 / RELEASE</span><b className="yellow-state">GATED</b></header><div className="release-line"><strong>Manufacturing package</strong><span>2 / 3 gates complete</span></div><div className="release-bar"><i /></div><p>Final gate: physical acceptance. No release is generated from an estimate.</p><Link href="/manufacturing" className="card-link">OPEN RELEASE GATE →</Link></article>
        </div>
      </section>
    </main>
  )
}
