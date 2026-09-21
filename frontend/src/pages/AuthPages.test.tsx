import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import LoginPage from './LoginPage'
import RegisterPage from './RegisterPage'

const authMock = vi.hoisted(() => ({
  login: vi.fn(),
  register: vi.fn(),
}))

vi.mock('../contexts/useAuth', () => ({
  useAuth: () => ({ login: authMock.login, register: authMock.register }),
}))

describe('authentication pages', () => {
  beforeEach(() => {
    authMock.login.mockReset()
    authMock.register.mockReset()
  })

  it('signs in and returns to the originally requested route', async () => {
    authMock.login.mockResolvedValue(undefined)
    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={[{ pathname: '/login', state: { from: '/journal' } }]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/journal" element={<p>Journal destination</p>} />
        </Routes>
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText('Email'), 'person@example.com')
    await user.type(screen.getByLabelText('Password'), 'password123')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByText('Journal destination')).toBeVisible()
    expect(authMock.login).toHaveBeenCalledWith('person@example.com', 'password123')
  })

  it('shows a safe message when sign-in fails', async () => {
    authMock.login.mockRejectedValue(new Error('provider details'))
    const user = userEvent.setup()
    render(<MemoryRouter><LoginPage /></MemoryRouter>)

    await user.type(screen.getByLabelText('Email'), 'person@example.com')
    await user.type(screen.getByLabelText('Password'), 'password123')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Authentication failed. Please try again.',
    )
  })

  it('rejects mismatched registration passwords without calling Firebase', async () => {
    const user = userEvent.setup()
    render(<MemoryRouter><RegisterPage /></MemoryRouter>)

    await user.type(screen.getByLabelText('Email'), 'person@example.com')
    await user.type(screen.getByLabelText('Password', { exact: true }), 'password123')
    await user.type(screen.getByLabelText('Confirm password'), 'different123')
    await user.click(screen.getByRole('button', { name: 'Create account' }))

    expect(screen.getByRole('alert')).toHaveTextContent('Passwords do not match.')
    expect(authMock.register).not.toHaveBeenCalled()
  })
})
