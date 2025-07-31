<template>
  <div class="space-y-6">
    <!-- Dashboard Header with Controls -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <!-- Left: Logo + Website Selector -->
      <div class="flex items-center space-x-4">
        <div class="relative">
          <button
            @click="showWebsiteDropdown = !showWebsiteDropdown"
            class="flex items-center space-x-3 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <div class="h-8 w-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <svg class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9v-9m0 9c0 5-4 9-9 9s-9-4-9-9m0 9v-9" />
              </svg>
            </div>
            <div class="text-left">
              <p class="text-sm font-medium text-gray-900 dark:text-white">
                {{ selectedWebsite.name }}
              </p>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                {{ selectedWebsite.url }}
              </p>
            </div>
            <ChevronDownIcon class="h-4 w-4 text-gray-400" />
          </button>

          <!-- Website Dropdown -->
          <div
            v-if="showWebsiteDropdown"
            class="absolute top-full left-0 mt-2 w-80 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50"
          >
            <div class="p-3 border-b border-gray-200 dark:border-gray-700">
              <p class="text-sm font-medium text-gray-900 dark:text-white">Select Website</p>
            </div>
            <div class="max-h-64 overflow-y-auto">
              <button
                @click="selectWebsite('all')"
                class="w-full px-3 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center space-x-3"
                :class="{ 'bg-indigo-50 dark:bg-indigo-900/20': selectedWebsite.id === 'all' }"
              >
                <div class="h-6 w-6 bg-gray-600 rounded flex items-center justify-center">
                  <svg class="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                </div>
                <div>
                  <p class="text-sm font-medium text-gray-900 dark:text-white">All Websites</p>
                  <p class="text-xs text-gray-500 dark:text-gray-400">Combined analytics</p>
                </div>
              </button>
              <button
                v-for="website in websites"
                :key="website.id"
                @click="selectWebsite(website.id)"
                class="w-full px-3 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center space-x-3 group"
                :class="{ 'bg-indigo-50 dark:bg-indigo-900/20': selectedWebsite.id === website.id }"
              >
                <div 
                  :class="[
                    'h-6 w-6 rounded flex items-center justify-center',
                    website.status === 'active' ? 'bg-green-600' : 'bg-gray-400'
                  ]"
                >
                  <svg class="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9v-9m0 9c0 5-4 9-9 9s-9-4-9-9m0 9v-9" />
                  </svg>
                </div>
                <div class="flex-1">
                  <p class="text-sm font-medium text-gray-900 dark:text-white">{{ website.name }}</p>
                  <p class="text-xs text-gray-500 dark:text-gray-400">{{ website.url }}</p>
                </div>
                <div class="opacity-0 group-hover:opacity-100 transition-opacity">
                  <span 
                    :class="[
                      'text-xs px-2 py-1 rounded-full',
                      website.status === 'active' 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
                    ]"
                  >
                    {{ website.status }}
                  </span>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Add Website + Current Website Info -->
      <div class="flex items-center space-x-4">
        <!-- Current Website Info (Hover Box) -->
        <div v-if="selectedWebsite.id !== 'all'" class="relative group">
          <div class="px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
            <p class="text-sm font-medium text-gray-900 dark:text-white">{{ selectedWebsite.name }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ selectedWebsite.url }}</p>
          </div>
          
          <!-- Hover Details -->
          <div class="absolute bottom-full right-0 mb-2 w-64 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-50">
            <div class="space-y-2">
              <div class="flex justify-between">
                <span>Status:</span>
                <span class="capitalize">{{ selectedWebsite.status }}</span>
              </div>
              <div class="flex justify-between">
                <span>Added:</span>
                <span>{{ formatDate(selectedWebsite.createdAt) }}</span>
              </div>
              <div class="flex justify-between">
                <span>Last Activity:</span>
                <span>{{ formatRelativeTime(selectedWebsite.lastActivity) }}</span>
              </div>
              <div class="flex justify-between">
                <span>Total Verifications:</span>
                <span>{{ formatNumber(selectedWebsite.totalVerifications) }}</span>
              </div>
            </div>
            <div class="absolute top-full right-6 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
          </div>
        </div>

        <!-- Add Website Button -->
        <button
          @click="showAddWebsiteModal = true"
          class="flex items-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
        >
          <PlusIcon class="h-4 w-4" />
          <span>Add Website</span>
        </button>
      </div>
    </div>

    <!-- KPI Cards Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      <KPICard
        title="Total Verifications"
        :value="analytics.totalVerifications"
        :change="analytics.verificationChange"
        icon="shield-check"
        color="indigo"
        :trend="analytics.verificationTrend"
      />
      <KPICard
        title="Human Detection Rate"
        :value="`${analytics.humanRate}%`"
        :change="analytics.humanRateChange"
        icon="user-check"
        color="green"
        :trend="analytics.humanRateTrend"
      />
      <KPICard
        title="Average Confidence"
        :value="`${analytics.avgConfidence}%`"
        :change="analytics.confidenceChange"
        icon="chart-bar"
        color="orange"
        :trend="analytics.confidenceTrend"
      />
      <KPICard
        title="Response Time"
        :value="`${analytics.avgResponseTime}ms`"
        :change="analytics.responseTimeChange"
        icon="clock"
        color="blue"
        :trend="analytics.responseTimeTrend"
      />
    </div>

    <!-- Charts Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Verification Trends -->
      <ChartCard
        title="Verification Trends"
        subtitle="Human vs Bot detection over time"
        :data="chartData.verificationTrends"
        type="line"
        :timeRange="selectedTimeRange"
        @timeRangeChange="handleTimeRangeChange"
      />

      <!-- Detection Distribution -->
      <ChartCard
        title="Detection Distribution"
        subtitle="Human vs Bot percentage breakdown"
        :data="chartData.detectionDistribution"
        type="doughnut"
      />
    </div>

    <!-- ML Model Metrics Section -->
    <MLMetricsSection />

    <!-- Analytics Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Geographic Distribution -->
      <AnalyticsCard
        title="Geographic Distribution"
        subtitle="Verifications by country"
        icon="globe"
      >
        <div class="space-y-3">
          <div v-for="country in analytics.topCountries" :key="country.code" class="flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <span class="text-lg">{{ country.flag }}</span>
              <span class="text-sm font-medium text-gray-900 dark:text-white">{{ country.name }}</span>
            </div>
            <div class="text-right">
              <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ formatNumber(country.count) }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400">{{ country.percentage }}%</div>
            </div>
          </div>
        </div>
      </AnalyticsCard>

      <!-- Top Threats -->
      <AnalyticsCard
        title="Threat Analysis"
        subtitle="Most detected bot types"
        icon="shield-exclamation"
      >
        <div class="space-y-3">
          <div v-for="threat in analytics.topThreats" :key="threat.type" class="flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div 
                :class="[
                  'w-3 h-3 rounded-full',
                  threat.severity === 'high' ? 'bg-red-500' :
                  threat.severity === 'medium' ? 'bg-yellow-500' : 'bg-orange-500'
                ]"
              ></div>
              <span class="text-sm font-medium text-gray-900 dark:text-white">{{ threat.type }}</span>
            </div>
            <div class="text-right">
              <div class="text-sm font-semibold text-gray-900 dark:text-white">{{ formatNumber(threat.count) }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400">{{ threat.percentage }}%</div>
            </div>
          </div>
        </div>
      </AnalyticsCard>

      <!-- System Health -->
      <AnalyticsCard
        title="System Health"
        subtitle="Infrastructure status"
        icon="cpu-chip"
      >
        <div class="space-y-4">
          <div v-for="service in systemHealth" :key="service.name" class="flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div 
                :class="[
                  'w-3 h-3 rounded-full',
                  service.status === 'healthy' ? 'bg-green-500' :
                  service.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                ]"
              ></div>
              <span class="text-sm font-medium text-gray-900 dark:text-white">{{ service.name }}</span>
            </div>
            <div class="text-right">
              <div class="text-xs font-medium text-gray-600 dark:text-gray-400">{{ service.uptime }}</div>
              <div 
                :class="[
                  'text-xs capitalize',
                  service.status === 'healthy' ? 'text-green-600 dark:text-green-400' :
                  service.status === 'warning' ? 'text-yellow-600 dark:text-yellow-400' : 'text-red-600 dark:text-red-400'
                ]"
              >
                {{ service.status }}
              </div>
            </div>
          </div>
        </div>
      </AnalyticsCard>
    </div>

    <!-- Live Activity Feed -->
    <LiveActivityFeed 
      :logs="realtimeLogs" 
      :isConnected="websocketConnected"
      @export="handleExportLogs"
      @filter="handleLogFilter"
    />

    <!-- Add Website Modal -->
    <AddWebsiteModal 
      v-if="showAddWebsiteModal"
      @close="showAddWebsiteModal = false"
      @success="handleWebsiteAdded"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { 
  ChevronDownIcon, 
  PlusIcon 
} from '@heroicons/vue/24/outline'
import { useDashboardStore } from '@/stores/dashboard'
import { useWebsiteStore } from '@/stores/websites'
import KPICard from './_components/KPICard.vue'
import ChartCard from './_components/ChartCard.vue'
import AnalyticsCard from './_components/AnalyticsCard.vue'
import LiveActivityFeed from './_components/LiveActivityFeed.vue'
import AddWebsiteModal from './_components/AddWebsiteModal.vue'
import MLMetricsSection from './_components/MLMetricsSection.vue'

// State
const showWebsiteDropdown = ref(false)
const showAddWebsiteModal = ref(false)
const selectedTimeRange = ref('24h')
const websocketConnected = ref(false)

// Use stores for dynamic data
const websitesStore = useWebsiteStore()
const dashboardStore = useDashboardStore()

// Computed properties for reactive data
const websites = computed(() => websitesStore.websites)
const selectedWebsite = computed(() => websitesStore.selectedWebsite || {
  id: 'all',
  name: 'All Websites',
  url: 'Combined Analytics',
  status: 'active' as const,
  createdAt: new Date().toISOString(),
  lastActivity: new Date().toISOString(),
  totalVerifications: dashboardStore.stats.totalVerifications
})

// Dynamic analytics data from stores
const analytics = computed(() => ({
  totalVerifications: dashboardStore.stats.totalVerifications,
  verificationChange: dashboardStore.stats.verificationChange,
  verificationTrend: [], // Will be populated from chart data
  humanRate: dashboardStore.stats.humanRate,
  humanRateChange: dashboardStore.stats.humanRateChange,
  humanRateTrend: [], // Will be populated from chart data
  avgConfidence: dashboardStore.stats.avgConfidence,
  confidenceChange: dashboardStore.stats.confidenceChange,
  confidenceTrend: [], // Will be populated from chart data
  avgResponseTime: dashboardStore.stats.avgResponseTime,
  responseTimeChange: dashboardStore.stats.responseTimeChange,
  responseTimeTrend: [], // Will be populated from chart data
  topCountries: [], // Will be populated from backend API
  topThreats: [] // Will be populated from backend API
}))

// Dynamic chart data from store
const chartData = computed(() => ({
  verificationTrends: {
    labels: dashboardStore.chartData.map(point => {
      const date = new Date(point.timestamp)
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    }),
    datasets: [
      {
        label: 'Human Verifications',
        data: dashboardStore.chartData.map(point => point.human),
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)'
      },
      {
        label: 'Bot Detections',
        data: dashboardStore.chartData.map(point => point.bot),
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)'
      }
    ]
  },
  detectionDistribution: {
    labels: ['Human Traffic', 'Bot Traffic'],
    datasets: [{
      data: [dashboardStore.detectionData.humanPercentage, dashboardStore.detectionData.botPercentage],
      backgroundColor: ['#10b981', '#ef4444'],
      borderWidth: 0
    }]
  }
}))

const systemHealth = ref([
  { name: 'API Server', status: 'healthy', uptime: '99.9%' },
  { name: 'Database', status: 'healthy', uptime: '99.8%' },
  { name: 'ML Model', status: 'healthy', uptime: '99.7%' },
  { name: 'Cache Layer', status: 'warning', uptime: '98.5%' }
])

const realtimeLogs = ref([
  {
    id: 1,
    timestamp: new Date(),
    type: 'human',
    ip: '192.168.1.100',
    country: 'US',
    confidence: 0.94,
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    website: 'example.com'
  }
])

// Methods
const selectWebsite = (websiteId: string) => {
  if (websiteId === 'all') {
    selectedWebsite.value = {
      id: 'all',
      name: 'All Websites',
      url: 'Combined Analytics',
      status: 'active',
      createdAt: '2024-01-01T00:00:00Z',
      lastActivity: new Date().toISOString(),
      totalVerifications: 27800
    }
  } else {
    const website = websites.value.find(w => w.id === websiteId)
    if (website) {
      selectedWebsite.value = website
    }
  }
  showWebsiteDropdown.value = false
  // Trigger data refresh for selected website
  refreshAnalytics()
}

const handleTimeRangeChange = (timeRange: string) => {
  selectedTimeRange.value = timeRange
  refreshAnalytics()
}

const handleWebsiteAdded = (newWebsite: any) => {
  websites.value.unshift(newWebsite)
  showAddWebsiteModal.value = false
}

const handleExportLogs = (format: string) => {
  console.log('Exporting logs in format:', format)
}

const handleLogFilter = (filter: string) => {
  console.log('Filtering logs:', filter)
}

const refreshAnalytics = async () => {
  try {
    // Refresh all dashboard data
    await Promise.all([
      dashboardStore.fetchStats(selectedTimeRange.value),
      dashboardStore.fetchChartData(selectedTimeRange.value),
      dashboardStore.fetchDetectionData(selectedTimeRange.value),
      dashboardStore.fetchSystemHealth(),
      dashboardStore.fetchRecentAlerts(),
      websitesStore.fetchWebsites()
    ])
    console.log('Analytics refreshed successfully')
  } catch (error) {
    console.error('Error refreshing analytics:', error)
  }
}

const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString()
}

const formatRelativeTime = (dateString: string): string => {
  const now = new Date()
  const date = new Date(dateString)
  const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
  
  if (diffInMinutes < 60) {
    return `${diffInMinutes}m ago`
  } else if (diffInMinutes < 1440) {
    return `${Math.floor(diffInMinutes / 60)}h ago`
  } else {
    return `${Math.floor(diffInMinutes / 1440)}d ago`
  }
}

// Auto-refresh functionality
let refreshInterval: number

onMounted(() => {
  refreshAnalytics()
  
  // Auto-refresh every 30 seconds
  refreshInterval = setInterval(refreshAnalytics, 30000)
  
  // Simulate WebSocket connection
  websocketConnected.value = true
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

// Close dropdown when clicking outside
const handleClickOutside = (event: Event) => {
  const target = event.target as Element
  if (!target.closest('.relative')) {
    showWebsiteDropdown.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* Dashboard page animations */
.space-y-8 > * {
  animation: fadeInUp 0.6s ease-out;
}

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

/* Stagger animation */
.space-y-8 > *:nth-child(1) { animation-delay: 0.1s; }
.space-y-8 > *:nth-child(2) { animation-delay: 0.2s; }
.space-y-8 > *:nth-child(3) { animation-delay: 0.3s; }
.space-y-8 > *:nth-child(4) { animation-delay: 0.4s; }
.space-y-8 > *:nth-child(5) { animation-delay: 0.5s; }
</style>