/**
 * Axios Interceptors for Authentication
 * Handles 401 responses by clearing auth state and redirecting to login
 */

import axios, { AxiosResponse } from 'axios'

// Add request interceptor to log all API calls
axios.interceptors.request.use((config) => {
  console.log('📡 API Request:', {
    method: config.method?.toUpperCase(),
    url: config.url,
    hasAuth: !!config.headers.Authorization,
    timestamp: new Date().toISOString()
  })
  return config
})

// Simplified response interceptor - only handle 401s by redirecting to login
axios.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log('✅ API Response:', {
      method: response.config.method?.toUpperCase(),
      url: response.config.url,
      status: response.status,
      timestamp: new Date().toISOString()
    })
    return response
  },
  async (error) => {
    // Handle 401 Unauthorized - token expired or invalid
    if (error.response?.status === 401) {
      console.error('🚨 401 Unauthorized received! Details:', {
        url: error.config?.url,
        method: error.config?.method,
        headers: error.config?.headers,
        response: error.response?.data,
        currentPath: window.location.pathname
      })
      console.trace('401 Error stack trace:')
      
      try {
        // Clear local storage
        localStorage.removeItem('admin_token')
        // Redirect to login page
        if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
          console.log('🚨 Redirecting to login due to 401')
          window.location.href = '/login'
        }
      } catch (e) {
        console.error('Error during 401 handling:', e)
      }
    }

    return Promise.reject(error)
  }
)

export default axios