<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="sm:flex sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Websites
        </h1>
        <p class="text-gray-600 dark:text-gray-400 mt-1">
          Manage your websites and their passive CAPTCHA protection
        </p>
      </div>
      
      <div class="mt-4 sm:mt-0">
        <button class="btn btn-primary">
          Add Website
        </button>
      </div>
    </div>

    <!-- Sample Websites -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-medium text-gray-900 dark:text-white">
            example.com
          </h3>
          <span class="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
            active
          </span>
        </div>
        
        <div class="mt-4 space-y-2">
          <div class="flex justify-between text-sm">
            <span class="text-gray-500 dark:text-gray-400">Verifications:</span>
            <span class="font-medium text-gray-900 dark:text-white">1,543</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-gray-500 dark:text-gray-400">Human Rate:</span>
            <span class="font-medium text-gray-900 dark:text-white">85.7%</span>
          </div>
        </div>
        
        <div class="mt-4 flex space-x-2">
          <router-link 
            to="/dashboard/websites/1"
            class="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 flex-1 text-center"
          >
            View Details
          </router-link>
          <button class="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600">
            Settings
          </button>
        </div>
      </div>
      
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-medium text-gray-900 dark:text-white">
            demo.site
          </h3>
          <span class="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
            active
          </span>
        </div>
        
        <div class="mt-4 space-y-2">
          <div class="flex justify-between text-sm">
            <span class="text-gray-500 dark:text-gray-400">Verifications:</span>
            <span class="font-medium text-gray-900 dark:text-white">892</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-gray-500 dark:text-gray-400">Human Rate:</span>
            <span class="font-medium text-gray-900 dark:text-white">78.3%</span>
          </div>
        </div>
        
        <div class="mt-4 flex space-x-2">
          <router-link 
            to="/dashboard/websites/2"
            class="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 flex-1 text-center"
          >
            View Details
          </router-link>
          <button class="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600">
            Settings
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Simplified websites page
console.log('Websites page loaded successfully!')
</script>