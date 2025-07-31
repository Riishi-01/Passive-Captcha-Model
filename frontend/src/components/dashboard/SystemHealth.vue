<template>
  <div class="space-y-4">
    <!-- Database Health -->
    <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
      <div class="flex items-center space-x-3">
        <div
          :class="[
            'w-3 h-3 rounded-full',
            getStatusColor(health.database.status)
          ]"
        ></div>
        <div>
          <div class="text-sm font-medium text-gray-900 dark:text-white">
            Database
          </div>
          <div class="text-xs text-gray-600 dark:text-gray-400">
            {{ health.database.totalVerifications.toLocaleString() }} total records
          </div>
        </div>
      </div>
      <div class="text-right">
        <div class="text-sm font-semibold text-gray-900 dark:text-white">
          {{ health.database.status }}
        </div>
        <div class="text-xs text-gray-600 dark:text-gray-400">
          {{ health.database.last24hVerifications }} today
        </div>
      </div>
    </div>

    <!-- ML Model Health -->
    <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
      <div class="flex items-center space-x-3">
        <div
          :class="[
            'w-3 h-3 rounded-full',
            getStatusColor(health.model.status)
          ]"
        ></div>
        <div>
          <div class="text-sm font-medium text-gray-900 dark:text-white">
            ML Model
          </div>
          <div class="text-xs text-gray-600 dark:text-gray-400">
            {{ health.model.info.algorithm || 'Random Forest' }}
          </div>
        </div>
      </div>
      <div class="text-right">
        <div class="text-sm font-semibold text-gray-900 dark:text-white">
          {{ health.model.loaded ? 'Loaded' : 'Error' }}
        </div>
        <div v-if="health.model.info.accuracy" class="text-xs text-gray-600 dark:text-gray-400">
          {{ Math.round(health.model.info.accuracy * 100) }}% accuracy
        </div>
      </div>
    </div>

    <!-- API Health -->
    <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
      <div class="flex items-center space-x-3">
        <div
          :class="[
            'w-3 h-3 rounded-full',
            getStatusColor(health.api.status)
          ]"
        ></div>
        <div>
          <div class="text-sm font-medium text-gray-900 dark:text-white">
            API Server
          </div>
          <div class="text-xs text-gray-600 dark:text-gray-400">
            Version {{ health.api.version }}
          </div>
        </div>
      </div>
      <div class="text-right">
        <div class="text-sm font-semibold text-gray-900 dark:text-white">
          {{ health.api.status }}
        </div>
        <div class="text-xs text-gray-600 dark:text-gray-400">
          {{ health.api.uptime }}
        </div>
      </div>
    </div>

    <!-- Overall Status -->
    <div class="border-t border-gray-200 dark:border-gray-600 pt-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <div
            :class="[
              'w-4 h-4 rounded-full',
              overallStatus === 'healthy' ? 'bg-green-500' :
              overallStatus === 'warning' ? 'bg-yellow-500' :
              'bg-red-500'
            ]"
          ></div>
          <span class="text-sm font-medium text-gray-900 dark:text-white">
            Overall System Status
          </span>
        </div>
        <div class="text-right">
          <div 
            :class="[
              'text-sm font-semibold capitalize',
              overallStatus === 'healthy' ? 'text-green-600' :
              overallStatus === 'warning' ? 'text-yellow-600' :
              'text-red-600'
            ]"
          >
            {{ overallStatus }}
          </div>
          <div class="text-xs text-gray-600 dark:text-gray-400">
            Last updated: {{ formatTime(health.timestamp || new Date().toISOString()) }}
          </div>
        </div>
      </div>
    </div>

    <!-- Performance Metrics -->
    <div v-if="showMetrics" class="border-t border-gray-200 dark:border-gray-600 pt-4">
      <h4 class="text-sm font-medium text-gray-900 dark:text-white mb-3">
        Performance Metrics
      </h4>
      
      <div class="grid grid-cols-2 gap-3">
        <!-- Response Time -->
        <div class="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <div class="text-lg font-bold text-blue-600 dark:text-blue-400">
            {{ averageResponseTime }}ms
          </div>
          <div class="text-xs text-gray-600 dark:text-gray-400">
            Avg Response Time
          </div>
        </div>

        <!-- Uptime -->
        <div class="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
          <div class="text-lg font-bold text-green-600 dark:text-green-400">
            {{ uptime }}%
          </div>
          <div class="text-xs text-gray-600 dark:text-gray-400">
            Uptime (24h)
          </div>
        </div>

        <!-- Memory Usage -->
        <div class="text-center p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
          <div class="text-lg font-bold text-yellow-600 dark:text-yellow-400">
            {{ memoryUsage }}%
          </div>
          <div class="text-xs text-gray-600 dark:text-gray-400">
            Memory Usage
          </div>
        </div>

        <!-- CPU Usage -->
        <div class="text-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
          <div class="text-lg font-bold text-purple-600 dark:text-purple-400">
            {{ cpuUsage }}%
          </div>
          <div class="text-xs text-gray-600 dark:text-gray-400">
            CPU Usage
          </div>
        </div>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="flex space-x-2 pt-4">
      <button
        @click="$emit('refresh')"
        class="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors duration-200"
      >
        Refresh Status
      </button>
      <button
        @click="showMetrics = !showMetrics"
        class="px-3 py-2 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 text-sm rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors duration-200"
      >
        {{ showMetrics ? 'Hide' : 'Show' }} Metrics
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { SystemHealth } from '@/stores/dashboard'

interface Props {
  health: SystemHealth
}

const props = defineProps<Props>()

defineEmits<{
  refresh: []
}>()

// State
const showMetrics = ref(false)

// Computed
const overallStatus = computed(() => {
  const { database, model, api } = props.health
  
  if (database.status === 'error' || model.status === 'error' || api.status === 'error') {
    return 'error'
  }
  
  if (database.status === 'warning' || model.status === 'warning' || api.status === 'warning') {
    return 'warning'
  }
  
  if (!model.loaded) {
    return 'error'
  }
  
  return 'healthy'
})

// Mock performance metrics (in a real app, these would come from the backend)
const averageResponseTime = computed(() => {
  // Simulate response time based on system health
  if (overallStatus.value === 'error') return Math.floor(Math.random() * 500) + 500
  if (overallStatus.value === 'warning') return Math.floor(Math.random() * 200) + 200
  return Math.floor(Math.random() * 100) + 50
})

const uptime = computed(() => {
  if (overallStatus.value === 'error') return (95 + Math.random() * 3).toFixed(1)
  if (overallStatus.value === 'warning') return (98 + Math.random() * 1.5).toFixed(1)
  return (99.5 + Math.random() * 0.4).toFixed(1)
})

const memoryUsage = computed(() => {
  return Math.floor(Math.random() * 30) + 45
})

const cpuUsage = computed(() => {
  if (overallStatus.value === 'error') return Math.floor(Math.random() * 40) + 60
  if (overallStatus.value === 'warning') return Math.floor(Math.random() * 30) + 30
  return Math.floor(Math.random() * 25) + 10
})

// Methods
const getStatusColor = (status: string) => {
  switch (status) {
    case 'healthy':
      return 'bg-green-500'
    case 'warning':
      return 'bg-yellow-500'
    case 'error':
      return 'bg-red-500'
    default:
      return 'bg-gray-500'
  }
}

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return 'Just now'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
  return date.toLocaleString()
}
</script>

<style scoped>
/* Status indicator pulse animation */
.bg-green-500,
.bg-yellow-500,
.bg-red-500 {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

/* Hover effects for health items */
.bg-gray-50:hover,
.dark .bg-gray-700:hover {
  transform: translateX(2px);
  transition: transform 0.2s ease;
}

/* Performance metrics grid animations */
.grid > div {
  transition: all 0.2s ease;
}

.grid > div:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Button hover effects */
button {
  transition: all 0.2s ease;
}

button:hover {
  transform: translateY(-1px);
}

button:active {
  transform: translateY(0);
}

/* Loading state for refresh */
button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

/* Dark mode transitions */
.dark * {
  transition: background-color 0.2s ease, color 0.2s ease;
}

/* Responsive adjustments */
@media (max-width: 640px) {
  .grid-cols-2 {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }
  
  .flex.space-x-2 {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .flex.space-x-2 > * + * {
    margin-left: 0;
  }
}
</style>