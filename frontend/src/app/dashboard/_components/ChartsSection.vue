<template>
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- Verification Trends Chart -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          Verification Trends
        </h3>
        <TimeRangeSelector 
          v-model="selectedTimeRange" 
          @update:modelValue="handleTimeRangeChange"
        />
      </div>
      <div class="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">
        Chart placeholder - Chart.js integration coming soon
      </div>
    </div>

    <!-- Detection Analytics -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Detection Analytics
      </h3>
      <div class="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">
        Pie chart placeholder - Chart.js integration coming soon
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useDashboardData } from '../_composables/useDashboardData'
import TimeRangeSelector from '@/components/common/TimeRangeSelector.vue'

// Composables
const { selectedTimeRange, handleTimeRangeChange } = useDashboardData()
</script>