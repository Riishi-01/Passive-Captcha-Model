import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5003'

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  setupInterceptors() {
    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('admin_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('admin_token')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  // Auth endpoints
  async login(password) {
    const response = await this.client.post('/admin/login', { password })
    return response.data
  }

  async verifyToken() {
    const response = await this.client.get('/admin/verify-token')
    return response.data
  }

  // Analytics endpoints
  async getStats() {
    const response = await this.client.get('/admin/analytics/stats')
    return response.data
  }

  async getChartData(type, period = '24h') {
    const response = await this.client.get(`/admin/analytics/charts/${type}`, {
      params: { period }
    })
    return response.data
  }

  // Website endpoints
  async getWebsites() {
    const response = await this.client.get('/admin/websites')
    return response.data
  }

  async getWebsite(id) {
    const response = await this.client.get(`/admin/websites/${id}`)
    return response.data
  }

  async createWebsite(data) {
    const response = await this.client.post('/admin/websites', data)
    return response.data
  }

  async updateWebsite(id, data) {
    const response = await this.client.put(`/admin/websites/${id}`, data)
    return response.data
  }

  async deleteWebsite(id) {
    const response = await this.client.delete(`/admin/websites/${id}`)
    return response.data
  }

  // Script management
  async generateScript(websiteId, options = {}) {
    const response = await this.client.post('/admin/scripts/generate', {
      website_id: websiteId,
      ...options
    })
    return response.data
  }

  async getScriptTokens(websiteId) {
    const response = await this.client.get(`/admin/scripts/tokens/${websiteId}`)
    return response.data
  }

  async revokeScriptToken(websiteId) {
    const response = await this.client.post(`/admin/scripts/tokens/${websiteId}/revoke`)
    return response.data
  }

  // ML endpoints
  async getModelHealth() {
    const response = await this.client.get('/admin/ml/health')
    return response.data
  }

  async getModelMetrics() {
    const response = await this.client.get('/admin/ml/metrics')
    return response.data
  }

  async retrain() {
    const response = await this.client.post('/admin/ml/retrain')
    return response.data
  }

  // Alerts endpoints
  async getAlerts(limit = 50) {
    const response = await this.client.get('/admin/alerts/recent', {
      params: { limit }
    })
    return response.data
  }

  async markAlertRead(alertId) {
    const response = await this.client.post(`/admin/alerts/${alertId}/read`)
    return response.data
  }

  async getAlertSettings() {
    const response = await this.client.get('/admin/alerts/settings')
    return response.data
  }

  async updateAlertSettings(settings) {
    const response = await this.client.put('/admin/alerts/settings', settings)
    return response.data
  }

  // Logs endpoints
  async getLogs(params = {}) {
    const response = await this.client.get('/admin/logs', { params })
    return response.data
  }

  // System health
  async getSystemHealth() {
    const response = await this.client.get('/admin/health')
    return response.data
  }

  // Settings endpoints
  async getSettings() {
    const response = await this.client.get('/admin/settings')
    return response.data
  }

  async updateSettings(settings) {
    const response = await this.client.put('/admin/settings', settings)
    return response.data
  }

  async changePassword(currentPassword, newPassword) {
    const response = await this.client.put('/admin/change-password', {
      current_password: currentPassword,
      new_password: newPassword
    })
    return response.data
  }
}

export default new ApiService()
