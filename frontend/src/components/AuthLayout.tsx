import { HeartPulse, LockKeyhole, ShieldCheck, Sparkles } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

interface AuthLayoutProps {
  children: ReactNode
  footer: string
  subtitle: string
  title: string
}

const highlights = [
  { icon: Sparkles, text: 'Reflect in English, Hindi, or Hinglish' },
  { icon: ShieldCheck, text: 'Privacy-aware emotion analysis' },
  { icon: LockKeyhole, text: 'Your check-ins stay scoped to your account' },
]

export default function AuthLayout({ children, footer, subtitle, title }: AuthLayoutProps) {
  return (
    <main className="auth-shell">
      <section className="auth-panel" aria-labelledby="auth-heading">
        <aside className="auth-intro">
          <Link className="inline-flex items-center gap-3 font-display text-xl font-semibold text-white" to="/">
            <span className="grid size-10 place-items-center rounded-2xl bg-white/12">
              <HeartPulse aria-hidden="true" size={22} />
            </span>
            MindMate
          </Link>
          <div className="my-auto py-10">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-white/60">A quieter place to reflect</p>
            <p className="mt-4 max-w-md font-display text-4xl font-semibold leading-tight text-white">
              Notice how your days feel, one check-in at a time.
            </p>
            <div className="mt-8 space-y-4">
              {highlights.map(({ icon: Icon, text }) => (
                <div className="flex items-center gap-3 text-sm text-white/75" key={text}>
                  <span className="grid size-8 shrink-0 place-items-center rounded-xl bg-white/10">
                    <Icon aria-hidden="true" size={16} />
                  </span>
                  {text}
                </div>
              ))}
            </div>
          </div>
          <p className="text-xs leading-5 text-white/55">Experimental wellbeing support, never medical diagnosis.</p>
        </aside>

        <div className="auth-form-wrap">
          <div className="mb-8 lg:hidden">
            <Link className="inline-flex items-center gap-2 font-display text-xl font-semibold" to="/">
              <HeartPulse aria-hidden="true" className="text-pine" size={25} /> MindMate
            </Link>
          </div>
          <div className="w-full max-w-md">
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-sage">Private check-in</p>
            <h1 className="mt-2 font-display text-3xl font-semibold tracking-tight" id="auth-heading">{title}</h1>
            <p className="mt-3 text-sm leading-6 text-muted">{subtitle}</p>
            <div className="mt-7">{children}</div>
            <p className="mt-7 text-center text-xs leading-5 text-muted">{footer}</p>
          </div>
        </div>
      </section>
    </main>
  )
}
