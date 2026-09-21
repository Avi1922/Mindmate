import { describe, expect, it } from 'vitest'

import {
  appendTranscriptTurn,
  finalizeTranscript,
  formatDuration,
  mergeTranscript,
} from './transcript'

describe('transcript helpers', () => {
  it('merges streaming words and punctuation naturally', () => {
    expect(mergeTranscript('I feel', 'better')).toBe('I feel better')
    expect(mergeTranscript('I feel better', '.')).toBe('I feel better.')
    expect(mergeTranscript('Hello ', 'again')).toBe('Hello again')
  })

  it('extends an unfinished speaker turn and starts a new speaker turn', () => {
    const first = appendTranscriptTurn([], 'user', 'Hello', 1)
    const extended = appendTranscriptTurn(first, 'user', 'there', 2)
    const reply = appendTranscriptTurn(extended, 'assistant', 'Hi', 2)

    expect(extended).toEqual([{ id: 1, role: 'user', text: 'Hello there', final: false }])
    expect(reply).toHaveLength(2)
    expect(reply[1]).toMatchObject({ id: 2, role: 'assistant', text: 'Hi' })
  })

  it('finalizes turns and formats elapsed time', () => {
    const turns = [{ id: 1, role: 'user' as const, text: 'Hello', final: false }]
    expect(finalizeTranscript(turns)[0].final).toBe(true)
    expect(formatDuration(65)).toBe('01:05')
  })
})
