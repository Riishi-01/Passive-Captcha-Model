import { useState, useEffect } from 'react'
import { Activity, Calendar, Clock, Server, Database, Cpu } from 'lucide-react'

export default function RealTimeSystemStatus({ systemHealth }) {
  const [currentTime, setCurrentTime] = useState(new Date())
  const [uptime, setUptime] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
      setUptime(prev => prev + 1)
    }, 1000)

    return () => clearInterval(timer)
  }, [])

  // Format IST time
  const formatISTDateTime = (date) => {
    return date.toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    })
  }

  // Format uptime
  const formatUptime = (seconds) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hours}h ${minutes}m ${secs}s`
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-300'
      case 'degraded': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900 dark:text-yellow-300'
      case 'unhealthy': return 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-300'
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-800 dark:text-gray-300'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return <Activity className="h-4 w-4" />
      case 'degraded': return <Clock className="h-4 w-4" />
      case 'unhealthy': return <Server className="h-4 w-4" />
      default: return <Activity className="h-4 w-4" />
    }
  }

  // Safely handle systemHealth prop with proper defaults
  const safeSystemHealth = systemHealth || {}
  const overallStatus = safeSystemHealth.status || 'unknown'
  const components = safeSystemHealth.components || {}

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          System Status
        </h3>
        <div className={`px-3 py-1 rounded-full text-sm font-medium flex items-center space-x-2 ${getStatusColor(overallStatus)}`}>
          {getStatusIcon(overallStatus)}
          <span className="capitalize">{overallStatus}</span>
        </div>
      </div>

      {/* Current Date & Time */}
      <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
        <div className="flex items-center space-x-2 mb-2">
          <Calendar className="h-5 w-5 text-blue-600 dark:text-blue-400" />
          <span className="font-medium text-gray-900 dark:text-gray-100">Current Time (IST)</span>
        </div>
        <div className="font-mono text-lg text-gray-800 dark:text-gray-200">
          {formatISTDateTime(currentTime)}
        </div>
      </div>

      {/* System Components */}
      <div className="space-y-3">
        <div className="flex items-center justify-between py-2 px-3 bg-gray-50 dark:bg-gray-700 rounded">
          <div className="flex items-center space-x-2">
            <Database className="h-4 w-4 text-gray-600 dark:text-gray-400" />
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Database</span>
          </div>
          <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(components.database || 'unknown')}`}>
            {components.database || 'unknown'}
          </span>
        </div>

        <div className="flex items-center justify-between py-2 px-3 bg-gray-50 dark:bg-gray-700 rounded">
          <div className="flex items-center space-x-2">
            <Cpu className="h-4 w-4 text-gray-600 dark:text-gray-400" />
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">ML Model</span>
          </div>
          <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(components.ml_model || 'unknown')}`}>
            {components.ml_model || 'unknown'}
          </span>
        </div>

        <div className="flex items-center justify-between py-2 px-3 bg-gray-50 dark:bg-gray-700 rounded">
          <div className="flex items-center space-x-2">
            <Server className="h-4 w-4 text-gray-600 dark:text-gray-400" />
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">API Server</span>
          </div>
          <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(components.api || 'healthy')}`}>
            {components.api || 'healthy'}
          </span>
        </div>

        {components.redis && (
          <div className="flex items-center justify-between py-2 px-3 bg-gray-50 dark:bg-gray-700 rounded">
            <div className="flex items-center space-x-2">
              <Activity className="h-4 w-4 text-gray-600 dark:text-gray-400" />
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Redis Cache</span>
            </div>
            <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(components.redis || 'unknown')}`}>
              {components.redis || 'unknown'}
            </span>
          </div>
        )}
      </div>

      {/* System Uptime */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">Session Uptime:</span>
          <span className="font-mono text-gray-900 dark:text-gray-100">
            {formatUptime(uptime)}
          </span>
        </div>
      </div>

      {/* Last Updated */}
      <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
        Last updated: {currentTime.toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata' })} IST
      </div>
    </div>
  )
}
