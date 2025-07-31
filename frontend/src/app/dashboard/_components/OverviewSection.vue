<template>
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <!-- Active Websites -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Active Websites
      </h3>
      <div class="space-y-3">
        <div 
          v-for="website in activeWebsites.slice(0, 3)" 
          :key="website.id"
          class="flex items-center justify-between"
        >
          <div>
            <p class="text-sm font-medium text-gray-900 dark:text-white">
              {{ website.domain }}
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              {{ website.totalVerifications }} verifications
            </p>
          </div>
          <span class="text-xs text-green-600 dark:text-green-400">
            {{ website.humanRate }}%
          </span>
        </div>
        <router-link 
          to="/dashboard/websites"
          class="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 block mt-4"
        >
          View all websites →
        </router-link>
      </div>
    </div>

    <!-- Recent Alerts -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Recent Alerts
      </h3>
      <div v-if="recentAlerts.length" class="space-y-3">
        <div 
          v-for="alert in recentAlerts.slice(0, 3)" 
          :key="alert.id"
          class="flex items-start space-x-3"
        >
          <div 
            :class="[
              'w-2 h-2 rounded-full mt-2',
              alert.type === 'error' ? 'bg-red-400' : 
              alert.type === 'warning' ? 'bg-yellow-400' : 'bg-blue-400'
            ]"
          ></div>
          <div class="flex-1 min-w-0">
            <p class="text-sm text-gray-900 dark:text-white">{{ alert.message }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ formatDate(alert.timestamp) }}</p>
          </div>
        </div>
      </div>
      <div v-else class="text-center text-gray-500 dark:text-gray-400 text-sm">
        No recent alerts
      </div>
    </div>

    <!-- System Health -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        System Health
      </h3>
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-600 dark:text-gray-400">API Server</span>
          <div class="flex items-center space-x-2">
            <div 
              :class="[
                'w-2 h-2 rounded-full',
                systemHealth.api === 'up' ? 'bg-green-400' : 'bg-red-400'
              ]"
            ></div>
            <span class="text-sm text-gray-900 dark:text-white">
              {{ systemHealth.api === 'up' ? 'Online' : 'Offline' }}
            </span>
          </div>
        </div>
        
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-600 dark:text-gray-400">Database</span>
          <div class="flex items-center space-x-2">
            <div 
              :class="[
                'w-2 h-2 rounded-full',
                systemHealth.database === 'connected' ? 'bg-green-400' : 'bg-red-400'
              ]"
            ></div>
            <span class="text-sm text-gray-900 dark:text-white">
              {{ systemHealth.database === 'connected' ? 'Connected' : 'Disconnected' }}
            </span>
          </div>
        </div>
        
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-600 dark:text-gray-400">ML Model</span>
          <div class="flex items-center space-x-2">
            <div 
              :class="[
                'w-2 h-2 rounded-full',
                systemHealth.mlModel === 'loaded' ? 'bg-green-400' : 'bg-red-400'
              ]"
            ></div>
            <span class="text-sm text-gray-900 dark:text-white">
              {{ systemHealth.mlModel === 'loaded' ? 'Loaded' : 'Not Loaded' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDashboardStore } from '../_stores/useDashboard'
import { useWebsiteStore } from '../websites/_stores/useWebsites'

// Stores
const dashboardStore = useDashboardStore()
const websiteStore = useWebsiteStore()

// Computed
const activeWebsites = computed(() => websiteStore.activeWebsites)
const recentAlerts = computed(() => dashboardStore.recentAlerts)
const systemHealth = computed(() => dashboardStore.systemHealth)

// Methods
const formatDate = (timestamp: string) => {
  return new Date(timestamp).toLocaleDateString()
}
</script>