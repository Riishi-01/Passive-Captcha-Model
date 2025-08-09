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
      // Handle the unified API response format
      const websites = response.success ? response.data.websites : response
      set({ 
        websites, 
        loading: false,
        error: null 
      })
      return websites
    } catch (error) {
      let errorMessage = 'Failed to fetch websites'
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
      const website = response.success ? response.data.website : response
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
