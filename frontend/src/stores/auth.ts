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
  user_id: string
  email: string
  role: string
  session_id: string
  ip_address: string
  sub?: string
  name?: string
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string | null>(null)
  const user = ref<User | null>(null)
  const isLoading = ref(false)
  const initialized = ref(false)

  // Getters
  const isAuthenticated = computed(() => {
    const result = !!token.value && !!user.value
    return result
  })
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
        window.location.port === '5002' 
          ? `${window.location.protocol}//${window.location.host}`
          : 'http://localhost:5002'
      )
      
      // Browser-specific request configuration
      const browser = detectBrowser()
      const requestConfig = {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          // Removed User-Agent - browsers don't allow setting this header
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

      if (import.meta.env.DEV) {
        console.log('[AUTH DEBUG] Full login response:', response.data)
        console.log('[AUTH DEBUG] Checking token locations:')
        console.log('[AUTH DEBUG] - response.data.token:', response.data.token ? 'EXISTS' : 'NOT FOUND')
        console.log('[AUTH DEBUG] - response.data.data?.token:', response.data.data?.token ? 'EXISTS' : 'NOT FOUND')
      }
      
      const authToken = response.data.token || response.data.data?.token
      if (import.meta.env.DEV) {
        console.log('[AUTH DEBUG] Final extracted token:', authToken ? authToken.substring(0, 20) + '...' : 'NULL/UNDEFINED')
      }
      
      if (authToken) {
        if (import.meta.env.DEV) {
          console.log('[AUTH DEBUG] Setting token...')
        }
        setToken(authToken)
        if (import.meta.env.DEV) {
          console.log('[AUTH DEBUG] Token set, fetching user...')
        }
        await fetchUser()
        
        // Ensure both token and user are set before returning success
        const isFullyAuthenticated = !!token.value && !!user.value
        if (import.meta.env.DEV) {
          console.log('[AUTH DEBUG] User fetched, fully authenticated:', isFullyAuthenticated)
        }
        
        if (isFullyAuthenticated) {
          return { success: true }
        } else {
          if (import.meta.env.DEV) {
            console.error('[AUTH DEBUG] Authentication incomplete - token or user missing')
          }
          clearAuth()
          return { success: false, error: 'Authentication setup failed' }
        }
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
    if (import.meta.env.DEV) {
      console.log('[AUTH DEBUG] setToken called with:', authToken ? authToken.substring(0, 20) + '...' : 'NULL/UNDEFINED')
    }
    token.value = authToken
    
    // Cross-browser localStorage with fallback
    try {
      localStorage.setItem('admin_token', authToken)
      if (import.meta.env.DEV) {
        console.log('[AUTH DEBUG] Token saved to localStorage successfully')
        // Verify it was saved
        const saved = localStorage.getItem('admin_token')
        console.log('[AUTH DEBUG] Verification - token in localStorage:', saved ? 'EXISTS' : 'NOT FOUND')
      }
    } catch (error) {
      console.warn('localStorage not available, using sessionStorage:', error)
      try {
        sessionStorage.setItem('admin_token', authToken)
        if (import.meta.env.DEV) {
          console.log('[AUTH DEBUG] Token saved to sessionStorage')
          const saved = sessionStorage.getItem('admin_token')
          console.log('[AUTH DEBUG] Verification - token in sessionStorage:', saved ? 'EXISTS' : 'NOT FOUND')
        }
      } catch (sessionError) {
        console.warn('sessionStorage not available, token will not persist:', sessionError)
      }
    }
    
    // Set default authorization header with browser-compatible format
    axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`
    
    // Additional headers for cross-browser compatibility
    axios.defaults.headers.common['Accept'] = 'application/json'
    axios.defaults.headers.common['Content-Type'] = 'application/json'
    
    if (import.meta.env.DEV) {
      console.log('[AUTH DEBUG] Token setup complete')
    }
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
    if (!token.value) {
      if (import.meta.env.DEV) {
        console.log('[AUTH DEBUG] fetchUser called but no token available')
      }
      return
    }

    try {
      const decoded = jwtDecode<JWTPayload>(token.value)
      if (import.meta.env.DEV) {
        console.log('[AUTH DEBUG] Decoded JWT in fetchUser:', decoded)
      }
      
      // Check if token is expired
      if (decoded.exp * 1000 < Date.now()) {
        if (import.meta.env.DEV) {
          console.log('[AUTH DEBUG] Token expired in fetchUser, clearing auth')
        }
        clearAuth()
        return
      }

      // For the admin system, create user object from JWT payload
      // The JWT contains user_id, email, role directly
      user.value = {
        id: decoded.user_id || decoded.sub || 'admin',
        email: decoded.email || 'admin@passivecaptcha.com',
        name: decoded.name || 'Administrator',
        role: decoded.role || 'admin',
        lastLogin: new Date()
      }
      if (import.meta.env.DEV) {
        console.log('[AUTH DEBUG] User set in fetchUser:', user.value)
        console.log('[AUTH DEBUG] isAuthenticated after fetchUser:', !!token.value && !!user.value)
      }
    } catch (error) {
      if (import.meta.env.DEV) {
        console.error('[AUTH DEBUG] Failed to decode token:', error)
      }
      clearAuth()
    }
  }

  async function restoreSession() {
    // Cross-browser token restoration with fallback
    let savedToken: string | null = null
    
    if (import.meta.env.DEV) {
      console.log('[AUTH DEBUG] Restoring session...')
    }
    
    try {
      savedToken = localStorage.getItem('admin_token')
      if (import.meta.env.DEV) {
        console.log('[AUTH DEBUG] Token from localStorage:', savedToken ? 'Found' : 'Not found')
      }
    } catch (error) {
      console.warn('localStorage not available, trying sessionStorage:', error)
      try {
        savedToken = sessionStorage.getItem('admin_token')
        if (import.meta.env.DEV) {
          console.log('[AUTH DEBUG] Token from sessionStorage:', savedToken ? 'Found' : 'Not found')
        }
      } catch (sessionError) {
        console.warn('sessionStorage not available:', sessionError)
      }
    }
    
    if (savedToken) {
      // Validate token format before setting
      try {
        const decoded = jwtDecode<JWTPayload>(savedToken)
        if (import.meta.env.DEV) {
          console.log('[AUTH DEBUG] Decoded JWT:', decoded)
        }
        
        const now = Date.now()
        const expTime = decoded.exp * 1000
        if (import.meta.env.DEV) {
          console.log('[AUTH DEBUG] Current time:', now, 'Token expires:', expTime, 'Valid:', expTime > now)
        }
        
        // Check if token is not expired
        if (expTime > now) {
          if (import.meta.env.DEV) {
            console.log('[AUTH DEBUG] Token valid, setting user...')
          }
          setToken(savedToken)
          await fetchUser()
          if (import.meta.env.DEV) {
            console.log('[AUTH DEBUG] User set, authenticated:', !!user.value)
          }
        } else {
          if (import.meta.env.DEV) {
            console.info('[AUTH DEBUG] Stored token expired, clearing auth')
          }
          clearAuth()
        }
      } catch (decodeError) {
        if (import.meta.env.DEV) {
          console.warn('[AUTH DEBUG] Invalid stored token, clearing auth:', decodeError)
        }
        clearAuth()
      }
    } else {
      if (import.meta.env.DEV) {
        console.log('[AUTH DEBUG] No saved token found')
      }
    }
    
    initialized.value = true
    if (import.meta.env.DEV) {
      console.log('[AUTH DEBUG] Session restore complete:')
      console.log('[AUTH DEBUG] - Token present:', !!token.value)
      console.log('[AUTH DEBUG] - User present:', !!user.value) 
      console.log('[AUTH DEBUG] - isAuthenticated:', !!token.value && !!user.value)
      if (user.value) {
        console.log('[AUTH DEBUG] - User details:', user.value)
      }
    }
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