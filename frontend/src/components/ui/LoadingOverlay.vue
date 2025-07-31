<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white dark:bg-gray-800 rounded-lg p-6 flex items-center space-x-3 shadow-lg">
      <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"></div>
      <span class="text-gray-900 dark:text-white font-medium">Loading...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
// Loading overlay component
</script>

<style scoped>
/* Loading animation */
.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>