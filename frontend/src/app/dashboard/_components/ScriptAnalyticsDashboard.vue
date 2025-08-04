<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
          Script Analytics
        </h2>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Monitor and analyze your Passive CAPTCHA script performance
        </p>
      </div>
      <div class="flex items-center space-x-3">
        <!-- Time Range Selector -->
        <select
          v-model="selectedTimeRange"
          @change="loadAnalytics"
          class="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
        >
          <option value="1h">Last Hour</option>
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
        </select>
        
        <!-- Refresh Button -->
        <button
          @click="loadAnalytics"
          :disabled="isLoading"
          class="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
        >
          <ArrowPathIcon class="h-4 w-4" :class="{ 'animate-spin': isLoading }" />
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading && !analytics" class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-indigo-500 border-t-transparent"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
      <div class="flex">
        <ExclamationTriangleIcon class="h-5 w-5 text-red-400 flex-shrink-0" />
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800 dark:text-red-200">Error loading analytics</h3>
          <p class="text-sm text-red-700 dark:text-red-300 mt-1">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Analytics Content -->
    <div v-else-if="analytics" class="space-y-6">
      <!-- Overview Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-4">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <ChartBarIcon class="h-8 w-8 text-blue-500" />
            </div>
            <div class="ml-4">
              <div class="text-2xl font-bold text-gray-900 dark:text-white">
                {{ formatNumber(analytics.overview.total_verifications) }}
              </div>
              <div class="text-sm text-gray-500 dark:text-gray-400">Total Verifications</div>
            </div>
          </div>
        </div>

        <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-4">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <UserIcon class="h-8 w-8 text-green-500" />
            </div>
            <div class="ml-4">
              <div class="text-2xl font-bold text-gray-900 dark:text-white">
                {{ analytics.overview.human_rate }}%
              </div>
              <div class="text-sm text-gray-500 dark:text-gray-400">Human Rate</div>
            </div>
          </div>
        </div>

        <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-4">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <ClockIcon class="h-8 w-8 text-yellow-500" />
            </div>
            <div class="ml-4">
              <div class="text-2xl font-bold text-gray-900 dark:text-white">
                {{ analytics.overview.average_response_time }}ms
              </div>
              <div class="text-sm text-gray-500 dark:text-gray-400">Avg Response Time</div>
            </div>
          </div>
        </div>

        <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-4">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <ShieldCheckIcon class="h-8 w-8 text-purple-500" />
            </div>
            <div class="ml-4">
              <div class="text-2xl font-bold text-gray-900 dark:text-white">
                {{ (analytics.overview.average_confidence * 100).toFixed(1) }}%
              </div>
              <div class="text-sm text-gray-500 dark:text-gray-400">Avg Confidence</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Script Performance -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div class="p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 class="text-lg font-medium text-gray-900 dark:text-white">Script Performance</h3>
        </div>
        <div class="p-4">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="space-y-2">
              <div class="text-sm font-medium text-gray-700 dark:text-gray-300">Integration Status</div>
              <div class="flex items-center space-x-2">
                <div 
                  :class="[
                    'w-3 h-3 rounded-full',
                    analytics.script_performance.integration_status === 'active' ? 'bg-green-500' : 'bg-red-500'
                  ]"
                ></div>
                <span class="text-sm text-gray-900 dark:text-white capitalize">
                  {{ analytics.script_performance.integration_status }}
                </span>
              </div>
            </div>
            
            <div class="space-y-2">
              <div class="text-sm font-medium text-gray-700 dark:text-gray-300">Script Version</div>
              <div class="text-sm text-gray-900 dark:text-white">
                {{ analytics.script_performance.script_version }}
              </div>
            </div>
            
            <div class="space-y-2">
              <div class="text-sm font-medium text-gray-700 dark:text-gray-300">Uptime</div>
              <div class="text-sm text-gray-900 dark:text-white">
                {{ analytics.script_performance.uptime_percentage }}%
              </div>
            </div>
            
            <div class="space-y-2">
              <div class="text-sm font-medium text-gray-700 dark:text-gray-300">Total Requests</div>
              <div class="text-sm text-gray-900 dark:text-white">
                {{ formatNumber(analytics.script_performance.total_requests) }}
              </div>
            </div>
            
            <div class="space-y-2">
              <div class="text-sm font-medium text-gray-700 dark:text-gray-300">Last Used</div>
              <div class="text-sm text-gray-900 dark:text-white">
                {{ formatDate(analytics.script_performance.last_used) }}
              </div>
            </div>
            
            <div class="space-y-2">
              <div class="text-sm font-medium text-gray-700 dark:text-gray-300">Performance Score</div>
              <div class="flex items-center space-x-2">
                <div class="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div 
                    class="h-2 rounded-full transition-all duration-300"
                    :class="getPerformanceScoreColor(analytics.integration_health.performance_score)"
                    :style="{ width: `${analytics.integration_health.performance_score}%` }"
                  ></div>
                </div>
                <span class="text-sm text-gray-900 dark:text-white">
                  {{ analytics.integration_health.performance_score }}/100
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Verification Trends Chart -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div class="p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 class="text-lg font-medium text-gray-900 dark:text-white">Verification Trends</h3>
        </div>
        <div class="p-4">
          <div v-if="analytics.time_series && analytics.time_series.length > 0" class="h-64">
            <!-- Chart would go here - for now showing data in table format -->
            <div class="space-y-2">
              <div class="text-sm text-gray-500 dark:text-gray-400 mb-4">Hourly verification data</div>
              <div class="max-h-48 overflow-y-auto">
                <table class="min-w-full text-xs">
                  <thead class="bg-gray-50 dark:bg-gray-900">
                    <tr>
                      <th class="px-3 py-2 text-left text-gray-500 dark:text-gray-400">Time</th>
                      <th class="px-3 py-2 text-left text-gray-500 dark:text-gray-400">Total</th>
                      <th class="px-3 py-2 text-left text-gray-500 dark:text-gray-400">Human</th>
                      <th class="px-3 py-2 text-left text-gray-500 dark:text-gray-400">Bot</th>
                      <th class="px-3 py-2 text-left text-gray-500 dark:text-gray-400">Confidence</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                    <tr v-for="point in analytics.time_series" :key="point.timestamp" class="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td class="px-3 py-2 text-gray-900 dark:text-white">{{ formatTime(point.timestamp) }}</td>
                      <td class="px-3 py-2 text-gray-900 dark:text-white">{{ point.total_verifications }}</td>
                      <td class="px-3 py-2 text-green-600 dark:text-green-400">{{ point.human_verifications }}</td>
                      <td class="px-3 py-2 text-red-600 dark:text-red-400">{{ point.bot_verifications }}</td>
                      <td class="px-3 py-2 text-gray-900 dark:text-white">{{ (point.average_confidence * 100).toFixed(1) }}%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-8 text-gray-500 dark:text-gray-400">
            No verification data available for the selected time range
          </div>
        </div>
      </div>

      <!-- Configuration & Optimization -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Current Configuration -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
          <div class="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">Current Configuration</h3>
          </div>
          <div class="p-4 space-y-3">
            <div v-for="(value, key) in analytics.configuration.current_config" :key="key" class="flex justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400 capitalize">
                {{ key.replace(/_/g, ' ') }}
              </span>
              <span class="text-sm text-gray-900 dark:text-white">
                {{ formatConfigValue(value) }}
              </span>
            </div>
          </div>
        </div>

        <!-- Optimization Suggestions -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
          <div class="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">Optimization Suggestions</h3>
          </div>
          <div class="p-4">
            <div v-if="analytics.configuration.optimization_suggestions.length > 0" class="space-y-3">
              <div 
                v-for="suggestion in analytics.configuration.optimization_suggestions" 
                :key="suggestion.title"
                :class="[
                  'p-3 rounded-lg border',
                  suggestion.type === 'warning' ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800' :
                  suggestion.type === 'info' ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800' :
                  'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                ]"
              >
                <div class="flex items-start">
                  <ExclamationTriangleIcon 
                    v-if="suggestion.type === 'warning'"
                    class="h-5 w-5 text-yellow-400 flex-shrink-0 mt-0.5"
                  />
                  <InformationCircleIcon 
                    v-else-if="suggestion.type === 'info'"
                    class="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5"
                  />
                  <CheckCircleIcon 
                    v-else
                    class="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5"
                  />
                  <div class="ml-3">
                    <h4 class="text-sm font-medium" :class="[
                      suggestion.type === 'warning' ? 'text-yellow-800 dark:text-yellow-200' :
                      suggestion.type === 'info' ? 'text-blue-800 dark:text-blue-200' :
                      'text-green-800 dark:text-green-200'
                    ]">
                      {{ suggestion.title }}
                    </h4>
                    <p class="text-xs mt-1" :class="[
                      suggestion.type === 'warning' ? 'text-yellow-700 dark:text-yellow-300' :
                      suggestion.type === 'info' ? 'text-blue-700 dark:text-blue-300' :
                      'text-green-700 dark:text-green-300'
                    ]">
                      {{ suggestion.description }}
                    </p>
                    <button class="text-xs font-medium mt-2 underline" :class="[
                      suggestion.type === 'warning' ? 'text-yellow-800 dark:text-yellow-200' :
                      suggestion.type === 'info' ? 'text-blue-800 dark:text-blue-200' :
                      'text-green-800 dark:text-green-200'
                    ]">
                      {{ suggestion.action }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="text-center py-4 text-gray-500 dark:text-gray-400">
              <CheckCircleIcon class="h-8 w-8 mx-auto mb-2 text-green-500" />
              <div class="text-sm">Configuration is optimized</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Real-time Status -->
      <div v-if="realtimeData" class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div class="p-4 border-b border-gray-200 dark:border-gray-700">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">Real-time Status</h3>
            <div class="flex items-center space-x-2">
              <div 
                :class="[
                  'w-2 h-2 rounded-full',
                  realtimeData.status === 'active' ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
                ]"
              ></div>
              <span class="text-sm text-gray-500 dark:text-gray-400 capitalize">{{ realtimeData.status }}</span>
            </div>
          </div>
        </div>
        <div class="p-4">
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="text-center">
              <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ realtimeData.active_sessions }}</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">Active Sessions</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ realtimeData.verifications_per_minute.toFixed(1) }}</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">Verifications/min</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ (realtimeData.current_load * 100).toFixed(0) }}%</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">Current Load</div>
            </div>
            <div class="text-center">
              <div class="text-sm text-gray-900 dark:text-white">{{ formatDate(realtimeData.last_activity) }}</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">Last Activity</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { 
  ArrowPathIcon, 
  ExclamationTriangleIcon, 
  ChartBarIcon,
  UserIcon,
  ClockIcon,
  ShieldCheckIcon,
  CheckCircleIcon,
  InformationCircleIcon
} from '@heroicons/vue/24/outline'
import { apiService } from '@/services/api'

interface Props {
  websiteId: string
}

const props = defineProps<Props>()

// State
const selectedTimeRange = ref('24h')
const isLoading = ref(false)
const error = ref('')
const analytics = ref<any>(null)
const realtimeData = ref<any>(null)
const realtimeInterval = ref<number | null>(null)

// Methods
const loadAnalytics = async () => {
  isLoading.value = true
  error.value = ''

  try {
    const response = await apiService.getScriptAnalytics(props.websiteId, selectedTimeRange.value)
    
    if (response.success) {
      analytics.value = response.data
    } else {
      throw new Error(response.error?.message || 'Failed to load analytics')
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to load analytics'
  } finally {
    isLoading.value = false
  }
}

const loadRealtimeData = async () => {
  try {
    const response = await apiService.getRealtimeScriptAnalytics(props.websiteId)
    
    if (response.success) {
      realtimeData.value = response.data
    }
  } catch (err) {
    // Silently fail for realtime data
    console.warn('Failed to load realtime data:', err)
  }
}

const startRealtimeUpdates = () => {
  // Load realtime data immediately
  loadRealtimeData()
  
  // Set up interval for updates
  realtimeInterval.value = window.setInterval(loadRealtimeData, 30000) // Update every 30 seconds
}

const stopRealtimeUpdates = () => {
  if (realtimeInterval.value) {
    clearInterval(realtimeInterval.value)
    realtimeInterval.value = null
  }
}

// Utility functions
const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

const formatDate = (dateString: string | null): string => {
  if (!dateString) return 'Never'
  
  const date = new Date(dateString)
  const now = new Date()
  const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
  
  if (diffInMinutes < 1) return 'Just now'
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`
  if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`
  
  return date.toLocaleDateString()
}

const formatTime = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
}

const formatConfigValue = (value: any): string => {
  if (typeof value === 'boolean') {
    return value ? 'Enabled' : 'Disabled'
  }
  if (typeof value === 'number') {
    return value.toString()
  }
  return String(value)
}

const getPerformanceScoreColor = (score: number): string => {
  if (score >= 90) return 'bg-green-500'
  if (score >= 70) return 'bg-yellow-500'
  return 'bg-red-500'
}

// Lifecycle
onMounted(() => {
  loadAnalytics()
  startRealtimeUpdates()
})

onUnmounted(() => {
  stopRealtimeUpdates()
})
</script>

<style scoped>
/* Custom animations */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>