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

        <!-- UIDAI Portal Integration -->
        <div class="mb-8">
          <div class="card p-6 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-4">
                <div class="p-3 bg-white/20 rounded-lg">
                  <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
                <div>
                  <h3 class="text-xl font-bold">UIDAI Government Portal</h3>
                  <p class="text-blue-100">Protected by Passive CAPTCHA • Real-time Monitoring Active</p>
                </div>
              </div>
              <div class="flex space-x-3">
                <a
                  href="/uidai"
                  target="_blank"
                  class="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors flex items-center space-x-2"
                >
                  <span>Visit Portal</span>
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
                <router-link
                  to="/analytics"
                  class="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors flex items-center space-x-2"
                >
                  <span>View Analytics</span>
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </router-link>
              </div>
            </div>
            <div class="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="text-center p-3 bg-white/10 rounded-lg">
                <div class="text-2xl font-bold">{{ uidaiStats.totalSessions || '---' }}</div>
                <div class="text-sm text-blue-100">Total Sessions</div>
              </div>
              <div class="text-center p-3 bg-white/10 rounded-lg">
                <div class="text-2xl font-bold">{{ uidaiStats.verifiedUsers || '---' }}</div>
                <div class="text-sm text-blue-100">Verified Users</div>
              </div>
              <div class="text-center p-3 bg-white/10 rounded-lg">
                <div class="text-2xl font-bold">{{ uidaiStats.detectionRate || '---' }}%</div>
                <div class="text-sm text-blue-100">Detection Rate</div>
              </div>
            </div>
          </div>
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
const uidaiStats = ref({
  totalSessions: 0,
  verifiedUsers: 0,
  detectionRate: 0
})

// Computed
const stats = computed(() => dashboardStore.stats)
const chartData = computed(() => dashboardStore.chartData)
const detectionData = computed(() => dashboardStore.detectionData)
const activeWebsites = computed(() => websiteStore.activeWebsites)
const recentAlerts = computed(() => dashboardStore.recentAlerts)
const systemHealth = computed(() => dashboardStore.systemHealth)
const timelineLogs = computed(() => dashboardStore.timelineLogs)

// Methods
async function fetchUidaiStats() {
  try {
    // Fetch UIDAI portal specific analytics
    const response = await fetch('/prototype/api/analytics?website=uidai-gov-in')
    if (response.ok) {
      const data = await response.json()
      uidaiStats.value = {
        totalSessions: data.total_verifications || 0,
        verifiedUsers: data.verified_users || 0,
        detectionRate: Math.round(data.detection_rate || 0)
      }
    }
  } catch (error) {
    console.error('Error fetching UIDAI stats:', error)
    // Keep default values on error
  }
}

async function refreshDashboard() {
  appStore.setLoading(true)
  try {
    await Promise.all([
      dashboardStore.fetchStats(selectedTimeRange.value),
      dashboardStore.fetchChartData(selectedTimeRange.value),
      dashboardStore.fetchDetectionData(selectedTimeRange.value),
      websiteStore.fetchActiveWebsites(),
      dashboardStore.fetchRecentAlerts(),
      dashboardStore.fetchSystemHealth(),
      fetchUidaiStats()
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