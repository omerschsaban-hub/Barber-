import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import { performance } from 'node:perf_hooks'

const ROOT = process.cwd()
const missionPath = 'engineering-loop/mission.json'
const stateDir = '.engineering-loop'
const statePath = `${stateDir}/state.json`
const mission = JSON.parse(readFileSync(missionPath, 'utf8'))
mkdirSync(stateDir, { recursive: true })
const now = () => new Date().toISOString()
const baseState = () => ({ status: 'running', iteration: 0, failures: 0, history: [], action_signatures: [], created_at: now() })
const loadState = () => {
  if (process.env.FABRIENT_LOOP_RESET === '1' || !existsSync(statePath)) return baseState()
  const state = JSON.parse(readFileSync(statePath, 'utf8'))
  return { ...baseState(), ...state, history: Array.isArray(state.history) ? state.history : [], action_signatures: Array.isArray(state.action_signatures) ? state.action_signatures : [] }
}
const saveState = state => writeFileSync(statePath, `${JSON.stringify(state, null, 2)}\n`)

function run(name, command, args) {
  if (process.env.FABRIENT_LOOP_TEST_MODE === '1') return { name, ok: true, status: 0, stdout: 'test-mode', stderr: '', duration_ms: 0 }
  const started = performance.now()
  const result = spawnSync(command, args, { cwd: ROOT, encoding: 'utf8', shell: process.platform === 'win32' })
  return { name, ok: result.status === 0, status: result.status, stdout: result.stdout ?? '', stderr: result.stderr ?? '', duration_ms: Math.round(performance.now() - started) }
}

function providerCatalog() {
  const source = readFileSync('engineering/app/mcp_integrations.py', 'utf8')
  return [...source.matchAll(/^\s+"([^"]+)":\s*\{[^\n]*?"endpoint":\s*"([^"]+)"/gm)].map(m => ({ id: m[1], endpoint: m[2] }))
}

function connectedToolInventory() {
  if (!process.env.FABRIENT_AGENT_TOOLS_JSON) return { source: 'none', tools: [], connected: false, catalog: providerCatalog() }
  try {
    const tools = JSON.parse(process.env.FABRIENT_AGENT_TOOLS_JSON)
    if (!Array.isArray(tools) || tools.length === 0) throw new Error('FABRIENT_AGENT_TOOLS_JSON must be a non-empty array')
    const normalized = tools.map(tool => ({ ...tool, id: tool.id ?? tool.name ?? tool.provider })).filter(tool => typeof tool.id === 'string')
    if (!normalized.length) throw new Error('runtime tool inventory contains no identifiable tools')
    return { source: 'runtime', tools: normalized, connected: true, catalog: providerCatalog() }
  } catch (error) { throw new Error(`Invalid FABRIENT_AGENT_TOOLS_JSON: ${error.message}`) }
}

function buildContext(state, inventory) {
  return {
    mission,
    state,
    repository: { cwd: ROOT, required_preflight: 'npm run agent:preflight' },
    tools: inventory,
    rules: {
      choose_next_step: true,
      require_evidence: true,
      require_tool_calls: true,
      never_claim_success_without_verifier: true,
      never_guess_credentials: true,
      checkpoint_high_risk_actions: mission.risk_policy.checkpoint_required,
      use_mission_required_tools_when_relevant: true,
      avoid_repeating_failed_action_signatures: true,
    },
  }
}

function askAgent(context) {
  const command = process.env.FABRIENT_AGENT_COMMAND
  if (!command) return null
  const result = spawnSync(command, { cwd: ROOT, input: `${JSON.stringify(context)}\n`, encoding: 'utf8', shell: true })
  if (result.status !== 0) throw new Error(`Agent command failed: ${result.stderr || result.stdout || `exit ${result.status}`}`)
  const output = result.stdout.trim()
  if (!output) throw new Error('Agent command returned no decision')
  let decision
  try { decision = JSON.parse(output) } catch (error) { throw new Error(`Agent returned invalid JSON: ${error.message}`) }
  if (!decision.action || typeof decision.action !== 'string') throw new Error('Agent decision must contain action')
  if (!Array.isArray(decision.tool_calls)) throw new Error('Agent decision must contain tool_calls')
  return decision
}

function validateToolCalls(decision, inventory) {
  const allowed = new Set(inventory.tools.map(tool => tool.id))
  return decision.tool_calls.every(call => call && typeof call.tool === 'string' && allowed.has(call.tool))
}

function actionSignature(decision) {
  const tools = decision.tool_calls.map(call => call.tool).sort().join(',')
  return `${decision.action}|${tools}|${decision.next_objective ?? ''}`
}

function deterministicGates() {
  return [
    ['preflight', 'npm', ['run', 'agent:preflight']],
    ['lint', 'npm', ['run', 'lint']],
    ['unit', 'npm', ['run', 'test:unit']],
    ['build', 'npm', ['run', 'build']],
  ].map(([name, command, args]) => run(name, command, args))
}

const state = loadState()
const inventory = connectedToolInventory()
if (!inventory.connected || !inventory.tools.length) {
  state.status = 'blocked_no_tools'
  state.updated_at = now()
  state.history.push({ at: now(), phase: 'startup', error: 'No runtime-connected tools were supplied.' })
  saveState(state)
  throw new Error('Engineering loop refused to start: no runtime-connected tools were supplied.')
}

const preflight = run('preflight', 'npm', ['run', 'agent:preflight'])
state.history.push({ at: now(), phase: 'preflight', result: preflight, tool_inventory: inventory })
if (!preflight.ok) { state.status = 'blocked_preflight'; state.failures += 1; state.updated_at = now(); saveState(state); process.exit(1) }
saveState(state)

const deadline = Date.now() + mission.budgets.max_runtime_minutes * 60_000
let finished = false
for (let i = state.iteration + 1; i <= mission.budgets.max_iterations; i += 1) {
  if (Date.now() >= deadline) break
  state.iteration = i
  saveState(state)

  let decision
  try {
    decision = askAgent(buildContext(state, inventory))
  } catch (error) {
    state.failures += 1
    state.history.push({ at: now(), iteration: i, phase: 'agent-error', error: error.message, recoverable: true })
    saveState(state)
    if (state.failures >= mission.budgets.max_failures) { state.status = 'failed_budget'; break }
    continue
  }
  if (!decision) { state.status = 'agent_not_configured'; saveState(state); break }

  if (!validateToolCalls(decision, inventory)) {
    state.failures += 1
    state.history.push({ at: now(), iteration: i, phase: 'tool-validation', error: 'Agent referenced a tool that is not in the runtime-connected inventory.', decision })
    saveState(state)
    if (state.failures >= mission.budgets.max_failures) { state.status = 'failed_budget'; break }
    continue
  }

  const signature = actionSignature(decision)
  const priorCount = state.action_signatures.filter(item => item === signature).length
  state.action_signatures.push(signature)
  if (priorCount >= 2 && decision.done !== true) {
    state.failures += 1
    state.history.push({ at: now(), iteration: i, phase: 'stagnation', error: 'Agent repeated the same action signature three times.', signature })
    saveState(state)
    if (state.failures >= mission.budgets.max_failures) { state.status = 'failed_stagnation'; break }
    continue
  }

  const requiresCheckpoint = mission.risk_policy.checkpoint_required.includes(decision.action)
  if (requiresCheckpoint && process.env.FABRIENT_LOOP_CHECKPOINT !== 'approved') {
    state.status = 'checkpoint_required'
    state.history.push({ at: now(), iteration: i, phase: 'decision', decision, blocked: 'high-risk action requires checkpoint' })
    saveState(state); process.exitCode = 2; break
  }

  state.history.push({ at: now(), iteration: i, phase: 'decision', decision })
  if (decision.done === true) {
    const gates = deterministicGates()
    state.history.push({ at: now(), iteration: i, phase: 'verification', gates })
    if (gates.every(gate => gate.ok)) { finished = true; state.status = 'verified'; saveState(state); break }
    state.failures += 1
  } else if (!Array.isArray(decision.evidence) || decision.evidence.length === 0) {
    state.failures += 1
    state.history.push({ at: now(), iteration: i, phase: 'evidence', error: 'Agent decision contained no evidence.' })
  }
  if (state.failures >= mission.budgets.max_failures) { state.status = 'failed_budget'; break }
  saveState(state)
}

if (!finished && state.status === 'running') state.status = Date.now() >= deadline ? 'runtime_budget_exhausted' : state.iteration >= mission.budgets.max_iterations ? 'iteration_budget_exhausted' : 'awaiting_agent'
state.updated_at = now()
saveState(state)
console.log(JSON.stringify({ status: state.status, iteration: state.iteration, failures: state.failures, connected_tool_count: inventory.tools.length, state_file: statePath }, null, 2))
if (state.status === 'verified' || state.status === 'awaiting_agent' || state.status === 'agent_not_configured') process.exit(0)
process.exit(1)
