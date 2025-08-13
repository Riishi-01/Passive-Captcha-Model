import { useState, useEffect } from 'react'
import { useAppStore } from '../stores/app'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { Brain, RefreshCw, AlertTriangle, CheckCircle, Activity, Database, Cpu, TrendingUp, Users, Shield } from 'lucide-react'
import apiService from '../services/api'

export default function MLMonitoringView() {
  const [loading, setLoading] = useState(false)
  const [mlHealth, setMlHealth] = useState(null)
  const [mlMetrics, setMlMetrics] = useState(null)
  const [recentActivity, setRecentActivity] = useState([])
  const [stats, setStats] = useState(null)
  const { addNotification } = useAppStore()

  useEffect(() => {
    loadMLData()
    // Refresh data every 30 seconds
    const interval = setInterval(loadMLData, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadMLData = async () => {
    setLoading(true)
    try {
      // Load ML health
      try {
        const healthResponse = await apiService.getMLHealth()
        setMlHealth(healthResponse)
      } catch (error) {
        console.warn('ML Health endpoint issues:', error)
        setMlHealth({
          status: 'degraded',
          message: 'Health check unavailable',
          model_loaded: false
        })
      }

      // Load analytics stats
      const statsResponse = await apiService.getStats()
      setStats(statsResponse)

      // Load recent detection activity
      const activityResponse = await apiService.getChartData('detection', '24h')
      if (activityResponse.success && activityResponse.data) {
        setRecentActivity(activityResponse.data.slice(-20)) // Last 20 activities
      }

    } catch (error) {
      console.error('Failed to load ML data:', error)
      addNotification({
        type: 'error',
        message: 'Failed to load ML monitoring data'
      })
    } finally {
      setLoading(false)
    }
  }

  const refreshMetrics = async () => {
    await loadMLData()
    addNotification({
      type: 'success',
      message: 'ML metrics refreshed'
    })
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-green-600 dark:text-green-400'
      case 'degraded': return 'text-yellow-600 dark:text-yellow-400'
      case 'unhealthy': return 'text-red-600 dark:text-red-400'
      default: return 'text-gray-600 dark:text-gray-400'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'degraded': return <AlertTriangle className="h-5 w-5 text-yellow-500" />
      case 'unhealthy': return <AlertTriangle className="h-5 w-5 text-red-500" />
      default: return <Activity className="h-5 w-5 text-gray-500" />
    }
  }

  const formatPercentage = (value) => {
    return value ? `${(value * 100).toFixed(1)}%` : 'N/A'
  }

  const humanRate = stats?.human_rate || 0
  const botRate = 1 - humanRate
  const totalVerifications = stats?.total_verifications || 0
  const avgConfidence = stats?.avg_confidence || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">ML Model Monitoring</h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Real-time monitoring of your Passive CAPTCHA ML model performance
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={refreshMetrics}
            disabled={loading}
            className="btn btn-secondary flex items-center"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Model Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Model Health */}
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Model Status</p>
              <div className="flex items-center mt-2">
                {getStatusIcon(mlHealth?.status)}
                <span className={`ml-2 text-sm font-medium ${getStatusColor(mlHealth?.status)}`}>
                  {mlHealth?.status || 'Unknown'}
                </span>
              </div>
            </div>
            <Brain className="h-8 w-8 text-blue-500" />
          </div>
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            {mlHealth?.message || 'Model health check'}
          </p>
        </div>

        {/* Total Verifications */}
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Verifications</p>
              <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">
                {totalVerifications.toLocaleString()}
              </p>
            </div>
            <Shield className="h-8 w-8 text-green-500" />
          </div>
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            All-time verification requests
          </p>
        </div>

        {/* Human Detection Rate */}
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Human Rate</p>
              <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">
                {formatPercentage(humanRate)}
              </p>
            </div>
            <Users className="h-8 w-8 text-blue-500" />
          </div>
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            Legitimate human users
          </p>
        </div>

        {/* Average Confidence */}
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Avg Confidence</p>
              <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">
                {formatPercentage(avgConfidence)}
              </p>
            </div>
            <TrendingUp className="h-8 w-8 text-purple-500" />
          </div>
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            Model prediction confidence
          </p>
        </div>
      </div>

      {/* Model Information */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Model Details */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Model Information
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Algorithm</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                Voting Ensemble (RF + GB)
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Features</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                11 behavioral features
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Classes</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                Human, Bot
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Model Loaded</span>
              <span className={`text-sm font-medium ${mlHealth?.model_loaded ? 'text-green-600' : 'text-red-600'}`}>
                {mlHealth?.model_loaded ? 'Yes' : 'No'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Last Updated</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {mlHealth?.timestamp ? new Date(mlHealth.timestamp).toLocaleDateString() : 'Unknown'}
              </span>
            </div>
          </div>
        </div>

        {/* Detection Distribution */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Detection Distribution
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">Human Users</span>
              </div>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {formatPercentage(humanRate)}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 dark:bg-gray-700">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all duration-300" 
                style={{width: `${humanRate * 100}%`}}
              ></div>
            </div>

            <div className="flex items-center justify-between mt-4">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-red-500 rounded-full mr-3"></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">Bot Detected</span>
              </div>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {formatPercentage(botRate)}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 dark:bg-gray-700">
              <div 
                className="bg-red-500 h-2 rounded-full transition-all duration-300" 
                style={{width: `${botRate * 100}%`}}
              ></div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity Chart */}
      {recentActivity.length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Recent Detection Activity (Last 24 Hours)
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={recentActivity}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis 
                  dataKey="time" 
                  className="text-xs"
                  stroke="currentColor"
                />
                <YAxis 
                  className="text-xs"
                  stroke="currentColor"
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: 'var(--bg-color)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px'
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="confidence" 
                  stroke="#3B82F6" 
                  strokeWidth={2}
                  dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
                  name="Confidence"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* System Components Status */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          System Components
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="flex items-center">
              <Database className="h-5 w-5 text-blue-500 mr-2" />
              <span className="text-sm text-gray-900 dark:text-white">Database</span>
            </div>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </div>
          
          <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="flex items-center">
              <Cpu className="h-5 w-5 text-purple-500 mr-2" />
              <span className="text-sm text-gray-900 dark:text-white">ML Model</span>
            </div>
            {mlHealth?.model_loaded ? 
              <CheckCircle className="h-4 w-4 text-green-500" /> :
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
            }
          </div>
          
          <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="flex items-center">
              <Activity className="h-5 w-5 text-green-500 mr-2" />
              <span className="text-sm text-gray-900 dark:text-white">API Server</span>
            </div>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </div>
        </div>
      </div>
    </div>
  )
}
