/**
 * WebSocket Service for Real-time Dashboard Updates
 * Handles connection to backend WebSocket server for live data streaming
 */

import { io, Socket } from 'socket.io-client'
import { useAuthStore } from '@/stores/auth'

interface WebSocketConfig {
  url: string
  autoConnect: boolean
  reconnection: boolean
  reconnectionAttempts: number
  reconnectionDelay: number
  timeout: number
}

interface LogEntry {
  id: string
  timestamp: string
  type: string
  level: string
  message: string
  website_id?: string
  ip?: string
  country?: string
  confidence?: number
  response_time?: string
  is_human?: boolean
  user_agent?: string
  metadata?: Record<string, any>
}

interface MetricUpdate {
  metric_type: string
  value: any
  website_id?: string
  timestamp: string
}

interface VerificationEvent {
  id: string
  timestamp: string
  type: 'human' | 'bot'
  ip: string
  country: string
  confidence: number
  user_agent: string
  website: string
}

interface DashboardData {
  website_id: string
  metrics: any
  ml_metrics: any
  timestamp: string
}

class WebSocketService {
  private socket: Socket | null = null
  private config: WebSocketConfig
  private eventListeners: Map<string, Set<Function>> = new Map()
  private isConnected: boolean = false
  private reconnectTimer: NodeJS.Timeout | null = null

  constructor(config?: Partial<WebSocketConfig>) {
    this.config = {
      url: import.meta.env.VITE_WS_URL || 'ws://localhost:5003',
      autoConnect: false,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      timeout: 20000,
      ...config
    }
  }

  /**
   * Connect to WebSocket server
   */
  async connect(): Promise<boolean> {
    try {
      const authStore = useAuthStore()
      
      if (!authStore.token) {
        console.warn('No auth token available for WebSocket connection')
        return false
      }

      if (this.socket) {
        this.disconnect()
      }

      this.socket = io(this.config.url, {
        auth: {
          token: authStore.token
        },
        autoConnect: this.config.autoConnect,
        reconnection: this.config.reconnection,
        reconnectionAttempts: this.config.reconnectionAttempts,
        reconnectionDelay: this.config.reconnectionDelay,
        timeout: this.config.timeout,
        transports: ['websocket', 'polling']
      })

      this.setupEventHandlers()
      
      return new Promise((resolve) => {
        this.socket!.on('connect', () => {
          this.isConnected = true
          console.log('WebSocket connected successfully')
          this.emit('connection_status', { connected: true })
          resolve(true)
        })

        this.socket!.on('connect_error', (error) => {
          console.error('WebSocket connection error:', error)
          this.isConnected = false
          this.emit('connection_status', { connected: false, error: error.message })
          resolve(false)
        })

        // Timeout fallback
        setTimeout(() => {
          if (!this.isConnected) {
            resolve(false)
          }
        }, this.config.timeout)
      })

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      return false
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
    this.isConnected = false
    this.eventListeners.clear()
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    
    console.log('WebSocket disconnected')
    this.emit('connection_status', { connected: false })
  }

  /**
   * Setup WebSocket event handlers
   */
  private setupEventHandlers(): void {
    if (!this.socket) return

    // Connection events
    this.socket.on('disconnect', (reason) => {
      this.isConnected = false
      console.log('WebSocket disconnected:', reason)
      this.emit('connection_status', { connected: false, reason })
      
      // Attempt reconnection for certain disconnect reasons
      if (reason === 'io server disconnect') {
        this.scheduleReconnect()
      }
    })

    this.socket.on('reconnect', (attemptNumber) => {
      this.isConnected = true
      console.log(`WebSocket reconnected after ${attemptNumber} attempts`)
      this.emit('connection_status', { connected: true, reconnected: true })
    })

    this.socket.on('reconnect_error', (error) => {
      console.error('WebSocket reconnection error:', error)
      this.emit('connection_status', { connected: false, error: error.message })
    })

    // Application events
    this.socket.on('connection_established', (data) => {
      console.log('WebSocket connection established:', data)
      this.emit('connection_established', data)
    })

    this.socket.on('new_log', (logEntry: LogEntry) => {
      this.emit('new_log', logEntry)
    })

    this.socket.on('new_verification', (verification: VerificationEvent) => {
      this.emit('new_verification', verification)
    })

    this.socket.on('metric_update', (update: MetricUpdate) => {
      this.emit('metric_update', update)
    })

    this.socket.on('dashboard_initial_data', (data: DashboardData) => {
      this.emit('dashboard_initial_data', data)
    })

    this.socket.on('dashboard_update', (data: DashboardData) => {
      this.emit('dashboard_update', data)
    })

    this.socket.on('system_alert', (alert: any) => {
      this.emit('system_alert', alert)
    })

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error)
      this.emit('error', error)
    })

    this.socket.on('pong', (data) => {
      this.emit('pong', data)
    })
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) return

    this.reconnectTimer = setTimeout(() => {
      console.log('Attempting WebSocket reconnection...')
      this.connect()
      this.reconnectTimer = null
    }, this.config.reconnectionDelay)
  }

  /**
   * Join dashboard room for live updates
   */
  joinDashboardRoom(websiteId: string = 'all'): void {
    if (!this.socket || !this.isConnected) {
      console.warn('Cannot join dashboard room: WebSocket not connected')
      return
    }

    this.socket.emit('join_dashboard_room', {
      website_id: websiteId
    })

    console.log(`Joined dashboard room for website: ${websiteId}`)
  }

  /**
   * Leave dashboard room
   */
  leaveDashboardRoom(websiteId: string = 'all'): void {
    if (!this.socket || !this.isConnected) {
      return
    }

    this.socket.emit('leave_dashboard_room', {
      website_id: websiteId
    })

    console.log(`Left dashboard room for website: ${websiteId}`)
  }

  /**
   * Subscribe to logs with filters
   */
  subscribeLogs(filters: Record<string, any> = {}): void {
    if (!this.socket || !this.isConnected) {
      console.warn('Cannot subscribe to logs: WebSocket not connected')
      return
    }

    this.socket.emit('subscribe_logs', {
      filters
    })

    console.log('Subscribed to logs with filters:', filters)
  }

  /**
   * Unsubscribe from logs
   */
  unsubscribeLogs(): void {
    if (!this.socket || !this.isConnected) {
      return
    }

    this.socket.emit('unsubscribe_logs')
    console.log('Unsubscribed from logs')
  }

  /**
   * Request manual dashboard update
   */
  requestDashboardUpdate(websiteId: string = 'all'): void {
    if (!this.socket || !this.isConnected) {
      console.warn('Cannot request dashboard update: WebSocket not connected')
      return
    }

    this.socket.emit('request_dashboard_update', {
      website_id: websiteId
    })
  }

  /**
   * Send ping to server
   */
  ping(): void {
    if (!this.socket || !this.isConnected) {
      return
    }

    this.socket.emit('ping')
  }

  /**
   * Add event listener
   */
  on(event: string, callback: Function): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, new Set())
    }
    this.eventListeners.get(event)!.add(callback)
  }

  /**
   * Remove event listener
   */
  off(event: string, callback: Function): void {
    if (this.eventListeners.has(event)) {
      this.eventListeners.get(event)!.delete(callback)
    }
  }

  /**
   * Emit event to listeners
   */
  private emit(event: string, data: any): void {
    if (this.eventListeners.has(event)) {
      this.eventListeners.get(event)!.forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          console.error(`Error in WebSocket event listener for ${event}:`, error)
        }
      })
    }
  }

  /**
   * Get connection status
   */
  get connected(): boolean {
    return this.isConnected && this.socket?.connected === true
  }

  /**
   * Get socket instance (for advanced usage)
   */
  get socketInstance(): Socket | null {
    return this.socket
  }
}

// Create singleton instance
export const websocketService = new WebSocketService()

// Export types
export type {
  LogEntry,
  MetricUpdate,
  VerificationEvent,
  DashboardData,
  WebSocketConfig
}