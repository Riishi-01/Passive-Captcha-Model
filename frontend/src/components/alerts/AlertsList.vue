<template>
  <div class="space-y-3">
    <!-- Loading State -->
    <div v-if="loading" class="space-y-3">
      <div v-for="i in 3" :key="i" class="animate-pulse">
        <div class="flex items-start space-x-3 p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
          <div class="w-2 h-2 bg-gray-300 dark:bg-gray-600 rounded-full mt-2"></div>
          <div class="flex-1 space-y-2">
            <div class="h-4 bg-gray-300 dark:bg-gray-600 rounded w-3/4"></div>
            <div class="h-3 bg-gray-300 dark:bg-gray-600 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Alerts List -->
    <div v-else-if="alerts.length > 0" class="space-y-2">
      <div
        v-for="alert in displayedAlerts"
        :key="alert.id"
        :class="[
          'flex items-start space-x-3 p-3 rounded-lg border cursor-pointer transition-all duration-200',
          alert.isRead ? 
            'bg-gray-50 dark:bg-gray-700 border-gray-200 dark:border-gray-600' :
            'bg-white dark:bg-gray-800 border-blue-200 dark:border-blue-700 shadow-sm',
          'hover:shadow-md hover:border-blue-300 dark:hover:border-blue-600'
        ]"
        @click="markAsRead(alert)"
      >
        <!-- Alert Type Indicator -->
        <div
          :class="[
            'w-2 h-2 rounded-full mt-2 flex-shrink-0',
            getAlertColor(alert.type)
          ]"
        ></div>
        
        <!-- Alert Content -->
        <div class="flex-1 min-w-0">
          <div class="flex items-start justify-between">
            <div class="min-w-0 flex-1">
              <h4 
                :class="[
                  'text-sm font-medium truncate',
                  alert.isRead ? 
                    'text-gray-700 dark:text-gray-300' : 
                    'text-gray-900 dark:text-white'
                ]"
              >
                {{ alert.title }}
              </h4>
              <p 
                :class="[
                  'text-sm mt-1',
                  alert.isRead ? 
                    'text-gray-500 dark:text-gray-400' : 
                    'text-gray-600 dark:text-gray-300'
                ]"
              >
                {{ alert.message }}
              </p>
            </div>
            
            <!-- Unread Indicator -->
            <div v-if="!alert.isRead" class="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 ml-2 mt-1"></div>
          </div>
          
          <!-- Timestamp -->
          <div class="flex items-center justify-between mt-2">
            <span class="text-xs text-gray-500 dark:text-gray-400">
              {{ formatTime(alert.timestamp) }}
            </span>
            
            <!-- Alert Type Badge -->
            <span 
              :class="[
                'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
                getAlertBadgeClass(alert.type)
              ]"
            >
              {{ alert.type }}
            </span>
          </div>
        </div>
      </div>

      <!-- Show More Button -->
      <div v-if="alerts.length > limit && !showAll" class="text-center">
        <button
          @click="showAll = true"
          class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium"
        >
          Show {{ alerts.length - limit }} more alerts
        </button>
      </div>

      <!-- Show Less Button -->
      <div v-if="showAll && alerts.length > limit" class="text-center">
        <button
          @click="showAll = false"
          class="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 font-medium"
        >
          Show less
        </button>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-8">
      <AlertTriangleIcon class="w-12 h-12 mx-auto text-gray-400 mb-3" />
      <p class="text-sm text-gray-600 dark:text-gray-400">
        No alerts at this time
      </p>
      <p class="text-xs text-gray-500 dark:text-gray-500 mt-1">
        System alerts and notifications will appear here
      </p>
    </div>

    <!-- Actions -->
    <div v-if="alerts.length > 0" class="pt-3 border-t border-gray-200 dark:border-gray-600">
      <div class="flex space-x-2">
        <button
          @click="markAllAsRead"
          :disabled="!hasUnreadAlerts"
          class="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 disabled:text-gray-400 disabled:cursor-not-allowed font-medium"
        >
          Mark all as read
        </button>
        <span class="text-xs text-gray-400">•</span>
        <button
          @click="clearAll"
          class="text-xs text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 font-medium"
        >
          Clear all
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { AlertTriangleIcon } from 'lucide-vue-next'
import type { Alert } from '@/stores/dashboard'

interface Props {
  alerts: Alert[]
  loading?: boolean
  limit?: number
}

interface Emits {
  'mark-read': [alert: Alert]
  'mark-all-read': []
  'clear-all': []
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  limit: 5
})

const emit = defineEmits<Emits>()

// State
const showAll = ref(false)

// Computed
const displayedAlerts = computed(() => {
  if (showAll.value || props.alerts.length <= props.limit) {
    return props.alerts
  }
  return props.alerts.slice(0, props.limit)
})

const hasUnreadAlerts = computed(() => 
  props.alerts.some(alert => !alert.isRead)
)

// Methods
const getAlertColor = (type: string) => {
  switch (type) {
    case 'error':
      return 'bg-red-500'
    case 'warning':
      return 'bg-yellow-500'
    case 'info':
      return 'bg-blue-500'
    default:
      return 'bg-gray-500'
  }
}

const getAlertBadgeClass = (type: string) => {
  switch (type) {
    case 'error':
      return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
    case 'warning':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
    case 'info':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400'
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
  }
}

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return 'Just now'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
  return `${Math.floor(diff / 86400000)}d ago`
}

const markAsRead = (alert: Alert) => {
  if (!alert.isRead) {
    emit('mark-read', alert)
  }
}

const markAllAsRead = () => {
  emit('mark-all-read')
}

const clearAll = () => {
  emit('clear-all')
}
</script>

<style scoped>
/* Pulse animation for loading */
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

/* Alert indicator pulse */
.bg-red-500,
.bg-yellow-500,
.bg-blue-500 {
  animation: alertPulse 2s infinite;
}

@keyframes alertPulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

/* Hover effects */
.cursor-pointer:hover {
  transform: translateY(-1px);
}

/* Unread indicator pulse */
.bg-blue-500.w-2.h-2 {
  animation: unreadPulse 1.5s infinite;
}

@keyframes unreadPulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}

/* Button hover effects */
button {
  transition: all 0.2s ease;
}

button:hover:not(:disabled) {
  transform: translateY(-1px);
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Badge animations */
.inline-flex {
  transition: all 0.2s ease;
}

/* Responsive adjustments */
@media (max-width: 640px) {
  .flex.items-start.justify-between {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
    justify-content: flex-start;
  }
  
  .flex.items-center.justify-between {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
    justify-content: flex-start;
  }
}

/* Dark mode transitions */
.dark * {
  transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  .animate-pulse,
  .bg-red-500,
  .bg-yellow-500,
  .bg-blue-500,
  button,
  .cursor-pointer,
  .inline-flex {
    animation: none !important;
    transition: none !important;
    transform: none !important;
  }
}

/* Focus states for accessibility */
button:focus,
.cursor-pointer:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}
</style>