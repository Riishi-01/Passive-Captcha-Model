import { useState, useEffect } from 'react'
import { useAppStore } from '../stores/app'
import { 
  FileText, 
  Download, 
  RefreshCw, 
  Search, 
  Filter,
  Calendar,
  Clock,
  User,
  Globe,
  Shield,
  AlertTriangle
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

const mockLogs = [
  {
    id: 1,
    timestamp: new Date(Date.now() - 5 * 60 * 1000),
    level: 'info',
    message: 'Verification request processed successfully',
    source: 'example.com',
    ip: '192.168.1.100',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    confidence: 96.8,
    result: 'human'
  },
  {
    id: 2,
    timestamp: new Date(Date.now() - 8 * 60 * 1000),
    level: 'warning',
    message: 'Bot detected and blocked',
    source: 'shop.demo',
    ip: '10.0.0.45',
    userAgent: 'HeadlessChrome/91.0.4472.124',
    confidence: 89.2,
    result: 'bot'
  },
  {
    id: 3,
    timestamp: new Date(Date.now() - 15 * 60 * 1000),
    level: 'info',
    message: 'New website added to monitoring',
    source: 'admin',
    ip: '192.168.1.200',
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
    confidence: null,
    result: 'admin_action'
  },
  {
    id: 4,
    timestamp: new Date(Date.now() - 22 * 60 * 1000),
    level: 'error',
    message: 'Model prediction failed - fallback applied',
    source: 'ml_service',
    ip: '127.0.0.1',
    userAgent: 'Internal Service',
    confidence: null,
    result: 'error'
  },
  {
    id: 5,
    timestamp: new Date(Date.now() - 30 * 60 * 1000),
    level: 'info',
    message: 'Verification request processed successfully',
    source: 'blog.example',
    ip: '203.0.113.45',
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)',
    confidence: 94.3,
    result: 'human'
  }
]

export default function LogsView() {
  const [logs, setLogs] = useState(mockLogs)
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [levelFilter, setLevelFilter] = useState('all')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [dateFilter, setDateFilter] = useState('24h')
  const { addNotification } = useAppStore()

  const refreshLogs = async () => {
    setLoading(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 1000))
      addNotification({
        type: 'success',
        message: 'Logs refreshed successfully'
      })
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to refresh logs'
      })
    } finally {
      setLoading(false)
    }
  }

  const exportLogs = () => {
    const csvContent = logs.map(log => 
      `${log.timestamp.toISOString()},${log.level},${log.source},"${log.message}",${log.ip}`
    ).join('\n')
    
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'logs.csv'
    a.click()
    
    addNotification({
      type: 'success',
      message: 'Logs exported successfully'
    })
  }

  const getLevelIcon = (level) => {
    switch (level) {
      case 'error':
        return AlertTriangle
      case 'warning':
        return AlertTriangle
      case 'info':
      default:
        return FileText
    }
  }

  const getLevelColor = (level) => {
    switch (level) {
      case 'error':
        return 'text-red-500 bg-red-50 dark:bg-red-900/20'
      case 'warning':
        return 'text-yellow-500 bg-yellow-50 dark:bg-yellow-900/20'
      case 'info':
      default:
        return 'text-blue-500 bg-blue-50 dark:bg-blue-900/20'
    }
  }

  const getResultColor = (result) => {
    switch (result) {
      case 'human':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'bot':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      case 'error':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      case 'admin_action':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
    }
  }

  const filteredLogs = logs.filter(log => {
    const matchesSearch = searchTerm === '' ||
      log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.source.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.ip.includes(searchTerm)

    const matchesLevel = levelFilter === 'all' || log.level === levelFilter
    const matchesSource = sourceFilter === 'all' || log.source === sourceFilter

    return matchesSearch && matchesLevel && matchesSource
  })

  const uniqueSources = [...new Set(logs.map(log => log.source))]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">System Logs</h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Monitor system activity and debug issues
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={refreshLogs}
            disabled={loading}
            className="btn btn-secondary flex items-center"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={exportLogs}
            className="btn btn-primary flex items-center"
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Search
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500" />
              <input
                type="text"
                placeholder="Search logs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input pl-10"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Level
            </label>
            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              className="input"
            >
              <option value="all">All Levels</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Source
            </label>
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              className="input"
            >
              <option value="all">All Sources</option>
              {uniqueSources.map(source => (
                <option key={source} value={source}>{source}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Time Period
            </label>
            <select
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="input"
            >
              <option value="1h">Last Hour</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
            </select>
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Level
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Source
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Message
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  IP Address
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Result
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {filteredLogs.map((log) => {
                const LevelIcon = getLevelIcon(log.level)
                
                return (
                  <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      <div className="flex items-center">
                        <Clock className="h-4 w-4 mr-2" />
                        <div>
                          <div>{log.timestamp.toLocaleTimeString()}</div>
                          <div className="text-xs">
                            {formatDistanceToNow(log.timestamp, { addSuffix: true })}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getLevelColor(log.level)}`}>
                        <LevelIcon className="h-3 w-3 mr-1" />
                        {log.level.toUpperCase()}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      <div className="flex items-center">
                        <Globe className="h-4 w-4 mr-2 text-gray-400" />
                        {log.source}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-white max-w-md">
                      <div className="truncate" title={log.message}>
                        {log.message}
                      </div>
                      {log.confidence && (
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          Confidence: {log.confidence}%
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      <div className="font-mono">{log.ip}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getResultColor(log.result)}`}>
                        {log.result.replace('_', ' ')}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {filteredLogs.length === 0 && (
          <div className="text-center py-12">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No logs found
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Try adjusting your filters or search terms
            </p>
          </div>
        )}
      </div>

      {/* Load More */}
      {filteredLogs.length > 0 && (
        <div className="text-center">
          <button className="btn btn-secondary">
            Load More Logs
          </button>
        </div>
      )}
    </div>
  )
}
