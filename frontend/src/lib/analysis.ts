import { authenticatedApiRequest } from './api'

export type EmotionLabel = 'joy' | 'sadness' | 'anger' | 'fear' | 'neutral'

export interface EmotionScores {
  joy: number
  sadness: number
  anger: number
  fear: number
  neutral: number
}

export interface AnalysisResult {
  analysis_id: string
  source_id: string | null
  created_at: string
  source: 'journal' | 'conversation'
  original_text: string
  language: 'en' | 'hi' | 'hinglish' | 'other' | 'unknown'
  language_confidence: number
  anonymized_text: string
  translated_text: string
  translation_applied: boolean
  pii_entities: Array<{ type: string; count: number }>
  emotions: EmotionScores
  dominant_emotion: EmotionLabel
  mood_score: number
  confidence: number
  disclaimer: string
}

export function analyzeText(
  text: string,
  source: 'journal' | 'conversation',
  sourceId?: string,
): Promise<AnalysisResult> {
  return authenticatedApiRequest<AnalysisResult>('/analyze', {
    method: 'POST',
    body: JSON.stringify({
      text,
      source,
      source_id: sourceId,
    }),
  })
}
