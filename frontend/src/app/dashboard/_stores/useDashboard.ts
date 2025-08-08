import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const stats = ref({
    totalVerifications: 0,
    humanRate: 0,
    avgConfidence: 0,
    avgResponseTime: 0,
    verificationChange: 0,
    humanRateChange: 0,
    confidenceChange: 0,
    responseTimeChange: 0
  })

  const chartData = ref([])
  const detectionData = ref({ humans: 0, bots: 0 })
  const recentAlerts = ref([])
  const systemHealth = ref({
    status: 'unknown',
    uptime: '0%',
    database: 'disconnected',
    mlModel: 'not_loaded',
    api: 'down'
  })
  
  const timelineLogs = ref([])
  const isLoading = ref(false)
  const currentLogOffset = ref(0)

  // API Base URL
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5002'

  // Auth token from localStorage
  const getAuthToken = () => localStorage.getItem('admin_token')

  // Create axios instance with auth
  const createAuthHeaders = () => ({
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`,
      'Content-Type': 'application/json'
    }
  })

  // Fetch stats
  const fetchStats = async (timeRange = '24h') => {
    try {
      const response = await axios.get(
        `${API_BASE}/admin/analytics?hours=${timeRange === '24h' ? 24 : timeRange === '7d' ? 168 : 30 * 24}`,
        createAuthHeaders()
      )

      const data = response.data
      stats.value = {
        totalVerifications: data.total_verifications || 0,
        humanRate: Math.round((data.human_percentage || 0) * 100) / 100,
        avgConfidence: Math.round((data.avg_confidence || 0) * 100) / 100,
        avgResponseTime: Math.round(data.avg_response_time || 0),
        verificationChange: data.verification_change || 0,
        humanRateChange: data.human_rate_change || 0,
        confidenceChange: data.confidence_change || 0,
        responseTimeChange: data.response_time_change || 0
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error)
      throw error
    }
  }

  // Fetch chart data
  const fetchChartData = async (timeRange = '24h') => {
    try {
      const response = await axios.get(
        `${API_BASE}/admin/analytics?hours=${timeRange === '24h' ? 24 : timeRange === '7d' ? 168 : 30 * 24}&format=chart`,
        createAuthHeaders()
      )

      chartData.value = response.data.chart_data || []
    } catch (error) {
      console.error('Failed to fetch chart data:', error)
      throw error
    }
  }

  // Fetch detection data
  const fetchDetectionData = async (timeRange = '24h') => {
    try {
      const response = await axios.get(
        `${API_BASE}/admin/analytics?hours=${timeRange === '24h' ? 24 : timeRange === '7d' ? 168 : 30 * 24}`,
        createAuthHeaders()
      )

      const data = response.data
      detectionData.value = {
        humans: Math.round((data.human_percentage || 0) * 100) / 100,
        bots: Math.round((100 - (data.human_percentage || 0)) * 100) / 100
      }
    } catch (error) {
      console.error('Failed to fetch detection data:', error)
      throw error
    }
  }

  // Fetch system health
  const fetchSystemHealth = async () => {
    try {
      const response = await axios.get(`${API_BASE}/health`)
      const data = response.data

      systemHealth.value = {
        status: data.status || 'unknown',
        uptime: '99.9%', // Placeholder
        database: data.database_status || 'disconnected',
        mlModel: data.model_loaded ? 'loaded' : 'not_loaded',
        api: 'up'
      }
    } catch (error) {
      console.error('Failed to fetch system health:', error)
      systemHealth.value.api = 'down'
    }
  }

  // Fetch recent alerts
  const fetchRecentAlerts = async () => {
    try {
      const response = await axios.get(
        `${API_BASE}/admin/alerts?limit=5`,
        createAuthHeaders()
      )
      recentAlerts.value = response.data.alerts || []
    } catch (error) {
      console.error('Failed to fetch alerts:', error)
      recentAlerts.value = []
    }
  }

  // Fetch timeline logs
  const fetchTimelineLogs = async (filter = 'all', reset = false) => {
    try {
      if (reset) {
        currentLogOffset.value = 0
      }

      const response = await axios.get(
        `${API_BASE}/admin/logs?limit=50&offset=${currentLogOffset.value}&filter=${filter}`,
        createAuthHeaders()
      )

      const newLogs = response.data.logs || []
      
      if (reset) {
        timelineLogs.value = newLogs
      } else {
        timelineLogs.value = [...timelineLogs.value, ...newLogs]
      }

      currentLogOffset.value += newLogs.length
    } catch (error) {
      console.error('Failed to fetch timeline logs:', error)
      throw error
    }
  }

  // Load more timeline logs
  const loadMoreTimelineLogs = async () => {
    await fetchTimelineLogs('all', false)
  }

  // Update real-time stats
  const updateRealTimeStats = (data: any) => {
    if (data.type === 'verification') {
      stats.value.totalVerifications += 1
      
      if (data.is_human) {
        const newHumanCount = Math.ceil(stats.value.totalVerifications * (stats.value.humanRate / 100)) + 1
        stats.value.humanRate = Math.round((newHumanCount / stats.value.totalVerifications) * 10000) / 100
      }
    }
  }

  // Add new alert
  const addAlert = (alert: any) => {
    recentAlerts.value.unshift(alert)
    if (recentAlerts.value.length > 5) {
      recentAlerts.value = recentAlerts.value.slice(0, 5)
    }
  }

  // Computed
  const isHealthy = computed(() => 
    systemHealth.value.status === 'healthy' && 
    systemHealth.value.api === 'up' && 
    systemHealth.value.mlModel === 'loaded'
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
    
    // Computed
    isHealthy,
    
    // Actions
    fetchStats,
    fetchChartData,
    fetchDetectionData,
    fetchSystemHealth,
    fetchRecentAlerts,
    fetchTimelineLogs,
    loadMoreTimelineLogs,
    updateRealTimeStats,
    addAlert
  }
})