import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import AppLayout from './components/AppLayout'
import ProtectedRoute from './components/ProtectedRoute'
import PublicOnlyRoute from './components/PublicOnlyRoute'
import JournalPage from './pages/JournalPage'
import LoginPage from './pages/LoginPage'
import NotFoundPage from './pages/NotFoundPage'
import RegisterPage from './pages/RegisterPage'

const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const AssistantPage = lazy(() => import('./pages/AssistantPage'))

function DashboardRoute() {
  return (
    <Suspense fallback={<div className="card min-h-72 animate-pulse" aria-label="Loading dashboard" />}>
      <DashboardPage />
    </Suspense>
  )
}

function AssistantRoute() {
  return (
    <Suspense fallback={<div className="card min-h-72 animate-pulse" aria-label="Loading voice assistant" />}>
      <AssistantPage />
    </Suspense>
  )
}

export default function App() {
  return (
    <Routes>
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate replace to="/dashboard" />} />
          <Route path="dashboard" element={<DashboardRoute />} />
          <Route path="assistant" element={<AssistantRoute />} />
          <Route path="journal" element={<JournalPage />} />
        </Route>
      </Route>
      <Route element={<PublicOnlyRoute />}>
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
