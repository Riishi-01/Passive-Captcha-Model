<template>
  <button
    class="p-2 text-gray-400 hover:text-gray-500 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 rounded-md relative"
    title="Notifications"
  >
    <BellIcon class="h-5 w-5" />
    <span 
      v-if="notificationCount > 0"
      class="absolute top-0 right-0 -mt-1 -mr-1 px-2 py-1 text-xs font-medium text-white bg-red-500 rounded-full"
    >
      {{ notificationCount > 9 ? '9+' : notificationCount }}
    </span>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { BellIcon } from '@heroicons/vue/24/outline'
import { useAppStore } from '@/stores/app'

// Store
const appStore = useAppStore()

// Computed
const notificationCount = computed(() => appStore.notifications.length)
</script>