<template>
  <div class="space-y-3">
    <!-- Loading State -->
    <div v-if="loading" class="space-y-3">
      <div v-for="i in 3" :key="i" class="animate-pulse">
        <div class="flex items-center space-x-3 p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
          <div class="w-3 h-3 bg-gray-300 dark:bg-gray-600 rounded-full"></div>
          <div class="flex-1 space-y-1">
            <div class="h-4 bg-gray-300 dark:bg-gray-600 rounded w-3/4"></div>
            <div class="h-3 bg-gray-300 dark:bg-gray-600 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Website List -->
    <div v-else-if="websites.length > 0" class="space-y-2">
      <div
        v-for="website in displayedWebsites"
        :key="website.id"
        class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors duration-200 cursor-pointer"
        @click="$emit('select', website)"
      >
        <div class="flex items-center space-x-3 min-w-0 flex-1">
          <!-- Status Indicator -->
          <div
            :class="[
              'w-3 h-3 rounded-full flex-shrink-0',
              getStatusColor(website.status)
            ]"
          ></div>
          
          <!-- Website Info -->
          <div class="min-w-0 flex-1">
            <div class="text-sm font-medium text-gray-900 dark:text-white truncate">
              {{ website.name }}
            </div>
            <div class="text-xs text-gray-600 dark:text-gray-400 truncate">
              {{ website.domain }}
            </div>
          </div>
        </div>

        <!-- Stats -->
        <div class="text-right flex-shrink-0 ml-3">
          <div class="text-sm font-semibold text-gray-900 dark:text-white">
            {{ website.totalVerifications.toLocaleString() }}
          </div>
          <div class="text-xs text-gray-600 dark:text-gray-400">
            {{ website.humanRate }}% human
          </div>
        </div>
      </div>

      <!-- Show More Button -->
      <div v-if="websites.length > limit && !showAll" class="text-center">
        <button
          @click="showAll = true"
          class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium"
        >
          Show {{ websites.length - limit }} more websites
        </button>
      </div>

      <!-- Show Less Button -->
      <div v-if="showAll && websites.length > limit" class="text-center">
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
      <GlobeIcon class="w-12 h-12 mx-auto text-gray-400 mb-3" />
      <p class="text-sm text-gray-600 dark:text-gray-400">
        No active websites found
      </p>
      <p class="text-xs text-gray-500 dark:text-gray-500 mt-1">
        Websites will appear here once they start using the CAPTCHA system
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { GlobeIcon } from 'lucide-vue-next'
import type { Website } from '@/stores/websites'

interface Props {
  websites: Website[]
  loading?: boolean
  limit?: number
}

interface Emits {
  select: [website: Website]
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  limit: 5
})

defineEmits<Emits>()

// State
const showAll = ref(false)

// Computed
const displayedWebsites = computed(() => {
  if (showAll.value || props.websites.length <= props.limit) {
    return props.websites
  }
  return props.websites.slice(0, props.limit)
})

// Methods
const getStatusColor = (status: string) => {
  switch (status) {
    case 'active':
      return 'bg-green-500'
    case 'inactive':
      return 'bg-gray-400'
    case 'error':
      return 'bg-red-500'
    default:
      return 'bg-gray-400'
  }
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

/* Hover effects */
.cursor-pointer:hover {
  transform: translateX(2px);
}

/* Status indicator pulse */
.bg-green-500 {
  animation: statusPulse 2s infinite;
}

@keyframes statusPulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

/* Button hover effects */
button {
  transition: all 0.2s ease;
}

button:hover {
  transform: translateY(-1px);
}

/* Responsive adjustments */
@media (max-width: 640px) {
  .flex.items-center.justify-between {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
    justify-content: flex-start;
  }
  
  .text-right {
    text-align: left;
    width: 100%;
  }
  
  .ml-3 {
    margin-left: 0;
  }
}

/* Dark mode transitions */
.dark * {
  transition: background-color 0.2s ease, color 0.2s ease;
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  .animate-pulse,
  .bg-green-500,
  button,
  .cursor-pointer {
    animation: none !important;
    transition: none !important;
    transform: none !important;
  }
}
</style>