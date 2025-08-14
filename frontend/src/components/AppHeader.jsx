import { useEffect } from 'react'
import { useAppStore } from '../stores/app'
import { Menu, Sun, Moon, Bell, LogOut } from 'lucide-react'
import { useAuthStore } from '../stores/auth'
import { useWebsitesStore } from '../stores/websites'
import { useDashboardStore } from '../stores/dashboard'
import RealTimeClock from './RealTimeClock'

export default function AppHeader() {
  const { theme, toggleTheme, toggleSidebar } = useAppStore()
  const { logout } = useAuthStore()
  const { websites, fetchWebsites } = useWebsitesStore()
  const { selectedWebsiteId, setSelectedWebsite } = useDashboardStore()

  const handleLogout = () => {
    logout()
    window.location.href = '/login'
  }

  useEffect(() => {
    if (websites.length === 0) {
      fetchWebsites().catch(() => {})
    }
  }, [websites.length, fetchWebsites])

  return (
    <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div className="px-6 py-4 flex items-center justify-between">
        <div className="flex items-center">
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-700"
          >
            <Menu className="h-5 w-5" />
          </button>
        </div>

        <div className="flex items-center space-x-4">
          <div>
            <select
              value={selectedWebsiteId || ''}
              onChange={(e) => setSelectedWebsite(e.target.value || null)}
              className="input py-2"
            >
              <option value="">All websites</option>
              {websites.map(w => (
                <option key={w.id} value={w.id}>{w.name || w.url}</option>
              ))}
            </select>
          </div>
          <button
            onClick={toggleTheme}
            className="p-2 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-700"
          >
            {theme === 'light' ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
          </button>

          <button className="p-2 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-700 relative">
            <Bell className="h-5 w-5" />
            <span className="absolute top-1 right-1 h-2 w-2 bg-red-500 rounded-full"></span>
          </button>

          <div className="relative">
            <button
              onClick={handleLogout}
              className="flex items-center space-x-2 p-2 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-700"
            >
              <LogOut className="h-5 w-5" />
              <span className="text-sm font-medium">Logout</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
