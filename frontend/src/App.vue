<template>
  <div id="app" class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Toast Container -->
    <div id="toast-container"></div>
    
    <!-- Main Router View -->
    <RouterView />
    
    <!-- Global Loading Indicator -->
    <LoadingOverlay v-if="isLoading" />
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'
import LoadingOverlay from '@/components/ui/LoadingOverlay.vue'

// Store
const appStore = useAppStore()

// Computed
const isLoading = computed(() => appStore.isLoading)
</script>

<style>
/* Global styles */
#app {
  font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  @apply bg-gray-100 dark:bg-gray-800;
}

::-webkit-scrollbar-thumb {
  @apply bg-gray-300 dark:bg-gray-600 rounded-full;
}

::-webkit-scrollbar-thumb:hover {
  @apply bg-gray-400 dark:bg-gray-500;
}

/* Custom scrollbar for Firefox */
* {
  scrollbar-width: thin;
  scrollbar-color: theme('colors.gray.300') theme('colors.gray.100');
}

@media (prefers-color-scheme: dark) {
  * {
    scrollbar-color: theme('colors.gray.600') theme('colors.gray.800');
  }
}

/* Focus ring improvements */
:focus {
  outline: 2px solid theme('colors.primary.500');
  outline-offset: 2px;
}

/* Smooth transitions */
* {
  transition-property: color, background-color, border-color, text-decoration-color, fill, stroke;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}
</style> 