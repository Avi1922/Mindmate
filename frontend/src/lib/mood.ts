import { authenticatedApiRequest } from './api'
import type { EmotionLabel, EmotionScores } from './analysis'

export interface DailyMoodRecord {
  date: string
  mood_score: number
  dominant_emotion: EmotionLabel
  emotions: EmotionScores
  journal_count: number
  conversation_count: number
  analysis_count: number
  updated_at: string
  disclaimer: string
}

interface DailyMoodHistoryResponse {
  count: number
  days: number
  items: DailyMoodRecord[]
}

export async function getDailyMoodHistory(days = 7): Promise<DailyMoodRecord[]> {
  const result = await authenticatedApiRequest<DailyMoodHistoryResponse>(
    `/mood/daily/history?days=${days}`,
  )
  return result.items
}
