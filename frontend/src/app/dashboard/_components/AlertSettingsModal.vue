<template>
  <!-- Modal Backdrop -->
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click="handleBackdropClick">
    <!-- Modal Content -->
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-2xl mx-4">
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
        <div>
          <h4 class="text-md font-medium text-gray-900 dark:text-white mb-4">Email Notifications</h4>
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
                  High Bot Detection Rate
                </label>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  Alert when bot detection exceeds threshold
                </p>
              </div>
              <button
                @click="settings.emailAlerts.highBotRate = !settings.emailAlerts.highBotRate"
                :class="[
                  'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                  settings.emailAlerts.highBotRate ? 'bg-indigo-600' : 'bg-gray-200 dark:bg-gray-700'
                ]"
              >
                <span
                  :class="[
                    'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                    settings.emailAlerts.highBotRate ? 'translate-x-6' : 'translate-x-1'
                  ]"
                />
              </button>
            </div>

            <div class="flex items-center justify-between">
              <div>
                <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
                  System Downtime
                </label>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  Alert when system components are offline
                </p>
              </div>
              <button
                @click="settings.emailAlerts.systemDown = !settings.emailAlerts.systemDown"
                :class="[
                  'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                  settings.emailAlerts.systemDown ? 'bg-indigo-600' : 'bg-gray-200 dark:bg-gray-700'
                ]"
              >
                <span
                  :class="[
                    'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                    settings.emailAlerts.systemDown ? 'translate-x-6' : 'translate-x-1'
                  ]"
                />
              </button>
            </div>

            <div class="flex items-center justify-between">
              <div>
                <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
                  API Rate Limit Exceeded
                </label>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  Alert when API rate limits are reached
                </p>
              </div>
              <button
                @click="settings.emailAlerts.rateLimitExceeded = !settings.emailAlerts.rateLimitExceeded"
                :class="[
                  'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                  settings.emailAlerts.rateLimitExceeded ? 'bg-indigo-600' : 'bg-gray-200 dark:bg-gray-700'
                ]"
              >
                <span
                  :class="[
                    'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                    settings.emailAlerts.rateLimitExceeded ? 'translate-x-6' : 'translate-x-1'
                  ]"
                />
              </button>
            </div>
          </div>
        </div>

        <!-- Email Recipients -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Email Recipients
          </label>
          <div class="space-y-2">
            <div v-for="(email, index) in settings.emailRecipients" :key="index" class="flex items-center space-x-2">
              <input
                v-model="settings.emailRecipients[index]"
                type="email"
                class="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
                placeholder="admin@example.com"
              />
              <button
                @click="removeEmailRecipient(index)"
                class="p-2 text-red-400 hover:text-red-600 transition-colors"
              >
                <TrashIcon class="h-4 w-4" />
              </button>
            </div>
            <button
              @click="addEmailRecipient"
              class="flex items-center space-x-2 text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300"
            >
              <PlusIcon class="h-4 w-4" />
              <span>Add Email</span>
            </button>
          </div>
        </div>

        <!-- Thresholds -->
        <div>
          <h4 class="text-md font-medium text-gray-900 dark:text-white mb-4">Alert Thresholds</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Bot Detection Rate (%)
              </label>
              <input
                v-model.number="settings.thresholds.botDetectionRate"
                type="number"
                min="0"
                max="100"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Response Time (ms)
              </label>
              <input
                v-model.number="settings.thresholds.responseTime"
                type="number"
                min="0"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>
        </div>

        <!-- Test Alert -->
        <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
          <div class="flex items-center justify-between">
            <div>
              <h4 class="text-sm font-medium text-gray-900 dark:text-white">Test Alert</h4>
              <p class="text-xs text-gray-500 dark:text-gray-400">Send a test notification to verify settings</p>
            </div>
            <button
              @click="sendTestAlert"
              :disabled="sendingTest"
              class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 text-white rounded-lg transition-colors flex items-center space-x-2"
            >
              <span v-if="sendingTest" class="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></span>
              <span>{{ sendingTest ? 'Sending...' : 'Send Test' }}</span>
            </button>
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
          @click="saveSettings"
          class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
        >
          Save Settings
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { XMarkIcon, TrashIcon, PlusIcon } from '@heroicons/vue/24/outline'

defineEmits<{
  close: []
}>()

// State
const sendingTest = ref(false)

const settings = ref({
  emailAlerts: {
    highBotRate: true,
    systemDown: true,
    rateLimitExceeded: false
  },
  emailRecipients: ['admin@passivecaptcha.com'],
  thresholds: {
    botDetectionRate: 25,
    responseTime: 500
  }
})

// Methods
const handleBackdropClick = (event: Event) => {
  if (event.target === event.currentTarget) {
    // Close modal when clicking on backdrop
  }
}

const addEmailRecipient = () => {
  settings.value.emailRecipients.push('')
}

const removeEmailRecipient = (index: number) => {
  settings.value.emailRecipients.splice(index, 1)
}

const sendTestAlert = async () => {
  sendingTest.value = true
  
  try {
    // Simulate sending test alert
    await new Promise(resolve => setTimeout(resolve, 1000))
    console.log('Test alert sent to:', settings.value.emailRecipients)
  } finally {
    sendingTest.value = false
  }
}

const saveSettings = () => {
  console.log('Saving alert settings:', settings.value)
  // Implement save functionality
}
</script>