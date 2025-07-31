<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          Verification Success/Failure Trends
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Real-time verification outcomes over time
        </p>
      </div>
      
      <div class="flex items-center space-x-4">
        <select
          :value="timeRange"
          @change="$emit('timeRangeChange', ($event.target as HTMLSelectElement).value)"
          class="text-sm border border-gray-300 dark:border-gray-600 rounded-md px-3 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
        >
          <option value="1h">Last Hour</option>
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
        </select>
      </div>
    </div>

    <!-- Chart Area -->
    <div class="relative h-64 mb-6">
      <!-- Chart Background -->
      <div class="absolute inset-0 bg-gradient-to-t from-gray-50 to-transparent dark:from-gray-700/20 rounded-lg"></div>
      
      <!-- Grid Lines -->
      <div class="absolute inset-0 flex flex-col justify-between">
        <div v-for="i in 6" :key="i" class="w-full h-px bg-gray-200 dark:bg-gray-600 opacity-50"></div>
      </div>
      
      <!-- Y-axis Labels -->
      <div class="absolute left-0 inset-y-0 flex flex-col justify-between text-xs text-gray-500 dark:text-gray-400 -ml-8">
        <span>{{ maxValue }}</span>
        <span>{{ Math.round(maxValue * 0.8) }}</span>
        <span>{{ Math.round(maxValue * 0.6) }}</span>
        <span>{{ Math.round(maxValue * 0.4) }}</span>
        <span>{{ Math.round(maxValue * 0.2) }}</span>
        <span>0</span>
      </div>
      
      <!-- Chart Bars -->
      <div class="relative h-full ml-4 mr-2 flex items-end justify-between space-x-1">
        <div 
          v-for="(label, index) in data.labels"
          :key="label"
          class="flex flex-col items-center space-y-1 flex-1"
        >
          <!-- Success Bar -->
          <div class="relative w-full flex flex-col items-end">
            <div 
              class="w-full bg-green-500 rounded-t transition-all duration-1000 hover:bg-green-600"
              :style="{ 
                height: `${(successData[index] / maxValue) * 100}%`,
                animationDelay: `${index * 0.1}s`
              }"
            ></div>
            
            <!-- Success Value -->
            <div v-if="successData[index] > 0" class="absolute -top-6 text-xs font-medium text-green-700 dark:text-green-400">
              {{ formatNumber(successData[index]) }}
            </div>
          </div>
          
          <!-- Failure Bar (stacked below) -->
          <div class="relative w-full">
            <div 
              class="w-full bg-red-500 rounded-b transition-all duration-1000 hover:bg-red-600"
              :style="{ 
                height: `${(failureData[index] / maxValue) * 100}%`,
                animationDelay: `${index * 0.1 + 0.5}s`
              }"
            ></div>
            
            <!-- Failure Value -->
            <div v-if="failureData[index] > 0" class="absolute -bottom-6 text-xs font-medium text-red-700 dark:text-red-400">
              {{ formatNumber(failureData[index]) }}
            </div>
          </div>
        </div>
      </div>
      
      <!-- X-axis Labels -->
      <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-4 ml-4 mr-2">
        <span v-for="label in data.labels" :key="label">{{ label }}</span>
      </div>
    </div>

    <!-- Summary Statistics -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
      <div class="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
        <div class="text-xl font-bold text-green-700 dark:text-green-400">
          {{ formatNumber(totalSuccessful) }}
        </div>
        <div class="text-xs text-green-600 dark:text-green-500">
          Total Successful
        </div>
      </div>
      
      <div class="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
        <div class="text-xl font-bold text-red-700 dark:text-red-400">
          {{ formatNumber(totalFailed) }}
        </div>
        <div class="text-xs text-red-600 dark:text-red-500">
          Total Failed
        </div>
      </div>
      
      <div class="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <div class="text-xl font-bold text-blue-700 dark:text-blue-400">
          {{ successRate }}%
        </div>
        <div class="text-xs text-blue-600 dark:text-blue-500">
          Success Rate
        </div>
      </div>
      
      <div class="text-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
        <div class="text-xl font-bold text-purple-700 dark:text-purple-400">
          {{ avgResponseTime }}ms
        </div>
        <div class="text-xs text-purple-600 dark:text-purple-500">
          Avg Response Time
        </div>
      </div>
    </div>

    <!-- Legend -->
    <div class="flex items-center justify-center space-x-6">
      <div class="flex items-center space-x-2">
        <div class="w-3 h-3 bg-green-500 rounded"></div>
        <span class="text-sm text-gray-600 dark:text-gray-400">Successful Verifications</span>
      </div>
      
      <div class="flex items-center space-x-2">
        <div class="w-3 h-3 bg-red-500 rounded"></div>
        <span class="text-sm text-gray-600 dark:text-gray-400">Failed Verifications</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  data: {
    labels: string[]
    datasets: {
      label: string
      data: number[]
      borderColor: string
      backgroundColor: string
      fill: boolean
    }[]
  }
  timeRange: string
}

const props = defineProps<Props>()

defineEmits<{
  timeRangeChange: [value: string]
}>()

// Computed values
const successData = computed(() => props.data.datasets[0]?.data || [])
const failureData = computed(() => props.data.datasets[1]?.data || [])

const maxValue = computed(() => {
  const allValues = [...successData.value, ...failureData.value]
  return Math.max(...allValues, 100) // Ensure minimum scale
})

const totalSuccessful = computed(() => {
  return successData.value.reduce((sum, value) => sum + value, 0)
})

const totalFailed = computed(() => {
  return failureData.value.reduce((sum, value) => sum + value, 0)
})

const successRate = computed(() => {
  const total = totalSuccessful.value + totalFailed.value
  return total > 0 ? Math.round((totalSuccessful.value / total) * 100) : 0
})

const avgResponseTime = computed(() => {
  // Simulated response time based on verification volume
  const totalVerifications = totalSuccessful.value + totalFailed.value
  const baseTime = 45
  const loadFactor = Math.min(totalVerifications / 1000, 2) // Max 2x increase
  return Math.round(baseTime * (1 + loadFactor * 0.5))
})

// Methods
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
/* Bar animations */
.transition-all {
  animation: growBar 1s ease-out forwards;
}

@keyframes growBar {
  from {
    height: 0% !important;
  }
}

/* Staggered animation for bars */
.transition-all:nth-child(odd) {
  animation-delay: 0.1s;
}

.transition-all:nth-child(even) {
  animation-delay: 0.2s;
}
</style>