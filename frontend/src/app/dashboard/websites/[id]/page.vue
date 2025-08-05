<template>
  <div class="space-y-6">
    <!-- Loading State -->
    <div v-if="isLoading && !website" class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-indigo-500 border-t-transparent"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
      <div class="flex">
        <ExclamationTriangleIcon class="h-5 w-5 text-red-400 flex-shrink-0" />
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800 dark:text-red-200">Error loading website</h3>
          <p class="text-sm text-red-700 dark:text-red-300 mt-1">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Website Content -->
    <div v-else-if="website">
      <!-- Header -->
      <div class="flex items-start justify-between">
        <div>
          <div class="flex items-center space-x-3">
            <button
              @click="$router.back()"
              class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              <ArrowLeftIcon class="h-5 w-5" />
            </button>
            <div>
              <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
                {{ website.name }}
              </h1>
              <div class="flex items-center space-x-4 mt-1">
                <a 
                  :href="website.url" 
                  target="_blank"
                  class="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-200"
                >
                  {{ website.url }}
                  <ArrowTopRightOnSquareIcon class="h-4 w-4 inline ml-1" />
                </a>
                <span 
                  :class="[
                    'px-2 py-1 text-xs font-medium rounded-full',
                    getStatusColor(website.status)
                  ]"
                >
                  {{ website.status }}
                </span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="flex items-center space-x-3">
          <button
            @click="toggleWebsiteStatus"
            :disabled="isTogglingStatus"
            :class="[
              'px-4 py-2 text-sm font-medium rounded-lg transition-colors disabled:opacity-50',
              website.status === 'active' 
                ? 'text-red-700 bg-red-50 hover:bg-red-100 dark:bg-red-900/20 dark:text-red-400 dark:hover:bg-red-900/30'
                : 'text-green-700 bg-green-50 hover:bg-green-100 dark:bg-green-900/20 dark:text-green-400 dark:hover:bg-green-900/30'
            ]"
          >
            {{ website.status === 'active' ? 'Pause Protection' : 'Activate Protection' }}
          </button>
          
          <button
            v-if="!website.has_script_token"
            @click="showScriptGeneratorModal = true"
            class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
          >
            <CodeBracketIcon class="h-4 w-4 inline mr-2" />
            Generate Script
          </button>
          
          <button
            v-else
            @click="showScriptGeneratorModal = true"
            class="px-4 py-2 text-sm font-medium text-indigo-700 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/20 hover:bg-indigo-100 dark:hover:bg-indigo-900/30 rounded-lg transition-colors"
          >
            <CogIcon class="h-4 w-4 inline mr-2" />
            Manage Script
          </button>
        </div>
      </div>

      <!-- Tab Navigation -->
      <div class="border-b border-gray-200 dark:border-gray-700">
        <nav class="flex space-x-8" aria-label="Tabs">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              activeTab === tab.id
                ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300',
              'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2'
            ]"
          >
            <component :is="tab.icon" class="h-5 w-5" />
            <span>{{ tab.name }}</span>
          </button>
        </nav>
      </div>

      <!-- Tab Content -->
      <div class="mt-6">
        <!-- Overview Tab -->
        <div v-show="activeTab === 'overview'" class="space-y-6">
          <!-- Key Metrics -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-4">
              <div class="flex items-center">
                <div class="flex-shrink-0">
                  <ChartBarIcon class="h-8 w-8 text-blue-500" />
                </div>
                <div class="ml-4">
                  <div class="text-2xl font-bold text-gray-900 dark:text-white">
                    {{ formatNumber(website.totalVerifications || 0) }}
                  </div>
                  <div class="text-sm text-gray-500 dark:text-gray-400">Total Verifications</div>
                </div>
              </div>
            </div>

            <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-4">
              <div class="flex items-center">
                <div class="flex-shrink-0">
                  <UserIcon class="h-8 w-8 text-green-500" />
                </div>
                <div class="ml-4">
                  <div class="text-2xl font-bold text-gray-900 dark:text-white">
                    {{ (website.humanRate || 0).toFixed(1) }}%
                  </div>
                  <div class="text-sm text-gray-500 dark:text-gray-400">Human Rate</div>
                </div>
              </div>
            </div>

            <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-4">
              <div class="flex items-center">
                <div class="flex-shrink-0">
                  <ShieldCheckIcon class="h-8 w-8 text-purple-500" />
                </div>
                <div class="ml-4">
                  <div class="text-2xl font-bold text-gray-900 dark:text-white">
                    {{ (website.avgConfidence || 0).toFixed(1) }}%
                  </div>
                  <div class="text-sm text-gray-500 dark:text-gray-400">Avg Confidence</div>
                </div>
              </div>
            </div>

            <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-4">
              <div class="flex items-center">
                <div class="flex-shrink-0">
                  <ClockIcon class="h-8 w-8 text-yellow-500" />
                </div>
                <div class="ml-4">
                  <div class="text-2xl font-bold text-gray-900 dark:text-white">
                    {{ formatDate(website.lastActivity) }}
                  </div>
                  <div class="text-sm text-gray-500 dark:text-gray-400">Last Activity</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Website Information -->
          <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
            <div class="p-4 border-b border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-medium text-gray-900 dark:text-white">Website Information</h3>
            </div>
            <div class="p-4">
              <dl class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Name</dt>
                  <dd class="mt-1 text-sm text-gray-900 dark:text-white">{{ website.name }}</dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">URL</dt>
                  <dd class="mt-1 text-sm text-gray-900 dark:text-white">
                    <a :href="website.url" target="_blank" class="text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-200">
                      {{ website.url }}
                    </a>
                  </dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Status</dt>
                  <dd class="mt-1">
                    <span :class="['px-2 py-1 text-xs font-medium rounded-full', getStatusColor(website.status)]">
                      {{ website.status }}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Created</dt>
                  <dd class="mt-1 text-sm text-gray-900 dark:text-white">{{ formatDate(website.createdAt) }}</dd>
                </div>
                <div>
                  <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Script Integration</dt>
                  <dd class="mt-1">
                    <div class="flex items-center space-x-2">
                      <div :class="['w-2 h-2 rounded-full', website.has_script_token ? 'bg-green-500' : 'bg-gray-400']"></div>
                      <span class="text-sm text-gray-900 dark:text-white">
                        {{ website.has_script_token ? 'Active' : 'Not configured' }}
                      </span>
                    </div>
                  </dd>
                </div>
              </dl>
            </div>
          </div>
        </div>

        <!-- Script Analytics Tab -->
        <div v-show="activeTab === 'analytics'">
          <ScriptAnalyticsDashboard v-if="website.has_script_token" :website-id="website.id" />
          <div v-else class="text-center py-12">
            <CodeBracketIcon class="mx-auto h-12 w-12 text-gray-400" />
            <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">No script integration</h3>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Generate and integrate the Passive CAPTCHA script to view analytics.
            </p>
            <div class="mt-6">
              <button
                @click="showScriptGeneratorModal = true"
                class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
              >
                <CodeBracketIcon class="h-4 w-4 inline mr-2" />
                Generate Script
              </button>
            </div>
          </div>
        </div>

        <!-- Settings Tab -->
        <div v-show="activeTab === 'settings'" class="space-y-6">
          <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
            <div class="p-4 border-b border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-medium text-gray-900 dark:text-white">Website Settings</h3>
            </div>
            <div class="p-4">
              <form @submit.prevent="updateWebsite" class="space-y-4">
                <div>
                  <label for="name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Website Name
                  </label>
                  <input
                    id="name"
                    v-model="editForm.name"
                    type="text"
                    required
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
                
                <div>
                  <label for="url" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Website URL
                  </label>
                  <input
                    id="url"
                    v-model="editForm.url"
                    type="url"
                    required
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div class="flex items-center justify-between pt-4">
                  <button
                    type="submit"
                    :disabled="isUpdating"
                    class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors disabled:opacity-50"
                  >
                    {{ isUpdating ? 'Updating...' : 'Update Website' }}
                  </button>
                  
                  <button
                    type="button"
                    @click="deleteWebsite"
                    :disabled="isDeleting"
                    class="px-4 py-2 text-sm font-medium text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors disabled:opacity-50"
                  >
                    {{ isDeleting ? 'Deleting...' : 'Delete Website' }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Script Generator Modal -->
    <ScriptGeneratorModal
      v-if="showScriptGeneratorModal"
      :website="website"
      @close="showScriptGeneratorModal = false"
      @success="handleScriptGenerated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  ArrowLeftIcon,
  ArrowTopRightOnSquareIcon,
  ExclamationTriangleIcon,
  ChartBarIcon,
  UserIcon,
  ShieldCheckIcon,
  ClockIcon,
  CodeBracketIcon,
  CogIcon,
  GlobeAltIcon,
  Cog6ToothIcon
} from '@heroicons/vue/24/outline'
import { apiService } from '@/services/api'
import ScriptGeneratorModal from '../../_components/ScriptGeneratorModal.vue'
import ScriptAnalyticsDashboard from '../../_components/ScriptAnalyticsDashboard.vue'

const route = useRoute()
const router = useRouter()

// State
const website = ref<any>(null)
const isLoading = ref(false)
const error = ref('')
const activeTab = ref('overview')
const showScriptGeneratorModal = ref(false)
const isTogglingStatus = ref(false)
const isUpdating = ref(false)
const isDeleting = ref(false)

// Edit form
const editForm = reactive({
  name: '',
  url: ''
})

// Tabs
const tabs = [
  { id: 'overview', name: 'Overview', icon: GlobeAltIcon },
  { id: 'analytics', name: 'Script Analytics', icon: ChartBarIcon },
  { id: 'settings', name: 'Settings', icon: Cog6ToothIcon }
]

// Methods
const loadWebsite = async () => {
  const websiteId = route.params.id as string
  if (!websiteId) return

  isLoading.value = true
  error.value = ''

  try {
    const response = await apiService.getWebsites(true)
    
    if (response.success) {
      const foundWebsite = response.data.websites.find((w: any) => w.id === websiteId)
      if (foundWebsite) {
        website.value = foundWebsite
        // Update edit form
        editForm.name = foundWebsite.name
        editForm.url = foundWebsite.url
      } else {
        error.value = 'Website not found'
      }
    } else {
      throw new Error(response.error?.message || 'Failed to load website')
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to load website'
  } finally {
    isLoading.value = false
  }
}

const toggleWebsiteStatus = async () => {
  if (!website.value) return

  isTogglingStatus.value = true

  try {
    const response = await apiService.toggleWebsiteStatus(website.value.id)
    
    if (response.success) {
      website.value = response.data.website
    } else {
      throw new Error(response.error?.message || 'Failed to toggle website status')
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to toggle website status'
  } finally {
    isTogglingStatus.value = false
  }
}

const updateWebsite = async () => {
  if (!website.value) return

  isUpdating.value = true

  try {
    const response = await apiService.updateWebsite(website.value.id, {
      name: editForm.name,
      url: editForm.url
    })
    
    if (response.success) {
      website.value = response.data.website
    } else {
      throw new Error(response.error?.message || 'Failed to update website')
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to update website'
  } finally {
    isUpdating.value = false
  }
}

const deleteWebsite = async () => {
  if (!website.value) return

  if (!confirm(`Are you sure you want to delete ${website.value.name}? This action cannot be undone.`)) {
    return
  }

  isDeleting.value = true

  try {
    const response = await apiService.deleteWebsite(website.value.id)
    
    if (response.success) {
      router.push('/dashboard/websites')
    } else {
      throw new Error(response.error?.message || 'Failed to delete website')
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to delete website'
  } finally {
    isDeleting.value = false
  }
}

const handleScriptGenerated = (data: any) => {
  // Update the website's script integration status
  if (website.value) {
    website.value.has_script_token = true
    website.value.script_token_info = data.token
  }
  showScriptGeneratorModal.value = false
  // Switch to analytics tab to show the new data
  activeTab.value = 'analytics'
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
  loadWebsite()
})

// Watch for route changes
watch(() => route.params.id, () => {
  loadWebsite()
})
</script>