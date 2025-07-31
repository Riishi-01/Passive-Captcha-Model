<template>
  <div class="flex items-center space-x-2">
    <div 
      :class="[
        'w-2 h-2 rounded-full',
        isHealthy ? 'bg-green-400' : 'bg-red-400'
      ]"
      :title="statusText"
    ></div>
    <span class="text-xs text-gray-500 dark:text-gray-400 hidden sm:inline">
      {{ statusText }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDashboardStore } from '../_stores/useDashboard'

// Store
const dashboardStore = useDashboardStore()

// Computed
const isHealthy = computed(() => dashboardStore.isHealthy)
const statusText = computed(() => isHealthy.value ? 'System Healthy' : 'System Issues')
</script>