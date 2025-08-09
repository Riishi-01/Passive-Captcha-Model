import { useEffect } from 'react'
import { useDashboardStore } from '../stores/dashboard'
import { useAppStore } from '../stores/app'
import KPICard from '../components/KPICard'
import SystemStatusIndicator from '../components/SystemStatusIndicator'
import LiveActivityFeed from '../components/LiveActivityFeed'
import ModelAccuracyChart from '../components/ModelAccuracyChart'
import { Shield, Eye, Brain, Globe, AlertTriangle, Clock } from 'lucide-react'

export default function DashboardView() {
  const { stats, systemHealth, loading, error, fetchStats, fetchSystemHealth } = useDashboardStore()
  const { addNotification } = useAppStore()

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        await Promise.all([
          fetchStats(),
          fetchSystemHealth()
        ])
      } catch (error) {
        addNotification({
          type: 'error',
          message: 'Failed to load dashboard data'
        })
      }
    }

    loadDashboard()
  }, [fetchStats, fetchSystemHealth, addNotification])

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error && !stats) {
    return (
      <div className="text-center py-8">
        <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <p className="text-gray-600 dark:text-gray-400">Failed to load dashboard</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Overview of your Passive CAPTCHA system
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <SystemStatusIndicator 
            status={systemHealth?.status || 'healthy'} 
            message={systemHealth?.message || 'System Operational'}
          />
          <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
            <Clock className="h-4 w-4 mr-1" />
            Last updated: {new Date().toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Total Verifications"
          value={stats?.total_verifications || '12,847'}
          change={stats?.verifications_change || 8.2}
          icon={Shield}
          trend="up"
        />
        <KPICard
          title="Detection Rate"
          value={stats?.detection_rate || '94.8%'}
          change={stats?.detection_change || 2.1}
          icon={Eye}
          trend="up"
        />
        <KPICard
          title="Model Accuracy"
          value={stats?.model_accuracy || '95.2%'}
          change={stats?.accuracy_change || -0.3}
          icon={Brain}
          trend="down"
        />
        <KPICard
          title="Protected Sites"
          value={stats?.protected_sites || '18'}
          change={stats?.sites_change || 12.5}
          icon={Globe}
          trend="up"
        />
      </div>

      {/* Charts and Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ModelAccuracyChart />
        <LiveActivityFeed />
      </div>

      {/* Additional Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Today's Summary
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Blocked Bots</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {stats?.blocked_bots || '247'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">False Positives</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {stats?.false_positives || '12'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Avg Response Time</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {stats?.avg_response_time || '45ms'}
              </span>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Top Threats
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Automated Scripts</span>
              <span className="text-sm font-medium text-red-600">68%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Headless Browsers</span>
              <span className="text-sm font-medium text-red-600">22%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Suspicious Patterns</span>
              <span className="text-sm font-medium text-red-600">10%</span>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            System Resources
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">CPU Usage</span>
              <span className="text-sm font-medium text-green-600">
                {systemHealth?.cpu_usage || '24%'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Memory Usage</span>
              <span className="text-sm font-medium text-green-600">
                {systemHealth?.memory_usage || '68%'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Storage</span>
              <span className="text-sm font-medium text-green-600">
                {systemHealth?.storage_usage || '45%'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
