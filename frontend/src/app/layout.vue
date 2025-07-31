<template>
  <div id="app" class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Main Router View -->
    <RouterView />
    
    <!-- Global Loading Indicator -->
    <LoadingOverlay v-if="isLoading" />
    
    <!-- Toast Notifications -->
    <div id="notifications" class="fixed top-4 right-4 z-50 space-y-2">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        :class="[
          'p-4 rounded-lg shadow-lg border max-w-sm transform transition-all duration-300',
          getNotificationClasses(notification.type)
        ]"
      >
        <div class="flex items-start space-x-3">
          <component :is="getNotificationIcon(notification.type)" class="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div class="flex-1">
            <h4 class="font-medium">{{ notification.title }}</h4>
            <p class="text-sm mt-1">{{ notification.message }}</p>
          </div>
          <button @click="removeNotification(notification.id)" class="text-gray-400 hover:text-gray-600">
            <XMarkIcon class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'
import LoadingOverlay from '@/components/ui/LoadingOverlay.vue'
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  XCircleIcon, 
  InformationCircleIcon,
  XMarkIcon 
} from '@heroicons/vue/24/outline'

// Store
const appStore = useAppStore()

// Computed
const isLoading = computed(() => appStore.isLoading)
const notifications = computed(() => appStore.notifications)

// Methods
const getNotificationClasses = (type: string) => {
  switch (type) {
    case 'success':
      return 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900/20 dark:border-green-800 dark:text-green-200'
    case 'error':
      return 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-800 dark:text-red-200'
    case 'warning':
      return 'bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-900/20 dark:border-yellow-800 dark:text-yellow-200'
    default:
      return 'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900/20 dark:border-blue-800 dark:text-blue-200'
  }
}

const getNotificationIcon = (type: string) => {
  switch (type) {
    case 'success':
      return CheckCircleIcon
    case 'error':
      return XCircleIcon
    case 'warning':
      return ExclamationTriangleIcon
    default:
      return InformationCircleIcon
  }
}

const removeNotification = (id: string) => {
  appStore.removeNotification(id)
}
</script>

<style>
/* Global styles */
#app {
  font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  @apply bg-gray-100 dark:bg-gray-800;
}

::-webkit-scrollbar-thumb {
  @apply bg-gray-300 dark:bg-gray-600 rounded-full;
}

::-webkit-scrollbar-thumb:hover {
  @apply bg-gray-400 dark:bg-gray-500;
}

/* Custom scrollbar for Firefox */
* {
  scrollbar-width: thin;
  scrollbar-color: theme('colors.gray.300') theme('colors.gray.100');
}

@media (prefers-color-scheme: dark) {
  * {
    scrollbar-color: theme('colors.gray.600') theme('colors.gray.800');
  }
}

/* Focus ring improvements */
:focus {
  outline: 2px solid theme('colors.primary.500');
  outline-offset: 2px;
}

/* Smooth transitions */
* {
  transition-property: color, background-color, border-color, text-decoration-color, fill, stroke;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}
</style>