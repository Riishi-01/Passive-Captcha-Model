<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          Performance Trend
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Precision & recall over time
        </p>
      </div>
      
      <select
        :value="timeRange"
        @change="$emit('timeRangeChange', ($event.target as HTMLSelectElement).value)"
        class="text-sm border border-gray-300 dark:border-gray-600 rounded-md px-3 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
      >
        <option value="24h">Last 24 Hours</option>
        <option value="7d">Last 7 Days</option>
        <option value="30d">Last 30 Days</option>
      </select>
    </div>

    <!-- Chart Area -->
    <div class="relative h-48 mb-4">
      <!-- Chart Grid Lines -->
      <div class="absolute inset-0 flex flex-col justify-between">
        <div v-for="i in 5" :key="i" class="w-full h-px bg-gray-200 dark:bg-gray-600"></div>
      </div>
      
      <!-- Y-axis Labels -->
      <div class="absolute left-0 inset-y-0 flex flex-col justify-between text-[10px] text-gray-500 dark:text-gray-400 -ml-8">
        <span>100%</span>
        <span>75%</span>
        <span>50%</span>
        <span>25%</span>
        <span>0%</span>
      </div>
      
      <!-- Chart Lines -->
      <div class="relative h-full ml-4 mr-2">
        <svg class="w-full h-full" viewBox="0 0 300 160" preserveAspectRatio="none">
          <!-- Precision Line -->
          <polyline
            :points="precisionPoints"
            fill="none"
            stroke="#8b5cf6"
            stroke-width="2"
            class="transition-all duration-1000"
          />
          
          <!-- Recall Line -->
          <polyline
            :points="recallPoints"
            fill="none"
            stroke="#06b6d4"
            stroke-width="2"
            class="transition-all duration-1000"
          />
          
          <!-- Data Points -->
          <circle
            v-for="(point, index) in precisionPointsArray"
            :key="`precision-${index}`"
            :cx="point.x"
            :cy="point.y"
            r="3"
            fill="#8b5cf6"
            class="transition-all duration-300 hover:r-5"
          />
          
          <circle
            v-for="(point, index) in recallPointsArray"
            :key="`recall-${index}`"
            :cx="point.x"
            :cy="point.y"
            r="3"
            fill="#06b6d4"
            class="transition-all duration-300 hover:r-5"
          />
        </svg>
      </div>
      
      <!-- X-axis Labels -->
      <div class="flex justify-between text-[10px] text-gray-500 dark:text-gray-400 mt-2 ml-4 mr-2">
        <span v-for="label in data.labels" :key="label" class="truncate">{{ label }}</span>
      </div>
    </div>

    <!-- Legend and Current Values -->
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-6">
        <div class="flex items-center space-x-2">
          <div class="w-3 h-3 bg-purple-500 rounded-full"></div>
          <span class="text-sm text-gray-600 dark:text-gray-400">Precision</span>
          <span class="text-sm font-semibold text-gray-900 dark:text-white">
            {{ currentPrecision }}%
          </span>
        </div>
        
        <div class="flex items-center space-x-2">
          <div class="w-3 h-3 bg-cyan-500 rounded-full"></div>
          <span class="text-sm text-gray-600 dark:text-gray-400">Recall</span>
          <span class="text-sm font-semibold text-gray-900 dark:text-white">
            {{ currentRecall }}%
          </span>
        </div>
      </div>
      
      <!-- Trend Indicators -->
      <div class="flex items-center space-x-4">
        <div class="flex items-center space-x-1">
          <component
            :is="precisionTrend > 0 ? 'ArrowUpIcon' : precisionTrend < 0 ? 'ArrowDownIcon' : 'MinusIcon'"
            :class="[
              'h-4 w-4',
              precisionTrend > 0 ? 'text-green-500' : 
              precisionTrend < 0 ? 'text-red-500' : 'text-gray-400'
            ]"
          />
          <span :class="[
            'text-xs font-medium',
            precisionTrend > 0 ? 'text-green-600 dark:text-green-400' : 
            precisionTrend < 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-500'
          ]">
            {{ Math.abs(precisionTrend).toFixed(1) }}%
          </span>
        </div>
        
        <div class="flex items-center space-x-1">
          <component
            :is="recallTrend > 0 ? 'ArrowUpIcon' : recallTrend < 0 ? 'ArrowDownIcon' : 'MinusIcon'"
            :class="[
              'h-4 w-4',
              recallTrend > 0 ? 'text-green-500' : 
              recallTrend < 0 ? 'text-red-500' : 'text-gray-400'
            ]"
          />
          <span :class="[
            'text-xs font-medium',
            recallTrend > 0 ? 'text-green-600 dark:text-green-400' : 
            recallTrend < 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-500'
          ]">
            {{ Math.abs(recallTrend).toFixed(1) }}%
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowUpIcon, ArrowDownIcon, MinusIcon } from '@heroicons/vue/24/outline'

interface Props {
  data: {
    labels: string[]
    datasets: {
      label: string
      data: number[]
      borderColor: string
      backgroundColor: string
    }[]
  }
  timeRange: string
}

const props = defineProps<Props>()

defineEmits<{
  timeRangeChange: [value: string]
}>()

// Computed values
const precisionData = computed(() => props.data.datasets[0]?.data || [])
const recallData = computed(() => props.data.datasets[1]?.data || [])

const currentPrecision = computed(() => {
  const data = precisionData.value
  return data[data.length - 1] || 0
})

const currentRecall = computed(() => {
  const data = recallData.value
  return data[data.length - 1] || 0
})

const precisionTrend = computed(() => {
  const data = precisionData.value
  if (data.length < 2) return 0
  return data[data.length - 1] - data[data.length - 2]
})

const recallTrend = computed(() => {
  const data = recallData.value
  if (data.length < 2) return 0
  return data[data.length - 1] - data[data.length - 2]
})

// SVG path generation
const precisionPoints = computed(() => {
  const data = precisionData.value
  const width = 300
  const height = 160
  
  return data.map((value, index) => {
    const x = (index / (data.length - 1)) * width
    const y = height - (value / 100) * height
    return `${x},${y}`
  }).join(' ')
})

const recallPoints = computed(() => {
  const data = recallData.value
  const width = 300
  const height = 160
  
  return data.map((value, index) => {
    const x = (index / (data.length - 1)) * width
    const y = height - (value / 100) * height
    return `${x},${y}`
  }).join(' ')
})

const precisionPointsArray = computed(() => {
  const data = precisionData.value
  const width = 300
  const height = 160
  
  return data.map((value, index) => ({
    x: (index / (data.length - 1)) * width,
    y: height - (value / 100) * height
  }))
})

const recallPointsArray = computed(() => {
  const data = recallData.value
  const width = 300
  const height = 160
  
  return data.map((value, index) => ({
    x: (index / (data.length - 1)) * width,
    y: height - (value / 100) * height
  }))
})
</script>

<style scoped>
/* Chart animations */
polyline {
  stroke-dasharray: 1000;
  stroke-dashoffset: 1000;
  animation: drawLine 2s ease-out forwards;
}

@keyframes drawLine {
  to {
    stroke-dashoffset: 0;
  }
}

/* Point hover effects */
circle:hover {
  filter: drop-shadow(0 0 8px currentColor);
}
</style>