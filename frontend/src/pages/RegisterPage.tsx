import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import AuthLayout from '../components/AuthLayout'
import { useAuth } from '../contexts/useAuth'
import { getAuthenticationErrorMessage } from '../lib/auth-errors'

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setSubmitting(true)
    try {
      await register(email.trim(), password)
      navigate('/dashboard', { replace: true })
    } catch (caughtError) {
      setError(getAuthenticationErrorMessage(caughtError))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout
      footer="This wellbeing tool provides estimates only and is not a medical service."
      subtitle="Start a private space for reflection and transparent mood estimates."
      title="Create your account"
    >
          <form className="space-y-5" onSubmit={(event) => void handleSubmit(event)}>
            <label className="field-label">
              Email
              <input autoComplete="email" className="field-input" onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" required type="email" value={email} />
            </label>
            <label className="field-label">
              Password
              <input autoComplete="new-password" className="field-input" minLength={8} onChange={(event) => setPassword(event.target.value)} placeholder="At least 8 characters" required type="password" value={password} />
            </label>
            <label className="field-label">
              Confirm password
              <input autoComplete="new-password" className="field-input" minLength={8} onChange={(event) => setConfirmPassword(event.target.value)} placeholder="Repeat your password" required type="password" value={confirmPassword} />
            </label>
            {error && <p className="form-error" role="alert">{error}</p>}
            <button className="button-primary w-full justify-center" disabled={submitting} type="submit">
              {submitting ? 'Creating account…' : 'Create account'}
            </button>
          </form>
          <p className="mt-5 text-center text-sm text-muted">
            Already registered? <Link className="text-link" to="/login">Sign in</Link>
          </p>
    </AuthLayout>
  )
}
