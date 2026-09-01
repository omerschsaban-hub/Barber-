import { existsSync, readFileSync, rmSync } from 'node:fs'
import { spawnSync } from 'node:child_process'

const statePath = '.engineering-loop/state.json'
rmSync(statePath, { force: true })
const env = {
  ...process.env,
  FABRIENT_LOOP_RESET: '1',
  FABRIENT_LOOP_TEST_MODE: '1',
  FABRIENT_AGENT_COMMAND: 'node scripts/agent-loop-fixture.mjs',
  FABRIENT_AGENT_TOOLS_JSON: JSON.stringify([{ id: 'fixture.inspect', name: 'Fixture Inspector' }]),
}
const result = spawnSync(process.execPath, ['scripts/agent-loop.mjs'], { encoding: 'utf8', env })
if (result.status !== 0) {
  console.error(result.stdout)
  console.error(result.stderr)
  process.exit(result.status ?? 1)
}
if (!existsSync(statePath)) throw new Error('Self-test did not create persistent state')
const state = JSON.parse(readFileSync(statePath, 'utf8'))
if (state.status !== 'verified') throw new Error(`Self-test expected verified status, got ${state.status}`)
if (state.iteration !== 3) throw new Error(`Self-test expected 3 iterations, got ${state.iteration}`)
if (state.history.filter(item => item.phase === 'decision').length !== 3) throw new Error('Self-test did not record all decisions')
if (!state.history.some(item => item.phase === 'verification')) throw new Error('Self-test did not record verification')
if (!state.action_signatures?.length) throw new Error('Self-test did not record action signatures')
console.log('PASS autonomous engineering loop end-to-end self-test')
console.log(JSON.stringify({ status: state.status, iterations: state.iteration, failures: state.failures }, null, 2))
rmSync(statePath, { force: true })
