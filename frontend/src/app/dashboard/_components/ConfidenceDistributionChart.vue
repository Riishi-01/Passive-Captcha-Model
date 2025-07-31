<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          Confidence Distribution
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Model prediction confidence levels
        </p>
      </div>
      
      <div class="flex items-center space-x-2">
        <div class="text-right">
          <div class="text-sm font-semibold text-gray-900 dark:text-white">
            {{ highConfidencePct }}%
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">
            High Confidence
          </div>
        </div>
      </div>
    </div>

    <!-- Chart Visualization -->
    <div class="relative h-48 mb-4">
      <!-- Confidence Bars -->
      <div class="flex items-end justify-center space-x-2 h-full">
        <div 
          v-for="(value, index) in data.datasets[0].data" 
          :key="index"
          class="flex flex-col items-center space-y-2"
        >
          <!-- Bar -->
          <div class="relative w-12 bg-gray-100 dark:bg-gray-700 rounded-t-lg overflow-hidden">
            <div 
              :class="[
                'rounded-t-lg transition-all duration-1000 ease-out',
                getBarColor(index)
              ]"
              :style="{ 
                height: `${(value / Math.max(...data.datasets[0].data)) * 160}px`,
                animationDelay: `${index * 0.1}s`
              }"
            ></div>
            
            <!-- Value Label -->
            <div class="absolute top-1 left-1/2 transform -translate-x-1/2 text-xs font-semibold text-white">
              {{ value }}%
            </div>
          </div>
          
          <!-- Label -->
          <div class="text-xs text-gray-600 dark:text-gray-400 text-center font-medium">
            {{ data.labels[index] }}
          </div>
        </div>
      </div>
    </div>

    <!-- Confidence Insights -->
    <div class="grid grid-cols-2 gap-4">
      <div class="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
        <div class="text-lg font-bold text-green-700 dark:text-green-400">
          {{ reliabilityScore }}%
        </div>
        <div class="text-xs text-green-600 dark:text-green-500">
          Model Reliability
        </div>
      </div>
      
      <div class="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <div class="text-lg font-bold text-blue-700 dark:text-blue-400">
          {{ avgConfidence }}%
        </div>
        <div class="text-xs text-blue-600 dark:text-blue-500">
          Average Confidence
        </div>
      </div>
    </div>

    <!-- Confidence Quality Indicator -->
    <div class="mt-4 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
          Model Certainty Level
        </span>
        <span :class="[
          'text-sm font-semibold',
          certaintyLevel.color
        ]">
          {{ certaintyLevel.label }}
        </span>
      </div>
      
      <!-- Certainty Bar -->
      <div class="w-full h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
        <div 
          :class="[
            'h-full rounded-full transition-all duration-1000',
            certaintyLevel.barColor
          ]"
          :style="{ width: `${certaintyLevel.percentage}%` }"
        ></div>
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
      backgroundColor: string[]
    }[]
  }
}

const props = defineProps<Props>()

// Computed metrics
const highConfidencePct = computed(() => {
  // Sum of 81-100% confidence (last element)
  const data = props.data.datasets[0].data
  return data[data.length - 1] || 0
})

const avgConfidence = computed(() => {
  const data = props.data.datasets[0].data
  const weights = [10, 30, 50, 70, 90] // Midpoints of ranges
  const weightedSum = data.reduce((sum, value, index) => sum + (value * weights[index]), 0)
  const totalSum = data.reduce((sum, value) => sum + value, 0)
  return totalSum > 0 ? Math.round(weightedSum / totalSum) : 0
})

const reliabilityScore = computed(() => {
  // High confidence + medium-high confidence
  const data = props.data.datasets[0].data
  return Math.round((data[3] || 0) + (data[4] || 0))
})

const certaintyLevel = computed(() => {
  const reliability = reliabilityScore.value
  
  if (reliability >= 85) {
    return {
      label: 'Excellent',
      color: 'text-green-600 dark:text-green-400',
      barColor: 'bg-green-500',
      percentage: reliability
    }
  } else if (reliability >= 70) {
    return {
      label: 'Good',
      color: 'text-blue-600 dark:text-blue-400',
      barColor: 'bg-blue-500',
      percentage: reliability
    }
  } else if (reliability >= 50) {
    return {
      label: 'Fair',
      color: 'text-yellow-600 dark:text-yellow-400',
      barColor: 'bg-yellow-500',
      percentage: reliability
    }
  } else {
    return {
      label: 'Poor',
      color: 'text-red-600 dark:text-red-400',
      barColor: 'bg-red-500',
      percentage: reliability
    }
  }
})

// Methods
const getBarColor = (index: number): string => {
  const colors = [
    'bg-red-500',      // 0-20%
    'bg-orange-500',   // 21-40%
    'bg-yellow-500',   // 41-60%
    'bg-blue-500',     // 61-80%
    'bg-green-500'     // 81-100%
  ]
  return colors[index] || 'bg-gray-500'
}
</script>

<style scoped>
/* Bar animation */
.transition-all {
  animation: growBar 1s ease-out forwards;
}

@keyframes growBar {
  from {
    height: 0px;
  }
}

/* Staggered animation for bars */
.transition-all:nth-child(1) { animation-delay: 0.1s; }
.transition-all:nth-child(2) { animation-delay: 0.2s; }
.transition-all:nth-child(3) { animation-delay: 0.3s; }
.transition-all:nth-child(4) { animation-delay: 0.4s; }
.transition-all:nth-child(5) { animation-delay: 0.5s; }
</style>