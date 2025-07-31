<template>
  <form @submit.prevent="handleLogin" class="space-y-6">
    <!-- Password Field -->
    <div>
      <label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
        Admin Password
      </label>
      <div class="mt-1 relative">
        <input
          id="password"
          v-model="password"
          :type="showPassword ? 'text' : 'password'"
          required
          class="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white sm:text-sm"
          placeholder="Enter your admin password"
          :disabled="isLoading"
        />
        <button
          type="button"
          @click="togglePasswordVisibility"
          class="absolute inset-y-0 right-0 pr-3 flex items-center"
          :disabled="isLoading"
        >
          <EyeIcon v-if="!showPassword" class="h-5 w-5 text-gray-400" />
          <EyeSlashIcon v-else class="h-5 w-5 text-gray-400" />
        </button>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-3">
      <div class="flex">
        <ExclamationTriangleIcon class="h-5 w-5 text-red-400" />
        <div class="ml-3">
          <p class="text-sm text-red-800 dark:text-red-200">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Submit Button -->
    <div>
      <button
        type="submit"
        :disabled="isLoading || !password.trim()"
        class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
      >
        <span v-if="isLoading" class="absolute left-0 inset-y-0 flex items-center pl-3">
          <div class="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
        </span>
        <LockClosedIcon v-else class="absolute left-0 inset-y-0 flex items-center pl-3 h-5 w-5 text-indigo-500 group-hover:text-indigo-400" />
        {{ isLoading ? 'Signing in...' : 'Sign in' }}
      </button>
    </div>
  </form>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { 
  EyeIcon, 
  EyeSlashIcon, 
  LockClosedIcon, 
  ExclamationTriangleIcon 
} from '@heroicons/vue/24/outline'

// Stores
const authStore = useAuthStore()
const appStore = useAppStore()
const router = useRouter()

// State
const password = ref('')
const showPassword = ref(false)
const isLoading = ref(false)
const error = ref('')

// Methods
const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value
}

const handleLogin = async () => {
  if (!password.value.trim()) return

  isLoading.value = true
  error.value = ''

  try {
    const result = await authStore.login(password.value)
    
    if (result.success) {
      // Success notification
      appStore.addNotification({
        type: 'success',
        title: 'Welcome!',
        message: 'Successfully signed in to your dashboard'
      })

      // Ensure auth state is properly updated in the next tick
      await nextTick()
      
      // Redirect to dashboard
      await router.push('/dashboard')
    } else {
      error.value = result.error || 'Login failed. Please check your password.'
      // Clear password on error
      password.value = ''
    }
  } catch (err: any) {
    console.error('Login exception:', err)
    error.value = err.message || 'Login failed. Please check your password.'
    
    // Clear password on error
    password.value = ''
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
/* Login form specific styles */
.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>