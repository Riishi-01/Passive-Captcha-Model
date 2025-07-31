<template>
  <!-- Modal Backdrop -->
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click="handleBackdropClick">
    <!-- Modal Content -->
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-2xl mx-4">
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
        <!-- API Endpoint -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            API Endpoint
          </label>
          <input
            v-model="config.apiEndpoint"
            type="url"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
            placeholder="https://api.passivecaptcha.com"
          />
        </div>

        <!-- API Key -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            API Key
          </label>
          <div class="relative">
            <input
              v-model="config.apiKey"
              :type="showApiKey ? 'text' : 'password'"
              class="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
              placeholder="sk-..."
            />
            <button
              @click="showApiKey = !showApiKey"
              class="absolute inset-y-0 right-0 pr-3 flex items-center"
            >
              <EyeIcon v-if="!showApiKey" class="h-5 w-5 text-gray-400" />
              <EyeSlashIcon v-else class="h-5 w-5 text-gray-400" />
            </button>
          </div>
        </div>

        <!-- Rate Limiting -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Rate Limit (requests per minute)
          </label>
          <input
            v-model.number="config.rateLimit"
            type="number"
            min="1"
            max="1000"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
          />
        </div>

        <!-- Timeout -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Request Timeout (seconds)
          </label>
          <input
            v-model.number="config.timeout"
            type="number"
            min="1"
            max="60"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
          />
        </div>

        <!-- Enable SSL Verification -->
        <div class="flex items-center justify-between">
          <div>
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
              Enable SSL Verification
            </label>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              Verify SSL certificates for HTTPS requests
            </p>
          </div>
          <button
            @click="config.sslVerification = !config.sslVerification"
            :class="[
              'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
              config.sslVerification ? 'bg-indigo-600' : 'bg-gray-200 dark:bg-gray-700'
            ]"
          >
            <span
              :class="[
                'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                config.sslVerification ? 'translate-x-6' : 'translate-x-1'
              ]"
            />
          </button>
        </div>

        <!-- Test Connection -->
        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
          <div class="flex items-center justify-between">
            <div>
              <h4 class="text-sm font-medium text-gray-900 dark:text-white">Test Connection</h4>
              <p class="text-xs text-gray-500 dark:text-gray-400">Verify your API configuration</p>
            </div>
            <button
              @click="testConnection"
              :disabled="testing"
              class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 text-white rounded-lg transition-colors flex items-center space-x-2"
            >
              <span v-if="testing" class="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></span>
              <span>{{ testing ? 'Testing...' : 'Test' }}</span>
            </button>
          </div>
          
          <div v-if="testResult" :class="[
            'mt-3 p-2 rounded text-xs',
            testResult.success 
              ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
              : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
          ]">
            {{ testResult.message }}
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-end space-x-3 p-6 border-t border-gray-200 dark:border-gray-700">
        <button
          @click="$emit('close')"
          class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
        >
          Cancel
        </button>
        <button
          @click="saveConfig"
          class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
        >
          Save Configuration
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { XMarkIcon, EyeIcon, EyeSlashIcon } from '@heroicons/vue/24/outline'

defineEmits<{
  close: []
}>()

// State
const showApiKey = ref(false)
const testing = ref(false)
const testResult = ref<{ success: boolean; message: string } | null>(null)

const config = ref({
  apiEndpoint: 'http://localhost:5003',
  apiKey: 'admin-secret-key',
  rateLimit: 100,
  timeout: 30,
  sslVerification: true
})

// Methods
const handleBackdropClick = (event: Event) => {
  if (event.target === event.currentTarget) {
    // Close modal when clicking on backdrop
  }
}

const testConnection = async () => {
  testing.value = true
  testResult.value = null
  
  try {
    // Simulate API test
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    testResult.value = {
      success: true,
      message: 'Connection successful! API is responding correctly.'
    }
  } catch (error) {
    testResult.value = {
      success: false,
      message: 'Connection failed. Please check your configuration.'
    }
  } finally {
    testing.value = false
  }
}

const saveConfig = () => {
  console.log('Saving API configuration:', config.value)
  // Implement save functionality
}
</script>