import { describe, expect, it } from 'vitest'
import { FABRINAT_PLANS, FEATURE_COPY, PLAN_COMPARISON_ROWS, PRODUCT_LOOP, planHasFeature, planUsageLabel } from '../../lib/fabrinat-plans'
import { checkAndConsumeLlmRun, resetLlmUsageForTests } from '../../lib/llm-usage'

describe('product execution contract', () => {
  it('keeps one coherent engineering lifecycle', () => {
    expect(PRODUCT_LOOP.map(stage => stage.title)).toEqual([
      'Define', 'Check', 'Fix', 'Prove', 'Build', 'Inspect', 'Learn',
    ])
    expect(PRODUCT_LOOP.every(stage => stage.description.length > 10)).toBe(true)
  })

  it('keeps feature gating monotonic', () => {
    expect(planHasFeature('free', 'requirements')).toBe(true)
    expect(planHasFeature('free', 'release')).toBe(false)
    expect(planHasFeature('hobbyist', 'release')).toBe(true)
    expect(planHasFeature('startup', 'release')).toBe(true)
    expect(planHasFeature('enterprise', 'release')).toBe(true)
  })

  it('gives Free a useful but bounded LLM allowance', () => {
    resetLlmUsageForTests()
    const now = 1_000_000
    for (let i = 0; i < 10; i += 1) expect(checkAndConsumeLlmRun('free-user', 'free', now + i * 600_001).allowed).toBe(true)
    const monthly = checkAndConsumeLlmRun('free-user', 'free', now + 10 * 600_001)
    expect(monthly.allowed).toBe(false)
    if (!monthly.allowed) expect(monthly.reason).toBe('monthly_limit')
  })

  it('slows bursts without making the Free plan unusable', () => {
    resetLlmUsageForTests()
    const now = 2_000_000
    expect(checkAndConsumeLlmRun('burst-user', 'free', now).allowed).toBe(true)
    expect(checkAndConsumeLlmRun('burst-user', 'free', now + 1).allowed).toBe(true)
    expect(checkAndConsumeLlmRun('burst-user', 'free', now + 2).allowed).toBe(true)
    const limited = checkAndConsumeLlmRun('burst-user', 'free', now + 3)
    expect(limited.allowed).toBe(false)
    if (!limited.allowed) expect(limited.reason).toBe('burst_limit')
  })

  it('gives Hobby every individual engineering feature and adds control by tier', () => {
    const individualFeatures = Object.keys(FEATURE_COPY).filter(feature => !['team', 'api_access', 'governance'].includes(feature))
    expect(individualFeatures.every(feature => planHasFeature('hobbyist', feature))).toBe(true)
    expect(planHasFeature('free', 'fix')).toBe(false)
    expect(planHasFeature('startup', 'team')).toBe(true)
    expect(planHasFeature('enterprise', 'governance')).toBe(true)
    expect(planUsageLabel('free')).toBe('10 AI runs / month')
    expect(planUsageLabel('enterprise')).toBe('Unlimited AI runs')
    expect(PLAN_COMPARISON_ROWS.length).toBeGreaterThan(8)
    expect(FABRINAT_PLANS.hobbyist.limits.llmRuns).toBe(100)
  })
})
