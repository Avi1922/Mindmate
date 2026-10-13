import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import GetHelp from './GetHelp'
describe('Get help', () => {
  beforeEach(() => {
    Object.defineProperty(HTMLDialogElement.prototype, 'showModal', {
      configurable: true,
      value: vi.fn(function (this: HTMLDialogElement) {
        this.setAttribute('open', '')
      }),
    })
    Object.defineProperty(HTMLDialogElement.prototype, 'close', {
      configurable: true,
      value: vi.fn(function (this: HTMLDialogElement) {
        this.removeAttribute('open')
      }),
    })
  })
  it('opens verified contacts without placing a call and can be closed', async () => {
    const user = userEvent.setup()
    render(<GetHelp />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Get help' }))
    expect(screen.getByRole('dialog', { name: 'You can reach out' })).toBeVisible()
    expect(screen.getByRole('link', { name: '14416' })).toHaveAttribute(
      'href',
      'tel:+9114416?oai_link_source=model_response_hotline',
    )
    expect(screen.getByRole('link', { name: '112' })).toHaveAttribute('href', 'tel:112')
    await user.click(screen.getByRole('button', { name: 'Close help' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
