import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/useAuth'
import PageHeader from '../components/PageHeader'
import PreferenceForm from '../components/PreferenceForm'
import { getProfile, saveProfile, type Preferences } from '../lib/wellness'
export default function ProfilePage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [profile, setProfile] = useState<Preferences | null>(null)
  const [message, setMessage] = useState('')
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
        if (active) setError('Profile could not be loaded.')
      })
    return () => {
      active = false
    }
  }, [attempt])
  async function save() {
    if (!profile) return
    setBusy(true)
    setError('')
    setMessage('')
    try {
      setProfile(await saveProfile({ ...profile, onboarding_complete: true }))
      setMessage('Your preferences are saved.')
    } catch {
      setError('Your preferences could not be saved.')
    } finally {
      setBusy(false)
    }
  }
  async function signOut() {
    setBusy(true)
    try {
      await logout()
      navigate('/login', { replace: true })
    } catch {
      setError('Sign out failed. Please try again.')
    } finally {
      setBusy(false)
    }
  }
  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Your space"
        title="Profile"
        description="Choose the support that works for you. All questionnaire answers are optional."
      />
      <div className="card space-y-6">
        <p className="text-sm text-muted">Signed in as {user?.email}</p>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        {profile ? (
          <>
            <PreferenceForm value={profile} onChange={setProfile} />
            <button className="button-primary" disabled={busy} onClick={() => void save()}>
              Save preferences
            </button>
          </>
        ) : (
          <button
            className="text-link"
            onClick={() => {
              setError('')
              setAttempt((a) => a + 1)
            }}
          >
            Reload profile
          </button>
        )}
        {message && <p role="status">{message}</p>}
        <div className="border-t border-line pt-5">
          <button className="text-link" disabled={busy} onClick={() => void signOut()}>
            Log out
          </button>
        </div>
      </div>
    </section>
  )
}
