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

  // Actions
  async function login(password: string) {
    try {
      isLoading.value = true
      
      const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5003'
      
      const response = await axios.post(`${API_BASE}/admin/login`, {
        password
      })

      const { token: authToken } = response.data
      
      if (authToken) {
        setToken(authToken)
        await fetchUser()
        return { success: true }
      }
      
      return { success: false, error: 'Invalid credentials' }
    } catch (error: any) {
      console.error('Login error:', error)
      return { 
        success: false, 
        error: error.response?.data?.error?.message || 'Login failed' 
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
    localStorage.setItem('admin_token', authToken)
    
    // Set default authorization header
    axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`
  }

  function clearAuth() {
    token.value = null
    user.value = null
    localStorage.removeItem('admin_token')
    
    // Remove authorization header
    delete axios.defaults.headers.common['Authorization']
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
    const savedToken = localStorage.getItem('admin_token')
    
    if (savedToken) {
      setToken(savedToken)
      await fetchUser()
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