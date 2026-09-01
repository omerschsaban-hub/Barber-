import { existsSync, readFileSync } from 'node:fs'

const mission = JSON.parse(readFileSync('engineering-loop/mission.json', 'utf8'))
const loop = readFileSync('scripts/agent-loop.mjs', 'utf8')
const packageJson = JSON.parse(readFileSync('package.json', 'utf8'))
const registry = readFileSync('engineering/app/mcp_integrations.py', 'utf8')

const checks = [
  ['mission has bounded iteration budget', mission.budgets?.max_iterations > 0],
  ['mission has failure budget', mission.budgets?.max_failures > 0],
  ['mission has runtime budget', mission.budgets?.max_runtime_minutes > 0],
  ['loop persists state', loop.includes('.engineering-loop/state.json')],
  ['loop requires evidence', loop.includes('require_evidence') && loop.includes('decision.evidence')],
  ['loop has independent deterministic gates', loop.includes('deterministicGates') && loop.includes('npm')],
  ['loop refuses missing tool inventory', loop.includes('no connected tools were supplied')],
  ['loop blocks high-risk actions without checkpoint', loop.includes('FABRIENT_LOOP_CHECKPOINT')],
  ['loop cannot claim done without gates', loop.includes('decision.done === true') && loop.includes('gates.every')],
  ['package exposes agent loop command', packageJson.scripts?.['agent:loop'] === 'node scripts/agent-loop.mjs'],
  ['MCP provider catalog is present', registry.includes('MCP_PROVIDERS')],
  ['preflight script is present', existsSync('scripts/agent-preflight.mjs')],
]

for (const [name, ok] of checks) console.log(`${ok ? 'PASS' : 'FAIL'} ${name}`)
const failed = checks.filter(([, ok]) => !ok)
if (failed.length) process.exit(1)
console.log(`Agent-loop architecture verification passed: ${checks.length}/${checks.length} checks.`)
