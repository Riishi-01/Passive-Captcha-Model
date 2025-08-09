import { useState } from 'react'
import { useAppStore } from '../stores/app'
import { 
  Save, 
  RefreshCw, 
  Shield, 
  Globe, 
  Bell, 
  Database,
  Key,
  Server,
  AlertTriangle 
} from 'lucide-react'

export default function SettingsView() {
  const { addNotification } = useAppStore()
  const [saving, setSaving] = useState(false)
  
  const [settings, setSettings] = useState({
    // System Settings
    systemName: 'Passive CAPTCHA System',
    adminEmail: 'admin@example.com',
    timezone: 'UTC',
    logLevel: 'info',
    
    // Security Settings
    sessionTimeout: 60,
    maxLoginAttempts: 3,
    passwordRequirements: {
      minLength: 8,
      requireUppercase: true,
      requireLowercase: true,
      requireNumbers: true,
      requireSpecialChars: true
    },
    
    // ML Model Settings
    confidenceThreshold: 0.85,
    retrainInterval: 168, // hours
    autoRetrain: true,
    modelVersion: 'v2.3.1',
    
    // API Settings
    rateLimitRequests: 1000,
    rateLimitWindow: 60, // minutes
    apiTimeout: 30, // seconds
    enableCors: true,
    
    // Alert Settings
    alertEmail: true,
    alertThresholds: {
      highBotActivity: 50,
      lowAccuracy: 94,
      systemError: true
    },
    
    // Monitoring Settings
    enableMetrics: true,
    metricsRetention: 90, // days
    enableHealthChecks: true,
    healthCheckInterval: 5 // minutes
  })

  const handleInputChange = (section, field, value) => {
    if (section) {
      setSettings(prev => ({
        ...prev,
        [section]: {
          ...prev[section],
          [field]: value
        }
      }))
    } else {
      setSettings(prev => ({
        ...prev,
        [field]: value
      }))
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      addNotification({
        type: 'success',
        message: 'Settings saved successfully'
      })
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to save settings'
      })
    } finally {
      setSaving(false)
    }
  }

  const resetToDefaults = () => {
    if (window.confirm('Are you sure you want to reset all settings to defaults?')) {
      // Reset logic would go here
      addNotification({
        type: 'success',
        message: 'Settings reset to defaults'
      })
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Configure system settings and preferences
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={resetToDefaults}
            className="btn btn-secondary flex items-center"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Reset Defaults
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="btn btn-primary flex items-center"
          >
            <Save className="h-4 w-4 mr-2" />
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Settings */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Server className="h-5 w-5 text-gray-500 mr-2" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              System Settings
            </h3>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                System Name
              </label>
              <input
                type="text"
                value={settings.systemName}
                onChange={(e) => handleInputChange(null, 'systemName', e.target.value)}
                className="input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Admin Email
              </label>
              <input
                type="email"
                value={settings.adminEmail}
                onChange={(e) => handleInputChange(null, 'adminEmail', e.target.value)}
                className="input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Timezone
              </label>
              <select
                value={settings.timezone}
                onChange={(e) => handleInputChange(null, 'timezone', e.target.value)}
                className="input"
              >
                <option value="UTC">UTC</option>
                <option value="America/New_York">Eastern Time</option>
                <option value="America/Chicago">Central Time</option>
                <option value="America/Denver">Mountain Time</option>
                <option value="America/Los_Angeles">Pacific Time</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Log Level
              </label>
              <select
                value={settings.logLevel}
                onChange={(e) => handleInputChange(null, 'logLevel', e.target.value)}
                className="input"
              >
                <option value="debug">Debug</option>
                <option value="info">Info</option>
                <option value="warning">Warning</option>
                <option value="error">Error</option>
              </select>
            </div>
          </div>
        </div>

        {/* Security Settings */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Shield className="h-5 w-5 text-gray-500 mr-2" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Security Settings
            </h3>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Session Timeout (minutes)
              </label>
              <input
                type="number"
                value={settings.sessionTimeout}
                onChange={(e) => handleInputChange(null, 'sessionTimeout', parseInt(e.target.value))}
                className="input"
                min="5"
                max="480"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Max Login Attempts
              </label>
              <input
                type="number"
                value={settings.maxLoginAttempts}
                onChange={(e) => handleInputChange(null, 'maxLoginAttempts', parseInt(e.target.value))}
                className="input"
                min="1"
                max="10"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Password Requirements
              </label>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={settings.passwordRequirements.requireUppercase}
                    onChange={(e) => handleInputChange('passwordRequirements', 'requireUppercase', e.target.checked)}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Require uppercase letters</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={settings.passwordRequirements.requireNumbers}
                    onChange={(e) => handleInputChange('passwordRequirements', 'requireNumbers', e.target.checked)}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Require numbers</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={settings.passwordRequirements.requireSpecialChars}
                    onChange={(e) => handleInputChange('passwordRequirements', 'requireSpecialChars', e.target.checked)}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Require special characters</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* ML Model Settings */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Database className="h-5 w-5 text-gray-500 mr-2" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              ML Model Settings
            </h3>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Confidence Threshold
              </label>
              <input
                type="number"
                step="0.01"
                min="0.5"
                max="1.0"
                value={settings.confidenceThreshold}
                onChange={(e) => handleInputChange(null, 'confidenceThreshold', parseFloat(e.target.value))}
                className="input"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Minimum confidence score to classify as bot (0.5 - 1.0)
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Retrain Interval (hours)
              </label>
              <input
                type="number"
                value={settings.retrainInterval}
                onChange={(e) => handleInputChange(null, 'retrainInterval', parseInt(e.target.value))}
                className="input"
                min="24"
                max="8760"
              />
            </div>
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.autoRetrain}
                  onChange={(e) => handleInputChange(null, 'autoRetrain', e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Enable automatic retraining</span>
              </label>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Current Model Version
              </label>
              <input
                type="text"
                value={settings.modelVersion}
                disabled
                className="input bg-gray-50 dark:bg-gray-700"
              />
            </div>
          </div>
        </div>

        {/* API Settings */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Key className="h-5 w-5 text-gray-500 mr-2" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              API Settings
            </h3>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Rate Limit (requests per window)
              </label>
              <input
                type="number"
                value={settings.rateLimitRequests}
                onChange={(e) => handleInputChange(null, 'rateLimitRequests', parseInt(e.target.value))}
                className="input"
                min="100"
                max="10000"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Rate Limit Window (minutes)
              </label>
              <input
                type="number"
                value={settings.rateLimitWindow}
                onChange={(e) => handleInputChange(null, 'rateLimitWindow', parseInt(e.target.value))}
                className="input"
                min="1"
                max="1440"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                API Timeout (seconds)
              </label>
              <input
                type="number"
                value={settings.apiTimeout}
                onChange={(e) => handleInputChange(null, 'apiTimeout', parseInt(e.target.value))}
                className="input"
                min="5"
                max="300"
              />
            </div>
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.enableCors}
                  onChange={(e) => handleInputChange(null, 'enableCors', e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Enable CORS</span>
              </label>
            </div>
          </div>
        </div>

        {/* Alert Settings */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Bell className="h-5 w-5 text-gray-500 mr-2" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Alert Settings
            </h3>
          </div>
          <div className="space-y-4">
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.alertEmail}
                  onChange={(e) => handleInputChange(null, 'alertEmail', e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Enable email alerts</span>
              </label>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                High Bot Activity Threshold (%)
              </label>
              <input
                type="number"
                value={settings.alertThresholds.highBotActivity}
                onChange={(e) => handleInputChange('alertThresholds', 'highBotActivity', parseInt(e.target.value))}
                className="input"
                min="10"
                max="100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Low Accuracy Threshold (%)
              </label>
              <input
                type="number"
                value={settings.alertThresholds.lowAccuracy}
                onChange={(e) => handleInputChange('alertThresholds', 'lowAccuracy', parseInt(e.target.value))}
                className="input"
                min="70"
                max="99"
              />
            </div>
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.alertThresholds.systemError}
                  onChange={(e) => handleInputChange('alertThresholds', 'systemError', e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Alert on system errors</span>
              </label>
            </div>
          </div>
        </div>

        {/* Monitoring Settings */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <Globe className="h-5 w-5 text-gray-500 mr-2" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Monitoring Settings
            </h3>
          </div>
          <div className="space-y-4">
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.enableMetrics}
                  onChange={(e) => handleInputChange(null, 'enableMetrics', e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Enable metrics collection</span>
              </label>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Metrics Retention (days)
              </label>
              <input
                type="number"
                value={settings.metricsRetention}
                onChange={(e) => handleInputChange(null, 'metricsRetention', parseInt(e.target.value))}
                className="input"
                min="7"
                max="365"
              />
            </div>
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.enableHealthChecks}
                  onChange={(e) => handleInputChange(null, 'enableHealthChecks', e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Enable health checks</span>
              </label>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Health Check Interval (minutes)
              </label>
              <input
                type="number"
                value={settings.healthCheckInterval}
                onChange={(e) => handleInputChange(null, 'healthCheckInterval', parseInt(e.target.value))}
                className="input"
                min="1"
                max="60"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Warning Section */}
      <div className="card p-6 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800">
        <div className="flex items-start">
          <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mr-3 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
              Important Notice
            </h3>
            <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
              Changes to security and ML model settings may affect system performance. 
              Please review all changes carefully before saving.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
