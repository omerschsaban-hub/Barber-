import { readFileSync } from 'node:fs'

const context = JSON.parse(readFileSync(0, 'utf8'))
const iteration = context.state.iteration
const tool = context.tools.tools[0]?.id
if (!tool) process.exit(2)

if (iteration === 1) {
  console.log(JSON.stringify({
    action: 'inspect',
    next_objective: 'Use the connected tool to inspect the target and establish a baseline.',
    tool_calls: [{ tool, input: { fixture: true, step: 1 } }],
    evidence: ['fixture inspection completed'],
    done: false,
  }))
} else if (iteration === 2) {
  console.log(JSON.stringify({
    action: 'test',
    next_objective: 'Verify the change using the connected tool.',
    tool_calls: [{ tool, input: { fixture: true, step: 2 } }],
    evidence: ['fixture verification completed'],
    done: false,
  }))
} else {
  console.log(JSON.stringify({
    action: 'verify',
    next_objective: 'Finish only after deterministic gates pass.',
    tool_calls: [{ tool, input: { fixture: true, step: 3 } }],
    evidence: ['fixture final evidence present'],
    done: true,
  }))
}
