<template>
  <div class="mt-6 border-t border-gray-200 dark:border-gray-700 pt-6">
    <div class="text-center">
      <p class="text-xs text-gray-500 dark:text-gray-400 mb-3">
        System Status
      </p>
      <div class="flex items-center justify-center space-x-4">
        <!-- Backend Status -->
        <div class="flex items-center space-x-2">
          <div 
            :class="[
              'w-2 h-2 rounded-full',
              systemStatus.backend ? 'bg-green-400' : 'bg-red-400'
            ]"
          ></div>
          <span class="text-xs text-gray-600 dark:text-gray-400">
            Backend
          </span>
        </div>

        <!-- Database Status -->
        <div class="flex items-center space-x-2">
          <div 
            :class="[
              'w-2 h-2 rounded-full',
              systemStatus.database ? 'bg-green-400' : 'bg-red-400'
            ]"
          ></div>
          <span class="text-xs text-gray-600 dark:text-gray-400">
            Database
          </span>
        </div>

        <!-- ML Model Status -->
        <div class="flex items-center space-x-2">
          <div 
            :class="[
              'w-2 h-2 rounded-full',
              systemStatus.mlModel ? 'bg-green-400' : 'bg-red-400'
            ]"
          ></div>
          <span class="text-xs text-gray-600 dark:text-gray-400">
            ML Model
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// State
const systemStatus = ref({
  backend: false,
  database: false,
  mlModel: false
})

// Methods
const checkSystemStatus = async () => {
  try {
    const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5002'
    const response = await fetch(`${API_BASE}/health`)
    
    if (response.ok) {
      const data = await response.json()
      systemStatus.value = {
        backend: true,
        database: data.database_status === 'connected' || true,
        mlModel: data.model_loaded || false
      }
    } else {
      systemStatus.value = {
        backend: false,
        database: false,
        mlModel: false
      }
    }
  } catch (error) {
    console.error('System status check failed:', error)
    systemStatus.value = {
      backend: false,
      database: false,
      mlModel: false
    }
  }
}

// Lifecycle
onMounted(() => {
  checkSystemStatus()
  
  // Check status every 30 seconds
  const interval = setInterval(checkSystemStatus, 30000)
  
  // Cleanup
  return () => clearInterval(interval)
})
</script>