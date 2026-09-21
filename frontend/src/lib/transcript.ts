import type { ConversationRole } from './conversation'

export interface TranscriptTurn {
  id: number
  role: ConversationRole
  text: string
  final: boolean
}

export function mergeTranscript(existing: string, fragment: string): string {
  const clean = fragment.trim()
  if (!existing) return clean
  if (!clean) return existing
  if (/\s$/.test(existing) || /^[.,!?;:]/.test(clean)) return `${existing}${clean}`
  return `${existing} ${clean}`
}

export function appendTranscriptTurn(
  turns: TranscriptTurn[],
  role: ConversationRole,
  fragment: string,
  nextId: number,
): TranscriptTurn[] {
  if (!fragment.trim()) return turns
  const last = turns.at(-1)
  if (last?.role === role && !last.final) {
    return [
      ...turns.slice(0, -1),
      { ...last, text: mergeTranscript(last.text, fragment) },
    ]
  }
  return [...turns, { id: nextId, role, text: fragment.trim(), final: false }]
}

export function finalizeTranscript(turns: TranscriptTurn[]): TranscriptTurn[] {
  return turns.map((turn) => ({ ...turn, final: true }))
}

export function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60).toString().padStart(2, '0')
  const remainder = (seconds % 60).toString().padStart(2, '0')
  return `${minutes}:${remainder}`
}
