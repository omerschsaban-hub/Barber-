import { existsSync, readFileSync } from 'node:fs'

const required = [
  'AGENTS.md',
  'CLAUDE.md',
  'docs/PRODUCT_EXECUTION_PRINCIPLES.md',
  'docs/DEEP_EXECUTION_STANDARD.md',
  'docs/PRODUCT_SIMPLIFICATION.md',
  '.claude/skills/playwright/SKILL.md',
]

const missing = required.filter(path => !existsSync(path))
if (missing.length) {
  console.error(`Agent preflight failed. Missing required operating documents:\n${missing.join('\n')}`)
  process.exit(1)
}

const agents = readFileSync('AGENTS.md', 'utf8')
const requiredTerms = [
  'READ THIS FILE BEFORE EVERY EXECUTION',
  'Test deeply',
  'Use the browser',
  'Simplify aggressively',
  'Optimize the whole system',
  'Automate repeated work',
]

const missingTerms = requiredTerms.filter(term => !agents.includes(term))
if (missingTerms.length) {
  console.error(`Agent preflight failed. AGENTS.md is missing required policy terms:\n${missingTerms.join('\n')}`)
  process.exit(1)
}

console.log('Agent preflight OK: mandatory execution, testing, simplification, hardening, and automation contracts are present.')
