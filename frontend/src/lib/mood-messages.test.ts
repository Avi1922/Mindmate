import { describe, expect, it } from 'vitest'
import { formatMoodScore, moodMessage } from './mood-messages'
describe('stored mood message boundaries', () => {
  it('uses the great mood message only above 80', () => {
    expect(moodMessage(81)).toBe('Your mood is great today.')
    expect(moodMessage(80)).not.toBe('Your mood is great today.')
  })
  it('offers gentle support for negative scores and balanced text at zero', () => {
    expect(moodMessage(-90)).toContain('You deserve care')
    expect(moodMessage(0)).toContain('balanced')
    expect(formatMoodScore(-90)).toBe('-90')
    expect(formatMoodScore(80)).toBe('+80')
  })
})
