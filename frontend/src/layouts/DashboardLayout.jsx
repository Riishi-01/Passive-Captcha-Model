import { Outlet } from 'react-router-dom'
import { useAppStore } from '../stores/app'
import AppHeader from '../components/AppHeader'
import AppSidebar from '../components/AppSidebar'

export default function DashboardLayout() {
  const { sidebarCollapsed } = useAppStore()

  return (
    <div className="h-screen flex bg-gray-50 dark:bg-gray-900">
      <AppSidebar />
      
      <div className={`flex-1 flex flex-col overflow-hidden transition-all duration-300 ${
        sidebarCollapsed ? 'ml-16' : 'ml-64'
      }`}>
        <AppHeader />
        
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50 dark:bg-gray-900">
          <div className="container mx-auto px-6 py-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
