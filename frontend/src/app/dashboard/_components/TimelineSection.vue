<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
    <div class="flex items-center justify-between mb-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
        Timeline Logs
      </h3>
      <div class="flex space-x-2">
        <select
          v-model="activeLogFilter"
          @change="handleLogFilterChange"
          class="text-sm border border-gray-300 dark:border-gray-600 rounded-md px-3 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        >
          <option value="all">All Logs</option>
          <option value="human">Human Only</option>
          <option value="bot">Bot Only</option>
          <option value="suspicious">Suspicious</option>
        </select>
        <button
          @click="refreshLogs"
          :disabled="isLoadingLogs"
          class="inline-flex items-center px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          <ArrowPathIcon 
            :class="[
              'h-4 w-4 mr-1',
              isLoadingLogs ? 'animate-spin' : ''
            ]" 
          />
          Refresh
        </button>
      </div>
    </div>
    
    <!-- Timeline Logs List -->
    <div v-if="timelineLogs.length" class="space-y-4 max-h-96 overflow-y-auto">
      <div 
        v-for="log in timelineLogs.slice(0, 10)" 
        :key="log.id"
        class="flex items-start space-x-4 pb-4 border-b border-gray-100 dark:border-gray-700 last:border-b-0"
      >
        <div 
          :class="[
            'w-3 h-3 rounded-full mt-1 flex-shrink-0',
            log.is_human ? 'bg-green-400' : 'bg-red-400'
          ]"
        ></div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between">
            <p class="text-sm font-medium text-gray-900 dark:text-white">
              {{ log.is_human ? 'Human' : 'Bot' }} Verification
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              {{ formatTimestamp(log.timestamp) }}
            </p>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Confidence: {{ Math.round(log.confidence * 100) }}% • 
            IP: {{ log.ip_address }} • 
            {{ log.user_agent ? log.user_agent.substring(0, 50) + '...' : 'Unknown UA' }}
          </p>
        </div>
      </div>
    </div>
    
    <!-- Empty State -->
    <div v-else-if="!isLoadingLogs" class="text-center py-8 text-gray-500 dark:text-gray-400">
      No logs available
    </div>
    
    <!-- Loading State -->
    <div v-else class="text-center py-8">
      <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600 mx-auto"></div>
      <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">Loading logs...</p>
    </div>
    
    <!-- View More Link -->
    <div v-if="timelineLogs.length > 10" class="mt-4 text-center">
      <router-link 
        to="/dashboard/logs"
        class="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-500"
      >
        View all logs →
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowPathIcon } from '@heroicons/vue/24/outline'
import { useDashboardStore } from '../_stores/useDashboard'
import { useDashboardData } from '../_composables/useDashboardData'

// Store and composables
const dashboardStore = useDashboardStore()
const { activeLogFilter, isLoadingLogs, refreshLogs, handleLogFilterChange } = useDashboardData()

// Computed
const timelineLogs = computed(() => dashboardStore.timelineLogs)

// Methods
const formatTimestamp = (timestamp: string) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString()
}
</script>