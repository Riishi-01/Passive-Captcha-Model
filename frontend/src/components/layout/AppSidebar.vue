<template>
  <aside class="w-64 bg-white dark:bg-gray-800 shadow-sm border-r border-gray-200 dark:border-gray-700 min-h-screen">
    <nav class="p-4 space-y-2">
      <!-- Dashboard -->
      <router-link
        to="/dashboard"
        class="nav-item"
        :class="{ 'nav-item-active': $route.path === '/dashboard' }"
      >
        <LayoutDashboardIcon class="w-5 h-5" />
        <span>Dashboard</span>
      </router-link>

      <!-- Websites -->
      <router-link
        to="/websites"
        class="nav-item"
        :class="{ 'nav-item-active': $route.path.startsWith('/websites') }"
      >
        <GlobeIcon class="w-5 h-5" />
        <span>Websites</span>
        <span v-if="activeWebsiteCount > 0" class="ml-auto bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs px-2 py-1 rounded-full">
          {{ activeWebsiteCount }}
        </span>
      </router-link>

      <!-- Verification Logs -->
      <router-link
        to="/logs"
        class="nav-item"
        :class="{ 'nav-item-active': $route.path === '/logs' }"
      >
        <FileTextIcon class="w-5 h-5" />
        <span>Verification Logs</span>
      </router-link>

      <!-- Analytics -->
      <router-link
        to="/analytics"
        class="nav-item"
        :class="{ 'nav-item-active': $route.path === '/analytics' }"
      >
        <BarChart3Icon class="w-5 h-5" />
        <span>Analytics</span>
      </router-link>

      <!-- Alerts -->
      <router-link
        to="/alerts"
        class="nav-item"
        :class="{ 'nav-item-active': $route.path === '/alerts' }"
      >
        <AlertTriangleIcon class="w-5 h-5" />
        <span>Alerts</span>
        <span v-if="unreadAlerts > 0" class="ml-auto bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 text-xs px-2 py-1 rounded-full">
          {{ unreadAlerts }}
        </span>
      </router-link>

      <!-- UIDAI Portal -->
      <a
        href="/uidai"
        target="_blank"
        class="nav-item hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
        title="Visit UIDAI Government Portal (Protected by Passive CAPTCHA)"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <span>UIDAI Portal</span>
        <svg class="w-4 h-4 ml-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>
      </a>

      <!-- Separator -->
      <div class="border-t border-gray-200 dark:border-gray-700 my-4"></div>

      <!-- Settings -->
      <router-link
        to="/settings"
        class="nav-item"
        :class="{ 'nav-item-active': $route.path === '/settings' }"
      >
        <SettingsIcon class="w-5 h-5" />
        <span>Settings</span>
      </router-link>

      <!-- API Documentation -->
      <router-link
        to="/api-docs"
        class="nav-item"
        :class="{ 'nav-item-active': $route.path === '/api-docs' }"
      >
        <BookOpenIcon class="w-5 h-5" />
        <span>API Docs</span>
      </router-link>

      <!-- System Health -->
      <div class="nav-item cursor-default">
        <ActivityIcon class="w-5 h-5" />
        <span>System Health</span>
        <div class="ml-auto flex items-center space-x-1">
          <div
            :class="[
              'w-2 h-2 rounded-full',
              systemStatus === 'healthy' ? 'bg-green-500' :
              systemStatus === 'warning' ? 'bg-yellow-500' :
              'bg-red-500'
            ]"
          ></div>
          <span class="text-xs capitalize">{{ systemStatus }}</span>
        </div>
      </div>
    </nav>

    <!-- Quick Stats Panel -->
    <div class="p-4 mt-8 border-t border-gray-200 dark:border-gray-700">
      <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-3">
        Quick Stats
      </h3>
      
      <div class="space-y-3">
        <!-- Total Verifications -->
        <div class="flex justify-between items-center">
          <span class="text-xs text-gray-600 dark:text-gray-400">
            Total Verifications
          </span>
          <span class="text-sm font-semibold text-gray-900 dark:text-white">
            {{ formatNumber(totalVerifications) }}
          </span>
        </div>

        <!-- Human Rate -->
        <div class="flex justify-between items-center">
          <span class="text-xs text-gray-600 dark:text-gray-400">
            Human Rate
          </span>
          <span class="text-sm font-semibold text-green-600">
            {{ humanRate }}%
          </span>
        </div>

        <!-- Active Websites -->
        <div class="flex justify-between items-center">
          <span class="text-xs text-gray-600 dark:text-gray-400">
            Active Sites
          </span>
          <span class="text-sm font-semibold text-blue-600">
            {{ activeWebsiteCount }}
          </span>
        </div>

        <!-- Model Status -->
        <div class="flex justify-between items-center">
          <span class="text-xs text-gray-600 dark:text-gray-400">
            ML Model
          </span>
          <span 
            :class="[
              'text-sm font-semibold',
              modelLoaded ? 'text-green-600' : 'text-red-600'
            ]"
          >
            {{ modelLoaded ? 'Active' : 'Error' }}
          </span>
        </div>
      </div>

      <!-- Model Info -->
      <div v-if="modelInfo" class="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
        <div class="text-xs text-gray-600 dark:text-gray-400 mb-1">
          Algorithm
        </div>
        <div class="text-sm font-medium text-gray-900 dark:text-white">
          {{ modelInfo.algorithm || 'Random Forest' }}
        </div>
        <div v-if="modelInfo.accuracy" class="text-xs text-gray-600 dark:text-gray-400 mt-1">
          Accuracy: {{ Math.round(modelInfo.accuracy * 100) }}%
        </div>
      </div>
    </div>

    <!-- Version Info -->
    <div class="absolute bottom-4 left-4 right-4">
      <div class="text-xs text-gray-500 dark:text-gray-400 text-center">
        Passive CAPTCHA v{{ version }}
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useDashboardStore } from '@/stores/dashboard'
import { useWebsiteStore } from '@/stores/websites'
import {
  LayoutDashboardIcon,
  GlobeIcon,
  FileTextIcon,
  BarChart3Icon,
  AlertTriangleIcon,
  SettingsIcon,
  BookOpenIcon,
  ActivityIcon
} from 'lucide-vue-next'

// Stores
const route = useRoute()
const dashboardStore = useDashboardStore()
const websiteStore = useWebsiteStore()

// Computed
const totalVerifications = computed(() => dashboardStore.stats.totalVerifications)
const humanRate = computed(() => dashboardStore.stats.humanRate)
const activeWebsiteCount = computed(() => websiteStore.activeWebsiteCount)
const unreadAlerts = computed(() => 
  dashboardStore.recentAlerts.filter(alert => !alert.isRead).length
)

const systemStatus = computed(() => {
  const health = dashboardStore.systemHealth
  if (!health.model.loaded || health.database.status !== 'healthy') {
    return 'error'
  }
  if (health.database.last24hVerifications > 1000) {
    return 'warning'
  }
  return 'healthy'
})

const modelLoaded = computed(() => dashboardStore.systemHealth.model.loaded)
const modelInfo = computed(() => dashboardStore.systemHealth.model.info)

const version = '1.0.0'

// Methods
const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}
</script>

<style scoped>
.nav-item {
  @apply flex items-center space-x-3 px-3 py-2 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200;
}

.nav-item-active {
  @apply bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 font-medium;
}

.nav-item-active:hover {
  @apply bg-blue-200 dark:bg-blue-800;
}

/* Custom scrollbar for sidebar */
aside {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e0 transparent;
}

aside::-webkit-scrollbar {
  width: 4px;
}

aside::-webkit-scrollbar-track {
  background: transparent;
}

aside::-webkit-scrollbar-thumb {
  background-color: #cbd5e0;
  border-radius: 2px;
}

aside::-webkit-scrollbar-thumb:hover {
  background-color: #a0aec0;
}

/* Dark mode scrollbar */
.dark aside {
  scrollbar-color: #4a5568 transparent;
}

.dark aside::-webkit-scrollbar-thumb {
  background-color: #4a5568;
}

.dark aside::-webkit-scrollbar-thumb:hover {
  background-color: #2d3748;
}

/* Hover effects */
.nav-item:hover {
  transform: translateX(2px);
}

/* Badge animations */
.nav-item span:last-child {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Quick stats animations */
.space-y-3 > div {
  transition: all 0.2s ease;
}

.space-y-3 > div:hover {
  background-color: rgba(59, 130, 246, 0.05);
  border-radius: 4px;
  padding: 4px 8px;
  margin: -4px -8px;
}
</style>