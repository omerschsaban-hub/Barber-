import Link from 'next/link'
import { PRODUCT_LOOP } from '../lib/fabrinat-plans'

export default function Home() {
  return <main className="cad-home">
    <section className="cad-hero friendly-hero">
      <div className="cad-intro">
        <div className="cad-kicker"><span className="live-dot" /> FABRINAT</div>
        <h1>From idea<br /><em>to real product.</em></h1>
        <p>Fabrient connects intent, CAD, engineering checks, physical build, testing and evidence in one controlled loop.</p>
        <div className="cad-actions"><Link href="/login?redirect=/workspace" className="cad-button cad-button-main">GET STARTED <span>→</span></Link><Link href="/login?redirect=/workspace" className="cad-button">LOG IN</Link></div>
        <div className="friendly-note"><span className="live-dot" /> The complicated engineering stays in the background until you need it.</div>
      </div>
      <div className="cad-stage friendly-stage" aria-label="product lifecycle preview">
        <div className="cad-floor" /><div className="part part-top"><span>DESIGN</span></div><div className="part part-board"><span>BUILD</span><i /></div><div className="part part-bottom"><span>REAL WORLD</span></div><div className="cad-tag tag-pass">READY ✓</div><div className="cad-tag tag-rev">LEARN → NEXT REVISION</div>
      </div>
    </section>

    <section className="cad-pipeline friendly-pipeline">
      {PRODUCT_LOOP.map((stage, i) => <div className="cad-stage-row" key={stage.key}><span className="stage-num">0{i + 1}</span><strong>{stage.title.toUpperCase()}</strong><small>{stage.description}</small>{i < PRODUCT_LOOP.length - 1 && <span className="stage-line" />}</div>)}
    </section>

    <section className="cad-work">
      <div className="cad-section-head"><div><span>THE PRODUCT LOOP</span><h2>One project. One source of truth.</h2></div><Link href="/login?redirect=/workspace">GET STARTED →</Link></div>
      <div className="cad-grid">
        <article className="cad-card large"><header><span>01 / CHECK</span><b>EARLY</b></header><div className="card-value">Catch problems before the printer or factory does.</div><p>Fit, geometry, tolerances and manufacturing checks stay attached to the exact revision that was tested.</p></article>
        <article className="cad-card"><header><span>02 / PROVE</span><b>TRACEABLE</b></header><div className="card-value">Every important answer has evidence.</div><p>Measurements, checks, assumptions and decisions stay together.</p></article>
        <article className="cad-card"><header><span>03 / BUILD</span><b>HANDOFF</b></header><div className="card-value">Ready-to-make package.</div><p>STEP, requirements, build instructions and inspection criteria travel together.</p></article>
        <article className="cad-card wide-card"><header><span>04 / LEARN</span><b className="yellow-state">CLOSE THE LOOP</b></header><div className="release-line"><strong>Real build result → next revision</strong><span>physical → digital</span></div><p>Inspection results and test outcomes become part of the product history instead of disappearing in a spreadsheet or chat.</p><Link href="/login?redirect=/workspace" className="card-link">GET STARTED →</Link></article>
      </div>
    </section>
    <section className="friendly-bottom"><strong>Simple on the surface. Serious underneath.</strong><span>Start with intent. Fabrient coordinates CAD, deterministic engineering, ML and evidence behind the scenes.</span><Link href="/login?redirect=/workspace">GET STARTED →</Link></section>
  </main>
}
