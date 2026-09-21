import { Navigate, Outlet } from 'react-router-dom'

import { useAuth } from '../contexts/useAuth'
import AuthLoadingScreen from './AuthLoadingScreen'

export default function PublicOnlyRoute() {
  const { user, loading } = useAuth()

  if (loading) {
    return <AuthLoadingScreen />
  }

  return user ? <Navigate replace to="/dashboard" /> : <Outlet />
}
