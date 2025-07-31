<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center space-x-3">
        <div class="p-2 bg-indigo-100 dark:bg-indigo-900/20 rounded-lg">
          <CpuChipIcon class="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
        </div>
        <div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            ML Model Health Status
          </h3>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            Real-time model performance monitoring
          </p>
        </div>
      </div>
      
      <div class="flex items-center space-x-2">
        <div 
          :class="[
            'w-3 h-3 rounded-full',
            health.status === 'healthy' ? 'bg-green-400 animate-pulse' :
            health.status === 'warning' ? 'bg-yellow-400' : 'bg-red-400'
          ]"
        ></div>
        <span :class="[
          'text-sm font-medium capitalize',
          health.status === 'healthy' ? 'text-green-600 dark:text-green-400' :
          health.status === 'warning' ? 'text-yellow-600 dark:text-yellow-400' : 'text-red-600 dark:text-red-400'
        ]">
          {{ health.status }}
        </span>
      </div>
    </div>

    <!-- Model Info Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
      <!-- Model Version & Accuracy -->
      <div class="space-y-4">
        <div>
          <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Model Version</div>
          <div class="flex items-center space-x-2">
            <span class="text-lg font-semibold text-gray-900 dark:text-white">{{ health.version }}</span>
            <span class="px-2 py-1 bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-400 rounded-full text-xs font-medium">
              Latest
            </span>
          </div>
        </div>
        
        <div>
          <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Model Accuracy</div>
          <div class="flex items-center space-x-3">
            <div class="flex-1 h-3 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
              <div 
                :class="[
                  'h-full rounded-full transition-all duration-1000',
                  health.accuracy >= 95 ? 'bg-green-500' :
                  health.accuracy >= 90 ? 'bg-blue-500' :
                  health.accuracy >= 80 ? 'bg-yellow-500' : 'bg-red-500'
                ]"
                :style="{ width: `${health.accuracy}%` }"
              ></div>
            </div>
            <span class="text-sm font-semibold text-gray-900 dark:text-white">
              {{ health.accuracy }}%
            </span>
          </div>
        </div>
      </div>

      <!-- Performance Metrics -->
      <div class="space-y-4">
        <div>
          <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Response Latency</div>
          <div class="flex items-center space-x-2">
            <span class="text-lg font-semibold text-gray-900 dark:text-white">{{ health.latency }}ms</span>
            <span :class="[
              'text-xs px-2 py-1 rounded-full',
              health.latency <= 50 ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' :
              health.latency <= 100 ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400' :
              'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
            ]">
              {{ health.latency <= 50 ? 'Excellent' : health.latency <= 100 ? 'Good' : 'Slow' }}
            </span>
          </div>
        </div>
        
        <div>
          <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">System Uptime</div>
          <div class="flex items-center space-x-3">
            <div class="flex-1 h-3 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
              <div 
                class="h-full bg-green-500 rounded-full transition-all duration-1000"
                :style="{ width: `${health.uptime}%` }"
              ></div>
            </div>
            <span class="text-sm font-semibold text-gray-900 dark:text-white">
              {{ health.uptime }}%
            </span>
          </div>
        </div>
      </div>

      <!-- Training Schedule -->
      <div class="space-y-4">
        <div>
          <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Last Training</div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ formatDate(health.lastTraining) }}
          </div>
        </div>
        
        <div>
          <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Next Retraining</div>
          <div class="flex items-center space-x-2">
            <span class="text-sm text-gray-600 dark:text-gray-400">
              {{ formatDate(health.nextRetraining) }}
            </span>
            <span class="text-xs text-gray-500 dark:text-gray-500">
              ({{ daysUntilRetraining }} days)
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Model Status Alerts -->
    <div v-if="statusAlerts.length > 0" class="space-y-3 mb-6">
      <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300">Status Alerts</h4>
      <div 
        v-for="alert in statusAlerts" 
        :key="alert.id"
        :class="[
          'p-3 rounded-lg border-l-4 flex items-start space-x-3',
          alert.type === 'warning' ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-400' :
          alert.type === 'error' ? 'bg-red-50 dark:bg-red-900/20 border-red-400' :
          'bg-blue-50 dark:bg-blue-900/20 border-blue-400'
        ]"
      >
        <component
          :is="getAlertIcon(alert.type)"
          :class="[
            'h-5 w-5 mt-0.5 flex-shrink-0',
            alert.type === 'warning' ? 'text-yellow-600 dark:text-yellow-400' :
            alert.type === 'error' ? 'text-red-600 dark:text-red-400' :
            'text-blue-600 dark:text-blue-400'
          ]"
        />
        <div class="flex-1">
          <div :class="[
            'text-sm font-medium',
            alert.type === 'warning' ? 'text-yellow-800 dark:text-yellow-200' :
            alert.type === 'error' ? 'text-red-800 dark:text-red-200' :
            'text-blue-800 dark:text-blue-200'
          ]">
            {{ alert.title }}
          </div>
          <div :class="[
            'text-xs mt-1',
            alert.type === 'warning' ? 'text-yellow-700 dark:text-yellow-300' :
            alert.type === 'error' ? 'text-red-700 dark:text-red-300' :
            'text-blue-700 dark:text-blue-300'
          ]">
            {{ alert.message }}
          </div>
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400">
          {{ formatRelativeTime(alert.timestamp) }}
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
      <div class="text-xs text-gray-500 dark:text-gray-400">
        Last updated: {{ formatRelativeTime(lastUpdated) }}
      </div>
      
      <div class="flex items-center space-x-3">
        <button
          @click="refreshModelStatus"
          class="text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 transition-colors"
        >
          Refresh Status
        </button>
        
        <button
          @click="triggerRetraining"
          class="px-3 py-1 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md transition-colors"
        >
          Trigger Retraining
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { 
  CpuChipIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  InformationCircleIcon
} from '@heroicons/vue/24/outline'

interface Props {
  health: {
    status: 'healthy' | 'warning' | 'error'
    version: string
    accuracy: number
    latency: number
    uptime: number
    lastTraining: string
    nextRetraining: string
  }
  lastUpdated: string
}

const props = defineProps<Props>()

// Sample alerts based on model health
const statusAlerts = ref([
  {
    id: 1,
    type: 'info' as const,
    title: 'Model Performance',
    message: 'Model accuracy is within expected range (98.7%)',
    timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString()
  }
])

// Add alerts based on health status
if (props.health.latency > 100) {
  statusAlerts.value.push({
    id: 2,
    type: 'warning' as const,
    title: 'High Latency Detected',
    message: `Response time is ${props.health.latency}ms (above 100ms threshold)`,
    timestamp: new Date(Date.now() - 2 * 60 * 1000).toISOString()
  })
}

if (props.health.accuracy < 95) {
  statusAlerts.value.push({
    id: 3,
    type: 'warning' as const,
    title: 'Accuracy Below Threshold',
    message: `Model accuracy is ${props.health.accuracy}% (below 95% threshold)`,
    timestamp: new Date(Date.now() - 10 * 60 * 1000).toISOString()
  })
}

// Computed
const daysUntilRetraining = computed(() => {
  const nextRetraining = new Date(props.health.nextRetraining)
  const now = new Date()
  const diffTime = nextRetraining.getTime() - now.getTime()
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  return Math.max(0, diffDays)
})

// Methods
const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const formatRelativeTime = (dateString: string): string => {
  const now = new Date()
  const date = new Date(dateString)
  const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
  
  if (diffInMinutes < 1) return 'Just now'
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`
  if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`
  return `${Math.floor(diffInMinutes / 1440)}d ago`
}

const getAlertIcon = (type: string) => {
  switch (type) {
    case 'warning': return ExclamationTriangleIcon
    case 'error': return XCircleIcon
    default: return InformationCircleIcon
  }
}

const refreshModelStatus = () => {
  console.log('Refreshing model status...')
  // Implement refresh functionality
}

const triggerRetraining = () => {
  console.log('Triggering model retraining...')
  // Implement retraining functionality
}
</script>

<style scoped>
/* Health status animations */
.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* Progress bar animations */
.transition-all {
  animation-delay: 0.5s;
}
</style>