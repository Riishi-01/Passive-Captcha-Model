import { useEffect } from 'react'
import { RouterProvider } from 'react-router-dom'
import { router } from './router'
import { useAppStore } from './stores/app'
import { useAuthStore } from './stores/auth'
import ErrorBoundary from './components/ErrorBoundary'
import NotificationContainer from './components/NotificationContainer'

export default function App() {
  const { theme, setTheme } = useAppStore()
  const { initializeAuth } = useAuthStore()

  useEffect(() => {
    // Initialize theme
    setTheme(theme)
    
    // Initialize authentication from localStorage
    initializeAuth()
  }, [theme, setTheme, initializeAuth])

  return (
    <ErrorBoundary>
      <div className="App">
        <RouterProvider router={router} />
        <NotificationContainer />
      </div>
    </ErrorBoundary>
  )
}
