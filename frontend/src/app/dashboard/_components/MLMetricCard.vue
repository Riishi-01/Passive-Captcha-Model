<template>
  <div 
    class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-all duration-300 group"
  >
    <div class="flex items-start justify-between">
      <div class="flex-1">
        <!-- Header -->
        <div class="flex items-center space-x-3 mb-4">
          <div 
            :class="[
              'p-3 rounded-xl transition-all duration-300 group-hover:scale-110',
              iconColorClasses
            ]"
          >
            <component 
              :is="iconComponent" 
              class="h-6 w-6 text-white"
            />
          </div>
          
          <div class="flex-1">
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400">
              {{ title }}
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-500 mt-1">
              {{ description }}
            </p>
          </div>
        </div>
        
        <!-- Value -->
        <div class="mb-3">
          <p class="text-3xl font-bold text-gray-900 dark:text-white">
            {{ formattedValue }}
          </p>
        </div>
        
        <!-- Change Indicator -->
        <div v-if="change !== undefined" class="flex items-center justify-between">
          <div class="flex items-center">
            <component 
              :is="changeIcon" 
              :class="[
                'h-4 w-4 mr-1',
                changeColorClass
              ]"
            />
            <span 
              :class="[
                'text-sm font-medium',
                changeColorClass
              ]"
            >
              {{ Math.abs(change) }}%
            </span>
            <span class="text-xs text-gray-500 dark:text-gray-400 ml-1">
              vs last period
            </span>
          </div>
        </div>
      </div>

      <!-- ML Confidence Indicator -->
      <div v-if="trend" class="ml-4 flex flex-col items-end">
        <div class="text-right mb-2">
          <div class="text-xs text-gray-500 dark:text-gray-400">Trend</div>
          <div class="flex items-center space-x-1">
            <component 
              :is="trendDirection === 'up' ? 'ArrowUpIcon' : trendDirection === 'down' ? 'ArrowDownIcon' : 'MinusIcon'" 
              :class="[
                'h-3 w-3',
                trendDirection === 'up' ? 'text-green-500' : 
                trendDirection === 'down' ? 'text-red-500' : 'text-gray-400'
              ]"
            />
            <span class="text-xs font-medium text-gray-600 dark:text-gray-300">
              {{ trendPercentage }}%
            </span>
          </div>
        </div>
        
        <!-- Mini Model Confidence Bar -->
        <div class="w-16 h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
          <div 
            :class="[
              'h-full rounded-full transition-all duration-1000',
              confidenceBarColor
            ]"
            :style="{ width: `${modelConfidence}%` }"
          ></div>
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {{ modelConfidence }}% confident
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { 
  ShieldCheckIcon,
  UserGroupIcon,
  ExclamationTriangleIcon,
  ChartBarIcon,
  CpuChipIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  MinusIcon
} from '@heroicons/vue/24/outline'

interface Props {
  title: string
  value: string | number
  change?: number
  icon: 'shield-check' | 'user-group' | 'exclamation-triangle' | 'chart-bar' | 'cpu-chip'
  color: 'purple' | 'green' | 'red' | 'blue' | 'indigo'
  trend?: number[]
  description: string
}

const props = defineProps<Props>()

// Icon mapping
const iconMap = {
  'shield-check': ShieldCheckIcon,
  'user-group': UserGroupIcon,
  'exclamation-triangle': ExclamationTriangleIcon,
  'chart-bar': ChartBarIcon,
  'cpu-chip': CpuChipIcon
}

// Color classes mapping
const colorMap = {
  purple: 'bg-purple-600',
  green: 'bg-green-600',
  red: 'bg-red-600',
  blue: 'bg-blue-600',
  indigo: 'bg-indigo-600'
}

// Computed
const iconComponent = computed(() => iconMap[props.icon])
const iconColorClasses = computed(() => colorMap[props.color])

const formattedValue = computed(() => {
  if (typeof props.value === 'number') {
    if (props.value >= 1000000) {
      return (props.value / 1000000).toFixed(1) + 'M'
    } else if (props.value >= 1000) {
      return (props.value / 1000).toFixed(1) + 'K'
    }
    return props.value.toLocaleString()
  }
  return props.value
})

const changeIcon = computed(() => {
  if (props.change === undefined) return MinusIcon
  if (props.change > 0) return ArrowUpIcon
  if (props.change < 0) return ArrowDownIcon
  return MinusIcon
})

const changeColorClass = computed(() => {
  if (props.change === undefined) return 'text-gray-500'
  if (props.change > 0) return 'text-green-600 dark:text-green-400'
  if (props.change < 0) return 'text-red-600 dark:text-red-400'
  return 'text-gray-500'
})

const trendDirection = computed(() => {
  if (!props.trend || props.trend.length < 2) return 'neutral'
  const first = props.trend[0]
  const last = props.trend[props.trend.length - 1]
  if (last > first) return 'up'
  if (last < first) return 'down'
  return 'neutral'
})

const trendPercentage = computed(() => {
  if (!props.trend || props.trend.length < 2) return 0
  const first = props.trend[0]
  const last = props.trend[props.trend.length - 1]
  if (first === 0) return 0
  return Math.abs(((last - first) / first) * 100).toFixed(1)
})

// Model confidence simulation based on trend and value
const modelConfidence = computed(() => {
  // Extract percentage from value if it's a percentage string
  const numericValue = typeof props.value === 'string' && props.value.includes('%') 
    ? parseFloat(props.value.replace('%', ''))
    : typeof props.value === 'number' 
    ? props.value 
    : 90

  // Calculate confidence based on stability and value
  const baseConfidence = Math.min(numericValue, 100)
  const stabilityBonus = props.trend && props.trend.length > 0 
    ? 100 - (Math.max(...props.trend) - Math.min(...props.trend)) 
    : 0
  
  return Math.min(Math.max((baseConfidence + stabilityBonus) / 2, 60), 98)
})

const confidenceBarColor = computed(() => {
  if (modelConfidence.value >= 90) return 'bg-green-500'
  if (modelConfidence.value >= 75) return 'bg-yellow-500'
  return 'bg-red-500'
})
</script>

<style scoped>
/* ML Metric card animations */
.group:hover .transition-all {
  transform: scale(1.02);
}

/* Confidence bar animation */
.h-full {
  animation: fillBar 2s ease-out;
}

@keyframes fillBar {
  from {
    width: 0%;
  }
  to {
    width: var(--final-width);
  }
}
</style>