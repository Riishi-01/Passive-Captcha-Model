<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          {{ title }}
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {{ subtitle }}
        </p>
      </div>
      
      <!-- Time Range Selector for trend charts -->
      <div v-if="timeRange" class="flex items-center space-x-2">
        <select
          :value="timeRange"
          @change="$emit('timeRangeChange', ($event.target as HTMLSelectElement).value)"
          class="text-sm border border-gray-300 dark:border-gray-600 rounded-md px-3 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        >
          <option value="1h">Last Hour</option>
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
        </select>
      </div>
    </div>

    <!-- Chart Container -->
    <div class="relative">
      <div v-if="type === 'line'" class="h-64">
        <!-- Line Chart Placeholder -->
        <div class="w-full h-full bg-gradient-to-br from-indigo-50 to-blue-50 dark:from-gray-700 dark:to-gray-600 rounded-lg flex items-center justify-center">
          <div class="text-center">
            <svg class="w-16 h-16 mx-auto mb-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <p class="text-sm text-gray-600 dark:text-gray-300 font-medium">{{ title }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Chart.js integration coming soon</p>
          </div>
        </div>
        
        <!-- Sample Data Visualization -->
        <div class="absolute bottom-4 left-4 right-4">
          <div class="flex items-end justify-between space-x-2 h-16">
            <div 
              v-for="(point, index) in sampleData" 
              :key="index"
              class="bg-indigo-500 rounded-t flex-1 transition-all duration-300 hover:bg-indigo-600"
              :style="{ height: `${point}%` }"
            ></div>
          </div>
        </div>
      </div>

      <div v-else-if="type === 'doughnut'" class="h-64">
        <!-- Doughnut Chart Placeholder -->
        <div class="w-full h-full bg-gradient-to-br from-green-50 to-emerald-50 dark:from-gray-700 dark:to-gray-600 rounded-lg flex items-center justify-center">
          <div class="text-center">
            <div class="relative w-32 h-32 mx-auto mb-4">
              <!-- Outer Ring -->
              <div class="absolute inset-0 rounded-full border-8 border-gray-200 dark:border-gray-600"></div>
              <!-- Human Traffic -->
              <div 
                class="absolute inset-0 rounded-full border-8 border-green-500"
                style="
                  clip-path: polygon(50% 50%, 50% 0%, 85.4% 14.6%, 85.4% 85.4%, 50% 50%);
                  transform: rotate(-90deg);
                "
              ></div>
              <!-- Bot Traffic -->
              <div 
                class="absolute inset-0 rounded-full border-8 border-red-500"
                style="
                  clip-path: polygon(50% 50%, 85.4% 85.4%, 50% 100%, 50% 50%);
                  transform: rotate(-90deg);
                "
              ></div>
              <!-- Center Text -->
              <div class="absolute inset-0 flex items-center justify-center">
                <div class="text-center">
                  <div class="text-lg font-bold text-gray-900 dark:text-white">85.7%</div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">Human</div>
                </div>
              </div>
            </div>
            <p class="text-sm text-gray-600 dark:text-gray-300 font-medium">{{ title }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Chart.js integration coming soon</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Legend -->
    <div v-if="data?.datasets" class="mt-4 flex items-center justify-center space-x-6">
      <div 
        v-for="(dataset, index) in data.datasets" 
        :key="index"
        class="flex items-center space-x-2"
      >
        <div 
          class="w-3 h-3 rounded-full"
          :style="{ backgroundColor: dataset.borderColor || dataset.backgroundColor }"
        ></div>
        <span class="text-sm text-gray-600 dark:text-gray-400">{{ dataset.label }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  title: string
  subtitle: string
  data: any
  type: 'line' | 'doughnut'
  timeRange?: string
}

defineProps<Props>()
defineEmits<{
  timeRangeChange: [value: string]
}>()

// Sample data for visualization
const sampleData = computed(() => [20, 35, 25, 55, 45, 65, 60, 70, 50, 75, 80, 85])
</script>

<style scoped>
/* Chart card animations */
.relative {
  animation: fadeIn 0.8s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>