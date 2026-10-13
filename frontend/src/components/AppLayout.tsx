import { BookOpenText, HeartPulse, LayoutDashboard, LogOut, Mic2, UserRound } from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import OnboardingGate from './OnboardingGate'
import GetHelp from './GetHelp'
import { useAuth } from '../contexts/useAuth'

const navigation = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/assistant', label: 'AI Assistant', icon: Mic2 },
  { to: '/journal', label: 'Journal', icon: BookOpenText },
  { to: '/profile', label: 'Profile', icon: UserRound },
]

export default function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [loggingOut, setLoggingOut] = useState(false)

  async function handleLogout() {
    setLoggingOut(true)
    try {
      await logout()
      navigate('/login', { replace: true })
    } finally {
      setLoggingOut(false)
    }
  }

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>
      <header className="sticky top-0 z-20 border-b border-line/80 bg-canvas/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
          <NavLink className="flex items-center gap-3" to="/dashboard">
            <span className="grid size-10 place-items-center rounded-2xl bg-pine text-white shadow-soft">
              <HeartPulse aria-hidden="true" size={21} strokeWidth={2.2} />
            </span>
            <span>
              <span className="block font-display text-lg font-semibold leading-none">
                MindMate
              </span>
              <span className="mt-1 hidden text-xs text-muted sm:block">
                A private space to check in
              </span>
            </span>
          </NavLink>

          <div className="flex min-w-0 items-center gap-2">
            <nav
              aria-label="Main navigation"
              className="hidden gap-1 rounded-2xl bg-white/70 p-1 shadow-sm md:flex"
            >
              {navigation.map(({ to, label, icon: Icon }) => (
                <NavLink
                  className={({ isActive }) =>
                    `flex shrink-0 items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-pine text-white shadow-sm'
                        : 'text-muted hover:bg-mist hover:text-ink'
                    }`
                  }
                  key={to}
                  aria-label={label}
                  to={to}
                >
                  <Icon aria-hidden="true" size={17} />
                  <span className="hidden lg:inline">{label}</span>
                </NavLink>
              ))}
            </nav>
            <GetHelp />
            <span className="hidden max-w-40 truncate text-xs text-muted 2xl:block">
              {user?.email}
            </span>
            <button
              aria-label={user?.email ? `Sign out ${user.email}` : 'Sign out'}
              className="icon-button hidden md:flex"
              disabled={loggingOut}
              onClick={() => void handleLogout()}
              title="Sign out"
              type="button"
            >
              <LogOut aria-hidden="true" size={17} />
            </button>
          </div>
        </div>
      </header>

      <main
        className="mx-auto w-full max-w-6xl px-4 py-7 pb-28 sm:px-6 md:pb-10 lg:px-8 lg:py-12"
        id="main-content"
      >
        <OnboardingGate key={user?.uid}>
          <Outlet />
        </OnboardingGate>
      </main>

      <footer className="mx-auto max-w-6xl px-4 pb-28 text-center text-xs leading-5 text-muted sm:px-6 md:pb-8 lg:px-8">
        MindMate provides experimental text-derived emotional signals, not medical advice or
        diagnosis.
      </footer>

      <nav aria-label="Mobile navigation" className="mobile-nav md:hidden">
        {navigation.map(({ to, label, icon: Icon }) => (
          <NavLink
            className={({ isActive }) =>
              `mobile-nav-link ${isActive ? 'mobile-nav-link-active' : ''}`
            }
            key={to}
            to={to}
          >
            <Icon aria-hidden="true" size={19} />
            <span>{label === 'AI Assistant' ? 'Assistant' : label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
