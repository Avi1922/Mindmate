import { beforeEach, describe, expect, it, vi } from 'vitest'

const authState = vi.hoisted(() => ({
  currentUser: null as null | { getIdToken: () => Promise<string> },
}))

vi.mock('./firebase', () => ({ firebaseAuth: authState }))

import { ApiError, authenticatedApiRequest } from './api'


describe('authenticatedApiRequest', () => {
  const fetchMock = vi.fn<typeof fetch>()

  beforeEach(() => {
    authState.currentUser = null
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
  })

  it('rejects before making a request when no user is signed in', async () => {
    await expect(authenticatedApiRequest('/journal')).rejects.toMatchObject({
      name: 'ApiError',
      status: 401,
    })
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('attaches the Firebase bearer token and JSON content type', async () => {
    authState.currentUser = { getIdToken: vi.fn().mockResolvedValue('firebase-token') }
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ id: 'journal-1' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    const result = await authenticatedApiRequest<{ id: string }>('/journal', {
      method: 'POST',
      body: JSON.stringify({ text: 'A calm day.' }),
    })

    expect(result).toEqual({ id: 'journal-1' })
    const [, init] = fetchMock.mock.calls[0]
    const headers = new Headers(init?.headers)
    expect(headers.get('Authorization')).toBe('Bearer firebase-token')
    expect(headers.get('Content-Type')).toBe('application/json')
  })

  it('surfaces a safe API detail message and status code', async () => {
    authState.currentUser = { getIdToken: vi.fn().mockResolvedValue('firebase-token') }
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Daily mood storage is temporarily unavailable' }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    const request = authenticatedApiRequest('/mood/daily/history?days=7')
    await expect(request).rejects.toEqual(
      new ApiError('Daily mood storage is temporarily unavailable', 503),
    )
  })

  it('turns network failures into a safe retryable error', async () => {
    authState.currentUser = { getIdToken: vi.fn().mockResolvedValue('firebase-token') }
    fetchMock.mockRejectedValue(new TypeError('network details'))

    await expect(authenticatedApiRequest('/journal')).rejects.toEqual(
      new ApiError('MindMate could not reach the server. Please try again.', 0),
    )
  })

  it('aborts stalled API calls after the configured timeout', async () => {
    vi.useFakeTimers()
    authState.currentUser = { getIdToken: vi.fn().mockResolvedValue('firebase-token') }
    fetchMock.mockImplementation((_input, init) => new Promise((_resolve, reject) => {
      init?.signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')))
    }))

    try {
      const request = authenticatedApiRequest('/journal')
      const assertion = expect(request).rejects.toEqual(
        new ApiError('The request timed out. Please try again.', 408),
      )
      await vi.advanceTimersByTimeAsync(15_000)

      await assertion
    } finally {
      vi.useRealTimers()
    }
  })
})
