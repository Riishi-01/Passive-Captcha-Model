import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { jwtDecode } from 'jwt-decode'

interface User {
  id: string
  email: string
  name: string
  role: string
  lastLogin?: Date
}

interface JWTPayload {
  exp: number
  iat: number
  admin?: boolean
  sub?: string
  email?: string
  name?: string
  role?: string
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string | null>(null)
  const user = ref<User | null>(null)
  const isLoading = ref(false)
  const initialized = ref(false)

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  // Browser detection for compatibility
  function detectBrowser(): string {
    const userAgent = navigator.userAgent
    if (userAgent.includes('Firefox')) return 'firefox'
    if (userAgent.includes('Safari') && !userAgent.includes('Chrome')) return 'safari'
    if (userAgent.includes('Edge')) return 'edge'
    if (userAgent.includes('Chrome')) return 'chrome'
    return 'unknown'
  }

  // Actions
  async function login(password: string) {
    try {
      isLoading.value = true
      
      const API_BASE = import.meta.env.VITE_API_URL || (
        window.location.hostname === 'localhost' 
          ? 'http://localhost:5003'
          : `${window.location.protocol}//${window.location.host}`
      )
      
      // Browser-specific request configuration
      const browser = detectBrowser()
      const requestConfig = {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'User-Agent': `PassiveCaptcha-Admin/${browser}`,
          // Firefox-specific headers
          ...(browser === 'firefox' && {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }),
          // Safari-specific headers
          ...(browser === 'safari' && {
            'X-Requested-With': 'XMLHttpRequest'
          })
        },
        withCredentials: true,
        timeout: 30000 // 30 second timeout for all browsers
      }
      
      const response = await axios.post(`${API_BASE}/admin/login`, {
        password
      }, requestConfig)

      const authToken = response.data.token || response.data.data?.token
      
      if (authToken) {
        setToken(authToken)
        await fetchUser()
        return { success: true }
      }
      
      return { success: false, error: 'Invalid credentials' }
    } catch (error: any) {
      console.error('Login error:', error)
      
      // Browser-specific error handling
      let errorMessage = 'Login failed'
      if (error.code === 'NETWORK_ERROR') {
        errorMessage = 'Network error - please check your connection'
      } else if (error.response?.status === 401) {
        errorMessage = 'Invalid password'
      } else if (error.response?.status === 403) {
        errorMessage = 'Access denied'
      } else if (error.response?.data?.error?.message) {
        errorMessage = error.response.data.error.message
      }
      
      return { 
        success: false, 
        error: errorMessage 
      }
    } finally {
      isLoading.value = false
    }
  }

  async function logout() {
    try {
      // Call logout endpoint if available
      if (token.value) {
        await axios.post('/api/admin/logout', {}, {
          headers: { Authorization: `Bearer ${token.value}` }
        })
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // Clear local state regardless of API call result
      clearAuth()
    }
  }

  function setToken(authToken: string) {
    token.value = authToken
    
    // Cross-browser localStorage with fallback
    try {
      localStorage.setItem('admin_token', authToken)
    } catch (error) {
      console.warn('localStorage not available, using sessionStorage:', error)
      try {
        sessionStorage.setItem('admin_token', authToken)
      } catch (sessionError) {
        console.warn('sessionStorage not available, token will not persist:', sessionError)
      }
    }
    
    // Set default authorization header with browser-compatible format
    axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`
    
    // Additional headers for cross-browser compatibility
    axios.defaults.headers.common['Accept'] = 'application/json'
    axios.defaults.headers.common['Content-Type'] = 'application/json'
  }

  function clearAuth() {
    token.value = null
    user.value = null
    
    // Cross-browser token cleanup
    try {
      localStorage.removeItem('admin_token')
    } catch (error) {
      console.warn('localStorage cleanup failed:', error)
    }
    
    try {
      sessionStorage.removeItem('admin_token')
    } catch (error) {
      console.warn('sessionStorage cleanup failed:', error)
    }
    
    // Remove authorization headers
    delete axios.defaults.headers.common['Authorization']
    delete axios.defaults.headers.common['Accept']
    delete axios.defaults.headers.common['Content-Type']
  }

  async function fetchUser() {
    if (!token.value) return

    try {
      const decoded = jwtDecode<JWTPayload>(token.value)
      
      // Check if token is expired
      if (decoded.exp * 1000 < Date.now()) {
        clearAuth()
        return
      }

      // For the simple admin system, create a basic user object
      // Check if this is an admin token
      if (decoded.admin) {
        user.value = {
          id: 'admin',
          email: 'admin@passivecaptcha.com',
          name: 'Administrator',
          role: 'admin',
          lastLogin: new Date()
        }
      } else {
        // Fallback for other token formats
        user.value = {
          id: decoded.sub || 'user',
          email: decoded.email || 'user@passivecaptcha.com',
          name: decoded.name || 'User',
          role: decoded.role || 'user',
          lastLogin: new Date()
        }
      }
    } catch (error) {
      console.error('Failed to decode token:', error)
      clearAuth()
    }
  }

  async function restoreSession() {
    // Cross-browser token restoration with fallback
    let savedToken: string | null = null
    
    try {
      savedToken = localStorage.getItem('admin_token')
    } catch (error) {
      console.warn('localStorage not available, trying sessionStorage:', error)
      try {
        savedToken = sessionStorage.getItem('admin_token')
      } catch (sessionError) {
        console.warn('sessionStorage not available:', sessionError)
      }
    }
    
    if (savedToken) {
      // Validate token format before setting
      try {
        const decoded = jwtDecode<JWTPayload>(savedToken)
        
        // Check if token is not expired
        if (decoded.exp * 1000 > Date.now()) {
          setToken(savedToken)
          await fetchUser()
        } else {
          console.info('Stored token expired, clearing auth')
          clearAuth()
        }
      } catch (decodeError) {
        console.warn('Invalid stored token, clearing auth:', decodeError)
        clearAuth()
      }
    }
    
    initialized.value = true
  }

  function isTokenExpired(): boolean {
    if (!token.value) return true
    
    try {
      const decoded = jwtDecode<JWTPayload>(token.value)
      return decoded.exp * 1000 < Date.now()
    } catch {
      return true
    }
  }

  async function refreshToken() {
    if (!token.value) return false

    try {
      const response = await axios.post('/api/admin/refresh', {}, {
        headers: { Authorization: `Bearer ${token.value}` }
      })

      const { token: newToken } = response.data
      
      if (newToken) {
        setToken(newToken)
        await fetchUser()
        return true
      }
    } catch (error) {
      console.error('Token refresh failed:', error)
      clearAuth()
    }

    return false
  }

  return {
    // State
    token,
    user,
    isLoading,
    initialized,
    
    // Getters
    isAuthenticated,
    isAdmin,
    
    // Actions
    login,
    logout,
    setToken,
    clearAuth,
    fetchUser,
    restoreSession,
    isTokenExpired,
    refreshToken
  }
}) 