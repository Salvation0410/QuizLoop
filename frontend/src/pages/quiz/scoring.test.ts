import { describe, expect, it } from 'vitest'
import { answersMatch } from './scoring'

describe('前端即时判题', () => {
  it('多选答案忽略顺序', () => {
    expect(answersMatch(['A', 'C'], ['C', 'A'])).toBe(true)
  })

  it('拒绝重复、缺失和多余选项', () => {
    expect(answersMatch(['A'], ['A', 'A'])).toBe(false)
    expect(answersMatch(['A', 'C'], ['A'])).toBe(false)
    expect(answersMatch(['A'], ['A', 'B'])).toBe(false)
  })
})
