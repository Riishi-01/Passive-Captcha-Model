<template>
  <div class="space-y-6">
    <!-- Breadcrumb -->
    <nav class="flex" aria-label="Breadcrumb">
      <ol class="flex items-center space-x-4">
        <li>
          <router-link to="/dashboard/websites" class="text-gray-400 hover:text-gray-500">
            Websites
          </router-link>
        </li>
        <li>
          <svg class="flex-shrink-0 h-5 w-5 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
          </svg>
        </li>
        <li>
          <span class="text-gray-500">{{ website?.domain || 'Website Details' }}</span>
        </li>
      </ol>
    </nav>

    <!-- Page Header -->
    <div class="sm:flex sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ website?.domain || 'Website Details' }}
        </h1>
        <p class="text-gray-600 dark:text-gray-400 mt-1">
          Detailed analytics and settings for this website
        </p>
      </div>
    </div>

    <!-- Website Info Card -->
    <div v-if="website" class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <h2 class="text-lg font-medium text-gray-900 dark:text-white mb-4">Website Information</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Domain</dt>
          <dd class="mt-1 text-sm text-gray-900 dark:text-white">{{ website.domain }}</dd>
        </div>
        
        <div>
          <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Status</dt>
          <dd class="mt-1">
            <span 
              :class="[
                'px-2 py-1 text-xs font-medium rounded-full',
                website.status === 'active' 
                  ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                  : 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
              ]"
            >
              {{ website.status }}
            </span>
          </dd>
        </div>
        
        <div>
          <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Total Verifications</dt>
          <dd class="mt-1 text-sm text-gray-900 dark:text-white">{{ website.totalVerifications }}</dd>
        </div>
        
        <div>
          <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Human Rate</dt>
          <dd class="mt-1 text-sm text-gray-900 dark:text-white">{{ website.humanRate }}%</dd>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-else-if="isLoading" class="text-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
      <p class="mt-2 text-sm text-gray-500">Loading website details...</p>
    </div>

    <!-- Error State -->
    <div v-else class="text-center py-12">
      <div class="mx-auto h-12 w-12 text-red-400">
        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      </div>
      <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">Website not found</h3>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">The website you're looking for doesn't exist.</p>
      <div class="mt-6">
        <router-link to="/dashboard/websites" class="btn btn-outline">
          Back to Websites
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useWebsiteStore } from '../_stores/useWebsites'

// Router
const route = useRoute()

// Store
const websiteStore = useWebsiteStore()

// Computed
const website = computed(() => websiteStore.currentWebsite)
const isLoading = computed(() => websiteStore.isLoading)

// Methods
const loadWebsite = async () => {
  const id = route.params.id as string
  if (id) {
    try {
      await websiteStore.fetchWebsite(id)
    } catch (error) {
      console.error('Failed to load website:', error)
    }
  }
}

// Lifecycle
onMounted(loadWebsite)

// Watch route changes
watch(() => route.params.id, loadWebsite)
</script>