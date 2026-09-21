import { authenticatedApiRequest } from './api'

export interface JournalEntry {
  id: string
  text: string
  source: 'journal'
  created_at: string
}

interface JournalListResponse {
  items: JournalEntry[]
  count: number
}

export function createJournal(text: string): Promise<JournalEntry> {
  return authenticatedApiRequest<JournalEntry>('/journal', {
    method: 'POST',
    body: JSON.stringify({ text }),
  })
}

export async function listJournals(limit = 20): Promise<JournalEntry[]> {
  const response = await authenticatedApiRequest<JournalListResponse>(
    `/journal?limit=${limit}`,
  )
  return response.items
}
