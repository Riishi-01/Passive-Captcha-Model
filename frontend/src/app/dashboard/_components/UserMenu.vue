<template>
  <div class="relative">
    <button
      @click="isOpen = !isOpen"
      class="flex items-center space-x-2 p-2 text-gray-400 hover:text-gray-500 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 rounded-md"
    >
      <div class="h-8 w-8 rounded-full bg-indigo-600 flex items-center justify-center">
        <UserIcon class="h-5 w-5 text-white" />
      </div>
      <ChevronDownIcon class="h-4 w-4" />
    </button>

    <!-- Dropdown -->
    <div
      v-if="isOpen"
      @click.away="isOpen = false"
      class="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 z-50"
    >
      <div class="py-1">
        <router-link
          to="/dashboard/profile"
          @click="isOpen = false"
          class="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          Profile
        </router-link>
        <router-link
          to="/dashboard/settings"
          @click="isOpen = false"
          class="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          Settings
        </router-link>
        <hr class="border-gray-200 dark:border-gray-700" />
        <button
          @click="handleLogout"
          class="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          Sign out
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { UserIcon, ChevronDownIcon } from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'

// State
const isOpen = ref(false)

// Stores
const authStore = useAuthStore()
const appStore = useAppStore()
const router = useRouter()

// Methods
const handleLogout = async () => {
  isOpen.value = false
  await authStore.logout()
  
  appStore.addNotification({
    type: 'success',
    title: 'Signed out',
    message: 'You have been successfully signed out'
  })
  
  router.push('/login')
}
</script>