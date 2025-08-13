import { create } from 'zustand'
import apiService from '../services/api'

export const useDashboardStore = create((set, get) => ({
  stats: null,
  chartData: {},
  systemHealth: {
    status: 'unknown',
    components: {}
  },
  loading: false,
  error: null,
  lastUpdated: null,

  fetchStats: async () => {
    set({ loading: true, error: null })
    try {
      const resp = await apiService.getStats()
      const payload = resp?.success && resp?.data ? resp.data : resp || {}
      const normalized = {
        totalVerifications: payload.totalVerifications ?? 0,
        humanRate: payload.humanRate ?? 0,
        avgConfidence: payload.avgConfidence ?? 0,
        avgResponseTime: payload.avgResponseTime ?? 0,
        // mirror snake_case for existing components
        total_verifications: payload.totalVerifications ?? 0,
        human_rate: payload.humanRate ?? 0,
        avg_confidence: payload.avgConfidence ?? 0,
        avg_response_time: payload.avgResponseTime ?? 0,
        protected_sites: payload.protectedSites ?? payload.protected_sites ?? null,
        model_accuracy: payload.modelAccuracy ?? null,
      }
      set({ 
        stats: normalized, 
        loading: false,
        lastUpdated: new Date(),
        error: null 
      })
      return normalized
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch stats'
      set({ 
        loading: false, 
        error: errorMessage 
      })
      throw error
    }
  },

  fetchChartData: async (type, period = '24h') => {
    try {
      const data = await apiService.getChartData(type, period)
      set((state) => ({
        chartData: {
          ...state.chartData,
          [`${type}_${period}`]: data
        }
      }))
      return data
    } catch (error) {
      console.error(`Failed to fetch chart data for ${type}:`, error)
      throw error
    }
  },

  fetchSystemHealth: async () => {
    try {
      const health = await apiService.getSystemHealth()
      set({ systemHealth: health || { status: 'unknown', components: {} } })
      return health
    } catch (error) {
      console.error('Failed to fetch system health:', error)
      // Set default system health on error
      set({ 
        systemHealth: { 
          status: 'unhealthy', 
          components: { 
            api: 'error',
            database: 'unknown',
            ml_model: 'unknown'
          } 
        } 
      })
      throw error
    }
  },

  getChartData: (type, period = '24h') => {
    return get().chartData[`${type}_${period}`] || null
  },

  refreshDashboard: async () => {
    try {
      await Promise.all([
        get().fetchStats(),
        get().fetchSystemHealth(),
      ])
    } catch (error) {
      console.error('Failed to refresh dashboard:', error)
    }
  },

  clearError: () => set({ error: null }),
}))
