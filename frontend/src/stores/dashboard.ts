import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiService, type DashboardStats, type ChartDataPoint, type SystemHealth, type Alert, type TimelineLog } from '@/services/api'

// Re-export types from API service for backward compatibility
export type VerificationStats = DashboardStats

// Re-export types from API service for backward compatibility
export type { ChartDataPoint, SystemHealth, Alert, TimelineLog } from '@/services/api'

export interface DetectionData {
  human: number
  bot: number
  humanPercentage: number
  botPercentage: number
}

export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const stats = ref<VerificationStats>({
    totalVerifications: 0,
    humanRate: 0,
    avgConfidence: 0,
    avgResponseTime: 0,
    verificationChange: 0,
    humanRateChange: 0,
    confidenceChange: 0,
    responseTimeChange: 0
  })

  const chartData = ref<ChartDataPoint[]>([])
  const detectionData = ref<DetectionData>({
    human: 0,
    bot: 0,
    humanPercentage: 0,
    botPercentage: 0
  })

  const recentAlerts = ref<Alert[]>([])
  const systemHealth = ref<SystemHealth>({
    database: {
      status: 'healthy',
      totalVerifications: 0,
      last24hVerifications: 0,
      lastVerification: null
    },
    model: {
      status: 'healthy',
      loaded: false,
      info: {}
    },
    api: {
      status: 'healthy',
      version: '1.0',
      uptime: 'healthy'
    }
  })

  const timelineLogs = ref<TimelineLog[]>([])
  const isLoading = ref(false)
  const hasMoreLogs = ref(true)
  const currentLogOffset = ref(0)

  // API helper methods using the centralized API service
  const handleApiError = (error: any, operation: string) => {
    console.error(`Error ${operation}:`, error)
    throw error
  }

  // Actions
  const fetchStats = async (timeRange: string = '24h') => {
    try {
      const response = await apiService.getDashboardStats(timeRange)
      if (response.success && response.data) {
        stats.value = response.data
      }
    } catch (error) {
      handleApiError(error, 'fetching dashboard stats')
    }
  }

  const fetchChartData = async (timeRange: string = '24h') => {
    try {
      const response = await apiService.getChartData(timeRange)
      if (response.success && response.data) {
        chartData.value = response.data
      }
    } catch (error) {
      handleApiError(error, 'fetching chart data')
    }
  }

  const fetchDetectionData = async (timeRange: string = '24h') => {
    try {
      const response = await apiService.getDetectionData(timeRange)
      if (response.success && response.data) {
        detectionData.value = {
          human: response.data.human,
          bot: response.data.bot,
          humanPercentage: response.data.humanPercentage,
          botPercentage: response.data.botPercentage
        }
      }
    } catch (error) {
      handleApiError(error, 'fetching detection data')
    }
  }

  const fetchSystemHealth = async () => {
    try {
      const response = await apiService.getSystemHealth()
      if (response.success && response.data) {
        systemHealth.value = response.data
      }
    } catch (error) {
      handleApiError(error, 'fetching system health')
    }
  }

  const fetchRecentAlerts = async () => {
    try {
      const response = await apiService.getRecentAlerts()
      if (response.success && response.data) {
        recentAlerts.value = response.data
      }
    } catch (error) {
      handleApiError(error, 'fetching recent alerts')
    }
  }

  const fetchTimelineLogs = async (filter: string = 'all', reset: boolean = false) => {
    try {
      if (reset) {
        currentLogOffset.value = 0
        timelineLogs.value = []
      }

      const response = await apiService.getTimelineLogs(filter, currentLogOffset.value, 20)
      if (response.success && response.data) {
        const newLogs = response.data.logs

        if (reset) {
          timelineLogs.value = newLogs
        } else {
          timelineLogs.value.push(...newLogs)
        }

        hasMoreLogs.value = response.data.hasMore
        currentLogOffset.value += newLogs.length
      }
    } catch (error) {
      handleApiError(error, 'fetching timeline logs')
    }
  }

  const loadMoreTimelineLogs = async () => {
    if (!hasMoreLogs.value) return
    await fetchTimelineLogs('all', false)
  }

  const updateRealTimeStats = (data: any) => {
    // Update stats with real-time data
    if (data.verification) {
      stats.value.totalVerifications++
      
      if (data.verification.isHuman) {
        const newHumanRate = ((stats.value.humanRate * (stats.value.totalVerifications - 1)) + 100) / stats.value.totalVerifications
        stats.value.humanRate = Math.round(newHumanRate * 100) / 100
      }
    }
  }

  const addAlert = (alert: Alert) => {
    recentAlerts.value.unshift(alert)
    // Keep only last 10 alerts
    if (recentAlerts.value.length > 10) {
      recentAlerts.value = recentAlerts.value.slice(0, 10)
    }
  }

  // Computed
  const totalVerifications = computed(() => stats.value.totalVerifications)
  const isHealthy = computed(() => 
    systemHealth.value.database.status === 'healthy' &&
    systemHealth.value.model.status === 'healthy' &&
    systemHealth.value.api.status === 'healthy'
  )

  return {
    // State
    stats,
    chartData,
    detectionData,
    recentAlerts,
    systemHealth,
    timelineLogs,
    isLoading,
    hasMoreLogs,
    
    // Actions
    fetchStats,
    fetchChartData,
    fetchDetectionData,
    fetchSystemHealth,
    fetchRecentAlerts,
    fetchTimelineLogs,
    loadMoreTimelineLogs,
    updateRealTimeStats,
    addAlert,
    
    // Computed
    totalVerifications,
    isHealthy
  }
})