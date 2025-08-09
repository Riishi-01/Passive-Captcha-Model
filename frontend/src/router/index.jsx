import { createBrowserRouter, Navigate } from 'react-router-dom'
import ProtectedRoute from '../components/ProtectedRoute'
import AuthLayout from '../layouts/AuthLayout'
import DashboardLayout from '../layouts/DashboardLayout'
import LoginView from '../views/LoginView'
import DashboardView from '../views/DashboardView'
import WebsitesView from '../views/WebsitesView'
import WebsiteDetailView from '../views/WebsiteDetailView'
import AnalyticsView from '../views/AnalyticsView'
import MLMonitoringView from '../views/MLMonitoringView'
import AlertsView from '../views/AlertsView'
import LogsView from '../views/LogsView'
import SettingsView from '../views/SettingsView'
import ProfileView from '../views/ProfileView'
import ErrorView from '../views/ErrorView'

export const router = createBrowserRouter([
  {
    path: '/login',
    element: (
      <AuthLayout>
        <LoginView />
      </AuthLayout>
    ),
  },
  {
    path: '/dashboard',
    element: (
      <ProtectedRoute>
        <DashboardLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <DashboardView />,
      },
      {
        path: 'websites',
        element: <WebsitesView />,
      },
      {
        path: 'websites/:id',
        element: <WebsiteDetailView />,
      },
      {
        path: 'analytics',
        element: <AnalyticsView />,
      },
      {
        path: 'ml',
        element: <MLMonitoringView />,
      },
      {
        path: 'alerts',
        element: <AlertsView />,
      },
      {
        path: 'logs',
        element: <LogsView />,
      },
      {
        path: 'settings',
        element: <SettingsView />,
      },
      {
        path: 'profile',
        element: <ProfileView />,
      },
    ],
  },
  {
    path: '/',
    element: <Navigate to="/dashboard" replace />,
  },
  {
    path: '/error',
    element: <ErrorView />,
  },
  {
    path: '*',
    element: <ErrorView />,
  },
])
