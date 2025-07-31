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
          
          <div>
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400">
              {{ title }}
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

      <!-- Trend Indicator (Simple) -->
      <div v-if="trend" class="ml-4 flex items-center">
        <div class="text-right">
          <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Trend</div>
          <div class="flex items-center space-x-1">
            <component 
              :is="trendDirection === 'up' ? 'ArrowUpIcon' : trendDirection === 'down' ? 'ArrowDownIcon' : 'MinusIcon'" 
              :class="[
                'h-4 w-4',
                trendDirection === 'up' ? 'text-green-500' : 
                trendDirection === 'down' ? 'text-red-500' : 'text-gray-400'
              ]"
            />
            <span class="text-xs font-medium text-gray-600 dark:text-gray-300">
              {{ trendPercentage }}%
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { 
  ShieldCheckIcon,
  UserIcon,
  ChartBarIcon,
  ClockIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  MinusIcon
} from '@heroicons/vue/24/outline'

interface Props {
  title: string
  value: string | number
  change?: number
  icon: 'shield-check' | 'user-check' | 'chart-bar' | 'clock'
  color: 'indigo' | 'green' | 'orange' | 'blue'
  trend?: number[]
}

const props = defineProps<Props>()

// Icon mapping
const iconMap = {
  'shield-check': ShieldCheckIcon,
  'user-check': UserIcon,
  'chart-bar': ChartBarIcon,
  'clock': ClockIcon
}

// Color classes mapping
const colorMap = {
  indigo: 'bg-indigo-600',
  green: 'bg-green-600',
  orange: 'bg-orange-600',
  blue: 'bg-blue-600'
}

const trendColorMap = {
  indigo: 'bg-indigo-200 dark:bg-indigo-400',
  green: 'bg-green-200 dark:bg-green-400',
  orange: 'bg-orange-200 dark:bg-orange-400',
  blue: 'bg-blue-200 dark:bg-blue-400'
}

// Computed
const iconComponent = computed(() => iconMap[props.icon])
const iconColorClasses = computed(() => colorMap[props.color])
const trendColorClass = computed(() => trendColorMap[props.color])

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
</script>

<style scoped>
/* KPI Card hover effects */
.bg-white:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.15);
}

.dark .bg-white:hover {
  box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.3);
}

/* Responsive adjustments */
@media (max-width: 640px) {
  .text-3xl {
    font-size: 1.5rem;
    line-height: 2rem;
  }
  
  .p-6 {
    padding: 1rem;
  }
}
</style>