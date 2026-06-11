import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/contexts/AuthContext'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import Layout from '@/components/Layout'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import CompaniesPage from '@/pages/CompaniesPage'
import ContactsPage from '@/pages/ContactsPage'
import LeadsPage from '@/pages/LeadsPage'
import EmailsPage from '@/pages/EmailsPage'
import MeetingsPage from '@/pages/MeetingsPage'
import AnalyticsPage from '@/pages/AnalyticsPage'
import NotificationsPage from '@/pages/NotificationsPage'
import SettingsPage from '@/pages/SettingsPage'
import ProfilePage from '@/pages/ProfilePage'
import CallsPage from '@/pages/CallsPage'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30000 } },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="companies" element={<CompaniesPage />} />
              <Route path="contacts" element={<ContactsPage />} />
              <Route path="leads" element={<LeadsPage />} />
              <Route path="emails" element={<EmailsPage />} />
              <Route path="meetings" element={<MeetingsPage />} />
              <Route path="calls" element={<CallsPage />} />
              <Route path="analytics" element={<AnalyticsPage />} />
              <Route path="notifications" element={<NotificationsPage />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route path="profile" element={<ProfilePage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}
