import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import apiService from '../services/api'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      isAuthenticated: false,
      token: null,
      loading: false,
      error: null,

      login: async (password) => {
        set({ loading: true, error: null })
        try {
          const response = await apiService.login(password)
          
          // Handle both new unified API response format and legacy formats
          let token = null
          if (response.success && response.data) {
            token = response.data.token
          } else {
            token = response.token || response.access_token
          }
          
          if (!token) {
            throw new Error('No token received from server')
          }
          
          localStorage.setItem('admin_token', token)
          set({ 
            isAuthenticated: true, 
            token, 
            loading: false,
            error: null 
          })
          return { success: true }
        } catch (error) {
          let errorMessage = 'Login failed'
          
          if (error.response?.data) {
            const errorData = error.response.data
            if (errorData.error?.message) {
              errorMessage = errorData.error.message
            } else if (errorData.detail) {
              errorMessage = errorData.detail
            } else if (errorData.message) {
              errorMessage = errorData.message
            }
          } else if (error.message) {
            errorMessage = error.message
          }
          
          set({ 
            loading: false, 
            error: errorMessage,
            isAuthenticated: false,
            token: null 
          })
          return { success: false, error: errorMessage }
        }
      },

      logout: () => {
        localStorage.removeItem('admin_token')
        set({ 
          isAuthenticated: false, 
          token: null,
          error: null 
        })
      },

      verifyToken: async () => {
        const token = localStorage.getItem('admin_token')
        if (!token) {
          set({ isAuthenticated: false, token: null })
          return false
        }

        try {
          await apiService.verifyToken()
          set({ 
            isAuthenticated: true, 
            token,
            error: null 
          })
          return true
        } catch (error) {
          localStorage.removeItem('admin_token')
          set({ 
            isAuthenticated: false, 
            token: null,
            error: null 
          })
          return false
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-store',
      partialize: (state) => ({ token: state.token }),
    }
  )
)
