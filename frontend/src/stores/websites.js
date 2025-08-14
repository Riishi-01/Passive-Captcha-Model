import { create } from 'zustand'
import apiService from '../services/api'

export const useWebsitesStore = create((set, get) => ({
  websites: [],
  selectedWebsite: null,
  loading: false,
  error: null,
  modalOpen: false,
  editingWebsite: null,

  fetchWebsites: async () => {
    set({ loading: true, error: null })
    try {
      const response = await apiService.getWebsites()
      // Normalize various backend shapes to a clean list
      let rawList = []
      if (response?.success && response?.data?.websites) {
        rawList = response.data.websites
      } else if (Array.isArray(response?.websites)) {
        rawList = response.websites
      } else if (Array.isArray(response)) {
        rawList = response
      }

      const websites = rawList.map((w) => ({
        id: w.id || w.website_id,
        name: w.name || w.website_name || 'Untitled',
        url: w.url || w.domain || w.website_url || '',
        status: w.status || 'inactive',
        token: w.token || (w.script_token_info && w.script_token_info.script_token) || w.api_key || '',
        description: w.description || '',
        created_at: w.created_at || null,
        last_activity: w.last_activity || null,
      })).sort((a, b) => {
        const ad = a.created_at ? Date.parse(a.created_at) : 0
        const bd = b.created_at ? Date.parse(b.created_at) : 0
        return bd - ad
      })
      set({ 
        websites, 
        loading: false,
        error: null 
      })
      return websites
    } catch (error) {
      // If unauthorized, let global redirect handle it without noisy error UI
      if (error.response?.status === 401) {
        set({ loading: false, error: null })
        return []
      }
      let errorMessage = 'Failed to retrieve websites. Please ensure you are logged in and try again.'
      if (error.response?.data) {
        const errorData = error.response.data
        if (errorData.error?.message) {
          errorMessage = errorData.error.message
        } else if (errorData.detail) {
          errorMessage = errorData.detail
        } else if (errorData.message) {
          errorMessage = errorData.message
        }
      }
      set({ 
        loading: false, 
        error: errorMessage 
      })
      throw error
    }
  },

  fetchWebsite: async (id) => {
    try {
      const website = await apiService.getWebsite(id)
      set({ selectedWebsite: website })
      return website
    } catch (error) {
      console.error('Failed to fetch website:', error)
      throw error
    }
  },

  createWebsite: async (data) => {
    set({ loading: true, error: null })
    try {
      const response = await apiService.createWebsite(data)
      
      // Handle different response formats
      let website
      if (response.success && response.data) {
        website = response.data.website || response.data
      } else if (response.data) {
        website = response.data
      } else {
        website = response
      }
      set((state) => ({
        websites: [...state.websites, website],
        loading: false,
        modalOpen: false,
        error: null
      }))
      return website
    } catch (error) {
      let errorMessage = 'Failed to create website'
      if (error.response?.data) {
        const errorData = error.response.data
        if (errorData.error?.message) {
          errorMessage = errorData.error.message
        } else if (errorData.detail) {
          errorMessage = errorData.detail
        } else if (errorData.message) {
          errorMessage = errorData.message
        }
      }
      set({ 
        loading: false, 
        error: errorMessage 
      })
      throw error
    }
  },

  updateWebsite: async (id, data) => {
    set({ loading: true, error: null })
    try {
      const website = await apiService.updateWebsite(id, data)
      set((state) => ({
        websites: state.websites.map(w => w.id === id ? website : w),
        selectedWebsite: state.selectedWebsite?.id === id ? website : state.selectedWebsite,
        loading: false,
        modalOpen: false,
        editingWebsite: null,
        error: null
      }))
      return website
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to update website'
      set({ 
        loading: false, 
        error: errorMessage 
      })
      throw error
    }
  },

  deleteWebsite: async (id) => {
    set({ loading: true, error: null })
    try {
      await apiService.deleteWebsite(id)
      set((state) => ({
        websites: state.websites.filter(w => w.id !== id),
        selectedWebsite: state.selectedWebsite?.id === id ? null : state.selectedWebsite,
        loading: false,
        error: null
      }))
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to delete website'
      set({ 
        loading: false, 
        error: errorMessage 
      })
      throw error
    }
  },

  openModal: (website = null) => {
    set({ 
      modalOpen: true, 
      editingWebsite: website 
    })
  },

  closeModal: () => {
    set({ 
      modalOpen: false, 
      editingWebsite: null,
      error: null 
    })
  },

  clearError: () => set({ error: null }),
}))
