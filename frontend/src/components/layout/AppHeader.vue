<template>
  <header class="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
    <div class="flex items-center justify-between px-6 py-4">
      <!-- Logo and Title -->
      <div class="flex items-center space-x-4">
        <div class="flex items-center space-x-2">
          <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <ShieldCheckIcon class="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 class="text-xl font-bold text-gray-900 dark:text-white">
              Passive CAPTCHA
            </h1>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              Admin Dashboard
            </p>
          </div>
        </div>
      </div>

      <!-- Search Bar -->
      <div class="flex-1 max-w-md mx-8">
        <div class="relative">
          <SearchIcon class="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search logs, websites, or alerts..."
            class="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            @keyup.enter="handleSearch"
          />
        </div>
      </div>

      <!-- Right Side Actions -->
      <div class="flex items-center space-x-4">
        <!-- Notifications -->
        <div class="relative">
          <button
            @click="toggleNotifications"
            class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 relative"
          >
            <BellIcon class="w-6 h-6" />
            <span
              v-if="unreadNotifications > 0"
              class="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center"
            >
              {{ unreadNotifications > 9 ? '9+' : unreadNotifications }}
            </span>
          </button>
          
          <!-- Notifications Dropdown -->
          <div
            v-if="showNotifications"
            class="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50"
          >
            <div class="p-4 border-b border-gray-200 dark:border-gray-700">
              <h3 class="text-sm font-semibold text-gray-900 dark:text-white">
                Notifications
              </h3>
            </div>
            <div class="max-h-96 overflow-y-auto">
              <div
                v-for="notification in notifications"
                :key="notification.id"
                class="p-4 border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                <div class="flex items-start space-x-3">
                  <div
                    :class="[
                      'w-2 h-2 rounded-full mt-2',
                      notification.type === 'error' ? 'bg-red-500' :
                      notification.type === 'warning' ? 'bg-yellow-500' :
                      'bg-blue-500'
                    ]"
                  ></div>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-900 dark:text-white">
                      {{ notification.title }}
                    </p>
                    <p class="text-sm text-gray-600 dark:text-gray-400">
                      {{ notification.message }}
                    </p>
                    <p class="text-xs text-gray-500 dark:text-gray-500 mt-1">
                      {{ formatTime(notification.timestamp) }}
                    </p>
                  </div>
                </div>
              </div>
              <div v-if="notifications.length === 0" class="p-4 text-center text-gray-500 dark:text-gray-400">
                No new notifications
              </div>
            </div>
          </div>
        </div>

        <!-- Theme Toggle -->
        <button
          @click="toggleTheme"
          class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        >
          <SunIcon v-if="isDark" class="w-6 h-6" />
          <MoonIcon v-else class="w-6 h-6" />
        </button>

        <!-- System Status -->
        <div class="flex items-center space-x-2">
          <div
            :class="[
              'w-2 h-2 rounded-full',
              systemStatus === 'healthy' ? 'bg-green-500' :
              systemStatus === 'warning' ? 'bg-yellow-500' :
              'bg-red-500'
            ]"
          ></div>
          <span class="text-sm text-gray-600 dark:text-gray-400 capitalize">
            {{ systemStatus }}
          </span>
        </div>

        <!-- User Menu -->
        <div class="relative">
          <button
            @click="toggleUserMenu"
            class="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <UserIcon class="w-5 h-5 text-white" />
            </div>
            <ChevronDownIcon class="w-4 h-4 text-gray-400" />
          </button>
          
          <!-- User Dropdown -->
          <div
            v-if="showUserMenu"
            class="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50"
          >
            <div class="p-2">
              <button
                @click="handleLogout"
                class="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md flex items-center space-x-2"
              >
                <LogOutIcon class="w-4 h-4" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { useDashboardStore } from '@/stores/dashboard'
import { useAuthStore } from '@/stores/auth'
import {
  ShieldCheckIcon,
  SearchIcon,
  BellIcon,
  SunIcon,
  MoonIcon,
  UserIcon,
  ChevronDownIcon,
  LogOutIcon
} from 'lucide-vue-next'

// Stores
const appStore = useAppStore()
const dashboardStore = useDashboardStore()
const authStore = useAuthStore()

// State
const searchQuery = ref('')
const showNotifications = ref(false)
const showUserMenu = ref(false)
const isDark = ref(false)

// Computed
const notifications = computed(() => dashboardStore.recentAlerts)
const unreadNotifications = computed(() => 
  notifications.value.filter(n => !n.isRead).length
)
const systemStatus = computed(() => {
  const health = dashboardStore.systemHealth
  if (!health.model.loaded || health.database.status !== 'healthy') {
    return 'error'
  }
  if (health.database.last24hVerifications > 1000) {
    return 'warning'
  }
  return 'healthy'
})

// Methods
const toggleNotifications = () => {
  showNotifications.value = !showNotifications.value
  showUserMenu.value = false
}

const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value
  showNotifications.value = false
}

const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

const handleSearch = () => {
  if (!searchQuery.value.trim()) return
  
  // Implement search functionality
  console.log('Searching for:', searchQuery.value)
  // This could navigate to a search results page or filter current data
}

const handleLogout = async () => {
  try {
    await authStore.logout()
    showUserMenu.value = false
  } catch (error) {
    console.error('Logout error:', error)
  }
}

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return 'Just now'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
  return `${Math.floor(diff / 86400000)}d ago`
}

// Close dropdowns when clicking outside
const handleClickOutside = (event: Event) => {
  const target = event.target as HTMLElement
  if (!target.closest('.relative')) {
    showNotifications.value = false
    showUserMenu.value = false
  }
}

// Lifecycle
onMounted(() => {
  // Set initial theme
  const savedTheme = localStorage.getItem('theme')
  isDark.value = savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)
  document.documentElement.classList.toggle('dark', isDark.value)
  
  // Add click outside listener
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* Custom animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Search input focus effect */
input:focus {
  transform: scale(1.02);
  transition: transform 0.2s ease;
}

/* Notification badge pulse */
.absolute span {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}
</style>