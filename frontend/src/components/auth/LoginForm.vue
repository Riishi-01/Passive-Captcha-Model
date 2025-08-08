<template>
  <div class="max-w-md w-full mx-4">
    <!-- Logo and Title -->
    <div class="text-center mb-8">
      <div class="flex justify-center mb-4">
        <div class="w-16 h-16 bg-blue-600 rounded-xl flex items-center justify-center">
          <ShieldCheckIcon class="w-8 h-8 text-white" />
        </div>
      </div>
      <h2 class="text-3xl font-bold text-gray-900 dark:text-white">
        Passive CAPTCHA
      </h2>
      <p class="text-gray-600 dark:text-gray-400 mt-2">
        Admin Dashboard Login
      </p>
    </div>

    <!-- Login Form -->
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-8">
      <form @submit.prevent="handleSubmit" class="space-y-6">
        <!-- Password Input -->
        <div>
          <label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Admin Password
          </label>
          <div class="relative">
            <input
              id="password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              required
              class="block w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
              placeholder="Enter admin password"
              :disabled="loading"
            />
            <button
              type="button"
              @click="showPassword = !showPassword"
              class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              :disabled="loading"
            >
              <EyeIcon v-if="!showPassword" class="w-5 h-5" />
              <EyeOffIcon v-else class="w-5 h-5" />
            </button>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="errorMessage" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div class="flex items-center space-x-2">
            <XCircleIcon class="w-5 h-5 text-red-500" />
            <span class="text-sm text-red-700 dark:text-red-400">
              {{ errorMessage }}
            </span>
          </div>
        </div>

        <!-- Submit Button -->
        <button
          type="submit"
          :disabled="loading || !password.trim()"
          class="w-full flex justify-center items-center px-4 py-3 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
        >
          <div v-if="loading" class="flex items-center space-x-2">
            <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            <span>Signing in...</span>
          </div>
          <span v-else>Sign In</span>
        </button>
      </form>

      <!-- Additional Info -->
      <div class="mt-6 text-center">
        <p class="text-xs text-gray-500 dark:text-gray-400">
          Secure admin access to your passive CAPTCHA system
        </p>
      </div>
    </div>

    <!-- System Status -->
    <div class="mt-6 text-center">
      <div class="inline-flex items-center space-x-2 px-3 py-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div
          :class="[
            'w-2 h-2 rounded-full',
            systemOnline ? 'bg-green-500' : 'bg-red-500'
          ]"
        ></div>
        <span class="text-sm text-gray-600 dark:text-gray-400">
          System {{ systemOnline ? 'Online' : 'Offline' }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ShieldCheckIcon, EyeIcon, EyeOffIcon, XCircleIcon } from 'lucide-vue-next'

interface Props {
  loading?: boolean
}

interface Emits {
  login: [password: string]
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<Emits>()

// State
const password = ref('')
const showPassword = ref(false)
const errorMessage = ref('')
const systemOnline = ref(false)

// Methods
const handleSubmit = () => {
  if (!password.value.trim()) return
  
  errorMessage.value = ''
  emit('login', password.value)
}

const checkSystemStatus = async () => {
  try {
    const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5002'
    const response = await fetch(`${API_BASE}/health`)
    systemOnline.value = response.ok
  } catch (error) {
    systemOnline.value = false
  }
}

// Lifecycle
onMounted(() => {
  checkSystemStatus()
  // Check system status periodically
  setInterval(checkSystemStatus, 30000) // Check every 30 seconds
})
</script>

<style scoped>
/* Custom animations */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}

/* Form focus effects */
input:focus {
  transform: scale(1.01);
  transition: transform 0.2s ease;
}

/* Button hover effects */
button:hover:not(:disabled) {
  transform: translateY(-1px);
}

button:active:not(:disabled) {
  transform: translateY(0);
}

/* Logo animation */
.w-16.h-16 {
  animation: logoFloat 3s ease-in-out infinite;
}

@keyframes logoFloat {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-4px);
  }
}

/* System status pulse */
.bg-green-500,
.bg-red-500 {
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

/* Responsive adjustments */
@media (max-width: 640px) {
  .max-w-md {
    max-width: 24rem;
  }
  
  .p-8 {
    padding: 1.5rem;
  }
  
  .text-3xl {
    font-size: 1.5rem;
    line-height: 2rem;
  }
}

/* Dark mode transitions */
.dark * {
  transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  .animate-spin,
  .w-16.h-16,
  .bg-green-500,
  .bg-red-500,
  input,
  button {
    animation: none !important;
    transition: none !important;
    transform: none !important;
  }
}

/* Focus states for accessibility */
input:focus,
button:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Loading state */
button:disabled {
  cursor: not-allowed;
  transform: none !important;
}

/* Error message animation */
.p-3 {
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>