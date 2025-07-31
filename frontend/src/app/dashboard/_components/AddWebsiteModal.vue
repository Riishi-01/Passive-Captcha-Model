<template>
  <!-- Modal Backdrop -->
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click="handleBackdropClick">
    <!-- Modal Content -->
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-md mx-4 transform transition-all duration-300 scale-100">
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          Add New Website
        </h3>
        <button
          @click="$emit('close')"
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
        >
          <XMarkIcon class="h-6 w-6" />
        </button>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="p-6 space-y-4">
        <!-- Website Name -->
        <div>
          <label for="website-name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Website Name
          </label>
          <input
            id="website-name"
            v-model="form.name"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
            placeholder="e.g., My Blog"
          />
        </div>

        <!-- Website URL -->
        <div>
          <label for="website-url" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Website URL
          </label>
          <input
            id="website-url"
            v-model="form.url"
            type="url"
            required
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
            placeholder="https://example.com"
          />
        </div>

        <!-- Description -->
        <div>
          <label for="website-description" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Description (Optional)
          </label>
          <textarea
            id="website-description"
            v-model="form.description"
            rows="3"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
            placeholder="Brief description of your website"
          ></textarea>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
          <div class="flex">
            <ExclamationTriangleIcon class="h-5 w-5 text-red-400 flex-shrink-0" />
            <div class="ml-3">
              <p class="text-sm text-red-800 dark:text-red-200">{{ error }}</p>
            </div>
          </div>
        </div>

        <!-- Form Actions -->
        <div class="flex items-center justify-end space-x-3 pt-4">
          <button
            type="button"
            @click="$emit('close')"
            class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            :disabled="isSubmitting"
            class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <span v-if="isSubmitting" class="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></span>
            <span>{{ isSubmitting ? 'Adding...' : 'Add Website' }}</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { XMarkIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'

defineEmits<{
  close: []
  success: [website: any]
}>()

// State
const form = ref({
  name: '',
  url: '',
  description: ''
})

const isSubmitting = ref(false)
const error = ref('')

// Methods
const handleBackdropClick = (event: Event) => {
  if (event.target === event.currentTarget) {
    // Close modal when clicking on backdrop
  }
}

const validateForm = (): boolean => {
  error.value = ''
  
  if (!form.value.name.trim()) {
    error.value = 'Website name is required'
    return false
  }
  
  if (!form.value.url.trim()) {
    error.value = 'Website URL is required'
    return false
  }
  
  // Basic URL validation
  try {
    new URL(form.value.url)
  } catch {
    error.value = 'Please enter a valid URL'
    return false
  }
  
  return true
}

const handleSubmit = async () => {
  if (!validateForm()) return
  
  isSubmitting.value = true
  error.value = ''
  
  try {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Create new website object
    const newWebsite = {
      id: Math.random().toString(36).substr(2, 9),
      name: form.value.name,
      url: form.value.url,
      description: form.value.description,
      status: 'active',
      createdAt: new Date().toISOString(),
      lastActivity: new Date().toISOString(),
      totalVerifications: 0
    }
    
    // Emit success event
    // $emit('success', newWebsite)
    
    // Reset form
    form.value = {
      name: '',
      url: '',
      description: ''
    }
    
  } catch (err: any) {
    error.value = err.message || 'Failed to add website'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
/* Modal animations */
.fixed {
  animation: fadeIn 0.3s ease-out;
}

.bg-white {
  animation: slideUp 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Spinning animation for loading */
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