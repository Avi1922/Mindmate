import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { LiveServerMessage } from '@google/genai'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import AssistantPage from './AssistantPage'

interface LiveCallbacks {
  onopen: () => void
  onmessage: (message: LiveServerMessage) => void
  onerror: () => void
  onclose: () => void
}

const assistantMock = vi.hoisted(() => ({
  analyzeText: vi.fn(),
  close: vi.fn(),
  connect: vi.fn(),
  createConversation: vi.fn(),
  createLiveToken: vi.fn(),
  microphoneStart: vi.fn(),
  microphoneStop: vi.fn(),
  playerClose: vi.fn(),
  playerPlay: vi.fn(),
  playerResume: vi.fn(),
  playerStop: vi.fn(),
  sendRealtimeInput: vi.fn(),
  callbacks: null as LiveCallbacks | null,
}))

vi.mock('@google/genai', () => ({
  GoogleGenAI: class {
    live = { connect: assistantMock.connect }
  },
  Modality: { AUDIO: 'AUDIO' },
}))

vi.mock('../lib/live', () => ({
  createLiveToken: assistantMock.createLiveToken,
  MicrophoneStreamer: class {
    start = assistantMock.microphoneStart
    stop = assistantMock.microphoneStop
  },
  PcmPlayer: class {
    close = assistantMock.playerClose
    play = assistantMock.playerPlay
    resume = assistantMock.playerResume
    stop = assistantMock.playerStop
  },
}))

vi.mock('../lib/conversation', () => ({
  createConversation: assistantMock.createConversation,
}))

vi.mock('../lib/analysis', () => ({
  analyzeText: assistantMock.analyzeText,
}))

const session = {
  close: assistantMock.close,
  sendRealtimeInput: assistantMock.sendRealtimeInput,
}

describe('AssistantPage', () => {
  beforeEach(() => {
    for (const mock of [
      assistantMock.analyzeText,
      assistantMock.close,
      assistantMock.connect,
      assistantMock.createConversation,
      assistantMock.createLiveToken,
      assistantMock.microphoneStart,
      assistantMock.microphoneStop,
      assistantMock.playerClose,
      assistantMock.playerPlay,
      assistantMock.playerResume,
      assistantMock.playerStop,
      assistantMock.sendRealtimeInput,
    ]) mock.mockReset()
    assistantMock.callbacks = null
    assistantMock.createLiveToken.mockResolvedValue({ token: 'short-lived', model: 'live-model' })
    assistantMock.connect.mockImplementation(async ({ callbacks }: { callbacks: LiveCallbacks }) => {
      assistantMock.callbacks = callbacks
      callbacks.onopen()
      return session
    })
  })

  it('shows an actionable microphone permission error and releases resources', async () => {
    assistantMock.microphoneStart.mockRejectedValue(
      new DOMException('Permission denied', 'NotAllowedError'),
    )
    const user = userEvent.setup()
    render(<AssistantPage />)

    await user.click(screen.getByRole('button', { name: 'Start conversation' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Microphone access was blocked')
    expect(assistantMock.microphoneStop).toHaveBeenCalled()
    expect(assistantMock.playerClose).toHaveBeenCalled()
  })

  it('starts, transcribes, ends, saves, and analyzes a conversation', async () => {
    const user = userEvent.setup()
    assistantMock.createConversation.mockResolvedValue({
      id: 'conversation-1',
      source: 'voice',
      transcript: 'User: I feel calm',
      turns: [{ role: 'user', text: 'I feel calm' }],
      started_at: '2026-09-21T10:00:00Z',
      ended_at: '2026-09-21T10:01:00Z',
      created_at: '2026-09-21T10:01:00Z',
    })
    assistantMock.analyzeText.mockResolvedValue({
      mood_score: 75,
      dominant_emotion: 'joy',
      language: 'en',
    })
    render(<AssistantPage />)

    await user.click(screen.getByRole('button', { name: 'Start conversation' }))
    expect(await screen.findByText('Listening')).toBeVisible()

    act(() => assistantMock.callbacks?.onmessage({
      serverContent: {
        inputTranscription: { text: 'I feel calm' },
        turnComplete: true,
      },
    } as LiveServerMessage))
    expect(await screen.findByText('I feel calm')).toBeVisible()

    await user.click(screen.getByRole('button', { name: 'End conversation' }))
    expect(assistantMock.close).toHaveBeenCalled()
    expect(assistantMock.microphoneStop).toHaveBeenCalled()

    await user.click(screen.getByRole('button', { name: 'Save and analyze' }))
    expect(await screen.findByText(/Conversation saved, analyzed/)).toBeVisible()
    expect(screen.getByText('75')).toBeVisible()
    expect(assistantMock.analyzeText).toHaveBeenCalledWith(
      'I feel calm',
      'conversation',
      'conversation-1',
    )
  })

  it('reports an unexpected live connection close and cleans up media', async () => {
    const user = userEvent.setup()
    render(<AssistantPage />)
    await user.click(screen.getByRole('button', { name: 'Start conversation' }))

    act(() => assistantMock.callbacks?.onclose())

    expect(await screen.findByRole('alert')).toHaveTextContent('The live session closed')
    expect(assistantMock.microphoneStop).toHaveBeenCalled()
    expect(assistantMock.playerClose).toHaveBeenCalled()
  })
})
