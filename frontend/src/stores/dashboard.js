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
      const stats = await apiService.getStats()
      set({ 
        stats, 
        loading: false,
        lastUpdated: new Date(),
        error: null 
      })
      return stats
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
