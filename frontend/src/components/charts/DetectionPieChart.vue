<template>
  <div class="relative">
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>

    <!-- Chart Container -->
    <div v-else-if="data.human > 0 || data.bot > 0" class="h-64">
      <canvas ref="chartCanvas" class="w-full h-full"></canvas>
    </div>

    <!-- No Data State -->
    <div v-else class="flex items-center justify-center h-64 text-gray-500 dark:text-gray-400">
      <div class="text-center">
        <PieChartIcon class="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>No detection data available</p>
      </div>
    </div>

    <!-- Stats Summary -->
    <div v-if="!loading && (data.human > 0 || data.bot > 0)" class="mt-4 grid grid-cols-2 gap-4">
      <!-- Human Stats -->
      <div class="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
        <div class="text-2xl font-bold text-green-600 dark:text-green-400">
          {{ data.humanPercentage }}%
        </div>
        <div class="text-sm text-gray-600 dark:text-gray-400">
          Human ({{ data.human.toLocaleString() }})
        </div>
      </div>

      <!-- Bot Stats -->
      <div class="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
        <div class="text-2xl font-bold text-red-600 dark:text-red-400">
          {{ data.botPercentage }}%
        </div>
        <div class="text-sm text-gray-600 dark:text-gray-400">
          Bot ({{ data.bot.toLocaleString() }})
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { Chart, type ChartConfiguration, registerables } from 'chart.js'
import { PieChartIcon } from 'lucide-vue-next'
import type { DetectionData } from '@/stores/dashboard'

// Register Chart.js components
Chart.register(...registerables)

interface Props {
  data: DetectionData
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// State
const chartCanvas = ref<HTMLCanvasElement>()
let chartInstance: Chart | null = null

// Computed
const hasData = computed(() => props.data.human > 0 || props.data.bot > 0)
const total = computed(() => props.data.human + props.data.bot)

// Chart configuration
const getChartConfig = (): ChartConfiguration => {
  const isDark = document.documentElement.classList.contains('dark')
  
  return {
    type: 'doughnut',
    data: {
      labels: ['Human Verifications', 'Bot Detections'],
      datasets: [
        {
          data: [props.data.human, props.data.bot],
          backgroundColor: [
            '#10b981', // Green for humans
            '#ef4444'  // Red for bots
          ],
          borderColor: [
            '#059669',
            '#dc2626'
          ],
          borderWidth: 2,
          hoverBackgroundColor: [
            '#059669',
            '#dc2626'
          ],
          hoverBorderColor: isDark ? '#1f2937' : '#ffffff',
          hoverBorderWidth: 3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '60%',
      plugins: {
        legend: {
          display: true,
          position: 'bottom',
          labels: {
            color: isDark ? '#d1d5db' : '#374151',
            usePointStyle: true,
            padding: 20,
            font: {
              family: 'Inter, sans-serif',
              size: 12
            },
            generateLabels: (chart) => {
              const data = chart.data
              if (data.labels?.length && data.datasets.length) {
                return data.labels.map((label, i) => {
                  const dataset = data.datasets[0]
                  const value = dataset.data[i] as number
                  const percentage = total.value > 0 ? Math.round((value / total.value) * 100) : 0
                  
                  return {
                    text: `${label}: ${value.toLocaleString()} (${percentage}%)`,
                    fillStyle: dataset.backgroundColor?.[i] as string,
                    strokeStyle: dataset.borderColor?.[i] as string,
                    lineWidth: dataset.borderWidth as number,
                    hidden: false,
                    index: i,
                    pointStyle: 'circle'
                  }
                })
              }
              return []
            }
          }
        },
        tooltip: {
          backgroundColor: isDark ? '#1f2937' : '#ffffff',
          titleColor: isDark ? '#f9fafb' : '#111827',
          bodyColor: isDark ? '#d1d5db' : '#374151',
          borderColor: isDark ? '#374151' : '#e5e7eb',
          borderWidth: 1,
          cornerRadius: 8,
          padding: 12,
          displayColors: true,
          callbacks: {
            label: (context) => {
              const value = context.parsed
              const percentage = total.value > 0 ? Math.round((value / total.value) * 100) : 0
              const label = context.label || ''
              return `${label}: ${value.toLocaleString()} (${percentage}%)`
            },
            footer: () => {
              return `Total: ${total.value.toLocaleString()} verifications`
            }
          }
        }
      },
      animation: {
        animateRotate: true,
        animateScale: true,
        duration: 1000,
        easing: 'easeInOutQuart'
      },
      interaction: {
        intersect: false
      },
      onHover: (event, elements) => {
        if (chartCanvas.value) {
          chartCanvas.value.style.cursor = elements.length > 0 ? 'pointer' : 'default'
        }
      }
    }
  }
}

// Methods
const createChart = async () => {
  if (!chartCanvas.value || !hasData.value) return

  await nextTick()

  // Destroy existing chart
  if (chartInstance) {
    chartInstance.destroy()
  }

  // Create new chart
  chartInstance = new Chart(chartCanvas.value, getChartConfig())
}

const updateChart = () => {
  if (!chartInstance || !hasData.value) return

  const config = getChartConfig()
  
  // Update data
  chartInstance.data = config.data!
  chartInstance.options = config.options!
  
  // Update chart
  chartInstance.update('active')
}

// Watchers
watch(() => props.data, () => {
  if (chartInstance && hasData.value) {
    updateChart()
  } else if (hasData.value) {
    createChart()
  }
}, { deep: true })

// Theme change handler
const handleThemeChange = () => {
  if (chartInstance) {
    updateChart()
  }
}

// Lifecycle
onMounted(() => {
  if (hasData.value) {
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

/* Stats grid hover effects */
.grid > div {
  transition: all 0.2s ease;
}

.grid > div:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Chart container hover effect */
.relative:hover canvas {
  transform: scale(1.01);
  transition: transform 0.2s ease;
}

/* Stats number animation */
.text-2xl {
  transition: all 0.3s ease;
}

/* Responsive adjustments */
@media (max-width: 640px) {
  .grid-cols-2 {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }
  
  .text-2xl {
    font-size: 1.25rem;
    line-height: 1.75rem;
  }
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  canvas,
  .text-2xl,
  .grid > div {
    transition: none !important;
  }
  
  .animate-spin {
    animation: none;
  }
}

/* Dark mode specific transitions */
.dark .bg-green-50,
.dark .bg-red-50 {
  transition: background-color 0.2s ease;
}
</style>