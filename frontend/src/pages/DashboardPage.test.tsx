import { render, screen } from '@testing-library/react'

import userEvent from '@testing-library/user-event'

import { MemoryRouter } from 'react-router-dom'

import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../lib/api'

import DashboardPage from './DashboardPage'

const moodMock = vi.hoisted(() => ({
  getDailyMoodHistory: vi.fn(),

  getStreak: vi.fn().mockResolvedValue({ current: 2, longest: 3, checked_in_today: false }),

  getInsight: vi.fn().mockResolvedValue({ message: 'Keep making time for yourself.' }),
}))

vi.mock('../lib/mood', () => ({
  getDailyMoodHistory: moodMock.getDailyMoodHistory,
}))

vi.mock('../lib/wellness', () => ({
  getStreak: moodMock.getStreak,
  getInsight: moodMock.getInsight,
}))

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,

  LineChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,

  CartesianGrid: () => null,
  ReferenceLine: () => null,

  Line: () => null,

  Tooltip: () => null,

  XAxis: () => null,

  YAxis: () => null,
}))

function renderDashboard() {
  return render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>,
  )
}

describe('DashboardPage', () => {
  beforeEach(() => moodMock.getDailyMoodHistory.mockReset())

  it('shows the first-check-in state for an empty history', async () => {
    moodMock.getDailyMoodHistory.mockResolvedValue([])

    renderDashboard()

    expect(await screen.findByText('Your dashboard is ready for a check-in')).toBeVisible()

    expect(moodMock.getDailyMoodHistory).toHaveBeenCalledWith(7)
  })

  it('offers a retry after a load failure', async () => {
    moodMock.getDailyMoodHistory

      .mockRejectedValueOnce(new ApiError('Dashboard unavailable', 503))

      .mockResolvedValueOnce([])

    const user = userEvent.setup()

    renderDashboard()

    expect(await screen.findByRole('alert')).toHaveTextContent('Dashboard unavailable')

    expect(screen.queryByText('No check-in yet')).not.toBeInTheDocument()

    expect(screen.queryByText('No emotion data for today.')).not.toBeInTheDocument()

    expect(screen.queryByText('Journal entries')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Try again' }))

    expect(await screen.findByText('Your dashboard is ready for a check-in')).toBeVisible()

    expect(moodMock.getDailyMoodHistory).toHaveBeenCalledTimes(2)
  })

  it('renders current mood, emotion signals, and activity totals', async () => {
    const today = new Date().toISOString().slice(0, 10)

    moodMock.getDailyMoodHistory.mockResolvedValue([
      {
        date: today,

        mood_score: 72,

        dominant_emotion: 'joy',

        emotions: { joy: 0.6, sadness: 0.1, anger: 0.05, fear: 0.05, neutral: 0.2 },

        journal_count: 2,

        conversation_count: 1,

        analysis_count: 3,

        updated_at: `${today}T10:00:00Z`,

        disclaimer: 'Not a diagnosis.',
      },
    ])

    renderDashboard()

    expect(await screen.findByText('+72')).toBeVisible()

    expect(screen.getAllByText('joy')).toHaveLength(2)

    expect(screen.getByLabelText('joy: 60%')).toBeVisible()

    expect(screen.getByText('Journal entries').closest('article')).toHaveTextContent('2')

    expect(screen.getByText('Conversations').closest('article')).toHaveTextContent('1')
  })

  it('switches the chart between week and month', async () => {
    moodMock.getDailyMoodHistory.mockResolvedValue([])

    const user = userEvent.setup()
    renderDashboard()

    await screen.findByText('Your dashboard is ready for a check-in')

    await user.selectOptions(screen.getByRole('combobox'), '30')

    expect(await screen.findByText('Your dashboard is ready for a check-in')).toBeVisible()

    expect(moodMock.getDailyMoodHistory).toHaveBeenLastCalledWith(30)

    expect(await screen.findByText('2 days in your streak')).toBeVisible()
  })
  it('shows preset message, signed score and streak in that order without AI', async () => {
    moodMock.getDailyMoodHistory.mockResolvedValue([
      {
        date: new Date().toISOString().slice(0, 10),
        mood_score: 85,
        dominant_emotion: 'joy',
        emotions: { joy: 1, sadness: 0, anger: 0, fear: 0, neutral: 0 },
        journal_count: 1,
        conversation_count: 0,
        analysis_count: 1,
        updated_at: new Date().toISOString(),
        disclaimer: 'Not a diagnosis.',
      },
    ])
    renderDashboard()
    const message = await screen.findByText('Your mood is great today.')
    const score = screen.getByText('+85')
    const streak = await screen.findByText('2 days in your streak')
    expect(message.compareDocumentPosition(score) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(score.compareDocumentPosition(streak) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(
      screen.queryByRole('button', { name: 'Generate personalized reflection' }),
    ).not.toBeInTheDocument()
  })
})
