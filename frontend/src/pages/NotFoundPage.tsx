import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <main className="auth-shell text-center">
      <section>
        <p className="font-display text-7xl font-semibold text-pine">404</p>
        <h1 className="mt-4 font-display text-2xl font-semibold">This page wandered off</h1>
        <p className="mt-2 text-sm text-muted">Let&apos;s return to your dashboard.</p>
        <Link className="button-primary mt-6" to="/dashboard">
          <ArrowLeft aria-hidden="true" size={17} /> Back to dashboard
        </Link>
      </section>
    </main>
  )
}
