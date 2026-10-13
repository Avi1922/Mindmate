// Stored message bands match the backend; scores are text-derived estimates.
export const moodMessages = [
  { min: 81, message: 'Your mood is great today.' },
  {
    min: 40,
    message: 'There is positive energy in your day. Enjoy a small moment that feels good.',
  },
  { min: 10, message: 'Your day has some encouraging moments. Keep making time for yourself.' },
  {
    min: -10,
    message: 'Your mood feels fairly balanced today. A small check-in can help you reflect.',
  },
  {
    min: -40,
    message: 'Today may feel a little difficult. Give yourself room for a gentle pause.',
  },
  {
    min: -80,
    message: 'Today feels heavy. Take one small step and consider talking to someone you trust.',
  },
  {
    min: -100,
    message:
      'You deserve care on difficult days. Slow down and reach out for support if you need it.',
  },
] as const
export function moodMessage(score: number): string {
  return (moodMessages.find((band) => score >= band.min) ?? moodMessages[moodMessages.length - 1])
    .message
}
export const formatMoodScore = (score: number) => (score > 0 ? `+${score}` : String(score))
