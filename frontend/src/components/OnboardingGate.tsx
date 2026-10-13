import { useEffect, useState, type ReactNode } from 'react'
import { emptyPreferences, getProfile, saveProfile, type Preferences } from '../lib/wellness'
import PreferenceForm from './PreferenceForm'
export default function OnboardingGate({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<Preferences | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    let active = true
    getProfile()
      .then((p) => {
        if (active) setProfile(p)
      })
      .catch(() => {
        if (active) setError('Your preferences could not be loaded. Please try again.')
      })
    return () => {
      active = false
    }
  }, [attempt])
  async function finish(skip: boolean) {
    setBusy(true)
    setError('')
    try {
      const p = await saveProfile({
        ...(skip ? emptyPreferences : profile!),
        onboarding_complete: true,
      })
      setProfile(p)
    } catch {
      setError('Preferences could not be saved. Please try again.')
    } finally {
      setBusy(false)
    }
  }
  if (profile?.onboarding_complete) return children
  return (
    <section className="card mx-auto max-w-2xl space-y-6">
      <p className="text-xs font-bold uppercase tracking-widest text-sage">
        A little about your preferences
      </p>
      <h1 className="font-display text-3xl font-semibold">Make this space yours</h1>
      <p className="text-sm text-muted">
        These optional questions help tailor reflections. No name, address or personal ID is needed.
        You can change your answers in Profile.
      </p>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      {profile ? (
        <>
          <PreferenceForm value={profile} onChange={setProfile} />
          <div className="flex flex-wrap gap-4">
            <button className="button-primary" disabled={busy} onClick={() => void finish(false)}>
              Save and continue
            </button>
            <button className="text-link" disabled={busy} onClick={() => void finish(true)}>
              Skip for now
            </button>
          </div>
        </>
      ) : error ? (
        <button
          className="button-primary"
          onClick={() => {
            setError('')
            setAttempt((a) => a + 1)
          }}
        >
          Try again
        </button>
      ) : (
        <p role="status">Loading your preferences…</p>
      )}
    </section>
  )
}
