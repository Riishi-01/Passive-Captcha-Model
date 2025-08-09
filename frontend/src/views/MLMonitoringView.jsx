import { useState, useEffect } from 'react'
import { useAppStore } from '../stores/app'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { Brain, RefreshCw, Play, AlertTriangle, CheckCircle, Zap } from 'lucide-react'

const mockAccuracyData = [
  { time: '00:00', accuracy: 94.2, precision: 93.8, recall: 94.6 },
  { time: '04:00', accuracy: 95.1, precision: 94.7, recall: 95.5 },
  { time: '08:00', accuracy: 93.8, precision: 93.2, recall: 94.4 },
  { time: '12:00', accuracy: 96.3, precision: 96.0, recall: 96.6 },
  { time: '16:00', accuracy: 94.9, precision: 94.5, recall: 95.3 },
  { time: '20:00', accuracy: 95.7, precision: 95.3, recall: 96.1 },
  { time: '24:00', accuracy: 95.2, precision: 94.9, recall: 95.5 },
]

const mockPredictionData = [
  { category: 'Human', confidence: 96.8 },
  { category: 'Bot', confidence: 89.2 },
  { category: 'Suspicious', confidence: 92.5 },
  { category: 'Automated', confidence: 94.1 },
]

export default function MLMonitoringView() {
  const [loading, setLoading] = useState(false)
  const [retraining, setRetraining] = useState(false)
  const { addNotification } = useAppStore()

  const [modelStatus] = useState({
    status: 'healthy',
    lastTrained: '2024-01-15T10:30:00Z',
    version: 'v2.3.1',
    accuracy: 95.2,
    precision: 94.9,
    recall: 95.5,
    f1Score: 95.2
  })

  const refreshMetrics = async () => {
    setLoading(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 1000))
      addNotification({
        type: 'success',
        message: 'ML metrics refreshed'
      })
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to refresh metrics'
      })
    } finally {
      setLoading(false)
    }
  }

  const triggerRetrain = async () => {
    setRetraining(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 3000))
      addNotification({
        type: 'success',
        message: 'Model retraining started successfully'
      })
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to start retraining'
      })
    } finally {
      setRetraining(false)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600'
      case 'warning':
        return 'text-yellow-600'
      case 'error':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return CheckCircle
      case 'warning':
      case 'error':
        return AlertTriangle
      default:
        return CheckCircle
    }
  }

  const StatusIcon = getStatusIcon(modelStatus.status)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">ML Monitoring</h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Monitor and manage your machine learning model performance
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
          <button
            onClick={triggerRetrain}
            disabled={retraining}
            className="btn btn-primary flex items-center"
          >
            <Play className="h-4 w-4 mr-2" />
            {retraining ? 'Retraining...' : 'Retrain Model'}
          </button>
        </div>
      </div>

      {/* Model Status */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <StatusIcon className={`w-8 h-8 ${getStatusColor(modelStatus.status)}`} />
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Model Status</h3>
              <p className={`text-lg font-bold ${getStatusColor(modelStatus.status)}`}>
                {modelStatus.status.charAt(0).toUpperCase() + modelStatus.status.slice(1)}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Version {modelStatus.version}
              </p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                <Brain className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Accuracy</h3>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {modelStatus.accuracy}%
              </p>
              <p className="text-xs text-green-600">Target: {'>'}94%</p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                <Zap className="w-4 h-4 text-green-600 dark:text-green-400" />
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Precision</h3>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {modelStatus.precision}%
              </p>
              <p className="text-xs text-green-600">Target: {'>'}93%</p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center">
                <Brain className="w-4 h-4 text-purple-600 dark:text-purple-400" />
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Recall</h3>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {modelStatus.recall}%
              </p>
              <p className="text-xs text-green-600">Target: {'>'}94%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance Trends */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Performance Trends (24h)
          </h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={mockAccuracyData}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis 
                  dataKey="time" 
                  tick={{ fill: 'currentColor', fontSize: 12 }}
                  className="text-gray-600 dark:text-gray-400"
                />
                <YAxis 
                  domain={[90, 100]}
                  tick={{ fill: 'currentColor', fontSize: 12 }}
                  className="text-gray-600 dark:text-gray-400"
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '0.5rem',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="accuracy" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  name="Accuracy"
                />
                <Line 
                  type="monotone" 
                  dataKey="precision" 
                  stroke="#10b981" 
                  strokeWidth={2}
                  name="Precision"
                />
                <Line 
                  type="monotone" 
                  dataKey="recall" 
                  stroke="#8b5cf6" 
                  strokeWidth={2}
                  name="Recall"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Prediction Confidence */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Prediction Confidence
          </h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={mockPredictionData}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis 
                  dataKey="category" 
                  tick={{ fill: 'currentColor', fontSize: 12 }}
                  className="text-gray-600 dark:text-gray-400"
                />
                <YAxis 
                  domain={[80, 100]}
                  tick={{ fill: 'currentColor', fontSize: 12 }}
                  className="text-gray-600 dark:text-gray-400"
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '0.5rem',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Bar 
                  dataKey="confidence" 
                  fill="#3b82f6"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Model Information */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Model Information
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Current Version</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">{modelStatus.version}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Last Trained</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {new Date(modelStatus.lastTrained).toLocaleDateString()}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Training Data Size</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">1.2M samples</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Model Type</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">Random Forest</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Feature Count</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">47 features</span>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Training Progress
          </h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600 dark:text-gray-400">Data Collection</span>
                <span className="text-green-600">Complete</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="bg-green-600 h-2 rounded-full w-full"></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600 dark:text-gray-400">Feature Engineering</span>
                <span className="text-green-600">Complete</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="bg-green-600 h-2 rounded-full w-full"></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600 dark:text-gray-400">Model Training</span>
                <span className="text-green-600">Complete</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="bg-green-600 h-2 rounded-full w-full"></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600 dark:text-gray-400">Validation</span>
                <span className="text-green-600">Complete</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="bg-green-600 h-2 rounded-full w-full"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Alert Section */}
      {modelStatus.accuracy < 94 && (
        <div className="card p-6 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mr-3" />
            <div>
              <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                Model Performance Alert
              </h3>
              <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                Model accuracy has dropped below the target threshold. Consider retraining the model.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
