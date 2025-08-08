<template>
  <div v-if="hasError" class="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
    <div class="max-w-md w-full">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-red-200 dark:border-red-800 p-6">
        <div class="flex items-center space-x-3 mb-4">
          <ExclamationTriangleIcon class="h-8 w-8 text-red-500" />
          <div>
            <h1 class="text-lg font-semibold text-gray-900 dark:text-white">Something went wrong</h1>
            <p class="text-sm text-gray-600 dark:text-gray-400">An unexpected error occurred</p>
          </div>
        </div>
        
        <div v-if="error && showDetails" class="mb-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
          <p class="text-xs font-mono text-gray-700 dark:text-gray-300 break-all">
            {{ error.message || error.toString() }}
          </p>
        </div>
        
        <div class="flex flex-col sm:flex-row gap-3">
          <button
            @click="retry"
            class="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
          >
            Try Again
          </button>
          <button
            @click="goHome"
            class="flex-1 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-gray-100 px-4 py-2 rounded-md text-sm font-medium transition-colors"
          >
            Go to Dashboard
          </button>
        </div>
        
        <button
          @click="showDetails = !showDetails"
          class="w-full mt-3 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
        >
          {{ showDetails ? 'Hide' : 'Show' }} Error Details
        </button>
      </div>
    </div>
  </div>
  <slot v-else />
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'
import { useRouter } from 'vue-router'
import { ExclamationTriangleIcon } from '@heroicons/vue/24/outline'

const router = useRouter()

const hasError = ref(false)
const error = ref<Error | null>(null)
const showDetails = ref(false)

const retry = () => {
  hasError.value = false
  error.value = null
  showDetails.value = false
  // Force component re-render
  window.location.reload()
}

const goHome = () => {
  hasError.value = false
  error.value = null
  showDetails.value = false
  router.push('/dashboard')
}

onErrorCaptured((err: Error) => {
  console.error('Error caught by boundary:', err)
  hasError.value = true
  error.value = err
  return false // Prevent error from propagating
})
</script>