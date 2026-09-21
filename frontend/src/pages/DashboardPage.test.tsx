import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../lib/api'
import DashboardPage from './DashboardPage'

const moodMock = vi.hoisted(() => ({
  getDailyMoodHistory: vi.fn(),
}))

vi.mock('../lib/mood', () => ({
  getDailyMoodHistory: moodMock.getDailyMoodHistory,
}))

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  LineChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CartesianGrid: () => null,
  Line: () => null,
  Tooltip: () => null,
  XAxis: () => null,
  YAxis: () => null,
}))

function renderDashboard() {
  return render(<MemoryRouter><DashboardPage /></MemoryRouter>)
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
    await user.click(screen.getByRole('button', { name: 'Try again' }))

    expect(await screen.findByText('Your dashboard is ready for a check-in')).toBeVisible()
    expect(moodMock.getDailyMoodHistory).toHaveBeenCalledTimes(2)
  })

  it('renders current mood, emotion signals, and activity totals', async () => {
    const today = new Date().toISOString().slice(0, 10)
    moodMock.getDailyMoodHistory.mockResolvedValue([{
      date: today,
      mood_score: 72,
      dominant_emotion: 'joy',
      emotions: { joy: 0.6, sadness: 0.1, anger: 0.05, fear: 0.05, neutral: 0.2 },
      journal_count: 2,
      conversation_count: 1,
      analysis_count: 3,
      updated_at: `${today}T10:00:00Z`,
      disclaimer: 'Not a diagnosis.',
    }])
    renderDashboard()

    expect(await screen.findByText('72')).toBeVisible()
    expect(screen.getAllByText('joy')).toHaveLength(2)
    expect(screen.getByLabelText('joy: 60%')).toBeVisible()
    expect(screen.getByText('Journal entries').closest('article')).toHaveTextContent('2')
    expect(screen.getByText('Conversations').closest('article')).toHaveTextContent('1')
  })
})
