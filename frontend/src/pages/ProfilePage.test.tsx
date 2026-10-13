import {render,screen} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {MemoryRouter} from 'react-router-dom'
import {describe,expect,it,vi} from 'vitest'
import ProfilePage from './ProfilePage'
const mocks=vi.hoisted(()=>({getProfile:vi.fn(),saveProfile:vi.fn(),logout:vi.fn()}))
vi.mock('../contexts/useAuth',()=>({useAuth:()=>({user:{email:'fixture@example.test'},logout:mocks.logout})}))
vi.mock('../lib/wellness',()=>({getProfile:mocks.getProfile,saveProfile:mocks.saveProfile,preferenceOptions:{goal:['Manage everyday stress'],support_style:['Gentle encouragement'],calming_activity:['Music'],check_in_time:['Evening']}}))
describe('Profile',()=>{
 it('edits optional preferences and logs out',async()=>{
  mocks.getProfile.mockResolvedValue({goal:'',support_style:'',calming_activity:'',check_in_time:'',onboarding_complete:true})
  mocks.saveProfile.mockImplementation(async p=>p);mocks.logout.mockResolvedValue(undefined)
  const user=userEvent.setup();render(<MemoryRouter><ProfilePage/></MemoryRouter>)
  await user.selectOptions(await screen.findByLabelText('What would you like MindMate to help with?'),'Manage everyday stress')
  await user.click(screen.getByRole('button',{name:'Save preferences'}))
  expect(await screen.findByText('Your preferences are saved.')).toBeVisible()
  expect(mocks.saveProfile).toHaveBeenCalledWith(expect.objectContaining({goal:'Manage everyday stress'}))
  await user.click(screen.getByRole('button',{name:'Log out'}))
  expect(mocks.logout).toHaveBeenCalled()
 })
 it('does not claim success when preference storage fails',async()=>{
  mocks.getProfile.mockResolvedValue({goal:'',support_style:'',calming_activity:'',check_in_time:'',onboarding_complete:true})
  mocks.saveProfile.mockRejectedValue(new Error('offline'))
  const user=userEvent.setup();render(<MemoryRouter><ProfilePage/></MemoryRouter>)
  await screen.findByLabelText('What helps you unwind?')
  await user.click(screen.getByRole('button',{name:'Save preferences'}))
  expect(await screen.findByRole('alert')).toHaveTextContent('could not be saved')
  expect(screen.queryByText('Your preferences are saved.')).not.toBeInTheDocument()
 })
})
