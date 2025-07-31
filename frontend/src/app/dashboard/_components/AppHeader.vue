<template>
  <header class="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
    <div class="px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">
        <!-- Logo and Title -->
        <div class="flex items-center space-x-4">
          <div class="flex items-center space-x-3">
            <div class="h-8 w-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <svg class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.031 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <h1 class="text-lg font-semibold text-gray-900 dark:text-white">
                Passive CAPTCHA
              </h1>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                Admin Dashboard
              </p>
            </div>
          </div>
        </div>

        <!-- Right side controls -->
        <div class="flex items-center space-x-4">
          <!-- System Status Indicator -->
          <SystemStatusIndicator />

          <!-- Theme Toggle -->
          <ThemeToggle />

          <!-- Notifications -->
          <NotificationBell />

          <!-- User Menu -->
          <UserMenu />
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import SystemStatusIndicator from './SystemStatusIndicator.vue'
import ThemeToggle from './ThemeToggle.vue'
import NotificationBell from './NotificationBell.vue'
import UserMenu from './UserMenu.vue'
</script>

<style scoped>
/* Header specific styles */
header {
  position: sticky;
  top: 0;
  z-index: 40;
  backdrop-filter: blur(8px);
}
</style>