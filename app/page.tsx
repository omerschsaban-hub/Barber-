import Link from 'next/link'
import { ENTERPRISE_CONTACT, FABRINAT_PLANS } from '@/lib/fabrinat-plans'

const PLAN_ORDER = ['free', 'hobbyist', 'startup', 'enterprise'] as const

const REAL_PHOTO = 'https://images.pexels.com/photos/22491107/pexels-photo-22491107.jpeg?auto=compress&cs=tinysrgb&w=1600'

const journey = [
  ['01', 'INTENT', 'Start with what you want to make.', 'Describe the job in plain English. Bring the CAD, dimensions, requirements, constraints, or problem you already have. Fabrient turns that into a clear job without making you learn a new workflow first.'],
  ['02', 'DESIGN', 'Turn the idea into something real.', 'Work with existing CAD or generate a parametric design. Dimensions, units, geometry, topology and exchange files are checked as the design takes shape.'],
  ['03', 'BUILD', 'Turn the design into something you can make.', 'Prepare the actual build package: the files, instructions, parts, manufacturing inputs and checks needed to move from a finished design to a physical build.'],
  ['04', 'ANALYZE', 'Find what could go wrong before you build.', 'Check fit, dimensions and manufacturability. Run deterministic engineering checks, DFM analysis and the simulations or validation steps that belong to the job.'],
  ['05', 'IMPROVE', 'Fix the things that can be fixed safely.', 'Fabrient can suggest and apply bounded changes where the rules allow it, then check the result again. Important geometry and topology changes stay behind the right human approval gate.'],
  ['06', 'VERIFY', 'Bring the real world back into the loop.', 'Build the part, upload measurements or inspection records, and use real images when they have a physical reference. Compare prediction with reality and keep the evidence with the project.'],
  ['07', 'LEARN', 'Make the next decision better.', 'Real machine and process observations can teach the system useful patterns. Learned corrections stay downstream of the engineering baseline and are validated before they are trusted.'],
  ['08', 'RELEASE', 'Finish with something you can actually hand off.', 'When the required gates pass, collect the validated CAD, findings, build guidance, manufacturing notes and inspection information into a release package. If something is missing, Fabrient tells you exactly what.'],
]

export default function Home() {
  return (
    <main className="cad-home">
      <section className="cad-hero friendly-hero">
        <div className="cad-intro">
          <div className="cad-kicker"><span className="live-dot" /> FABRIENT / PHYSICAL ENGINEERING</div>
          <h1>From <em>intent</em><br />to something real.</h1>
          <p className="hero-lead">Fabrient brings the work around a physical product into one place — from the first idea, through design and engineering, to the build, the measurements and the final proof.</p>
          <div className="cad-actions">
            <Link href="/login?redirect=/workspace" className="cad-button cad-button-main">START A PROJECT <span>→</span></Link>
            <Link href="#journey" className="cad-button">SEE THE JOURNEY</Link>
          </div>
          <div className="friendly-note"><span className="live-dot" /> AI helps move the work forward. Engineering rules, measurements and evidence decide what is actually true.</div>
        </div>
        <div className="cad-stage friendly-stage" aria-label="Real manufacturing photograph">
          <img src={REAL_PHOTO} alt="A real machine used for precision manufacturing" loading="eager" referrerPolicy="no-referrer" />
          <div className="photo-credit">Physical products do not stay on a screen.</div>
          <div className="cad-tag tag-pass">REAL-WORLD ENGINEERING</div>
          <div className="cad-tag tag-rev">INTENT → BUILD → PROOF</div>
        </div>
      </section>

      <section id="journey" className="cad-work journey-section">
        <div className="cad-section-head">
          <div><span>THE WHOLE JOURNEY</span><h2>One job. From intent to release.</h2></div>
          <p>You should not have to stitch together a chat, CAD tool, spreadsheet, inspection log and manufacturing folder just to understand where a part stands.</p>
        </div>
        <div className="journey-list">
          {journey.map(([n, title, headline, text]) => (
            <article className="journey-step" key={n}>
              <div className="journey-index">{n}</div>
              <div className="journey-copy"><span>{title}</span><h3>{headline}</h3><p>{text}</p></div>
            </article>
          ))}
        </div>
      </section>

      <section className="cad-work technical-section">
        <div className="cad-section-head"><div><span>WHAT YOU GET ALONG THE WAY</span><h2>The important pieces are there. They just stay out of your way.</h2></div></div>
        <div className="capability-grid">
          <article><span>DESIGN</span><h3>Real CAD, not a picture of CAD.</h3><p>Bring an existing STEP file or work from a parametric design. Fabrient can inspect geometry, dimensions and topology and keep the actual engineering artifact attached to the job.</p><b>CAD · STEP · geometry · dimensions</b></article>
          <article><span>ENGINEERING</span><h3>Checks that give you an answer you can follow.</h3><p>DFM, dimensional checks, geometry validation and bounded self-fix workflows turn “looks okay” into a concrete engineering state with findings and next actions.</p><b>DFM · validation · self-fix · release gates</b></article>
          <article><span>MEASUREMENT</span><h3>Bring the part back into the conversation.</h3><p>Inspection records and real images can become supporting evidence. Units, references, notes and provenance stay attached so you know where a measurement came from.</p><b>inspection · images · scale · provenance</b></article>
          <article><span>LEARNING</span><h3>Let reality teach the system.</h3><p>Real machine and process observations can be used to learn process behavior and remaining error. Validation happens before a learned correction is treated as useful.</p><b>real observations · ML · validation · uncertainty</b></article>
          <article><span>MANUFACTURING</span><h3>Go beyond “the design is done.”</h3><p>Build guidance, manufacturing notes, inspection planning and the final release package keep the handoff connected to the engineering work that produced it.</p><b>build guide · notes · inspection · package</b></article>
          <article><span>AGENTS</span><h3>Humans and software can use the same system.</h3><p>Bounded agents can gather context, choose the next action, run tools, inspect results and continue. The same capabilities are available through authenticated APIs and MCP.</p><b>agents · API · MCP · human approval</b></article>
        </div>
      </section>

      <section className="cad-work technical-section reality-section">
        <div className="cad-section-head"><div><span>THE PART THAT MATTERS</span><h2>Fabrient keeps prediction and reality separate.</h2></div></div>
        <div className="reality-flow">
          <div><small>01</small><strong>Predict</strong><p>Use the design and engineering baseline to say what should happen.</p></div>
          <i>→</i>
          <div><small>02</small><strong>Build</strong><p>Make the physical thing instead of assuming the screen is enough.</p></div>
          <i>→</i>
          <div><small>03</small><strong>Measure</strong><p>Bring back observations, inspection results, fit and failures.</p></div>
          <i>→</i>
          <div><small>04</small><strong>Learn</strong><p>Use supported evidence to improve the next decision.</p></div>
        </div>
        <p className="section-note">That distinction is the point. A model can help you think faster. It cannot turn an unmeasured part into measured reality.</p>
      </section>

      <section className="cad-work technical-section intelligence-section">
        <div className="cad-section-head"><div><span>WHAT IS ACTUALLY UNDER THE HOOD</span><h2>Simple on the surface. Serious underneath.</h2></div><p>When you want the deeper story, it is there. The product does not need to make you learn the machinery before you can use it.</p></div>
        <div className="intelligence-stack">
          <div><span>01</span><strong>Language + agents</strong><p>Understand the job, gather context, plan bounded work and explain what happened.</p></div>
          <div><span>02</span><strong>Deterministic engineering</strong><p>CadQuery / OCCT, explicit dimensions and units, geometry/topology checks, DFM and release gates.</p></div>
          <div><span>03</span><strong>Real measurement</strong><p>Inspection data and image-based evidence with physical references, quality checks and provenance.</p></div>
          <div><span>04</span><strong>Machine learning</strong><p>Current system identification and residual learning use real observations and held-out validation rather than invented calibration.</p></div>
          <div><span>05</span><strong>Uncertainty + decisions</strong><p>Evidence is kept visible. Weak evidence becomes a limitation or a request for more information, not fake certainty.</p></div>
          <div><span>06</span><strong>Audit + release</strong><p>Important inputs, results, artifacts and decisions stay traceable through the job and into manufacturing.</p></div>
        </div>
      </section>

      <section id="plans" className="cad-work pricing-section">
        <div className="cad-section-head"><div><span>PLANS THAT MATCH THE JOB</span><h2>Start small. Add the operating system when the team is ready.</h2></div><p>Free is genuinely useful but intentionally limited. Hobby gives one builder room to work. Startup adds the shared controls for teams of 1–29. Enterprise is for 30+ people and needs a conversation about deployment, governance and support.</p></div>
        <div className="pricing-grid">
          {PLAN_ORDER.map((key) => {
            const plan = FABRINAT_PLANS[key]
            const isEnterprise = key === 'enterprise'
            return <article className={`pricing-card ${key === 'startup' ? 'pricing-card-featured' : ''}`} key={key}>
              <div className="pricing-topline"><span>{plan.audience}</span>{key === 'startup' && <b>MOST FOR TEAMS</b>}</div>
              <h3>{plan.name}</h3>
              <div className="pricing-price">{plan.price === null ? <span className="pricing-talk">Let’s talk</span> : <><strong>${plan.price}</strong><small>{plan.price === 0 ? 'forever' : '/ month'}</small></>}</div>
              <p className="pricing-tagline">{plan.tagline}</p>
              <div className="pricing-limit">{plan.teamSize} · {plan.limits.llmRuns < 0 ? 'unlimited AI runs' : `${plan.limits.llmRuns} AI runs / month`}</div>
              <ul>{plan.highlights.map((highlight) => <li key={highlight}>{highlight}</li>)}</ul>
              {isEnterprise ? <div className="pricing-contact"><a href={`mailto:${ENTERPRISE_CONTACT.email}?subject=Fabrient%20Enterprise%20plan`}>Email {ENTERPRISE_CONTACT.email}</a><a href={`tel:${ENTERPRISE_CONTACT.phone}`}>Call {ENTERPRISE_CONTACT.phone}</a></div> : <Link href={key === 'free' ? '/login?redirect=/workspace' : `/billing?plan=${key}`} className={`cad-button ${key === 'startup' ? 'cad-button-main' : ''}`}>{key === 'free' ? 'START FREE' : `CHOOSE ${plan.name.toUpperCase()}`} <span>→</span></Link>}
            </article>
          })}
        </div>
      </section>

      <section className="cad-work technical-section">
        <div className="cad-section-head"><div><span>THE AGENT PROMISE</span><h2>Automation that knows when to stop.</h2></div></div>
        <div className="agent-story">
          <div className="agent-node"><span>YOU</span><strong>“Make this enclosure fit the board and get it ready to manufacture.”</strong></div>
          <div className="agent-arrow">↓</div>
          <div className="agent-node"><span>FABRIENT</span><strong>Gathers the context, works through the checks, proposes bounded changes, measures what it can, and keeps the evidence together.</strong></div>
          <div className="agent-arrow">↓</div>
          <div className="agent-node"><span>WHEN IT KNOWS ENOUGH</span><strong>You get the result and the artifacts. When it does not, it asks for the missing evidence or human decision instead of guessing.</strong></div>
        </div>
        <div className="prohibition-strip"><span>NO MADE-UP MEASUREMENTS</span><span>NO FAKE CERTAINTY</span><span>NO SILENT TOLERANCE CHANGES</span><span>NO PRETENDING A SIMULATION IS A BUILD</span></div>
      </section>

      <section className="cad-work final-cta-section">
        <div><span>START WITH THE THING YOU ARE ACTUALLY BUILDING</span><h2>Bring the problem.<br /><em>We will work through the rest.</em></h2><p>CAD, dimensions, measurements, a manufacturing problem, or just the goal. Start with what you have.</p></div>
        <Link href="/login?redirect=/workspace" className="cad-button cad-button-main">START A PROJECT <span>→</span></Link>
      </section>
    </main>
  )
}
