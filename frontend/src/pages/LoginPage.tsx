import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import AuthLayout from '../components/AuthLayout'
import { useAuth } from '../contexts/useAuth'
import { getAuthenticationErrorMessage } from '../lib/auth-errors'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const destination =
    typeof location.state === 'object' &&
    location.state !== null &&
    'from' in location.state &&
    typeof location.state.from === 'string'
      ? location.state.from
      : '/dashboard'

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(email.trim(), password)
      navigate(destination, { replace: true })
    } catch (caughtError) {
      setError(getAuthenticationErrorMessage(caughtError))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout
      footer="Authentication is provided by Firebase. Never share your password with anyone."
      subtitle="Sign in to continue your private reflections and mood history."
      title="Welcome back"
    >
          <form className="space-y-5" onSubmit={(event) => void handleSubmit(event)}>
            <label className="field-label">
              Email
              <input
                autoComplete="email"
                className="field-input"
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                required
                type="email"
                value={email}
              />
            </label>
            <label className="field-label">
              Password
              <input
                autoComplete="current-password"
                className="field-input"
                minLength={8}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="••••••••"
                required
                type="password"
                value={password}
              />
            </label>
            {error && <p className="form-error" role="alert">{error}</p>}
            <button className="button-primary w-full justify-center" disabled={submitting} type="submit">
              {submitting ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
          <p className="mt-5 text-center text-sm text-muted">
            New here? <Link className="text-link" to="/register">Create an account</Link>
          </p>
    </AuthLayout>
  )
}
