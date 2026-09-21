import { HeartPulse } from 'lucide-react'

export default function AuthLoadingScreen() {
  return (
    <main className="auth-shell" role="status">
      <div className="text-center">
        <HeartPulse className="mx-auto animate-pulse text-pine" size={40} />
        <p className="mt-4 text-sm font-medium text-muted">Checking your session…</p>
      </div>
    </main>
  )
}
