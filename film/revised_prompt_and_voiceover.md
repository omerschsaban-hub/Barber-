# Fabrient Launch + Product Demo Film — Revised 120-Second Prompt

Create one continuous, exactly 120-second, 16:9 landscape product-launch film at 1920×1080 minimum and 24 fps. Preserve the core visual language of the existing Fabrient film: warm ivory, deep graphite, charcoal, muted olive, restrained industrial green, and safety yellow only for active states. Keep the same believable PCB and matte graphite enclosure from the first frame through the final physical close-up.

The film is one engineering job, not a feature montage: an engineer needs a custom FDM enclosure around a PCB. Every important action must show input → process → result. The product is the hero. Show realistic CAD, deterministic engineering checks, physical evidence, trained ML, human approval, autonomous software agents, MCP/tool execution, manufacturing coordination, sourcing, cost trade-offs, and release artifacts. The LLM is an orchestration layer: it understands intent, decomposes work, coordinates tools, interprets results, and proposes bounded next actions. It never invents measurements, physics, calibration, pass/fail evidence, or engineering truth.

## Exact Timeline

**0:00–0:08 — Opening.** Near-silence. Engineering grid, PCB, and enclosure assemble from credible CAD geometry. Editorial titles: “AI CAN GENERATE ANYTHING.” “ENGINEERING HAS TO PROVE IT.” “FABRIENT.” No flashy transition.

**0:08–0:20 — Define.** Real Fabrient workspace. Human enters: “Design an enclosure around this PCB. Preserve mounting points and connector access. Maintain clearance. Prepare an FDM build.” Show request becoming explicit constraints: PCB envelope, mounting, connectors, wall thickness, internal volume, material, process, tolerance, and required physical evidence.

**0:20–0:31 — Assembly, sourcing, and cost.** Show a multi-part assembly tree: PCB, lower shell, cover, gasket, bosses, fasteners, and connector hardware. The system checks component availability and presents two manufacturable options: local FDM with lower lead time and a different finish, or CNC with higher cost and tighter tolerance. Show a restrained cost/lead-time trade-off and a human selecting the FDM path. Keep the same enclosure geometry.

**0:31–0:43 — Design and deterministic analysis.** Show perspective, top, section, transparent, exploded, and macro boss/connector views. Show geometry, topology, dimensions, tolerances, DFM, manufacturability, and variation checks running. Produce a real-looking STEP artifact and structured results.

**0:43–0:54 — Failure and fix.** Connector clearance fails: required 2.0 mm, current insufficient. Highlight the exact geometry. Human requests “Move the connector opening 3 mm outward.” Show input → bounded CAD modification → changed opening and surrounding geometry → clearance recheck. Show PASS, DFM PASS, GEOMETRY VERIFIED.

**0:54–1:06 — Physical evidence and ML.** Cut to the printed part, PCB, calipers, inspection record, machine/process/part/timestamp/units. Show physical measurements entering the system. Visually show: DETERMINISTIC BASELINE + PHYSICAL DATA + FABRIENT-TRAINED MODEL = BETTER PREDICTION. Display measured vs predicted, residual analysis, validation set, predictive analytics, background optimization, and uncertainty. The model estimates learned residual behavior; it does not replace the baseline.

**1:06–1:15 — Uncertainty and human gate.** The uncertainty band expands outside the validated range. State changes to “OUTSIDE VERIFIED RANGE” and “REVIEW REQUIRED.” Show measured data, model prediction, uncertainty, validation range, and provenance. A real engineer reviews and explicitly approves the consequential action. State changes to “HUMAN APPROVAL” then “VERIFICATION CONTINUES.”

**1:15–1:31 — Human plus autonomous agent.** Split screen. Left: human in Fabrient Workspace. Right: a software agent using Fabrient MCP, not a humanoid or avatar. Show both pointing to the same engineering state. The agent executes bounded structured tool calls: `inspect_geometry` → result, `analyze_clearance` → result, `modify_connector_opening` → result, `verify_geometry` → result. Show automated decision logs, tool inputs, structured outputs, provenance, and escalation when judgment is required. State: “SAME ENGINEERING SYSTEM. DIFFERENT INTERFACE.” Explicitly communicate: Fabrient is built for human engineers and autonomous AI agents working in tandem.

**1:31–1:52 — Verify, build, and release package.** Pacing increases slightly. Show verified state flowing into provenance, evidence, manufacturing, build guide, and release. Generate a comprehensive package containing visual 3D renders, STEP/CAD, machine instructions, process parameters, material and machine settings, assembly instructions, sourcing choices, cost/lead-time decision, inspection history, revision, verification state, and decision log. Show the digital model becoming the same physical enclosure.

**1:52–2:00 — End.** Close-up of the real part with realistic PCB fit, bosses, fasteners, connector access, and FDM surface. Dark graphite and warm ivory. Typography: “DEFINE. ANALYZE. FIX. VERIFY. BUILD. RELEASE.” Then “FABRIENT” and “FOR HUMANS. FOR AGENTS. FOR THE PHYSICAL WORLD.” Resolve quietly. No cheesy CTA.

## Visual and Audio Guardrails

Use stable technical cinematography, controlled camera movement, orthographic engineering views, shallow depth of field only on physical-object shots, and geometry-based transitions. A dimension line can become a UI divider; a CAD edge can become a wipe; a measurement marker can become the next active state. No glowing brains, robots, holograms, neon gradients, blue or purple, random particles, fake futuristic labs, stock engineer footage, impossible CAD, disconnected scenes, or meaningless numbers.

Use a professional human founder/product-lead voice: warm, precise, conversational, slightly fast, deliberate, and exceptionally clear. The narrator must pronounce technical terms cleanly and leave brief pauses after failures, approvals, and key distinctions. Keep the 3D animation timing unchanged; improve clarity through diction, phrasing, and controlled pauses rather than slowing the visuals. Voice is foreground. Music is an original restrained industrial bed with low analog pulse, subtle mechanical percussion, muted synth texture, soft sub-bass, metallic clicks, and no trailer swell. Duck music under speech. Add grounded UI clicks, processing ticks, a restrained warning tone, tactile approval, tool-call clicks, and a subtle release completion sound.

# Voiceover Script — Target 120 Seconds

Physical engineering starts with intent.

An engineer needs a custom enclosure around this board: preserve the mounting points, keep every connector accessible, hold the clearance, and prepare a reliable FDM build.

Fabrient turns that request into an explicit job. It captures the PCB envelope, wall thickness, internal volume, material, process, tolerances, and the evidence required to trust the result.

The work is not only one part. Fabrient understands the assembly: shell, cover, gasket, bosses, fasteners, and connectors. It can compare sourcing paths, lead times, and cost, so the engineer can choose a manufacturable trade-off before committing.

Then real geometry takes shape. The PCB stays in position. Views move from perspective to section, transparent inspection, and exploded assembly. A STEP artifact is created, while topology, dimensions, tolerances, DFM, and variation are checked.

One check fails. Connector clearance is insufficient.

Fabrient shows the exact geometry, the requirement, the evidence, and the review state. It does not hide the failure.

The engineer requests a bounded change: move the opening three millimeters outward.

The opening moves. The surrounding geometry updates. The board stays fixed. The clearance check runs again. Pass. DFM passes. Geometry is verified.

Now the physical part comes back. Measurements, machine, process, part, timestamp, and units become evidence. A Fabrient-trained model runs background optimization and predictive analytics on validated observations. Measured data, a deterministic baseline, a validation set, residual analysis, and uncertainty remain visible.

When prediction leaves the verified range, Fabrient stops. Review required. A human engineer checks the provenance and approves the consequential action.

At the same time, an autonomous engineering agent can work through Fabrient MCP. It inspects, analyzes, modifies within bounds, verifies, records automated decisions, and escalates when judgment is needed. Humans and agents work in tandem on the same engineering state, through different interfaces.

The loop closes with a complete manufacturing package: visual 3D renders, CAD, machine instructions, process parameters, sourcing and cost decisions, assembly guidance, inspection history, verification evidence, and release logs.

From intent to a physical outcome, Fabrient connects the work that must be defined, analyzed, fixed, verified, built, and released.

For humans. For agents. For the physical world.
