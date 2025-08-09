/**
 * Simplified Authentication Store - Race Condition Free
 * Clean, reliable implementation without browser compatibility complexity
 */

import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import axios from '@/utils/axios-interceptors'
import { jwtDecode } from 'jwt-decode'
import { API_BASE, API_ENDPOINTS, API_CONFIG } from '@/config/api'

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
  name?: string
}

interface LoginResult {
  success: boolean
  error?: string
}

export const useAuthStore = defineStore('auth', () => {
  // State - Single source of truth
  const token = ref<string | null>(null)
  const user = ref<User | null>(null)
  const isLoading = ref(false)
  const initialized = ref(false)

  // Watch for any changes to token/user and log them
  watch([token, user], ([newToken, newUser], [oldToken, oldUser]) => {
    console.log('🔍 Auth state changed:', {
      tokenChanged: newToken !== oldToken,
      userChanged: newUser !== oldUser,
      newToken: newToken ? 'EXISTS' : 'NULL',
      newUser: newUser ? 'EXISTS' : 'NULL',
      oldToken: oldToken ? 'EXISTS' : 'NULL',
      oldUser: oldUser ? 'EXISTS' : 'NULL'
    })
    if (!newToken && oldToken) {
      console.error('🚨 TOKEN WAS CLEARED!')
      console.trace()
    }
    if (!newUser && oldUser) {
      console.error('🚨 USER WAS CLEARED!')
      console.trace()
    }
  }, { immediate: false })

  // Computed - Reactive authentication status
  const isAuthenticated = computed(() => {
    const result = !!(token.value && user.value)
    console.log('🔐 isAuthenticated computed:', {
      result,
      hasToken: !!token.value,
      hasUser: !!user.value,
      tokenValue: token.value ? 'EXISTS' : 'NULL',
      userValue: user.value ? 'EXISTS' : 'NULL'
    })
    return result
  })

  const isAdmin = computed(() => {
    return user.value?.role === 'admin'
  })


  // Authentication Actions
  async function login(password: string): Promise<LoginResult> {
    if (isLoading.value) {
      return { success: false, error: 'Login already in progress' }
    }
    
    // Clear any existing auth state first
    clearAuth()
    
    try {
      isLoading.value = true
      
      const response = await axios.post(`${API_BASE}${API_ENDPOINTS.ADMIN_LOGIN}`, {
        password
      }, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        withCredentials: API_CONFIG.WITH_CREDENTIALS,
        timeout: API_CONFIG.TIMEOUT
      })

      // Extract token from response - backend returns nested structure
      const authToken = response.data?.data?.token || response.data?.token
      
      if (!authToken) {
        console.error('Token extraction failed. Response data:', response.data)
        return { success: false, error: 'No token received from server' }
      }

      // Set authentication state synchronously
      await setAuthState(authToken)
      
      // Double-check auth state is properly set
      console.log('🔐 Auth state after setAuthState:', {
        isAuthenticated: isAuthenticated.value,
        hasToken: !!token.value,
        hasUser: !!user.value,
        tokenLength: token.value?.length || 0,
        userId: user.value?.id || 'none'
      })
      
      // Verify token server-side to ensure session is valid
      try {
        await axios.get(`${API_BASE}/admin/verify-token`, {
          headers: { Authorization: `Bearer ${authToken}` }
        })
      } catch (e) {
        console.warn('Server-side token verification failed immediately after login:', e)
      }
      
      return { success: true }
      
    } catch (error: any) {
      console.error('Login error:', error)
      console.error('Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        statusText: error.response?.statusText
      })
      
      let errorMessage = 'Login failed'
      if (error.response?.status === 401) {
        errorMessage = 'Invalid password'
      } else if (error.response?.status === 403) {
        errorMessage = 'Access denied'
      } else if (error.response?.data?.error?.message) {
        errorMessage = error.response.data.error.message
      } else if (error.message) {
        errorMessage = error.message
      }
      
      return { success: false, error: errorMessage }
      
    } finally {
      isLoading.value = false
    }
  }

  async function setAuthState(authToken: string): Promise<void> {
    try {
      // Decode token for user info only - let server handle expiry validation
      const decoded = jwtDecode<JWTPayload>(authToken)
      
      console.log('Token validation:', {
        tokenIssued: new Date(decoded.iat * 1000).toISOString(),
        tokenExpires: new Date(decoded.exp * 1000).toISOString(),
        currentTime: new Date().toISOString(),
        timeUntilExpiry: Math.round((decoded.exp * 1000 - Date.now()) / 1000) + ' seconds'
      })
      
      // Set token first
      token.value = authToken
      
      // Create user object from JWT payload
      user.value = {
        id: decoded.user_id || 'admin',
        email: decoded.email || 'admin@passivecaptcha.com',
        name: decoded.name || 'Administrator',
        role: decoded.role || 'admin',
        lastLogin: new Date()
      }

      // Persist token
      try {
        localStorage.setItem('admin_token', authToken)
      } catch (error) {
        console.warn('Could not save token to localStorage:', error)
      }

      // Set axios default header for future requests
      axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`
      
      // Mark store as initialized to avoid restore race during navigation
      initialized.value = true
      
    } catch (error) {
      console.error('Failed to set auth state:', error)
      clearAuth()
      throw error
    }
  }

  function clearAuth(): void {
    console.error('🚨 clearAuth() called! Stack trace:')
    console.trace()
    
    token.value = null
    user.value = null
    
    // Clear stored token
    try {
      localStorage.removeItem('admin_token')
    } catch (error) {
      console.warn('Could not clear localStorage:', error)
    }
    
    // Remove axios header
    delete axios.defaults.headers.common['Authorization']
    initialized.value = false
  }

  async function logout(reason: string = 'manual'): Promise<void> {
    console.error(`🚨 logout() called due to: ${reason}! Stack trace:`)
    console.trace()
    
    try {
      if (token.value) {
        await axios.post(`${API_BASE}${API_ENDPOINTS.ADMIN_LOGOUT}`, {}, {
          headers: { Authorization: `Bearer ${token.value}` }
        })
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      clearAuth()
    }
  }

  async function restoreSession(): Promise<void> {
    if (initialized.value) {
      console.log('🔄 Session already initialized, skipping restoration')
      return // Prevent multiple restoration calls
    }
    
    // If we already have a valid auth state, don't restore from storage
    if (token.value && user.value && !isTokenExpired()) {
      console.log('🔄 Valid session already exists, marking as initialized')
      initialized.value = true
      return
    }
    
    // Get stored token
    let savedToken: string | null = null
    
    try {
      savedToken = localStorage.getItem('admin_token')
    } catch (error) {
      console.warn('Could not access localStorage:', error)
      initialized.value = true
      return
    }
    
    if (!savedToken) {
      initialized.value = true
      return
    }
    
    // Check token expiry first (client-side optimization)
    try {
      const decoded = jwtDecode<JWTPayload>(savedToken)
      if (Math.floor(Date.now() / 1000) >= decoded.exp) {
        console.log('Stored token expired, clearing')
        clearAuth()
        initialized.value = true
        return
      }
    } catch (error) {
      console.warn('Invalid stored token format, clearing:', error)
      clearAuth()
      initialized.value = true
      return
    }
    
    // Set axios header immediately to prevent unauthenticated requests
    axios.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`
    
    try {
      // Validate token with server
      await axios.get(`${API_BASE}/admin/verify-token`, {
        headers: { Authorization: `Bearer ${savedToken}` }
      })
      await setAuthState(savedToken)
    } catch (error) {
      console.warn('Server rejected stored token, clearing:', error)
      clearAuth()
    } finally {
      initialized.value = true
    }
  }

  function isTokenExpired(bufferSeconds = 300): boolean {
    if (!token.value) return true
    
    try {
      const decoded = jwtDecode<JWTPayload>(token.value)
      const currentTime = Math.floor(Date.now() / 1000)
      const expiryTime = decoded.exp - bufferSeconds
      
      const isExpired = currentTime >= expiryTime
      if (isExpired) {
        console.log('Token expired:', {
          currentTime: new Date(currentTime * 1000).toISOString(),
          expiryTime: new Date(decoded.exp * 1000).toISOString(),
          bufferSeconds
        })
      }
      
      return isExpired
    } catch (error) {
      console.error('Error checking token expiry:', error)
      return true
    }
  }

  async function refreshToken(): Promise<boolean> {
    if (!token.value) return false

    try {
      const response = await axios.post(`${API_BASE}${API_ENDPOINTS.ADMIN_REFRESH}`, {}, {
        headers: { Authorization: `Bearer ${token.value}` }
      })

      const newToken = response.data?.token || response.data?.data?.token
      if (newToken) {
        await setAuthState(newToken)
        return true
      }
    } catch (error) {
      console.error('Token refresh failed:', error)
      clearAuth()
    }

    return false
  }

  // TEMPORARY: Disable auto session restoration for debugging
  console.log('🚫 Auto session restoration DISABLED for debugging')
  /*
  // Initialize store - restore session on creation (but not if we're on login page)
  if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
    restoreSession().catch(error => {
      console.warn('Session restoration failed:', error)
    })
  } else {
    console.log('⏭️ Skipping auto session restoration on login page')
  }
  */

  return {
    // State
    token,
    user,
    isLoading,
    initialized,
    
    // Computed
    isAuthenticated,
    isAdmin,
    
    // Actions
    login,
    logout,
    clearAuth,
    restoreSession,
    isTokenExpired,
    refreshToken
  }
})