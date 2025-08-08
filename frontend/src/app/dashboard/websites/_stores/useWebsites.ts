import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

export const useWebsiteStore = defineStore('websites', () => {
  // State
  const websites = ref([])
  const activeWebsites = ref([])
  const currentWebsite = ref(null)
  const isLoading = ref(false)
  const error = ref('')

  // API Base URL
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5002'

  // Auth token helper
  const getAuthToken = () => localStorage.getItem('admin_token')

  // Create axios instance with auth
  const createAuthHeaders = () => ({
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`,
      'Content-Type': 'application/json'
    }
  })

  // Fetch all websites
  const fetchWebsites = async () => {
    isLoading.value = true
    error.value = ''
    
    try {
      const response = await axios.get(
        `${API_BASE}/admin/websites`,
        createAuthHeaders()
      )
      
      websites.value = response.data.websites || []
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to fetch websites'
      console.error('Failed to fetch websites:', err)
    } finally {
      isLoading.value = false
    }
  }

  // Fetch active websites (for dashboard)
  const fetchActiveWebsites = async () => {
    try {
      const response = await axios.get(
        `${API_BASE}/admin/websites?status=active&limit=5`,
        createAuthHeaders()
      )
      
      activeWebsites.value = response.data.websites || []
    } catch (err: any) {
      console.error('Failed to fetch active websites:', err)
      // Fallback to mock data for development
      activeWebsites.value = [
        {
          id: 1,
          domain: 'example.com',
          status: 'active',
          totalVerifications: 1543,
          humanRate: 85.7,
          lastActivity: new Date().toISOString()
        },
        {
          id: 2,
          domain: 'demo.site',
          status: 'active',
          totalVerifications: 892,
          humanRate: 78.3,
          lastActivity: new Date().toISOString()
        }
      ]
    }
  }

  // Fetch single website by ID
  const fetchWebsite = async (id: string) => {
    isLoading.value = true
    error.value = ''
    
    try {
      const response = await axios.get(
        `${API_BASE}/admin/websites/${id}`,
        createAuthHeaders()
      )
      
      currentWebsite.value = response.data.website
      return response.data.website
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to fetch website'
      console.error('Failed to fetch website:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Add new website
  const addWebsite = async (websiteData: any) => {
    isLoading.value = true
    error.value = ''
    
    try {
      const response = await axios.post(
        `${API_BASE}/admin/websites`,
        websiteData,
        createAuthHeaders()
      )
      
      const newWebsite = response.data.website
      websites.value.unshift(newWebsite)
      
      return newWebsite
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to add website'
      console.error('Failed to add website:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Update website
  const updateWebsite = async (id: string, updates: any) => {
    isLoading.value = true
    error.value = ''
    
    try {
      const response = await axios.patch(
        `${API_BASE}/admin/websites/${id}`,
        updates,
        createAuthHeaders()
      )
      
      const updatedWebsite = response.data.website
      
      // Update in websites list
      const index = websites.value.findIndex((w: any) => w.id === id)
      if (index !== -1) {
        websites.value[index] = updatedWebsite
      }
      
      // Update current website if it's the same
      if (currentWebsite.value?.id === id) {
        currentWebsite.value = updatedWebsite
      }
      
      return updatedWebsite
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to update website'
      console.error('Failed to update website:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Delete website
  const deleteWebsite = async (id: string) => {
    isLoading.value = true
    error.value = ''
    
    try {
      await axios.delete(
        `${API_BASE}/admin/websites/${id}`,
        createAuthHeaders()
      )
      
      // Remove from websites list
      websites.value = websites.value.filter((w: any) => w.id !== id)
      
      // Clear current website if it's the deleted one
      if (currentWebsite.value?.id === id) {
        currentWebsite.value = null
      }
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to delete website'
      console.error('Failed to delete website:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Computed
  const activeWebsiteCount = computed(() => 
    websites.value.filter((w: any) => w.status === 'active').length
  )

  const totalVerifications = computed(() => 
    websites.value.reduce((sum: number, w: any) => sum + (w.totalVerifications || 0), 0)
  )

  return {
    // State
    websites,
    activeWebsites,
    currentWebsite,
    isLoading,
    error,
    
    // Computed
    activeWebsiteCount,
    totalVerifications,
    
    // Actions
    fetchWebsites,
    fetchActiveWebsites,
    fetchWebsite,
    addWebsite,
    updateWebsite,
    deleteWebsite
  }
})