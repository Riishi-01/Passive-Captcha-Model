<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Header -->
    <AppHeader />
    
    <!-- Main Content -->
    <div class="flex">
      <!-- Sidebar -->
      <AppSidebar />
      
      <!-- Dashboard Content -->
      <main class="flex-1 p-6 lg:p-8">
        <!-- Page Header -->
        <div class="mb-8">
          <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p class="text-gray-600 dark:text-gray-400 mt-2">
            Monitor your passive CAPTCHA protection across all websites
          </p>
        </div>

        <!-- KPI Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <KPICard
            title="Total Verifications"
            :value="stats.totalVerifications"
            :change="stats.verificationChange"
            icon="shield-check"
            color="primary"
          />
          <KPICard
            title="Human Rate"
            :value="`${stats.humanRate}%`"
            :change="stats.humanRateChange"
            icon="user-check"
            color="success"
          />
          <KPICard
            title="Avg Confidence"
            :value="`${stats.avgConfidence}%`"
            :change="stats.confidenceChange"
            icon="chart-bar"
            color="warning"
          />
          <KPICard
            title="Response Time"
            :value="`${stats.avgResponseTime}ms`"
            :change="stats.responseTimeChange"
            icon="clock"
            color="info"
          />
        </div>

        <!-- Charts Row -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <!-- Verification Trends Chart -->
          <div class="card p-6">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                Verification Trends
              </h3>
              <TimeRangeSelector v-model="selectedTimeRange" />
            </div>
            <VerificationChart :data="chartData" :timeRange="selectedTimeRange" />
          </div>

          <!-- Detection Analytics -->
          <div class="card p-6">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Detection Analytics
            </h3>
            <DetectionPieChart :data="detectionData" />
          </div>
        </div>

        <!-- Websites Overview -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <!-- Active Websites -->
          <div class="card p-6">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Active Websites
            </h3>
            <WebsiteList :websites="activeWebsites" />
          </div>

          <!-- Recent Alerts -->
          <div class="card p-6">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Recent Alerts
            </h3>
            <AlertsList :alerts="recentAlerts" />
          </div>

          <!-- System Health -->
          <div class="card p-6">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              System Health
            </h3>
            <SystemHealth :health="systemHealth" />
          </div>
        </div>

        <!-- Timeline Logs Section -->
        <div class="card p-6">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
              Timeline Logs
            </h3>
            <div class="flex space-x-2">
              <LogFilterTabs v-model="activeLogFilter" />
              <button
                @click="refreshLogs"
                class="btn btn-outline"
                :disabled="isLoadingLogs"
              >
                <RefreshIcon class="w-4 h-4 mr-2" />
                Refresh
              </button>
            </div>
          </div>
          
          <TimelineLogs 
            :logs="timelineLogs" 
            :filter="activeLogFilter"
            :loading="isLoadingLogs"
            @load-more="loadMoreLogs"
          />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useAppStore } from '@/stores/app'
import { useDashboardStore } from '@/stores/dashboard'
import { useWebsiteStore } from '@/stores/websites'

// Components
import AppHeader from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import KPICard from '@/components/dashboard/KPICard.vue'
import TimeRangeSelector from '@/components/common/TimeRangeSelector.vue'
import VerificationChart from '@/components/charts/VerificationChart.vue'
import DetectionPieChart from '@/components/charts/DetectionPieChart.vue'
import WebsiteList from '@/components/websites/WebsiteList.vue'
import AlertsList from '@/components/alerts/AlertsList.vue'
import SystemHealth from '@/components/dashboard/SystemHealth.vue'
import LogFilterTabs from '@/components/logs/LogFilterTabs.vue'
import TimelineLogs from '@/components/logs/TimelineLogs.vue'
import { RefreshIcon } from 'lucide-vue-next'

// Stores
const appStore = useAppStore()
const dashboardStore = useDashboardStore()
const websiteStore = useWebsiteStore()

// State
const selectedTimeRange = ref('24h')
const activeLogFilter = ref('active')
const isLoadingLogs = ref(false)

// Computed
const stats = computed(() => dashboardStore.stats)
const chartData = computed(() => dashboardStore.chartData)
const detectionData = computed(() => dashboardStore.detectionData)
const activeWebsites = computed(() => websiteStore.activeWebsites)
const recentAlerts = computed(() => dashboardStore.recentAlerts)
const systemHealth = computed(() => dashboardStore.systemHealth)
const timelineLogs = computed(() => dashboardStore.timelineLogs)

// Methods
async function refreshDashboard() {
  appStore.setLoading(true)
  try {
    await Promise.all([
      dashboardStore.fetchStats(selectedTimeRange.value),
      dashboardStore.fetchChartData(selectedTimeRange.value),
      dashboardStore.fetchDetectionData(selectedTimeRange.value),
      websiteStore.fetchActiveWebsites(),
      dashboardStore.fetchRecentAlerts(),
      dashboardStore.fetchSystemHealth()
    ])
  } catch (error) {
    console.error('Error refreshing dashboard:', error)
    appStore.addNotification({
      type: 'error',
      title: 'Error',
      message: 'Failed to refresh dashboard data'
    })
  } finally {
    appStore.setLoading(false)
  }
}

async function refreshLogs() {
  isLoadingLogs.value = true
  try {
    await dashboardStore.fetchTimelineLogs(activeLogFilter.value, true)
  } catch (error) {
    console.error('Error refreshing logs:', error)
    appStore.addNotification({
      type: 'error',
      title: 'Error',
      message: 'Failed to refresh logs'
    })
  } finally {
    isLoadingLogs.value = false
  }
}

async function loadMoreLogs() {
  try {
    await dashboardStore.loadMoreTimelineLogs()
  } catch (error) {
    console.error('Error loading more logs:', error)
  }
}

// Watchers
watch(selectedTimeRange, (newRange) => {
  dashboardStore.fetchStats(newRange)
  dashboardStore.fetchChartData(newRange)
  dashboardStore.fetchDetectionData(newRange)
})

watch(activeLogFilter, (newFilter) => {
  dashboardStore.fetchTimelineLogs(newFilter, true)
})

// Lifecycle
onMounted(() => {
  refreshDashboard()
  dashboardStore.fetchTimelineLogs(activeLogFilter.value)
  
  // Auto-refresh every 30 seconds
  const interval = setInterval(() => {
    if (!document.hidden) {
      refreshDashboard()
    }
  }, 30000)
  
  // Cleanup on unmount
  return () => clearInterval(interval)
})

// Real-time updates via WebSocket (if available)
onMounted(() => {
  if (typeof io !== 'undefined') {
    const socket = io()
    
    socket.on('verification_update', (data) => {
      dashboardStore.updateRealTimeStats(data)
    })
    
    socket.on('new_alert', (alert) => {
      dashboardStore.addAlert(alert)
      appStore.addNotification({
        type: 'warning',
        title: 'New Alert',
        message: alert.message
      })
    })
    
    return () => socket.disconnect()
  }
})
</script>

<style scoped>
/* Custom styles for dashboard */
.grid {
  animation: fadeIn 0.6s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .grid {
    grid-template-columns: 1fr;
  }
}

/* Dark mode specific styles */
.dark .card {
  background: rgba(31, 41, 55, 0.8);
  backdrop-filter: blur(10px);
}

/* Loading states */
.loading-shimmer {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

/* Hover effects */
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.15);
}

/* Focus states for accessibility */
.btn:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Print styles */
@media print {
  .no-print {
    display: none !important;
  }
}
</style> 