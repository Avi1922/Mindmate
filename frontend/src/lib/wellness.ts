import { authenticatedApiRequest } from './api'
import type { ConversationTurnInput } from './conversation'

export const preferenceOptions = {
  goal: [
    'Understand my feelings',
    'Manage everyday stress',
    'Build a reflection habit',
    'Feel more balanced',
  ],
  support_style: ['Gentle encouragement', 'Practical small steps', 'Questions to reflect on'],
  calming_activity: ['Music', 'Walking', 'Breathing', 'Writing', 'Talking to someone'],
  check_in_time: ['Morning', 'Afternoon', 'Evening', 'Whenever works'],
} as const
export interface Preferences {
  goal: string
  support_style: string
  calming_activity: string
  check_in_time: string
  onboarding_complete: boolean
}
export const emptyPreferences: Preferences = {
  goal: '',
  support_style: '',
  calming_activity: '',
  check_in_time: '',
  onboarding_complete: false,
}
export const getProfile = () => authenticatedApiRequest<Preferences>('/profile')
export const saveProfile = (profile: Preferences) =>
  authenticatedApiRequest<Preferences>('/profile', {
    method: 'PUT',
    body: JSON.stringify(profile),
  })
export interface Streak {
  current: number
  longest: number
  checked_in_today: boolean
}
export const getStreak = () => authenticatedApiRequest<Streak>('/mood/streak')
export const sendChat = (turns: ConversationTurnInput[]) =>
  authenticatedApiRequest<{ reply: string }>(
    '/assistant/chat',
    { method: 'POST', body: JSON.stringify({ turns }) },
    35000,
  )
