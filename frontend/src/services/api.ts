/**
 * Centralized API Service Layer
 * Handles all backend communication with proper error handling and type safety
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'

// Types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: {
    code: string
    message: string
  }
  timestamp?: string
}

export interface ApiError {
  code: string
  message: string
  status?: number
}

export interface DashboardStats {
  totalVerifications: number
  humanRate: number
  avgConfidence: number
  avgResponseTime: number
  verificationChange: number
  humanRateChange: number
  confidenceChange: number
  responseTimeChange: number
}

export interface ChartDataPoint {
  timestamp: string
  human: number
  bot: number
  confidence: number
}

export interface SystemHealth {
  database: {
    status: string
    totalVerifications: number
    last24hVerifications: number
    lastVerification: string | null
  }
  model: {
    status: string
    loaded: boolean
    info: Record<string, any>
  }
  api: {
    status: string
    version: string
    uptime: string
  }
}

export interface Website {
  id: string
  name: string
  url: string
  status: 'active' | 'inactive' | 'suspended' | 'pending_integration'
  createdAt: string
  lastActivity: string
  totalVerifications: number
  humanRate: number
  avgConfidence: number
  integration_status?: string
  has_script_token?: boolean
  script_token_info?: any
}

export interface MLMetrics {
  totalVerificationAttempts: number
  humanDetectionRate: number
  botDetectionRate: number
  averageConfidence: number
  falsePositives: number
  falseNegatives: number
  verificationTrends: ChartDataPoint[]
  confidenceDistribution: Record<string, number>
  accuracyMetrics: {
    truePositives: number
    trueNegatives: number
    falsePositives: number
    falseNegatives: number
  }
  performanceTrends: ChartDataPoint[]
  modelHealth: {
    status: string
    lastUpdated: string
    version: string
  }
}

export interface Alert {
  id: string
  type: 'error' | 'warning' | 'info' | 'success'
  title: string
  message: string
  timestamp: string
  websiteId?: string
  resolved: boolean
}

export interface TimelineLog {
  id: string
  timestamp: string
  type: 'verification' | 'alert' | 'system' | 'user_action'
  level: 'info' | 'warning' | 'error' | 'success'
  message: string
  details?: Record<string, any>
}

class ApiService {
  private axiosInstance: AxiosInstance
  private baseURL: string

  constructor() {
    // Auto-detect API URL based on environment
    const isProduction = import.meta.env.PROD
    
    // In production, use relative URLs (same origin) to avoid CORS issues
    // In development, use localhost backend
    let defaultUrl: string
    if (isProduction) {
      // For production deployments, use relative URLs to avoid CORS issues
      defaultUrl = window.location.origin
    } else {
      // For development, proxy through Vite dev server
      defaultUrl = 'http://localhost:5003'
    }
    
    this.baseURL = import.meta.env.VITE_API_URL || defaultUrl
    
    this.axiosInstance = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor to add auth token
    this.axiosInstance.interceptors.request.use((config) => {
      const token = localStorage.getItem('admin_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    // Response interceptor for error handling
    this.axiosInstance.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('admin_token')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  private async handleRequest<T>(request: Promise<AxiosResponse<any>>): Promise<ApiResponse<T>> {
    try {
      const response = await request
      return response.data
    } catch (error: any) {
      console.error('API Error:', error)
      
      if (error.response?.data) {
        throw {
          code: error.response.data.error?.code || 'API_ERROR',
          message: error.response.data.error?.message || 'An error occurred',
          status: error.response.status
        } as ApiError
      }
      
      throw {
        code: 'NETWORK_ERROR',
        message: 'Network connection failed',
        status: 0
      } as ApiError
    }
  }

  // Authentication APIs
  async login(password: string): Promise<ApiResponse<{ token: string; user: any }>> {
    return this.handleRequest(
      this.axiosInstance.post('/admin/login', { password })
    )
  }

  async verifyToken(): Promise<ApiResponse<{ user: any }>> {
    return this.handleRequest(
      this.axiosInstance.get('/admin/verify-token')
    )
  }

  // Dashboard Analytics APIs
  async getDashboardStats(timeRange: string = '24h'): Promise<ApiResponse<DashboardStats>> {
    return this.handleRequest(
      this.axiosInstance.get(`/admin/analytics/stats?timeRange=${timeRange}`)
    )
  }

  async getChartData(timeRange: string = '24h'): Promise<ApiResponse<ChartDataPoint[]>> {
    return this.handleRequest(
      this.axiosInstance.get(`/admin/analytics/charts?timeRange=${timeRange}`)
    )
  }

  async getDetectionData(timeRange: string = '24h'): Promise<ApiResponse<{ human: number; bot: number; humanPercentage: number; botPercentage: number }>> {
    return this.handleRequest(
      this.axiosInstance.get(`/admin/analytics/detection?timeRange=${timeRange}`)
    )
  }

  async getSystemHealth(): Promise<ApiResponse<SystemHealth>> {
    return this.handleRequest(
      this.axiosInstance.get('/admin/health')
    )
  }

  async getRecentAlerts(): Promise<ApiResponse<Alert[]>> {
    return this.handleRequest(
      this.axiosInstance.get('/admin/alerts/recent')
    )
  }

  async getTimelineLogs(filter: string = 'all', offset: number = 0, limit: number = 50): Promise<ApiResponse<{ logs: TimelineLog[]; hasMore: boolean; total: number }>> {
    return this.handleRequest(
      this.axiosInstance.get(`/admin/logs/timeline?filter=${filter}&offset=${offset}&limit=${limit}`)
    )
  }

  // Website Management APIs
  async getWebsites(includeAnalytics: boolean = true): Promise<ApiResponse<{ websites: Website[]; total_count: number }>> {
    return this.handleRequest(
      this.axiosInstance.get(`/admin/websites?include_analytics=${includeAnalytics}`)
    )
  }

  async createWebsite(data: { name: string; url: string; description?: string }): Promise<ApiResponse<{ website: Website }>> {
    return this.handleRequest(
      this.axiosInstance.post('/admin/websites', data)
    )
  }

  async updateWebsite(id: string, data: Partial<Website>): Promise<ApiResponse<{ website: Website }>> {
    return this.handleRequest(
      this.axiosInstance.put(`/admin/websites/${id}`, data)
    )
  }

  async deleteWebsite(id: string): Promise<ApiResponse<{}>> {
    return this.handleRequest(
      this.axiosInstance.delete(`/admin/websites/${id}`)
    )
  }

  async toggleWebsiteStatus(id: string): Promise<ApiResponse<{ website: Website }>> {
    return this.handleRequest(
      this.axiosInstance.patch(`/admin/websites/${id}/status`)
    )
  }

  // ML Model APIs
  async getMLMetrics(timeRange: string = '24h'): Promise<ApiResponse<MLMetrics>> {
    return this.handleRequest(
      this.axiosInstance.get(`/admin/ml/metrics?timeRange=${timeRange}`)
    )
  }

  async getModelInfo(): Promise<ApiResponse<{ algorithm: string; version: string; features: number; accuracy: number }>> {
    return this.handleRequest(
      this.axiosInstance.get('/admin/ml/info')
    )
  }

  async retrainModel(): Promise<ApiResponse<{ status: string; message: string }>> {
    return this.handleRequest(
      this.axiosInstance.post('/admin/ml/retrain')
    )
  }

  // Script Integration APIs
  async generateScriptToken(websiteId: string): Promise<ApiResponse<{ token: string; expires: string }>> {
    return this.handleRequest(
      this.axiosInstance.post(`/admin/scripts/tokens/${websiteId}`)
    )
  }

  async getScriptTokenInfo(websiteId: string): Promise<ApiResponse<{ token_info: any }>> {
    return this.handleRequest(
      this.axiosInstance.get(`/admin/scripts/tokens/${websiteId}`)
    )
  }

  async deleteScriptToken(websiteId: string): Promise<ApiResponse<{}>> {
    return this.handleRequest(
      this.axiosInstance.delete(`/admin/scripts/tokens/${websiteId}`)
    )
  }

  // Export APIs
  async exportData(format: 'csv' | 'json' | 'excel', dataType: 'logs' | 'analytics' | 'websites', timeRange?: string): Promise<ApiResponse<{ download_url: string }>> {
    const params = new URLSearchParams({
      format,
      type: dataType,
      ...(timeRange && { timeRange })
    })
    
    return this.handleRequest(
      this.axiosInstance.get(`/admin/export?${params}`)
    )
  }

  // Real-time APIs
  async getRealtimeStats(): Promise<ApiResponse<{ activeConnections: number; requestsPerMinute: number; averageResponseTime: number }>> {
    return this.handleRequest(
      this.axiosInstance.get('/admin/realtime/stats')
    )
  }

  // Configuration APIs
  async getApiConfig(): Promise<ApiResponse<any>> {
    return this.handleRequest(
      this.axiosInstance.get('/admin/config/api')
    )
  }

  async updateApiConfig(config: any): Promise<ApiResponse<any>> {
    return this.handleRequest(
      this.axiosInstance.put('/admin/config/api', config)
    )
  }
}

// Export singleton instance
export const apiService = new ApiService()
export default apiService