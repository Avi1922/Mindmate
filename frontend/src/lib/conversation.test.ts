import { beforeEach, describe, expect, it, vi } from 'vitest'

const apiRequest = vi.hoisted(() => vi.fn())
vi.mock('./api', () => ({ authenticatedApiRequest: apiRequest }))

import { createConversation } from './conversation'


describe('createConversation', () => {
  beforeEach(() => apiRequest.mockReset())

  it('sends only structured turns and timestamps to the protected API', async () => {
    apiRequest.mockResolvedValue({ id: 'conversation-1' })
    const turns = [
      { role: 'user' as const, text: 'I feel calmer.' },
      { role: 'assistant' as const, text: 'What helped?' },
    ]

    await createConversation(
      turns,
      '2026-09-20T10:00:00.000Z',
      '2026-09-20T10:03:00.000Z',
    )

    expect(apiRequest).toHaveBeenCalledWith('/conversations', {
      method: 'POST',
      body: JSON.stringify({
        turns,
        started_at: '2026-09-20T10:00:00.000Z',
        ended_at: '2026-09-20T10:03:00.000Z',
      }),
    })
  })
})
