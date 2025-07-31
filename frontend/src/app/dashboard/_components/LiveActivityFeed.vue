<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center space-x-3">
        <div class="flex items-center space-x-2">
          <div 
            :class="[
              'w-3 h-3 rounded-full',
              isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'
            ]"
          ></div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Live Activity Feed
          </h3>
        </div>
        <span 
          :class="[
            'text-xs px-2 py-1 rounded-full',
            isConnected 
              ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
              : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
          ]"
        >
          {{ isConnected ? 'Connected' : 'Disconnected' }}
        </span>
      </div>

      <!-- Controls -->
      <div class="flex items-center space-x-2">
        <!-- Filter Dropdown -->
        <select
          v-model="selectedFilter"
          @change="$emit('filter', selectedFilter)"
          class="text-sm border border-gray-300 dark:border-gray-600 rounded-md px-3 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
        >
          <option value="all">All Activity</option>
          <option value="human">Human Only</option>
          <option value="bot">Bot Only</option>
          <option value="suspicious">Suspicious</option>
        </select>

        <!-- Export Button -->
        <div class="relative">
          <button
            @click="showExportMenu = !showExportMenu"
            class="flex items-center space-x-2 px-3 py-1 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors"
          >
            <ArrowDownTrayIcon class="h-4 w-4" />
            <span>Export</span>
          </button>

          <!-- Export Menu -->
          <div
            v-if="showExportMenu"
            class="absolute right-0 top-full mt-2 w-32 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50"
          >
            <button
              @click="handleExport('csv')"
              class="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 first:rounded-t-lg"
            >
              CSV Format
            </button>
            <button
              @click="handleExport('json')"
              class="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              JSON Format
            </button>
            <button
              @click="handleExport('excel')"
              class="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 last:rounded-b-lg"
            >
              Excel Format
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Activity Feed -->
    <div class="space-y-3 max-h-96 overflow-y-auto">
      <!-- Sample Log Entries -->
      <div 
        v-for="log in sampleLogs" 
        :key="log.id"
        class="flex items-start space-x-4 p-3 rounded-lg border border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
      >
        <!-- Status Icon -->
        <div 
          :class="[
            'w-3 h-3 rounded-full mt-2 flex-shrink-0',
            log.type === 'human' ? 'bg-green-500' : 'bg-red-500'
          ]"
        ></div>

        <!-- Log Content -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <span 
                :class="[
                  'text-sm font-medium',
                  log.type === 'human' ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400'
                ]"
              >
                {{ log.type === 'human' ? 'Human Verified' : 'Bot Detected' }}
              </span>
              <span class="text-xs text-gray-500 dark:text-gray-400">
                {{ log.confidence }}% confidence
              </span>
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400">
              {{ formatTime(log.timestamp) }}
            </div>
          </div>
          
          <div class="mt-1 text-sm text-gray-600 dark:text-gray-400">
            <div class="flex items-center space-x-4">
              <span>IP: {{ log.ip }}</span>
              <span>{{ log.country }}</span>
              <span>{{ log.website }}</span>
            </div>
          </div>
          
          <div class="mt-1 text-xs text-gray-500 dark:text-gray-400 truncate">
            {{ log.userAgent }}
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="!sampleLogs.length" class="text-center py-8">
        <div class="w-16 h-16 mx-auto mb-4 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
          <ClockIcon class="w-8 h-8 text-gray-400" />
        </div>
        <p class="text-sm text-gray-500 dark:text-gray-400">No activity logs yet</p>
        <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">Logs will appear here as verifications happen</p>
      </div>
    </div>

    <!-- Footer -->
    <div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
      <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
        <span>{{ sampleLogs.length }} entries shown</span>
        <span>Auto-refresh: {{ isConnected ? 'On' : 'Off' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ArrowDownTrayIcon, ClockIcon } from '@heroicons/vue/24/outline'

interface LogEntry {
  id: number
  timestamp: Date
  type: 'human' | 'bot'
  ip: string
  country: string
  confidence: number
  userAgent: string
  website: string
}

interface Props {
  logs: LogEntry[]
  isConnected: boolean
}

defineProps<Props>()
defineEmits<{
  export: [format: string]
  filter: [filter: string]
}>()

// State
const selectedFilter = ref('all')
const showExportMenu = ref(false)

// Sample data
const sampleLogs = ref<LogEntry[]>([
  {
    id: 1,
    timestamp: new Date(Date.now() - 1000 * 30),
    type: 'human',
    ip: '192.168.1.100',
    country: 'US',
    confidence: 94,
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    website: 'example.com'
  },
  {
    id: 2,
    timestamp: new Date(Date.now() - 1000 * 45),
    type: 'bot',
    ip: '10.0.0.50',
    country: 'CN',
    confidence: 87,
    userAgent: 'Python/3.9 requests/2.25.1',
    website: 'demo.site'
  },
  {
    id: 3,
    timestamp: new Date(Date.now() - 1000 * 60),
    type: 'human',
    ip: '172.16.0.25',
    country: 'GB',
    confidence: 91,
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    website: 'example.com'
  },
  {
    id: 4,
    timestamp: new Date(Date.now() - 1000 * 90),
    type: 'bot',
    ip: '203.0.113.15',
    country: 'RU',
    confidence: 76,
    userAgent: 'curl/7.68.0',
    website: 'test.portal.com'
  },
  {
    id: 5,
    timestamp: new Date(Date.now() - 1000 * 120),
    type: 'human',
    ip: '198.51.100.42',
    country: 'DE',
    confidence: 89,
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    website: 'demo.site'
  }
])

// Methods
const formatTime = (timestamp: Date): string => {
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - timestamp.getTime()) / 1000)
  
  if (diffInSeconds < 60) {
    return `${diffInSeconds}s ago`
  } else if (diffInSeconds < 3600) {
    return `${Math.floor(diffInSeconds / 60)}m ago`
  } else {
    return timestamp.toLocaleTimeString()
  }
}

const handleExport = (format: string) => {
  showExportMenu.value = false
  // Emit the export event with the selected format
}
</script>

<style scoped>
/* Activity feed animations */
.space-y-3 > * {
  animation: slideInLeft 0.3s ease-out;
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Pulse animation for connection indicator */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>