import { ref } from 'vue'
import { useAppStore } from '@/stores/app'
import { useDashboardStore } from '../_stores/useDashboard'
import { useWebsiteStore } from '../websites/_stores/useWebsites'

export function useDashboardData() {
  const appStore = useAppStore()
  const dashboardStore = useDashboardStore()
  const websiteStore = useWebsiteStore()
  
  const selectedTimeRange = ref('24h')
  const activeLogFilter = ref('active')
  const isLoadingLogs = ref(false)

  // Refresh all dashboard data
  const refreshDashboard = async () => {
    appStore.setLoading(true)
    try {
      await Promise.all([
        dashboardStore.fetchStats(selectedTimeRange.value),
        dashboardStore.fetchChartData(selectedTimeRange.value),
        dashboardStore.fetchDetectionData(selectedTimeRange.value),
        websiteStore.fetchActiveWebsites(),
        dashboardStore.fetchRecentAlerts(),
        dashboardStore.fetchSystemHealth()
      ])
    } catch (error) {
      console.error('Error refreshing dashboard:', error)
      appStore.addNotification({
        type: 'error',
        title: 'Error',
        message: 'Failed to refresh dashboard data'
      })
    } finally {
      appStore.setLoading(false)
    }
  }

  // Refresh logs
  const refreshLogs = async () => {
    isLoadingLogs.value = true
    try {
      await dashboardStore.fetchTimelineLogs(activeLogFilter.value, true)
    } catch (error) {
      console.error('Error refreshing logs:', error)
      appStore.addNotification({
        type: 'error',
        title: 'Error',
        message: 'Failed to refresh logs'
      })
    } finally {
      isLoadingLogs.value = false
    }
  }

  // Load more logs
  const loadMoreLogs = async () => {
    try {
      await dashboardStore.loadMoreTimelineLogs()
    } catch (error) {
      console.error('Error loading more logs:', error)
    }
  }

  // Setup real-time updates
  const setupRealtimeUpdates = () => {
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      if (!document.hidden) {
        refreshDashboard()
      }
    }, 30000)

    // WebSocket updates (if available)
    if (typeof io !== 'undefined') {
      const socket = io()
      
      socket.on('verification_update', (data) => {
        dashboardStore.updateRealTimeStats(data)
      })
      
      socket.on('new_alert', (alert) => {
        dashboardStore.addAlert(alert)
        appStore.addNotification({
          type: 'warning',
          title: 'New Alert',
          message: alert.message
        })
      })
      
      return () => {
        clearInterval(interval)
        socket.disconnect()
      }
    }

    return () => clearInterval(interval)
  }

  // Handle time range changes
  const handleTimeRangeChange = (newRange: string) => {
    selectedTimeRange.value = newRange
    dashboardStore.fetchStats(newRange)
    dashboardStore.fetchChartData(newRange)
    dashboardStore.fetchDetectionData(newRange)
  }

  // Handle log filter changes
  const handleLogFilterChange = (newFilter: string) => {
    activeLogFilter.value = newFilter
    dashboardStore.fetchTimelineLogs(newFilter, true)
  }

  return {
    // State
    selectedTimeRange,
    activeLogFilter,
    isLoadingLogs,
    
    // Methods
    refreshDashboard,
    refreshLogs,
    loadMoreLogs,
    setupRealtimeUpdates,
    handleTimeRangeChange,
    handleLogFilterChange
  }
}