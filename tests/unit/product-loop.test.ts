import { describe, expect, it } from 'vitest'
import { PRODUCT_LOOP, planHasFeature } from '../../lib/fabrinat-plans'

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
})
