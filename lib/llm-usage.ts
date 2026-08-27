import {FABRINAT_PLANS, type FabrinatPlan} from './fabrinat-plans'

export type LlmUsagePlan = FabrinatPlan

export const LLM_USAGE_POLICY = {
  free: {burstRuns: 3, burstWindowMs: 10 * 60 * 1000},
  hobbyist: {burstRuns: 12, burstWindowMs: 10 * 60 * 1000},
  startup: {burstRuns: 30, burstWindowMs: 10 * 60 * 1000},
  enterprise: {burstRuns: 60, burstWindowMs: 10 * 60 * 1000},
} as const

type UsageRecord = { windowStartedAt: number; runs: number; recentRuns: number[] }

const usage = new Map<string, UsageRecord>()
const MONTH_MS = 30 * 24 * 60 * 60 * 1000

function recordFor(key: string, now: number): UsageRecord {
  const current = usage.get(key)
  if (!current || now - current.windowStartedAt >= MONTH_MS) {
    const fresh = { windowStartedAt: now, runs: 0, recentRuns: [] }
    usage.set(key, fresh)
    return fresh
  }
  current.recentRuns = current.recentRuns.filter(timestamp => now - timestamp < 10 * 60 * 1000)
  return current
}

export function checkAndConsumeLlmRun(
  key: string,
  plan: LlmUsagePlan,
  now = Date.now(),
): { allowed: true; used: number; limit: number; resetAt: number } | {
  allowed: false; reason: 'monthly_limit' | 'burst_limit'; used: number; limit: number; resetAt: number; retryAfterSeconds?: number
} {
  const record = recordFor(key, now)
  const policy = LLM_USAGE_POLICY[plan]
  const monthlyRuns = FABRINAT_PLANS[plan].limits.llmRuns
  const resetAt = record.windowStartedAt + MONTH_MS

  if (monthlyRuns !== -1 && record.runs >= monthlyRuns) {
    return { allowed: false, reason: 'monthly_limit', used: record.runs, limit: monthlyRuns, resetAt }
  }

  const oldestAllowed = now - policy.burstWindowMs
  record.recentRuns = record.recentRuns.filter(timestamp => timestamp > oldestAllowed)
  if (record.recentRuns.length >= policy.burstRuns) {
    const retryAfterSeconds = Math.max(1, Math.ceil((record.recentRuns[0] + policy.burstWindowMs - now) / 1000))
    return { allowed: false, reason: 'burst_limit', used: record.runs, limit: monthlyRuns, resetAt, retryAfterSeconds }
  }

  record.runs += 1
  record.recentRuns.push(now)
  return { allowed: true, used: record.runs, limit: monthlyRuns, resetAt }
}

export function resetLlmUsageForTests() {
  usage.clear()
}

export function llmUsageMessage(plan: LlmUsagePlan, used: number, limit: number) {
  if (limit === -1) return `${plan} plan: ${used} LLM runs used.`
  return `${plan} plan: ${used} of ${limit} LLM runs used this month.`
}
