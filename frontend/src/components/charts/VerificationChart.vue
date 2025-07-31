<template>
  <div class="relative">
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>

    <!-- Chart Container -->
    <div v-else class="h-64">
      <canvas ref="chartCanvas" class="w-full h-full"></canvas>
    </div>

    <!-- No Data State -->
    <div v-if="!loading && (!data || data.length === 0)" class="flex items-center justify-center h-64 text-gray-500 dark:text-gray-400">
      <div class="text-center">
        <BarChart3Icon class="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>No verification data available</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Chart, type ChartConfiguration, registerables } from 'chart.js'
import { BarChart3Icon } from 'lucide-vue-next'
import type { ChartDataPoint } from '@/stores/dashboard'

// Register Chart.js components
Chart.register(...registerables)

interface Props {
  data: ChartDataPoint[]
  timeRange: string
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// State
const chartCanvas = ref<HTMLCanvasElement>()
let chartInstance: Chart | null = null

// Chart configuration
const getChartConfig = (): ChartConfiguration => {
  const isDark = document.documentElement.classList.contains('dark')
  
  return {
    type: 'line',
    data: {
      labels: props.data.map(item => formatLabel(item.timestamp)),
      datasets: [
        {
          label: 'Human Verifications',
          data: props.data.map(item => item.human),
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: '#10b981',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2
        },
        {
          label: 'Bot Detections',
          data: props.data.map(item => item.bot),
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: '#ef4444',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            color: isDark ? '#d1d5db' : '#374151',
            usePointStyle: true,
            padding: 20,
            font: {
              family: 'Inter, sans-serif',
              size: 12
            }
          }
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: isDark ? '#1f2937' : '#ffffff',
          titleColor: isDark ? '#f9fafb' : '#111827',
          bodyColor: isDark ? '#d1d5db' : '#374151',
          borderColor: isDark ? '#374151' : '#e5e7eb',
          borderWidth: 1,
          cornerRadius: 8,
          padding: 12,
          displayColors: true,
          callbacks: {
            title: (context) => {
              const dataPoint = props.data[context[0].dataIndex]
              return formatTooltipTitle(dataPoint.timestamp)
            },
            label: (context) => {
              const value = context.parsed.y
              const total = props.data[context.dataIndex].total
              const percentage = total > 0 ? Math.round((value / total) * 100) : 0
              return `${context.dataset.label}: ${value} (${percentage}%)`
            },
            footer: (context) => {
              const total = props.data[context[0].dataIndex].total
              return `Total: ${total} verifications`
            }
          }
        }
      },
      scales: {
        x: {
          display: true,
          grid: {
            color: isDark ? '#374151' : '#f3f4f6',
            drawBorder: false
          },
          ticks: {
            color: isDark ? '#9ca3af' : '#6b7280',
            font: {
              family: 'Inter, sans-serif',
              size: 11
            },
            maxTicksLimit: 8
          }
        },
        y: {
          display: true,
          beginAtZero: true,
          grid: {
            color: isDark ? '#374151' : '#f3f4f6',
            drawBorder: false
          },
          ticks: {
            color: isDark ? '#9ca3af' : '#6b7280',
            font: {
              family: 'Inter, sans-serif',
              size: 11
            },
            callback: (value) => {
              if (typeof value === 'number') {
                return value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value.toString()
              }
              return value
            }
          }
        }
      },
      interaction: {
        mode: 'nearest',
        axis: 'x',
        intersect: false
      },
      animation: {
        duration: 750,
        easing: 'easeInOutQuart'
      },
      elements: {
        point: {
          hoverRadius: 8
        }
      }
    }
  }
}

// Methods
const formatLabel = (timestamp: string): string => {
  const date = new Date(timestamp)
  
  if (props.timeRange === '24h') {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    })
  } else if (props.timeRange === '7d') {
    return date.toLocaleDateString('en-US', { 
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    })
  } else {
    return date.toLocaleDateString('en-US', { 
      month: 'short',
      day: 'numeric'
    })
  }
}

const formatTooltipTitle = (timestamp: string): string => {
  const date = new Date(timestamp)
  return date.toLocaleString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const createChart = async () => {
  if (!chartCanvas.value || !props.data.length) return

  await nextTick()

  // Destroy existing chart
  if (chartInstance) {
    chartInstance.destroy()
  }

  // Create new chart
  chartInstance = new Chart(chartCanvas.value, getChartConfig())
}

const updateChart = () => {
  if (!chartInstance || !props.data.length) return

  const config = getChartConfig()
  
  // Update data
  chartInstance.data = config.data!
  chartInstance.options = config.options!
  
  // Update chart
  chartInstance.update('active')
}

// Watchers
watch(() => props.data, () => {
  if (chartInstance && props.data.length > 0) {
    updateChart()
  } else if (props.data.length > 0) {
    createChart()
  }
}, { deep: true })

watch(() => props.timeRange, () => {
  if (chartInstance) {
    updateChart()
  }
})

// Theme change handler
const handleThemeChange = () => {
  if (chartInstance) {
    updateChart()
  }
}

// Lifecycle
onMounted(() => {
  if (props.data.length > 0) {
    createChart()
  }
  
  // Listen for theme changes
  const observer = new MutationObserver(handleThemeChange)
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class']
  })
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
  }
})
</script>

<style scoped>
canvas {
  max-height: 256px;
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

/* Chart container hover effect */
.relative:hover canvas {
  transform: scale(1.01);
  transition: transform 0.2s ease;
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  canvas {
    transition: none !important;
  }
  
  .animate-spin {
    animation: none;
  }
}
</style>