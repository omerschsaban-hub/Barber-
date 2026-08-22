import Link from 'next/link'

const stages = [
  ['01', 'START', 'Tell us what you are making'],
  ['02', 'FIT', 'Make sure everything fits'],
  ['03', 'CHECK', 'Catch problems before building'],
  ['04', 'BUILD', 'Get it ready to make'],
]

export default function Home() {
  return (
    <main className="cad-home">
      <section className="cad-hero friendly-hero">
        <div className="cad-intro">
          <div className="cad-kicker"><span className="live-dot" /> FABRIENT</div>
          <h1>Make something.<br /><em>Make it work.</em></h1>
          <p>Fabrient helps you turn an idea into a physical product that fits, works, and is ready to build. The complicated engineering happens quietly in the background.</p>
          <div className="cad-actions">
            <Link href="/manufacturing" className="cad-button cad-button-main">START A PROJECT <span>→</span></Link>
            <Link href="/workspace" className="cad-button">SEE MY PROJECT</Link>
          </div>
          <div className="friendly-note"><span className="live-dot" /> We check the details so you don't have to.</div>
        </div>

        <div className="cad-stage friendly-stage" aria-label="3D product preview">
          <div className="cad-axis axis-x">↔</div><div className="cad-axis axis-y">↕</div><div className="cad-axis axis-z">↗</div>
          <div className="cad-floor" />
          <div className="part part-top"><span>YOUR DESIGN</span></div>
          <div className="part part-board"><span>INSIDE</span><i /></div>
          <div className="part part-bottom"><span>READY TO BUILD</span></div>
          <div className="part-part part-side side-a" /><div className="part-part part-side side-b" />
          <div className="dimension dim-x"><b>Fits ✓</b></div>
          <div className="dimension dim-y"><b>Looks good ✓</b></div>
          <div className="cad-tag tag-pass">READY ✓</div>
          <div className="cad-tag tag-rev">YOUR PROJECT</div>
        </div>
      </section>

      <section className="cad-pipeline friendly-pipeline">
        {stages.map(([num, name, detail], i) => <div className="cad-stage-row" key={name}>
          <span className="stage-num">{num}</span><strong>{name}</strong><small>{detail}</small>{i < stages.length - 1 && <span className="stage-line" />}
        </div>)}
      </section>

      <section className="cad-work">
        <div className="cad-section-head"><div><span>YOUR PROJECT</span><h2>Everything is looking good.</h2></div><Link href="/engineering">SEE DETAILS →</Link></div>
        <div className="cad-grid">
          <article className="cad-card large"><header><span>01 / YOUR DESIGN</span><b>LOOKING GOOD</b></header><div className="card-value">Fits perfectly <small>✓</small></div><p>Your parts line up and the important measurements are in place.</p><div className="mini-wire"><i /><i /><i /><i /></div></article>
          <article className="cad-card"><header><span>02 / FIT CHECK</span><b>PASS</b></header><div className="card-value">All good ✓</div><p>We checked the important places where parts need to fit together.</p><div className="checkline"><span /> walls <b>good</b></div><div className="checkline"><span /> clearances <b>good</b></div><div className="checkline"><span /> shape <b>good</b></div></article>
          <article className="cad-card"><header><span>03 / YOUR PROOF</span><b>3 SAVED</b></header><div className="card-value">Looks right</div><p>Your measurements, checks and test results stay together with your project.</p><Link href="/records" className="card-link">SEE MY RESULTS →</Link></article>
          <article className="cad-card wide-card"><header><span>04 / READY TO BUILD</span><b className="yellow-state">ALMOST THERE</b></header><div className="release-line"><strong>Your build package</strong><span>2 of 3 steps done</span></div><div className="release-bar"><i /></div><p>One last real-world check, then you'll have everything you need to make it.</p><Link href="/manufacturing" className="card-link">FINISH MY PROJECT →</Link></article>
        </div>
      </section>

      <section className="friendly-bottom"><strong>Want the engineering details?</strong><span>They are all there when you need them — just not in your way.</span><Link href="/engineering">SHOW ME THE DETAILS →</Link></section>
    </main>
  )
}
