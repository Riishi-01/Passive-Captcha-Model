<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- One-Page Dashboard Header -->
    <header class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 sticky top-0 z-40">
      <div class="flex items-center justify-between">
        <!-- Left: Logo and Title -->
        <div class="flex items-center space-x-4">
          <div class="h-8 w-8 bg-indigo-600 rounded-lg flex items-center justify-center">
            <svg class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h1 class="text-xl font-bold text-gray-900 dark:text-white">
            Passive CAPTCHA Dashboard
          </h1>
        </div>
        
        <!-- Right: Settings Dropdown -->
        <div class="flex items-center space-x-4">
          <!-- System Status Indicator -->
          <div class="flex items-center space-x-2">
            <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span class="text-sm text-gray-600 dark:text-gray-400">System Online</span>
          </div>

          <!-- Settings Dropdown -->
          <div class="relative">
            <button
              @click="showSettingsMenu = !showSettingsMenu"
              class="flex items-center space-x-2 px-3 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <CogIcon class="h-5 w-5" />
              <span class="text-sm font-medium">Settings</span>
              <ChevronDownIcon class="h-4 w-4" />
            </button>

            <!-- Settings Dropdown Menu -->
            <div
              v-if="showSettingsMenu"
              class="absolute right-0 top-full mt-2 w-56 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50"
            >
              <div class="p-2">
                <!-- Website Management -->
                <button
                  @click="showWebsitesModal = true; showSettingsMenu = false"
                  class="w-full flex items-center space-x-3 px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
                >
                  <GlobeAltIcon class="h-4 w-4" />
                  <span>Manage Websites</span>
                </button>

                <!-- API Configuration -->
                <button
                  @click="showApiConfigModal = true; showSettingsMenu = false"
                  class="w-full flex items-center space-x-3 px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
                >
                  <KeyIcon class="h-4 w-4" />
                  <span>API Configuration</span>
                </button>

                <!-- Alert Settings -->
                <button
                  @click="showAlertSettingsModal = true; showSettingsMenu = false"
                  class="w-full flex items-center space-x-3 px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
                >
                  <BellIcon class="h-4 w-4" />
                  <span>Alert Settings</span>
                </button>

                <div class="border-t border-gray-200 dark:border-gray-600 my-2"></div>

                <!-- Export Data -->
                <button
                  @click="exportData(); showSettingsMenu = false"
                  class="w-full flex items-center space-x-3 px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
                >
                  <ArrowDownTrayIcon class="h-4 w-4" />
                  <span>Export Data</span>
                </button>

                <!-- Logout -->
                <button
                  @click="logout(); showSettingsMenu = false"
                  class="w-full flex items-center space-x-3 px-3 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md"
                >
                  <ArrowRightOnRectangleIcon class="h-4 w-4" />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content - Single Page Dashboard -->
    <main class="p-6">
      <RouterView />
    </main>

    <!-- Settings Modals -->
    <WebsitesModal 
      v-if="showWebsitesModal"
      @close="showWebsitesModal = false"
    />
    
    <ApiConfigModal 
      v-if="showApiConfigModal"
      @close="showApiConfigModal = false"
    />
    
    <AlertSettingsModal 
      v-if="showAlertSettingsModal"
      @close="showAlertSettingsModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { RouterView } from 'vue-router'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { 
  CogIcon, 
  ChevronDownIcon,
  GlobeAltIcon,
  KeyIcon,
  BellIcon,
  ArrowDownTrayIcon,
  ArrowRightOnRectangleIcon
} from '@heroicons/vue/24/outline'
import WebsitesModal from './_components/WebsitesModal.vue'
import ApiConfigModal from './_components/ApiConfigModal.vue'
import AlertSettingsModal from './_components/AlertSettingsModal.vue'

// State
const showSettingsMenu = ref(false)
const showWebsitesModal = ref(false)
const showApiConfigModal = ref(false)
const showAlertSettingsModal = ref(false)

// Stores
const router = useRouter()
const authStore = useAuthStore()

// Methods
const exportData = () => {
  console.log('Exporting dashboard data...')
  // Implement data export functionality
}

const logout = async () => {
  await authStore.logout()
  router.push('/login')
}

// Close dropdown when clicking outside
const handleClickOutside = (event: Event) => {
  const target = event.target as Element
  if (!target.closest('.relative')) {
    showSettingsMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* Clean one-page dashboard styles */
main {
  min-height: calc(100vh - 80px);
}

/* Smooth animations */
.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
</style>