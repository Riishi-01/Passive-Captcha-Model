<template>
  <aside class="hidden md:flex md:flex-shrink-0">
    <div class="flex flex-col w-64">
      <div class="flex flex-col h-0 flex-1 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
        <!-- Navigation -->
        <nav class="flex-1 px-4 pt-6 pb-4 space-y-1">
          <router-link
            v-for="item in navigation"
            :key="item.name"
            :to="item.href"
            :class="[
              item.current
                ? 'bg-indigo-50 dark:bg-indigo-900/20 border-indigo-500 text-indigo-700 dark:text-indigo-200'
                : 'border-transparent text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white',
              'group flex items-center px-3 py-2 text-sm font-medium border-l-4 transition-colors duration-200'
            ]"
          >
            <component
              :is="item.icon"
              :class="[
                item.current 
                  ? 'text-indigo-500 dark:text-indigo-300' 
                  : 'text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-300',
                'mr-3 h-5 w-5 transition-colors duration-200'
              ]"
            />
            {{ item.name }}
          </router-link>
        </nav>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  HomeIcon,
  GlobeAltIcon,
  ChartBarIcon,
  CogIcon,
  UserIcon
} from '@heroicons/vue/24/outline'

// Router
const route = useRoute()

// Navigation items
const navigationItems = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Websites', href: '/dashboard/websites', icon: GlobeAltIcon },
  { name: 'Analytics', href: '/dashboard/analytics', icon: ChartBarIcon },
  { name: 'Settings', href: '/dashboard/settings', icon: CogIcon },
  { name: 'Profile', href: '/dashboard/profile', icon: UserIcon }
]

// Computed
const navigation = computed(() =>
  navigationItems.map(item => ({
    ...item,
    current: route.path === item.href || (item.href !== '/dashboard' && route.path.startsWith(item.href))
  }))
)
</script>

<style scoped>
/* Sidebar specific styles */
aside {
  position: sticky;
  top: 64px; /* Header height */
  height: calc(100vh - 64px);
}

/* Active link animation */
.router-link-active {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(-4px);
    opacity: 0.8;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
</style>