/**
 * API Configuration
 * Centralized configuration for API endpoints and settings
 */

export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5002'

export const API_ENDPOINTS = {
  ADMIN_LOGIN: '/admin/login',
  ADMIN_LOGOUT: '/admin/logout',
  ADMIN_REFRESH: '/admin/refresh',
  HEALTH: '/health'
} as const

export const API_CONFIG = {
  TIMEOUT: 30000,
  WITH_CREDENTIALS: true
} as const