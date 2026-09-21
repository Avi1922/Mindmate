import { authenticatedApiRequest } from './api'

export type ConversationRole = 'user' | 'assistant'

export interface ConversationTurnInput {
  role: ConversationRole
  text: string
}

export interface ConversationRecord {
  id: string
  source: 'voice'
  transcript: string
  turns: ConversationTurnInput[]
  started_at: string
  ended_at: string
  created_at: string
}

interface ConversationListResponse {
  items: ConversationRecord[]
  count: number
}

export function createConversation(
  turns: ConversationTurnInput[],
  startedAt: string,
  endedAt: string,
): Promise<ConversationRecord> {
  return authenticatedApiRequest<ConversationRecord>('/conversations', {
    method: 'POST',
    body: JSON.stringify({
      turns,
      started_at: startedAt,
      ended_at: endedAt,
    }),
  })
}

export async function listConversations(limit = 20): Promise<ConversationRecord[]> {
  const result = await authenticatedApiRequest<ConversationListResponse>(
    `/conversations?limit=${limit}`,
  )
  return result.items
}
