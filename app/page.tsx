import Link from 'next/link'

const REAL_PHOTO = 'https://images.pexels.com/photos/22491107/pexels-photo-22491107.jpeg?auto=compress&cs=tinysrgb&w=1600'

export default function Home() {
  return (
    <main className="cad-home">
      <section className="cad-hero friendly-hero">
        <div className="cad-intro">
          <div className="cad-kicker"><span className="live-dot" /> FABRIENT / PHYSICAL ENGINEERING</div>
          <h1>Build it.<br /><em>Prove it.</em></h1>
          <p>Fabrient helps you take a physical product from an idea to something you can actually build and trust. Tell it what you are trying to make, give it the files and measurements you have, and Fabrient works through the engineering with you.</p>
          <div className="cad-actions">
            <Link href="/login?redirect=/workspace" className="cad-button cad-button-main">TRY FABRIENT <span>→</span></Link>
            <Link href="#how-it-works" className="cad-button">SEE HOW IT WORKS</Link>
          </div>
          <div className="friendly-note"><span className="live-dot" /> AI helps with the thinking and coordination. The important parts are checked against real engineering rules and real evidence.</div>
        </div>
        <div className="cad-stage friendly-stage" aria-label="Real manufacturing photograph">
          <img src={REAL_PHOTO} alt="A real machine used for precision manufacturing" loading="eager" referrerPolicy="no-referrer" />
          <div className="photo-credit">Physical products are different. Fabrient is built for that.</div>
          <div className="cad-tag tag-pass">REAL-WORLD ENGINEERING</div>
          <div className="cad-tag tag-rev">IDEA → BUILD → PROOF</div>
        </div>
      </section>

      <section id="how-it-works" className="cad-pipeline technical-pipeline" aria-label="How Fabrient works">
        {[
          ['01', 'START', 'Tell Fabrient what you need.'],
          ['02', 'UNDERSTAND', 'It turns the request into a clear job.'],
          ['03', 'CHECK', 'The design is tested against what matters.'],
          ['04', 'IMPROVE', 'It finds problems and suggests practical fixes.'],
          ['05', 'BUILD', 'You make the part and bring back what happened.'],
          ['06', 'PROVE', 'The final result comes with the evidence behind it.'],
        ].map(([n, title, text]) => (
          <div className="cad-stage-row" key={n}><span className="stage-num">{n}</span><strong>{title}</strong><small>{text}</small><i className="stage-line" /></div>
        ))}
      </section>

      <section className="cad-work technical-section">
        <div className="cad-section-head"><div><span>THE SIMPLE VERSION</span><h2>You describe the job. Fabrient helps finish it.</h2></div></div>
        <div className="system-map">
          <div className="system-column system-ai"><span>YOU</span><strong>Start with the problem, not a form.</strong><p>Explain what you are trying to build, what you already have, and what needs to be true when you are done. You do not need to translate your idea into a dozen engineering screens first.</p><div className="system-code">“Make this fit. Make it manufacturable. Show me what changed.”</div></div>
          <div className="system-connector">→</div>
          <div className="system-column"><span>FABRIENT</span><strong>Works through the hard parts.</strong><p>Fabrient can reason about the design, check dimensions and manufacturability, work with CAD, compare measurements, learn from real builds, and keep track of what is known versus what still needs proof.</p><div className="system-code">understand · check · improve · verify</div></div>
          <div className="system-connector">→</div>
          <div className="system-column system-evidence"><span>RESULT</span><strong>Know what you can trust.</strong><p>You get the useful thing at the end: a better design, a clear explanation of the remaining problem, or a manufacturing package backed by the evidence collected along the way.</p><div className="system-code">result · evidence · next step</div></div>
        </div>
      </section>

      <section className="cad-work technical-section">
        <div className="cad-section-head"><div><span>WHY IT IS DIFFERENT</span><h2>It does not pretend a computer simulation is the real world.</h2></div></div>
        <div className="model-grid">
          <article className="model-card"><span>THE DESIGN</span><h3>Work with the actual part.</h3><p>Fabrient works with real CAD and real dimensions. It checks whether the thing you designed is coherent before you spend time and money making it.</p><div className="model-spec">CAD · dimensions · fit · manufacturability</div></article>
          <article className="model-card"><span>THE MACHINE</span><h3>Learn from what your machine actually does.</h3><p>When enough real measurements exist, Fabrient can learn patterns in a machine or process and use them to make the next prediction more useful.</p><div className="model-spec">real observations · validation · learned corrections</div></article>
          <article className="model-card"><span>THE CAMERA</span><h3>Turn images into useful evidence.</h3><p>Images can help measure a part when there is a real reference to establish scale. Fabrient keeps that distinction clear instead of quietly treating a picture as perfect truth.</p><div className="model-spec">reference scale · image checks · measured evidence</div></article>
          <article className="model-card"><span>THE BOTTOM LINE</span><h3>When it is unsure, it says so.</h3><p>Fabrient is designed to show uncertainty and ask for more evidence when the evidence is not strong enough. A confident answer is not useful if the part will fail in the real world.</p><div className="model-spec">evidence first · honest limits · human approval when needed</div></article>
        </div>
      </section>

      <section className="cad-work technical-section">
        <div className="cad-section-head"><div><span>FROM DESIGN TO FACTORY</span><h2>The last mile matters.</h2></div></div>
        <div className="cad-grid technical-cards">
          <article className="cad-card"><header><span>DESIGN</span><b>REAL CAD</b></header><div className="card-value">Make the part make sense.</div><p>Generate or bring in a part, check the important dimensions, and catch issues before they become an expensive physical iteration.</p></article>
          <article className="cad-card"><header><span>MANUFACTURING</span><b>CHECK → FIX → CHECK</b></header><div className="card-value">Find the problem early.</div><p>Fabrient looks for manufacturing problems and can handle safe, bounded fixes while keeping consequential changes under human control.</p></article>
          <article className="cad-card"><header><span>REALITY</span><b>BUILD → MEASURE</b></header><div className="card-value">Bring reality back in.</div><p>What happened when you actually made it? Measurements, fit, failures and corrections become part of the engineering record instead of disappearing into a spreadsheet.</p></article>
          <article className="cad-card wide-card"><header><span>WHEN YOU ARE READY</span><b className="yellow-state">RELEASE</b></header><div className="release-line"><strong>One place for the design, checks, build notes and evidence.</strong><span>ready when the gates pass</span></div><div className="release-bar"><i /></div><p>The goal is not another dashboard. It is a package you can hand to the next person and know why the part is ready—or exactly what still needs attention.</p></article>
        </div>
      </section>

      <section className="cad-work technical-section">
        <div className="cad-section-head"><div><span>THE LEARNING LOOP</span><h2>Every real build can make the next one better.</h2></div></div>
        <div className="flywheel-row">
          <div><b>DESIGN</b><span>what you wanted to make</span></div><i>→</i><div><b>PREDICT</b><span>what should happen</span></div><i>→</i><div><b>BUILD</b><span>what actually happened</span></div><i>→</i><div><b>MEASURE</b><span>what the part tells you</span></div><i>→</i><div><b>LEARN</b><span>use the evidence next time</span></div>
        </div>
        <p className="section-note">The important part is the loop: predictions can be compared with reality, corrections can be remembered, and the system can become more useful without pretending that synthetic examples are the same as real manufacturing evidence.</p>
      </section>

      <section className="cad-work technical-section">
        <div className="cad-section-head"><div><span>AI, WITHOUT THE THEATER</span><h2>Useful autonomy, with a line it will not cross.</h2></div></div>
        <div className="agent-story"><div className="agent-node"><span>YOU SAY</span><strong>“Make this enclosure fit the board and make it manufacturable.”</strong></div><div className="agent-arrow">↓</div><div className="agent-node"><span>FABRIENT WORKS</span><strong>It gathers context, checks the design, works through bounded changes, looks at evidence and tells you what happened.</strong></div><div className="agent-arrow">↓</div><div className="agent-node"><span>YOU GET</span><strong>A result you can inspect, evidence you can follow, or a clear request for the human decision it cannot safely make alone.</strong></div></div>
        <div className="prohibition-strip"><span>NO MADE-UP MEASUREMENTS</span><span>NO FAKE CERTAINTY</span><span>NO SILENT TOLERANCE CHANGES</span><span>NO PRETENDING A SIMULATION IS A BUILD</span></div>
      </section>

      <section className="friendly-bottom technical-bottom"><strong>Physical engineering, without the paperwork maze.</strong><span>Tell us what you are building. Fabrient helps you get from idea to evidence.</span><Link href="/login?redirect=/workspace" className="cad-button cad-button-main">START WITH FABRIENT →</Link></section>
    </main>
  )
}
