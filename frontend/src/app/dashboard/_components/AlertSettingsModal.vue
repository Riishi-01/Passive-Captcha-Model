<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click="handleBackdropClick">
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-2xl mx-4 transform transition-all duration-300 scale-100">
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          Alert Settings
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
        <!-- Email Notifications -->
        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h4 class="text-sm font-medium text-gray-900 dark:text-white">Email Notifications</h4>
              <p class="text-xs text-gray-500 dark:text-gray-400">Receive alerts via email</p>
            </div>
            <button
              @click="settings.emailEnabled = !settings.emailEnabled"
              :class="[
                'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                settings.emailEnabled ? 'bg-indigo-600' : 'bg-gray-200 dark:bg-gray-700'
              ]"
            >
              <span
                :class="[
                  'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                  settings.emailEnabled ? 'translate-x-6' : 'translate-x-1'
                ]"
              />
            </button>
          </div>
          
          <div v-if="settings.emailEnabled" class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Email Address
              </label>
              <input
                v-model="settings.email"
                type="email"
                class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
                placeholder="admin@example.com"
              />
            </div>
          </div>
        </div>

        <!-- Alert Thresholds -->
        <div class="space-y-4">
          <h4 class="text-sm font-medium text-gray-900 dark:text-white">Alert Thresholds</h4>
          
          <!-- High Threat Detection -->
          <div class="flex items-center justify-between">
            <div>
              <label class="text-sm text-gray-700 dark:text-gray-300">High Threat Detection</label>
              <p class="text-xs text-gray-500 dark:text-gray-400">Alert when threat level exceeds threshold</p>
            </div>
            <div class="flex items-center space-x-2">
              <input
                v-model.number="settings.threatThreshold"
                type="number"
                min="0"
                max="100"
                class="w-20 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
              />
              <span class="text-sm text-gray-500">%</span>
            </div>
          </div>

          <!-- Failed Verification Rate -->
          <div class="flex items-center justify-between">
            <div>
              <label class="text-sm text-gray-700 dark:text-gray-300">Failed Verification Rate</label>
              <p class="text-xs text-gray-500 dark:text-gray-400">Alert when failure rate exceeds threshold</p>
            </div>
            <div class="flex items-center space-x-2">
              <input
                v-model.number="settings.failureThreshold"
                type="number"
                min="0"
                max="100"
                class="w-20 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
              />
              <span class="text-sm text-gray-500">%</span>
            </div>
          </div>

          <!-- System Resource Usage -->
          <div class="flex items-center justify-between">
            <div>
              <label class="text-sm text-gray-700 dark:text-gray-300">System Resource Usage</label>
              <p class="text-xs text-gray-500 dark:text-gray-400">Alert when CPU/Memory usage exceeds threshold</p>
            </div>
            <div class="flex items-center space-x-2">
              <input
                v-model.number="settings.resourceThreshold"
                type="number"
                min="0"
                max="100"
                class="w-20 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
              />
              <span class="text-sm text-gray-500">%</span>
            </div>
          </div>
        </div>

        <!-- Alert Frequency -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Alert Frequency
          </label>
          <select
            v-model="settings.frequency"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="immediate">Immediate</option>
            <option value="hourly">Hourly</option>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
          </select>
        </div>

        <!-- Test Alert -->
        <div>
          <button
            @click="sendTestAlert"
            :disabled="isSendingTest"
            class="w-full px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 rounded-lg transition-colors"
          >
            <span v-if="!isSendingTest">Send Test Alert</span>
            <span v-else>Sending...</span>
          </button>
          
          <div v-if="testStatus" class="mt-2 text-sm" :class="testStatus.success ? 'text-green-600' : 'text-red-600'">
            {{ testStatus.message }}
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
          @click="saveSettings"
          :disabled="isSaving"
          class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 rounded-lg transition-colors"
        >
          <span v-if="!isSaving">Save Settings</span>
          <span v-else>Saving...</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'

// Emits
const emit = defineEmits<{
  close: []
}>()

// State
const isSaving = ref(false)
const isSendingTest = ref(false)
const testStatus = ref<{success: boolean, message: string} | null>(null)

const settings = ref({
  emailEnabled: true,
  email: 'admin@example.com',
  threatThreshold: 75,
  failureThreshold: 50,
  resourceThreshold: 80,
  frequency: 'immediate'
})

// Methods
const handleBackdropClick = (event: Event) => {
  if (event.target === event.currentTarget) {
    emit('close')
  }
}

const sendTestAlert = async () => {
  isSendingTest.value = true
  testStatus.value = null
  
  try {
    // Simulate sending test alert
    await new Promise(resolve => setTimeout(resolve, 1000))
    testStatus.value = {
      success: true,
      message: 'Test alert sent successfully!'
    }
  } catch (error) {
    testStatus.value = {
      success: false,
      message: 'Failed to send test alert. Please check your settings.'
    }
  } finally {
    isSendingTest.value = false
  }
}

const saveSettings = async () => {
  isSaving.value = true
  
  try {
    // Simulate save operation
    await new Promise(resolve => setTimeout(resolve, 500))
    emit('close')
  } catch (error) {
    console.error('Failed to save alert settings:', error)
  } finally {
    isSaving.value = false
  }
}
</script>