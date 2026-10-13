import { useEffect, useState } from 'react'
import { getStreak, type Streak } from '../lib/wellness'
export default function StreakCard({ refreshKey }: { refreshKey: number }) {
  const [streak, setStreak] = useState<Streak | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    let active = true
    getStreak()
      .then((s) => {
        if (active) {
          setStreak(s)
          setError('')
        }
      })
      .catch(() => {
        if (active) setError('Streak could not be loaded.')
      })
    return () => {
      active = false
    }
  }, [refreshKey])
  return (
    <article className="card">
      <p className="text-xs font-bold uppercase tracking-widest text-sage">
        Your reflection habit · UTC days
      </p>
      {error ? (
        <p className="mt-3 text-sm">{error}</p>
      ) : streak ? (
        <>
          <p className="mt-3 font-display text-3xl font-semibold">
            {streak.current} day{streak.current === 1 ? '' : 's'} in your streak
          </p>
          <p className="mt-2 text-sm text-muted">
            Longest streak: {streak.longest} days.{' '}
            {streak.checked_in_today
              ? 'You made time for yourself today.'
              : streak.current
                ? 'A small check-in today can keep your habit going.'
                : 'One small check-in is a fresh start. Missing a day is okay.'}
          </p>
          <p className="mt-2 text-xs text-muted">
            A day counts after a journal or conversation is successfully analyzed.
          </p>
        </>
      ) : (
        <p className="mt-3" role="status">
          Loading your streak…
        </p>
      )}
    </article>
  )
}
