<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="sm:flex sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Websites
        </h1>
        <p class="text-gray-600 dark:text-gray-400 mt-1">
          Manage your websites and their passive CAPTCHA protection
        </p>
      </div>
      
      <div class="mt-4 sm:mt-0 flex space-x-3">
        <button
          @click="showAddWebsiteModal = true"
          class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
        >
          <PlusIcon class="h-4 w-4 inline mr-2" />
          Add Website
        </button>
        <button
          @click="refreshWebsites"
          :disabled="isLoading"
          class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
        >
          <ArrowPathIcon class="h-4 w-4" :class="{ 'animate-spin': isLoading }" />
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading && websites.length === 0" class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-indigo-500 border-t-transparent"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
      <div class="flex">
        <ExclamationTriangleIcon class="h-5 w-5 text-red-400 flex-shrink-0" />
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800 dark:text-red-200">Error loading websites</h3>
          <p class="text-sm text-red-700 dark:text-red-300 mt-1">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="websites.length === 0" class="text-center py-12">
      <GlobeAltIcon class="mx-auto h-12 w-12 text-gray-400" />
      <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">No websites</h3>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Get started by adding your first website.</p>
      <div class="mt-6">
        <button
          @click="showAddWebsiteModal = true"
          class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
        >
          <PlusIcon class="h-4 w-4 inline mr-2" />
          Add your first website
        </button>
      </div>
    </div>

    <!-- Websites Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div 
        v-for="website in websites" 
        :key="website.id" 
        class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow"
      >
        <!-- Website Header -->
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <GlobeAltIcon class="h-5 w-5 text-gray-400" />
            <h3 class="text-lg font-medium text-gray-900 dark:text-white truncate">
              {{ website.name }}
            </h3>
          </div>
          <span 
            :class="[
              'px-2 py-1 text-xs font-medium rounded-full',
              getStatusColor(website.status)
            ]"
          >
            {{ website.status }}
          </span>
        </div>

        <!-- Website URL -->
        <div class="mt-2">
          <a 
            :href="website.url" 
            target="_blank"
            class="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-200 truncate block"
          >
            {{ website.url }}
          </a>
        </div>
        
        <!-- Statistics -->
        <div class="mt-4 space-y-2">
          <div class="flex justify-between text-sm">
            <span class="text-gray-500 dark:text-gray-400">Total Verifications:</span>
            <span class="font-medium text-gray-900 dark:text-white">
              {{ formatNumber(website.totalVerifications || 0) }}
            </span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-gray-500 dark:text-gray-400">Human Rate:</span>
            <span class="font-medium text-gray-900 dark:text-white">
              {{ (website.humanRate || 0).toFixed(1) }}%
            </span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-gray-500 dark:text-gray-400">Avg Confidence:</span>
            <span class="font-medium text-gray-900 dark:text-white">
              {{ (website.avgConfidence || 0).toFixed(1) }}%
            </span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-gray-500 dark:text-gray-400">Last Activity:</span>
            <span class="font-medium text-gray-900 dark:text-white">
              {{ formatDate(website.lastActivity) }}
            </span>
          </div>
        </div>

        <!-- Script Integration Status -->
        <div class="mt-4 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <CodeBracketIcon class="h-4 w-4 text-gray-400" />
              <span class="text-sm text-gray-700 dark:text-gray-300">Script Integration</span>
            </div>
            <div class="flex items-center space-x-1">
              <div 
                :class="[
                  'w-2 h-2 rounded-full',
                  website.has_script_token ? 'bg-green-500' : 'bg-gray-400'
                ]"
              ></div>
              <span class="text-xs text-gray-500 dark:text-gray-400">
                {{ website.has_script_token ? 'Active' : 'Not configured' }}
              </span>
            </div>
          </div>
        </div>
        
        <!-- Action Buttons -->
        <div class="mt-4 flex flex-col space-y-2">
          <div class="flex space-x-2">
            <router-link 
              :to="`/dashboard/websites/${website.id}`"
              class="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 flex-1 text-center transition-colors"
            >
              <ChartBarIcon class="h-4 w-4 inline mr-1" />
              Analytics
            </router-link>
            <button
              @click="toggleWebsiteStatus(website)"
              :disabled="isTogglingStatus[website.id]"
              :class="[
                'px-3 py-2 text-sm font-medium rounded-md transition-colors disabled:opacity-50',
                website.status === 'active' 
                  ? 'text-red-700 bg-red-50 hover:bg-red-100 dark:bg-red-900/20 dark:text-red-400 dark:hover:bg-red-900/30'
                  : 'text-green-700 bg-green-50 hover:bg-green-100 dark:bg-green-900/20 dark:text-green-400 dark:hover:bg-green-900/30'
              ]"
            >
              {{ website.status === 'active' ? 'Pause' : 'Activate' }}
            </button>
          </div>
          
          <div class="flex space-x-2">
            <button
              v-if="!website.has_script_token"
              @click="generateScript(website)"
              :disabled="isGeneratingScript[website.id]"
              class="px-3 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md flex-1 transition-colors disabled:opacity-50"
            >
              <span v-if="isGeneratingScript[website.id]" class="inline-flex items-center">
                <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Generating...
              </span>
              <span v-else>
                <CodeBracketIcon class="h-4 w-4 inline mr-1" />
                Generate Script
              </span>
            </button>
            
            <button
              v-else
              @click="showScriptManager(website)"
              class="px-3 py-2 text-sm font-medium text-indigo-700 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/20 hover:bg-indigo-100 dark:hover:bg-indigo-900/30 rounded-md flex-1 transition-colors"
            >
              <CogIcon class="h-4 w-4 inline mr-1" />
              Manage Script
            </button>

            <button
              @click="deleteWebsite(website)"
              :disabled="isDeletingWebsite[website.id]"
              class="px-3 py-2 text-sm font-medium text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-md transition-colors disabled:opacity-50"
            >
              <TrashIcon class="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <AddWebsiteModal
      v-if="showAddWebsiteModal"
      @close="showAddWebsiteModal = false"
      @success="handleWebsiteAdded"
    />

    <ScriptGeneratorModal
      v-if="showScriptGeneratorModal"
      :website="selectedWebsite"
      @close="showScriptGeneratorModal = false"
      @success="handleScriptGenerated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { 
  PlusIcon, 
  ArrowPathIcon, 
  ExclamationTriangleIcon,
  GlobeAltIcon,
  ChartBarIcon,
  CodeBracketIcon,
  CogIcon,
  TrashIcon
} from '@heroicons/vue/24/outline'
import { apiService } from '@/services/api'
import AddWebsiteModal from '../_components/AddWebsiteModal.vue'
import ScriptGeneratorModal from '../_components/ScriptGeneratorModal.vue'

// State
const websites = ref<any[]>([])
const isLoading = ref(false)
const error = ref('')
const showAddWebsiteModal = ref(false)
const showScriptGeneratorModal = ref(false)
const selectedWebsite = ref<any>(null)

// Loading states for individual operations
const isTogglingStatus = reactive<Record<string, boolean>>({})
const isGeneratingScript = reactive<Record<string, boolean>>({})
const isDeletingWebsite = reactive<Record<string, boolean>>({})

// Methods
const loadWebsites = async () => {
  isLoading.value = true
  error.value = ''

  try {
    const response = await apiService.getWebsites(true)
    
    if (response.success) {
      websites.value = response.data.websites || []
    } else {
      throw new Error(response.error?.message || 'Failed to load websites')
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to load websites'
  } finally {
    isLoading.value = false
  }
}

const refreshWebsites = () => {
  loadWebsites()
}

const toggleWebsiteStatus = async (website: any) => {
  isTogglingStatus[website.id] = true

  try {
    const response = await apiService.toggleWebsiteStatus(website.id)
    
    if (response.success) {
      const updatedWebsite = response.data.website
      const index = websites.value.findIndex(w => w.id === website.id)
      if (index !== -1) {
        websites.value[index] = updatedWebsite
      }
    } else {
      throw new Error(response.error?.message || 'Failed to toggle website status')
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to toggle website status'
  } finally {
    isTogglingStatus[website.id] = false
  }
}

const generateScript = async (website: any) => {
  selectedWebsite.value = website
  showScriptGeneratorModal.value = true
}

const showScriptManager = (website: any) => {
  selectedWebsite.value = website
  showScriptGeneratorModal.value = true
}

const deleteWebsite = async (website: any) => {
  if (!confirm(`Are you sure you want to delete ${website.name}? This action cannot be undone.`)) {
    return
  }

  isDeletingWebsite[website.id] = true

  try {
    const response = await apiService.deleteWebsite(website.id)
    
    if (response.success) {
      websites.value = websites.value.filter(w => w.id !== website.id)
    } else {
      throw new Error(response.error?.message || 'Failed to delete website')
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to delete website'
  } finally {
    isDeletingWebsite[website.id] = false
  }
}

const handleWebsiteAdded = (newWebsite: any) => {
  websites.value.push(newWebsite)
  showAddWebsiteModal.value = false
}

const handleScriptGenerated = (data: any) => {
  // Update the website's script integration status
  if (selectedWebsite.value) {
    const index = websites.value.findIndex(w => w.id === selectedWebsite.value.id)
    if (index !== -1) {
      websites.value[index].has_script_token = true
      websites.value[index].script_token_info = data.token
    }
  }
  showScriptGeneratorModal.value = false
}

// Utility functions
const getStatusColor = (status: string): string => {
  switch (status) {
    case 'active':
      return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
    case 'inactive':
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
    case 'suspended':
      return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
    case 'pending_integration':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
  }
}

const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

const formatDate = (dateString: string | null): string => {
  if (!dateString) return 'Never'
  
  const date = new Date(dateString)
  const now = new Date()
  const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
  
  if (diffInMinutes < 1) return 'Just now'
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`
  if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`
  
  return date.toLocaleDateString()
}

// Lifecycle
onMounted(() => {
  loadWebsites()
})
</script>