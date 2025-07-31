<template>
  <div class="mb-8">
    <div class="sm:flex sm:items-center sm:justify-between">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
          Dashboard
        </h1>
        <p class="text-gray-600 dark:text-gray-400 mt-2">
          Monitor your passive CAPTCHA protection across all websites
        </p>
      </div>
      
      <div class="mt-4 sm:mt-0 flex items-center space-x-3">
        <!-- Time Range Selector -->
        <TimeRangeSelector 
          v-model="selectedTimeRange" 
          @update:modelValue="handleTimeRangeChange"
        />
        
        <!-- Refresh Button -->
        <button
          @click="handleRefresh"
          :disabled="isLoading"
          class="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ArrowPathIcon 
            :class="[
              'h-4 w-4 mr-2',
              isLoading ? 'animate-spin' : ''
            ]" 
          />
          {{ isLoading ? 'Refreshing...' : 'Refresh' }}
        </button>
      </div>
    </div>
    
    <!-- Quick Stats Summary -->
    <div class="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-4">
      <div class="text-center">
        <div class="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
          {{ formatNumber(stats.totalVerifications) }}
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400">
          Total Verifications
        </div>
      </div>
      
      <div class="text-center">
        <div class="text-2xl font-bold text-green-600 dark:text-green-400">
          {{ stats.humanRate }}%
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400">
          Human Rate
        </div>
      </div>
      
      <div class="text-center">
        <div class="text-2xl font-bold text-orange-600 dark:text-orange-400">
          {{ stats.avgConfidence }}%
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400">
          Avg Confidence
        </div>
      </div>
      
      <div class="text-center">
        <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">
          {{ stats.avgResponseTime }}ms
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400">
          Response Time
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowPathIcon } from '@heroicons/vue/24/outline'
import { useDashboardStore } from '../_stores/useDashboard'
import { useDashboardData } from '../_composables/useDashboardData'
import TimeRangeSelector from '@/components/common/TimeRangeSelector.vue'

// Stores and composables
const dashboardStore = useDashboardStore()
const { selectedTimeRange, refreshDashboard, handleTimeRangeChange } = useDashboardData()

// Computed
const stats = computed(() => dashboardStore.stats)
const isLoading = computed(() => dashboardStore.isLoading)

// Methods
const handleRefresh = async () => {
  await refreshDashboard()
}

const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}
</script>

<style scoped>
/* Dashboard header animations */
.grid > div {
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Responsive adjustments */
@media (max-width: 640px) {
  .text-3xl {
    font-size: 1.875rem;
    line-height: 2.25rem;
  }
  
  .grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
  }
}
</style>