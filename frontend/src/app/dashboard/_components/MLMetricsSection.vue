<template>
  <div class="space-y-6">
    <!-- ML Section Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="p-2 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
          <CpuChipIcon class="h-6 w-6 text-purple-600 dark:text-purple-400" />
        </div>
        <div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            ML Model Performance
          </h3>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            Real-time machine learning model metrics and insights
          </p>
        </div>
      </div>
      
      <div class="flex items-center space-x-2">
        <div class="flex items-center space-x-2">
          <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span class="text-sm text-gray-600 dark:text-gray-400">Model Active</span>
        </div>
        <button
          @click="refreshMLMetrics"
          class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <ArrowPathIcon class="h-4 w-4" />
        </button>
      </div>
    </div>

    <!-- Core ML Metrics Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- Total Verification Attempts -->
      <MLMetricCard
        title="Total Verifications"
        :value="mlMetrics.totalVerifications"
        :change="mlMetrics.verificationsChange"
        icon="shield-check"
        color="purple"
        :trend="mlMetrics.verificationsTrend"
        description="Passive CAPTCHA checks performed"
      />

      <!-- Human Detection Rate -->
      <MLMetricCard
        title="Human Detection Rate"
        :value="`${mlMetrics.humanDetectionRate}%`"
        :change="mlMetrics.humanRateChange"
        icon="user-group"
        color="green"
        :trend="mlMetrics.humanRateTrend"
        description="Requests classified as human"
      />

      <!-- Bot Detection Rate -->
      <MLMetricCard
        title="Bot Detection Rate"
        :value="`${mlMetrics.botDetectionRate}%`"
        :change="mlMetrics.botRateChange"
        icon="exclamation-triangle"
        color="red"
        :trend="mlMetrics.botRateTrend"
        description="Requests classified as bot"
      />

      <!-- Average Model Confidence -->
      <MLMetricCard
        title="Model Confidence"
        :value="`${mlMetrics.avgConfidence}%`"
        :change="mlMetrics.confidenceChange"
        icon="chart-bar"
        color="blue"
        :trend="mlMetrics.confidenceTrend"
        description="Mean prediction confidence"
      />
    </div>

    <!-- Advanced ML Metrics Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Confidence Distribution -->
      <ConfidenceDistributionChart
        :data="mlMetrics.confidenceDistribution"
        class="lg:col-span-1"
      />

      <!-- False Positive/Negative Tracking -->
      <ModelAccuracyChart
        :data="mlMetrics.accuracyMetrics"
        class="lg:col-span-1"
      />

      <!-- Model Performance Over Time -->
      <ModelPerformanceTrend
        :data="mlMetrics.performanceTrend"
        :timeRange="selectedTimeRange"
        @timeRangeChange="handleTimeRangeChange"
        class="lg:col-span-1"
      />
    </div>

    <!-- Verification Trends Chart -->
    <VerificationTrendsChart
      :data="mlMetrics.verificationTrends"
      :timeRange="selectedTimeRange"
      @timeRangeChange="handleTimeRangeChange"
    />

    <!-- ML Model Health Status -->
    <MLModelHealthStatus
      :health="mlMetrics.modelHealth"
      :lastUpdated="mlMetrics.lastModelUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { CpuChipIcon, ArrowPathIcon } from '@heroicons/vue/24/outline'
import MLMetricCard from './MLMetricCard.vue'
import ConfidenceDistributionChart from './ConfidenceDistributionChart.vue'
import ModelAccuracyChart from './ModelAccuracyChart.vue'
import ModelPerformanceTrend from './ModelPerformanceTrend.vue'
import VerificationTrendsChart from './VerificationTrendsChart.vue'
import MLModelHealthStatus from './MLModelHealthStatus.vue'

// State
const selectedTimeRange = ref('24h')

// Sample ML metrics data (replace with real data from API)
const mlMetrics = ref({
  totalVerifications: 127834,
  verificationsChange: 8.2,
  verificationsTrend: [1200, 1350, 1100, 1450, 1380, 1520, 1600],
  
  humanDetectionRate: 87.3,
  humanRateChange: -1.2,
  humanRateTrend: [88, 87.5, 87.8, 87.1, 87.3, 87.6, 87.3],
  
  botDetectionRate: 12.7,
  botRateChange: 1.2,
  botRateTrend: [12, 12.5, 12.2, 12.9, 12.7, 12.4, 12.7],
  
  avgConfidence: 92.8,
  confidenceChange: 2.1,
  confidenceTrend: [91, 91.5, 92.1, 92.5, 92.8, 92.6, 92.8],
  
  confidenceDistribution: {
    labels: ['0-20%', '21-40%', '41-60%', '61-80%', '81-100%'],
    datasets: [{
      label: 'Confidence Distribution',
      data: [2, 5, 8, 15, 70],
      backgroundColor: ['#fee2e2', '#fed7aa', '#fef3c7', '#d1fae5', '#dcfce7']
    }]
  },
  
  accuracyMetrics: {
    falsePositives: 156,
    falseNegatives: 89,
    truePositives: 11234,
    trueNegatives: 3421,
    precision: 98.6,
    recall: 99.2,
    f1Score: 98.9
  },
  
  performanceTrend: {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        label: 'Precision',
        data: [98.2, 98.5, 98.1, 98.8, 98.6, 98.9, 98.6],
        borderColor: '#8b5cf6',
        backgroundColor: 'rgba(139, 92, 246, 0.1)'
      },
      {
        label: 'Recall',
        data: [99.1, 99.0, 99.3, 98.9, 99.2, 99.1, 99.2],
        borderColor: '#06b6d4',
        backgroundColor: 'rgba(6, 182, 212, 0.1)'
      }
    ]
  },
  
  verificationTrends: {
    labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'],
    datasets: [
      {
        label: 'Successful Verifications',
        data: [245, 189, 234, 456, 398, 512, 445],
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: true
      },
      {
        label: 'Failed Verifications',
        data: [12, 8, 15, 23, 18, 28, 21],
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        fill: true
      }
    ]
  },
  
  modelHealth: {
    status: 'healthy',
    version: 'v2.1.3',
    accuracy: 98.7,
    latency: 45,
    uptime: 99.8,
    lastTraining: '2024-07-25T10:30:00Z',
    nextRetraining: '2024-08-01T10:30:00Z'
  },
  
  lastModelUpdate: new Date().toISOString()
})

// Methods
const refreshMLMetrics = () => {
  console.log('Refreshing ML metrics...')
  // Implement API call to refresh metrics
}

const handleTimeRangeChange = (timeRange: string) => {
  selectedTimeRange.value = timeRange
  console.log('Time range changed to:', timeRange)
  // Refresh charts with new time range
}

// Auto-refresh functionality
let refreshInterval: number

onMounted(() => {
  // Auto-refresh every 30 seconds
  refreshInterval = setInterval(refreshMLMetrics, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
/* ML Metrics section animations */
.space-y-6 > * {
  animation: fadeInUp 0.6s ease-out;
  animation-fill-mode: both;
}

.space-y-6 > *:nth-child(1) { animation-delay: 0.1s; }
.space-y-6 > *:nth-child(2) { animation-delay: 0.2s; }
.space-y-6 > *:nth-child(3) { animation-delay: 0.3s; }
.space-y-6 > *:nth-child(4) { animation-delay: 0.4s; }
.space-y-6 > *:nth-child(5) { animation-delay: 0.5s; }

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>