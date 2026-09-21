import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '../contexts/useAuth'
import AuthLoadingScreen from './AuthLoadingScreen'

export default function ProtectedRoute() {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return <AuthLoadingScreen />
  }

  if (!user) {
    return <Navigate replace state={{ from: location.pathname }} to="/login" />
  }

  return <Outlet />
}
