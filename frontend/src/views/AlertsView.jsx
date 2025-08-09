import { useState, useEffect } from 'react'
import { useAppStore } from '../stores/app'
import { 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Filter, 
  Search,
  Bell,
  Settings 
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

const mockAlerts = [
  {
    id: 1,
    type: 'warning',
    title: 'High Bot Activity Detected',
    message: 'Unusual bot activity detected on example.com - 50% increase in blocking rate',
    timestamp: new Date(Date.now() - 10 * 60 * 1000),
    read: false,
    severity: 'medium',
    source: 'example.com'
  },
  {
    id: 2,
    type: 'error',
    title: 'Model Accuracy Drop',
    message: 'ML model accuracy dropped below 94% threshold',
    timestamp: new Date(Date.now() - 30 * 60 * 1000),
    read: false,
    severity: 'high',
    source: 'ML Monitor'
  },
  {
    id: 3,
    type: 'success',
    title: 'System Health Check Passed',
    message: 'All systems operational - performance within normal parameters',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
    read: true,
    severity: 'low',
    source: 'System'
  },
  {
    id: 4,
    type: 'warning',
    title: 'Rate Limit Exceeded',
    message: 'API rate limit exceeded for shop.demo - temporarily blocking requests',
    timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
    read: true,
    severity: 'medium',
    source: 'shop.demo'
  },
  {
    id: 5,
    type: 'info',
    title: 'New Website Added',
    message: 'Website "newsite.com" has been added to monitoring',
    timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000),
    read: true,
    severity: 'low',
    source: 'Admin'
  }
]

export default function AlertsView() {
  const [alerts, setAlerts] = useState(mockAlerts)
  const [filter, setFilter] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [showSettings, setShowSettings] = useState(false)
  const { addNotification } = useAppStore()

  const getAlertIcon = (type) => {
    switch (type) {
      case 'error':
        return XCircle
      case 'warning':
        return AlertTriangle
      case 'success':
        return CheckCircle
      case 'info':
      default:
        return Bell
    }
  }

  const getAlertColor = (type) => {
    switch (type) {
      case 'error':
        return 'text-red-500'
      case 'warning':
        return 'text-yellow-500'
      case 'success':
        return 'text-green-500'
      case 'info':
      default:
        return 'text-blue-500'
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
      case 'low':
      default:
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
    }
  }

  const filteredAlerts = alerts.filter(alert => {
    const matchesFilter = filter === 'all' || 
      (filter === 'unread' && !alert.read) ||
      (filter === 'read' && alert.read) ||
      alert.type === filter

    const matchesSearch = searchTerm === '' ||
      alert.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      alert.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      alert.source.toLowerCase().includes(searchTerm.toLowerCase())

    return matchesFilter && matchesSearch
  })

  const markAsRead = (alertId) => {
    setAlerts(alerts.map(alert => 
      alert.id === alertId ? { ...alert, read: true } : alert
    ))
    addNotification({
      type: 'success',
      message: 'Alert marked as read'
    })
  }

  const markAllAsRead = () => {
    setAlerts(alerts.map(alert => ({ ...alert, read: true })))
    addNotification({
      type: 'success',
      message: 'All alerts marked as read'
    })
  }

  const deleteAlert = (alertId) => {
    setAlerts(alerts.filter(alert => alert.id !== alertId))
    addNotification({
      type: 'success',
      message: 'Alert deleted'
    })
  }

  const unreadCount = alerts.filter(alert => !alert.read).length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Alerts</h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Monitor system alerts and notifications
            {unreadCount > 0 && (
              <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                {unreadCount} unread
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {unreadCount > 0 && (
            <button
              onClick={markAllAsRead}
              className="btn btn-secondary"
            >
              Mark All Read
            </button>
          )}
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="btn btn-primary flex items-center"
          >
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </button>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-gray-500" />
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="input py-2 pr-8"
          >
            <option value="all">All Alerts</option>
            <option value="unread">Unread</option>
            <option value="read">Read</option>
            <option value="error">Errors</option>
            <option value="warning">Warnings</option>
            <option value="success">Success</option>
            <option value="info">Info</option>
          </select>
        </div>
        
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search alerts..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input pl-10 w-full"
          />
        </div>
      </div>

      {/* Alert Settings Panel */}
      {showSettings && (
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Alert Settings
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                Alert Types
              </h4>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input type="checkbox" defaultChecked className="rounded border-gray-300 text-primary-600 focus:ring-primary-500" />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">High bot activity</span>
                </label>
                <label className="flex items-center">
                  <input type="checkbox" defaultChecked className="rounded border-gray-300 text-primary-600 focus:ring-primary-500" />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Model performance</span>
                </label>
                <label className="flex items-center">
                  <input type="checkbox" defaultChecked className="rounded border-gray-300 text-primary-600 focus:ring-primary-500" />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">System health</span>
                </label>
                <label className="flex items-center">
                  <input type="checkbox" className="rounded border-gray-300 text-primary-600 focus:ring-primary-500" />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Rate limiting</span>
                </label>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                Thresholds
              </h4>
              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                    Bot Activity Threshold (%)
                  </label>
                  <input type="number" defaultValue="30" className="input py-1 text-sm" />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                    Model Accuracy Threshold (%)
                  </label>
                  <input type="number" defaultValue="94" className="input py-1 text-sm" />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Alerts List */}
      <div className="space-y-4">
        {filteredAlerts.length === 0 ? (
          <div className="text-center py-12">
            <Bell className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No alerts found
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              {searchTerm || filter !== 'all' 
                ? 'Try adjusting your filters or search terms'
                : 'All systems are operating normally'
              }
            </p>
          </div>
        ) : (
          filteredAlerts.map((alert) => {
            const AlertIcon = getAlertIcon(alert.type)
            
            return (
              <div
                key={alert.id}
                className={`card p-4 ${!alert.read ? 'ring-2 ring-primary-200 dark:ring-primary-800' : ''}`}
              >
                <div className="flex items-start space-x-4">
                  <div className={`flex-shrink-0 ${getAlertColor(alert.type)}`}>
                    <AlertIcon className="h-5 w-5" />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                          {alert.title}
                          {!alert.read && (
                            <span className="ml-2 inline-block w-2 h-2 bg-primary-600 rounded-full"></span>
                          )}
                        </h3>
                        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                          {alert.message}
                        </p>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                          {alert.severity}
                        </span>
                        {!alert.read && (
                          <button
                            onClick={() => markAsRead(alert.id)}
                            className="text-xs text-primary-600 hover:text-primary-500"
                          >
                            Mark Read
                          </button>
                        )}
                        <button
                          onClick={() => deleteAlert(alert.id)}
                          className="text-xs text-red-600 hover:text-red-500"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                    
                    <div className="mt-2 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center">
                          <Clock className="h-3 w-3 mr-1" />
                          {formatDistanceToNow(alert.timestamp, { addSuffix: true })}
                        </div>
                        <span>Source: {alert.source}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )
          })
        )}
      </div>

      {/* Load More */}
      {filteredAlerts.length > 0 && (
        <div className="text-center">
          <button className="btn btn-secondary">
            Load More Alerts
          </button>
        </div>
      )}
    </div>
  )
}
