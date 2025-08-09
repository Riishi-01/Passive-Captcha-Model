import { useEffect } from 'react'
import { RouterProvider } from 'react-router-dom'
import { router } from './router'
import { useAppStore } from './stores/app'
import ErrorBoundary from './components/ErrorBoundary'
import NotificationContainer from './components/NotificationContainer'

export default function App() {
  const { theme, setTheme } = useAppStore()

  useEffect(() => {
    // Initialize theme
    setTheme(theme)
  }, [theme, setTheme])

  return (
    <ErrorBoundary>
      <div className="App">
        <RouterProvider router={router} />
        <NotificationContainer />
      </div>
    </ErrorBoundary>
  )
}
