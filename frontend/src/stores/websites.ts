import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiService, type Website } from '@/services/api'

// Re-export Website type for backward compatibility
export type { Website } from '@/services/api'

export interface WebsiteStats {
  hourlyVerifications: number[]
  humanVsBotRatio: {
    human: number
    bot: number
  }
  topPages: Array<{
    path: string
    verifications: number
  }>
  averageResponseTime: number
}

export const useWebsiteStore = defineStore('websites', () => {
  // State
  const websites = ref<Website[]>([])
  const activeWebsites = ref<Website[]>([])
  const selectedWebsite = ref<Website | null>(null)
  const websiteStats = ref<Record<string, WebsiteStats>>({})
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // API Base URL
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5002'

  // Auth token helper
  const getAuthToken = () => localStorage.getItem('admin_token')

  // API request helper with enhanced error handling
  const apiRequest = async (endpoint: string, options: any = {}) => {
    const token = getAuthToken()
    if (!token) {
      throw new Error('No authentication token found')
    }

    try {
      const response = await axios({
        url: `${API_BASE}${endpoint}`,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      })

      // Check if response follows the new API format
      if (response.data.success !== undefined) {
        if (!response.data.success) {
          throw new Error(response.data.error?.message || 'API request failed')
        }
        return response.data.data || response.data
      }

      return response.data
    } catch (error: any) {
      console.error('API request failed:', error)
      if (error.response?.status === 401) {
        // Token expired, redirect to login
        localStorage.removeItem('admin_token')
        window.location.href = '/login'
      }
      throw error
    }
  }

  // Actions
    const fetchWebsites = async (includeAnalytics: boolean = true) => {
    try {
      isLoading.value = true
      error.value = null

      const response = await apiService.getWebsites(includeAnalytics)
      
      if (response.success && response.data) {
        websites.value = response.data.websites
        activeWebsites.value = response.data.websites.filter(w => w.status === 'active')
      }
      
    } catch (err: any) {
      console.error('Failed to fetch websites:', err)
      error.value = err.message || 'Failed to fetch websites'
      
      // Fallback to empty array on error
      websites.value = []
      activeWebsites.value = []
    } finally {
      isLoading.value = false
    }
  }

  const fetchActiveWebsites = async () => {
    await fetchWebsites()
    return activeWebsites.value
  }

  const fetchWebsiteStats = async (websiteId: string, timeRange: string = '24h') => {
    try {
      const hours = timeRange === '24h' ? 24 : timeRange === '7d' ? 168 : 24
      
      // Get logs for specific website
      const response = await apiRequest(`/admin/logs?origin=${websiteId}&hours=${hours}&limit=1000`)
      const logs = response.data.logs || []
      
      // Process logs into stats
      const stats: WebsiteStats = {
        hourlyVerifications: new Array(24).fill(0),
        humanVsBotRatio: { human: 0, bot: 0 },
        topPages: [],
        averageResponseTime: 100
      }
      
      // Group by hour
      const hourlyMap = new Map<number, number>()
      const pageMap = new Map<string, number>()
      
      logs.forEach((log: any) => {
        const date = new Date(log.timestamp)
        const hour = date.getHours()
        
        hourlyMap.set(hour, (hourlyMap.get(hour) || 0) + 1)
        
        if (log.isHuman || log.is_human) {
          stats.humanVsBotRatio.human++
        } else {
          stats.humanVsBotRatio.bot++
        }
        
        // Extract page path from origin
        const path = extractPath(log.origin || '/')
        pageMap.set(path, (pageMap.get(path) || 0) + 1)
      })
      
      // Fill hourly data
      for (let i = 0; i < 24; i++) {
        stats.hourlyVerifications[i] = hourlyMap.get(i) || 0
      }
      
      // Get top pages
      stats.topPages = Array.from(pageMap.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([path, count]) => ({ path, verifications: count }))
      
      websiteStats.value[websiteId] = stats
      return stats
      
    } catch (error) {
      console.error('Error fetching website stats:', error)
      throw error
    }
  }

  const selectWebsite = (website: Website) => {
    selectedWebsite.value = website
  }

  const addWebsite = async (name: string, url: string, description?: string) => {
    try {
      isLoading.value = true
      error.value = null
      
      const response = await apiService.createWebsite({ name, url, description })
      
      if (response.success && response.data) {
        websites.value.unshift(response.data.website)
        
        if (response.data.website.status === 'active') {
          activeWebsites.value.unshift(response.data.website)
        }
        
        return response.data.website
      }
      
    } catch (err: any) {
      console.error('Failed to add website:', err)
      error.value = err.message || 'Failed to add website'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const updateWebsite = async (websiteId: string, updates: Partial<Website>) => {
    const index = websites.value.findIndex(w => w.id === websiteId)
    if (index !== -1) {
      websites.value[index] = { ...websites.value[index], ...updates }
      return websites.value[index]
    }
    throw new Error('Website not found')
  }

  const deleteWebsite = async (websiteId: string) => {
    websites.value = websites.value.filter(w => w.id !== websiteId)
    delete websiteStats.value[websiteId]
    
    if (selectedWebsite.value?.id === websiteId) {
      selectedWebsite.value = null
    }
  }

  // Helper functions
  const extractDomain = (url: string): string => {
    try {
      if (!url.startsWith('http')) {
        url = 'http://' + url
      }
      return new URL(url).hostname
    } catch {
      return url.split('/')[0] || 'localhost'
    }
  }

  const extractPath = (url: string): string => {
    try {
      if (!url.startsWith('http')) {
        return url.startsWith('/') ? url : '/' + url
      }
      return new URL(url).pathname
    } catch {
      return '/'
    }
  }



  // Computed
  const totalWebsites = computed(() => websites.value.length)
  const activeWebsiteCount = computed(() => activeWebsites.value.length)
  const totalVerifications = computed(() => 
    websites.value.reduce((sum, site) => sum + site.totalVerifications, 0)
  )
  const avgHumanRate = computed(() => {
    if (websites.value.length === 0) return 0
    const sum = websites.value.reduce((sum, site) => sum + site.humanRate, 0)
    return Math.round(sum / websites.value.length)
  })

  return {
    // State
    websites,
    activeWebsites,
    selectedWebsite,
    websiteStats,
    isLoading,
    error,
    
    // Actions
    fetchWebsites,
    fetchActiveWebsites,
    fetchWebsiteStats,
    selectWebsite,
    addWebsite,
    updateWebsite,
    deleteWebsite,
    
    // Computed
    totalWebsites,
    activeWebsiteCount,
    totalVerifications,
    avgHumanRate
  }
})