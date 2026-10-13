import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import OnboardingGate from './OnboardingGate'
const mocks = vi.hoisted(() => ({ getProfile: vi.fn(), saveProfile: vi.fn() }))
vi.mock('../lib/wellness', () => ({
  getProfile: mocks.getProfile,
  saveProfile: mocks.saveProfile,
  emptyPreferences: {
    goal: '',
    support_style: '',
    calming_activity: '',
    check_in_time: '',
    onboarding_complete: false,
  },
  preferenceOptions: {
    goal: ['Manage everyday stress'],
    support_style: ['Gentle encouragement'],
    calming_activity: ['Music'],
    check_in_time: ['Evening'],
  },
}))
describe('optional onboarding', () => {
  beforeEach(() => {
    mocks.getProfile.mockReset()
    mocks.saveProfile.mockReset()
  })
  it('allows skipping without requiring identifying information', async () => {
    mocks.getProfile.mockResolvedValue({
      goal: '',
      support_style: '',
      calming_activity: '',
      check_in_time: '',
      onboarding_complete: false,
    })
    mocks.saveProfile.mockImplementation(async (p) => p)
    const user = userEvent.setup()
    render(
      <OnboardingGate>
        <p>Dashboard content</p>
      </OnboardingGate>,
    )
    await user.click(await screen.findByRole('button', { name: 'Skip for now' }))
    expect(await screen.findByText('Dashboard content')).toBeVisible()
    expect(mocks.saveProfile).toHaveBeenCalledWith(
      expect.objectContaining({ onboarding_complete: true, goal: '' }),
    )
  })
  it('does not repeat completed onboarding', async () => {
    mocks.getProfile.mockResolvedValue({ onboarding_complete: true })
    render(
      <OnboardingGate>
        <p>Dashboard content</p>
      </OnboardingGate>,
    )
    expect(await screen.findByText('Dashboard content')).toBeVisible()
    expect(screen.queryByText('Make this space yours')).not.toBeInTheDocument()
  })
})
