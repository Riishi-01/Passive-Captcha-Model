<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click="handleBackdropClick">
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-2xl mx-4 transform transition-all duration-300 scale-100">
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          API Configuration
        </h3>
        <button
          @click="$emit('close')"
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
        >
          <XMarkIcon class="h-6 w-6" />
        </button>
      </div>

      <!-- Content -->
      <div class="p-6 space-y-6">
        <!-- API Key Section -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            API Key
          </label>
          <div class="flex space-x-2">
            <input
              v-model="apiKey"
              :type="showApiKey ? 'text' : 'password'"
              class="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
              placeholder="Enter your API key"
            />
            <button
              @click="showApiKey = !showApiKey"
              class="px-3 py-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <EyeIcon v-if="!showApiKey" class="h-5 w-5" />
              <EyeSlashIcon v-else class="h-5 w-5" />
            </button>
          </div>
        </div>

        <!-- API Endpoint -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            API Endpoint
          </label>
          <input
            v-model="apiEndpoint"
            type="url"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
            placeholder="https://api.example.com"
          />
        </div>

        <!-- Rate Limiting -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Rate Limit (requests/minute)
          </label>
          <input
            v-model.number="rateLimit"
            type="number"
            min="1"
            max="1000"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
          />
        </div>

        <!-- Test Connection -->
        <div>
          <button
            @click="testConnection"
            :disabled="isTestingConnection"
            class="w-full px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 rounded-lg transition-colors"
          >
            <span v-if="!isTestingConnection">Test Connection</span>
            <span v-else>Testing...</span>
          </button>
          
          <div v-if="connectionStatus" class="mt-2 text-sm" :class="connectionStatus.success ? 'text-green-600' : 'text-red-600'">
            {{ connectionStatus.message }}
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex justify-end space-x-3 p-6 border-t border-gray-200 dark:border-gray-700">
        <button
          @click="$emit('close')"
          class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
        >
          Cancel
        </button>
        <button
          @click="saveConfiguration"
          :disabled="isSaving"
          class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 rounded-lg transition-colors"
        >
          <span v-if="!isSaving">Save Configuration</span>
          <span v-else>Saving...</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { XMarkIcon, EyeIcon, EyeSlashIcon } from '@heroicons/vue/24/outline'

// Emits
defineEmits<{
  close: []
}>()

// State
const apiKey = ref('')
const apiEndpoint = ref('')
const rateLimit = ref(100)
const showApiKey = ref(false)
const isTestingConnection = ref(false)
const isSaving = ref(false)
const connectionStatus = ref<{success: boolean, message: string} | null>(null)

// Methods
const handleBackdropClick = (event: Event) => {
  if (event.target === event.currentTarget) {
    emit('close')
  }
}

const testConnection = async () => {
  isTestingConnection.value = true
  connectionStatus.value = null
  
  try {
    // Simulate API test
    await new Promise(resolve => setTimeout(resolve, 1000))
    connectionStatus.value = {
      success: true,
      message: 'Connection successful!'
    }
  } catch (error) {
    connectionStatus.value = {
      success: false,
      message: 'Connection failed. Please check your configuration.'
    }
  } finally {
    isTestingConnection.value = false
  }
}

const saveConfiguration = async () => {
  isSaving.value = true
  
  try {
    // Simulate save operation
    await new Promise(resolve => setTimeout(resolve, 500))
    emit('close')
  } catch (error) {
    console.error('Failed to save configuration:', error)
  } finally {
    isSaving.value = false
  }
}

const emit = defineEmits<{
  close: []
}>()
</script>