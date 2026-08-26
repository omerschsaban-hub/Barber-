# Fabrient

**Build it. Prove it.**

Fabrient helps people building physical products get from an engineering idea to something they can actually make, test, improve and trust.

You can start with a plain-English request, the CAD you already have, measurements, manufacturing information, or a problem you are trying to solve. Fabrient helps work through the job instead of making you translate everything into a maze of separate engineering tools.

## What Fabrient is for

Think of Fabrient as a place where the digital and physical sides of engineering finally meet.

It can help you:

- turn an engineering request into a clear job;
- work with real CAD and dimensions;
- find design and manufacturing problems before they become expensive physical iterations;
- make safe, bounded improvements and show what changed;
- prepare a part for manufacturing;
- keep build notes, inspections and measurements with the project;
- compare what was predicted with what actually happened;
- learn useful patterns from real machine/process observations;
- turn images and inspection records into supporting evidence;
- keep a clear record of why something passed, failed or still needs attention;
- give both humans and software agents access to the same underlying engineering workflows.

The point is not to make another AI chat window. The point is to help finish real engineering work.

## How it works

The core loop is deliberately simple:

**Start → Understand → Check → Improve → Build → Prove**

You describe what you are trying to accomplish. Fabrient works through the information it has, checks the parts that can be checked automatically, helps identify what needs changing, and keeps the evidence together.

When you make the physical thing, reality comes back into the loop. Measurements, fit, failures and corrections can then improve the next decision.

If the evidence is not strong enough, Fabrient should tell you that. It should never hide uncertainty behind a confident-looking answer.

## What is underneath

The experience is intentionally simple, but the system underneath it is not a toy.

### Engineering and CAD

Fabrient uses deterministic engineering code and CAD tooling for the things that need repeatable answers. The current implementation uses **CadQuery / OCCT** for parametric CAD and STEP exchange, explicit dimensional checks, geometry/topology validation, manufacturing checks and bounded self-fix workflows.

That means an AI response is not allowed to quietly become the engineering truth. The actual engineering layer produces the result that matters.

### Machine learning

ML is used where real observations can make the engineering baseline better.

The current implementation can learn machine/process behavior from real observations and can model remaining error after a deterministic baseline. It uses held-out validation before treating a learned model as useful, and it keeps uncertainty visible.

In plain English: **the system can learn from what your machine really did, but it does not get to invent the evidence.**

### Images and measurement

Real images can be useful when there is a physical reference that establishes scale. Fabrient checks image quality, finds measurable geometry and keeps the measurement separate from ground truth.

A photograph can support an engineering decision. It does not magically become a perfect measurement just because an AI looked at it.

### Physical learning loop

Fabrient is designed around the difference between **what we expected** and **what actually happened**.

A useful loop looks like this:

**Design → Predict → Build → Measure → Learn**

The system keeps provenance around those observations so a later decision can be traced back to where the evidence came from. Synthetic examples are not presented as real calibration evidence.

## Manufacturing

Fabrient's manufacturing workflow is intended to take a design beyond “the CAD looks okay.”

The workflow can move through:

1. create or bring in the CAD;
2. check the geometry and exchange file;
3. look for manufacturing problems;
4. make allowed, bounded fixes;
5. prepare build guidance;
6. collect inspection information;
7. produce a manufacturing package when the required checks pass.

That package can include the validated CAD, release information, manufacturing findings, build guidance, notes and an inspection plan.

A green screen is not the definition of done. **The useful outcome is an artifact you can actually hand to someone and build from.**

## AI and agents

Fabrient is designed so humans and software agents can work with the same engineering system.

An agent can help gather context, choose the next bounded action, run an engineering operation, look at the result and continue. The system still keeps hard boundaries around consequential changes and unsupported conclusions.

The basic rule is simple:

> **AI can help decide what to do next. Engineering evidence decides what is true.**

Fabrient does not intentionally:

- make up measurements;
- make up confidence or calibration evidence;
- silently change tolerances;
- pretend a simulation is the same as a physical build;
- claim a manufacturing release while required evidence is still missing;
- make consequential geometry/topology changes without the required human gate.

## Current product areas

- `/` — the public product experience
- `/login` — passwordless email access
- `/workspace` — the main engineering workspace
- `/manufacturing` — design, manufacturing checks, build and release
- `/geometry` — CAD/STEP geometry work
- `/records` — inspection records and exports
- `/graph` — the agent workflow
- `/projects` — project history

## Architecture

The current production architecture uses:

- Next.js + TypeScript
- PostgreSQL
- passwordless email authentication
- Python/FastAPI engineering services
- CadQuery / OCCT
- NumPy + scikit-learn
- OpenCV measurement tooling
- provenance and audit records
- authenticated MCP engineering tools
- GitHub Actions and Playwright acceptance testing

PostgreSQL is the canonical production database architecture. Legacy Supabase references are treated as migration/compatibility material and must be audited before removal; new production database functionality should not be built around Supabase.

## For developers

Agents and contributors should read `AGENTS.md` before making changes.

The main product documents are:

- `docs/PRODUCT_EXECUTION_PRINCIPLES.md`
- `docs/DEEP_EXECUTION_STANDARD.md`
- `docs/PRODUCT_SIMPLIFICATION.md`
- `docs/PRODUCT_SURFACE.md`
- `.claude/skills/playwright/SKILL.md`

Useful checks:

```bash
npm run agent:preflight
npm run test:unit
npm run test:e2e
npm run test:deep
npm run test:all
pytest -q tests/mcp
```

For UI changes, use a real browser for acceptance. A page that merely builds is not automatically a page that works.

## Local development

```bash
npm install
npm run agent:preflight
npm run dev
cd engineering
pip install -r requirements.txt
uvicorn app.composed:app --reload --port 8000
```

Set `NEXT_PUBLIC_ENGINEERING_API` when the engineering service is not running on `http://localhost:8000`.

## Public URL

The intended public hostname is **getfabrient.com**. Application metadata uses that hostname as the canonical/Open Graph URL. The domain still needs to be attached and configured in the hosting account before it becomes the live production hostname.
