import { render, screen } from '@testing-library/react'

import userEvent from '@testing-library/user-event'

import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../lib/api'

import JournalPage from './JournalPage'

const journalMock = vi.hoisted(() => ({
  createJournal: vi.fn(),

  listJournals: vi.fn(),

  analyzeJournal: vi.fn(),
}))

vi.mock('../lib/journal', () => ({
  createJournal: journalMock.createJournal,

  listJournals: journalMock.listJournals,
}))

vi.mock('../lib/analysis', () => ({
  analyzeJournal: journalMock.analyzeJournal,
}))

const entry = {
  id: 'journal-1',

  source: 'journal' as const,

  text: 'A calmer day.',

  created_at: '2026-09-21T10:00:00Z',
}

const analysis = {
  analysis_id: 'analysis-1',

  source_id: entry.id,

  created_at: entry.created_at,

  source: 'journal' as const,

  original_text: entry.text,

  language: 'en' as const,

  language_confidence: 0.99,

  anonymized_text: entry.text,

  translated_text: entry.text,

  translation_applied: false,

  pii_entities: [],

  emotions: { joy: 0.6, sadness: 0.1, anger: 0.05, fear: 0.05, neutral: 0.2 },

  dominant_emotion: 'joy' as const,

  mood_score: 72,

  confidence: 0.6,

  disclaimer: 'Not a diagnosis.',
}

describe('JournalPage', () => {
  beforeEach(() => {
    journalMock.createJournal.mockReset()

    journalMock.listJournals.mockReset().mockResolvedValue([])

    journalMock.analyzeJournal.mockReset()
  })

  it('shows a history failure instead of an empty database and supports retry', async () => {
    journalMock.listJournals

      .mockRejectedValueOnce(new ApiError('The request timed out. Please try again.', 408))

      .mockResolvedValueOnce([entry])

    const user = userEvent.setup()

    render(<JournalPage />)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Your journal history could not be loaded',
    )

    expect(screen.queryByText('No journal entries yet')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Try again' }))

    expect(await screen.findByText(entry.text)).toBeVisible()

    expect(screen.queryByRole('alert')).not.toBeInTheDocument()

    expect(journalMock.listJournals).toHaveBeenCalledTimes(2)
  })

  it('rejects a blank entry without calling the API', async () => {
    const user = userEvent.setup()

    render(<JournalPage />)

    await user.click(screen.getByRole('button', { name: 'Save and analyze' }))

    expect(screen.getByRole('alert')).toHaveTextContent('Write something before saving')

    expect(journalMock.createJournal).not.toHaveBeenCalled()
  })

  it('saves and analyzes a journal entry', async () => {
    journalMock.createJournal.mockResolvedValue(entry)

    journalMock.analyzeJournal.mockResolvedValue(analysis)

    const user = userEvent.setup()

    render(<JournalPage />)

    await user.type(screen.getByLabelText('Journal entry'), entry.text)

    await user.click(screen.getByRole('button', { name: 'Save and analyze' }))

    expect(
      await screen.findByText('Your journal entry was saved and analyzed privately.'),
    ).toBeVisible()

    expect(screen.getByText('+72')).toBeVisible()

    expect(journalMock.analyzeJournal).toHaveBeenCalledWith(entry.id)
  })

  it('keeps a saved entry visible when analysis fails', async () => {
    journalMock.createJournal.mockResolvedValue(entry)

    journalMock.analyzeJournal.mockRejectedValue(new ApiError('Analysis unavailable', 503))

    const user = userEvent.setup()

    render(<JournalPage />)

    await user.type(screen.getByLabelText('Journal entry'), entry.text)

    await user.click(screen.getByRole('button', { name: 'Save and analyze' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Your journal was saved, but analysis failed: Analysis unavailable',
    )

    expect(screen.getByText(entry.text)).toBeVisible()
  })

  it('retries only analysis after a saved journal fails and searches history', async () => {
    journalMock.createJournal.mockResolvedValue(entry)

    journalMock.analyzeJournal
      .mockRejectedValueOnce(new ApiError('AI unavailable', 503))
      .mockResolvedValueOnce(analysis)

    const user = userEvent.setup()
    render(<JournalPage />)

    await user.type(screen.getByLabelText('Journal entry'), entry.text)

    await user.click(screen.getByRole('button', { name: 'Save and analyze' }))

    await user.click(await screen.findByRole('button', { name: 'Retry analysis only' }))

    expect(
      await screen.findByText('Your saved journal was analyzed. No duplicate entry was created.'),
    ).toBeVisible()

    expect(journalMock.createJournal).toHaveBeenCalledTimes(1)

    expect(journalMock.analyzeJournal).toHaveBeenCalledTimes(2)

    await user.type(screen.getByRole('searchbox'), 'unmatched word')

    expect(screen.getByText('No journals match your search.')).toBeVisible()
  })
})
