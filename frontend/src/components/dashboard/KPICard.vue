<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow duration-200">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center space-x-3">
        <div
          :class="[
            'w-10 h-10 rounded-lg flex items-center justify-center',
            iconBackgroundColor
          ]"
        >
          <component :is="iconComponent" class="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 class="text-sm font-medium text-gray-600 dark:text-gray-400">
            {{ title }}
          </h3>
        </div>
      </div>
      
      <!-- Trend Indicator -->
      <div v-if="change !== undefined" class="flex items-center space-x-1">
        <component
          :is="trendIcon"
          :class="[
            'w-4 h-4',
            trendColor
          ]"
        />
        <span
          :class="[
            'text-sm font-medium',
            trendColor
          ]"
        >
          {{ Math.abs(change) }}%
        </span>
      </div>
    </div>

    <!-- Value -->
    <div class="mb-2">
      <div class="text-3xl font-bold text-gray-900 dark:text-white">
        {{ formattedValue }}
      </div>
    </div>

    <!-- Description and trend -->
    <div class="flex items-center justify-between">
      <p class="text-sm text-gray-600 dark:text-gray-400">
        {{ description || 'Last 24 hours' }}
      </p>
      
      <div v-if="change !== undefined" class="text-xs text-gray-500 dark:text-gray-400">
        <span :class="trendColor">
          {{ change > 0 ? '+' : '' }}{{ change }}%
        </span>
        vs previous period
      </div>
    </div>

    <!-- Mini Chart (Optional) -->
    <div v-if="showMiniChart && chartData.length > 0" class="mt-4">
      <div class="h-12 flex items-end space-x-1">
        <div
          v-for="(point, index) in normalizedChartData"
          :key="index"
          :class="[
            'flex-1 bg-opacity-50 rounded-sm transition-all duration-200 hover:bg-opacity-75',
            iconBackgroundColor.replace('bg-', 'bg-opacity-50 bg-')
          ]"
          :style="{ height: `${point}%` }"
        ></div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="absolute inset-0 bg-white dark:bg-gray-800 bg-opacity-75 flex items-center justify-center rounded-lg">
      <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, type Component } from 'vue'
import {
  ShieldCheckIcon,
  UserIcon,
  BarChart3Icon,
  ClockIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  MinusIcon,
  ActivityIcon,
  AlertTriangleIcon
} from 'lucide-vue-next'

interface Props {
  title: string
  value: string | number
  change?: number
  icon: string
  color: 'primary' | 'success' | 'warning' | 'info' | 'danger'
  description?: string
  loading?: boolean
  chartData?: number[]
  showMiniChart?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  chartData: () => [],
  showMiniChart: false
})

// Icon mapping
const iconMap: Record<string, Component> = {
  'shield-check': ShieldCheckIcon,
  'user-check': UserIcon,
  'chart-bar': BarChart3Icon,
  'clock': ClockIcon,
  'activity': ActivityIcon,
  'alert-triangle': AlertTriangleIcon
}

// Color mappings
const colorMap = {
  primary: {
    bg: 'bg-blue-600',
    text: 'text-blue-600'
  },
  success: {
    bg: 'bg-green-600',
    text: 'text-green-600'
  },
  warning: {
    bg: 'bg-yellow-600',
    text: 'text-yellow-600'
  },
  info: {
    bg: 'bg-cyan-600',
    text: 'text-cyan-600'
  },
  danger: {
    bg: 'bg-red-600',
    text: 'text-red-600'
  }
}

// Computed
const iconComponent = computed(() => iconMap[props.icon] || ShieldCheckIcon)

const iconBackgroundColor = computed(() => colorMap[props.color].bg)

const formattedValue = computed(() => {
  if (typeof props.value === 'number') {
    if (props.value >= 1000000) {
      return (props.value / 1000000).toFixed(1) + 'M'
    }
    if (props.value >= 1000) {
      return (props.value / 1000).toFixed(1) + 'K'
    }
    return props.value.toLocaleString()
  }
  return props.value
})

const trendIcon = computed(() => {
  if (props.change === undefined) return MinusIcon
  if (props.change > 0) return TrendingUpIcon
  if (props.change < 0) return TrendingDownIcon
  return MinusIcon
})

const trendColor = computed(() => {
  if (props.change === undefined) return 'text-gray-400'
  if (props.change > 0) return 'text-green-600'
  if (props.change < 0) return 'text-red-600'
  return 'text-gray-400'
})

const normalizedChartData = computed(() => {
  if (!props.chartData.length) return []
  
  const max = Math.max(...props.chartData)
  const min = Math.min(...props.chartData)
  const range = max - min
  
  if (range === 0) return props.chartData.map(() => 50)
  
  return props.chartData.map(value => {
    const normalized = ((value - min) / range) * 80 + 20 // 20-100% range
    return Math.round(normalized)
  })
})
</script>

<style scoped>
/* Card hover effects */
.hover\:shadow-md:hover {
  transform: translateY(-1px);
}

/* Loading animation */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}

/* Mini chart hover effects */
.h-12 > div:hover {
  transform: scaleY(1.1);
  transform-origin: bottom;
}

/* Value number animation */
.text-3xl {
  transition: all 0.3s ease;
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

/* Dark mode specific animations */
.dark .bg-white {
  transition: background-color 0.2s ease;
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* Print styles */
@media print {
  .hover\:shadow-md:hover {
    transform: none;
  }
  
  .animate-spin {
    animation: none;
  }
}
</style>