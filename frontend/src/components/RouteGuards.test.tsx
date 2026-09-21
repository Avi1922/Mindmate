import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import ProtectedRoute from './ProtectedRoute'
import PublicOnlyRoute from './PublicOnlyRoute'

const authState = vi.hoisted(() => ({
  loading: false,
  user: null as object | null,
}))

vi.mock('../contexts/useAuth', () => ({
  useAuth: () => authState,
}))

function renderRoutes(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route element={<ProtectedRoute />}>
          <Route path="/journal" element={<p>Private journal</p>} />
        </Route>
        <Route element={<PublicOnlyRoute />}>
          <Route path="/login" element={<p>Public login</p>} />
        </Route>
        <Route path="/dashboard" element={<p>Private dashboard</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('route guards', () => {
  beforeEach(() => {
    authState.loading = false
    authState.user = null
  })

  it('redirects a signed-out visitor to login', async () => {
    renderRoutes('/journal')
    expect(await screen.findByText('Public login')).toBeVisible()
  })

  it('renders protected content for a signed-in user', () => {
    authState.user = { uid: 'user-1' }
    renderRoutes('/journal')
    expect(screen.getByText('Private journal')).toBeVisible()
  })

  it('redirects signed-in users away from public authentication pages', async () => {
    authState.user = { uid: 'user-1' }
    renderRoutes('/login')
    expect(await screen.findByText('Private dashboard')).toBeVisible()
  })

  it('shows a loading state while authentication initializes', () => {
    authState.loading = true
    renderRoutes('/journal')
    expect(screen.getByRole('status')).toBeVisible()
  })
})
