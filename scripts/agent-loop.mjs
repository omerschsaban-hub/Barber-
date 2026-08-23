import { spawnSync } from 'node:child_process'

const steps = [
  ['preflight', 'npm', ['run', 'agent:preflight']],
  ['lint', 'npm', ['run', 'lint']],
  ['unit', 'npm', ['run', 'test:unit']],
  ['build', 'npm', ['run', 'build']],
  ['browser', 'npm', ['run', 'test:e2e']],
]

for (const [name, command, args] of steps) {
  console.log(`\n=== agent loop: ${name} ===`)
  const result = spawnSync(command, args, { stdio: 'inherit', shell: process.platform === 'win32' })
  if (result.status !== 0) {
    console.error(`agent loop stopped at ${name}; fix the failure before claiming acceptance`)
    process.exit(result.status ?? 1)
  }
}

console.log('\nAgent loop passed local preflight/lint/unit/build/browser gates.')
console.log('Production acceptance still requires deployed-runtime verification and MCP/engineering integration tests.')
