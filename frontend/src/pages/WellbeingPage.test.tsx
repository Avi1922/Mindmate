import {render,screen} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {describe,expect,it,vi} from 'vitest'
import WellbeingPage from './WellbeingPage'
describe('Mood toolkit',()=>{
 it('starts audio only on request and stops it when leaving',async()=>{
  const close=vi.fn().mockResolvedValue(undefined);const resume=vi.fn().mockResolvedValue(undefined);const start=vi.fn()
  vi.stubGlobal('AudioContext',class {destination={};close=close;resume=resume;createGain(){return {gain:{value:0},connect:vi.fn()}}createOscillator(){return {frequency:{value:0},detune:{value:0},connect:vi.fn(),start}}})
  const user=userEvent.setup();const view=render(<WellbeingPage/>)
  expect(start).not.toHaveBeenCalled()
  await user.click(screen.getByRole('button',{name:'Play gentle tones'}))
  expect(start).toHaveBeenCalledTimes(4)
  expect(screen.getByRole('button',{name:'Stop gentle tones'})).toHaveAttribute('aria-pressed','true')
  view.unmount();expect(close).toHaveBeenCalledOnce();vi.unstubAllGlobals()
 })
 it('allows a breathing pause to be started and stopped',async()=>{
  const user=userEvent.setup();render(<WellbeingPage/>)
  await user.click(screen.getByRole('button',{name:'Start breathing pause'}))
  expect(screen.getByText('Breathe in gently')).toBeVisible()
  await user.click(screen.getByRole('button',{name:'Finish breathing pause'}))
  expect(screen.getByText('A moment to slow down')).toBeVisible()
 })
})
