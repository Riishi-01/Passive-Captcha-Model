import { NavLink } from 'react-router-dom'
import { useAppStore } from '../stores/app'
import { 
  LayoutDashboard, 
  Globe, 
  BarChart3, 
  Brain, 
  AlertTriangle, 
  FileText, 
  Settings, 
  User 
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Websites', href: '/dashboard/websites', icon: Globe },
  { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
  { name: 'ML Monitoring', href: '/dashboard/ml', icon: Brain },
  { name: 'Alerts', href: '/dashboard/alerts', icon: AlertTriangle },
  { name: 'Logs', href: '/dashboard/logs', icon: FileText },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
  { name: 'Profile', href: '/dashboard/profile', icon: User },
]

export default function AppSidebar() {
  const { sidebarCollapsed } = useAppStore()

  return (
    <div className={`fixed inset-y-0 left-0 z-50 flex flex-col bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-300 ${
      sidebarCollapsed ? 'w-16' : 'w-64'
    }`}>
      <div className="flex flex-col flex-1 overflow-y-auto">
        <div className="flex items-center justify-center h-16 px-4 bg-primary-600">
          <h1 className={`font-bold text-white transition-all duration-300 ${
            sidebarCollapsed ? 'text-lg' : 'text-xl'
          }`}>
            {sidebarCollapsed ? 'PC' : 'Passive CAPTCHA'}
          </h1>
        </div>

        <nav className="flex-1 px-2 py-4 space-y-1">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                `group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors ${
                  isActive
                    ? 'bg-primary-100 text-primary-900 dark:bg-primary-900 dark:text-primary-100'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white'
                }`
              }
            >
              <item.icon className={`flex-shrink-0 h-5 w-5 ${sidebarCollapsed ? 'mx-auto' : 'mr-3'}`} />
              {!sidebarCollapsed && item.name}
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  )
}
