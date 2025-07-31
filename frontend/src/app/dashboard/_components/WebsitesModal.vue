<template>
  <!-- Modal Backdrop -->
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click="handleBackdropClick">
    <!-- Modal Content -->
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-4xl mx-4 max-h-[90vh] overflow-hidden">
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          Website Management
        </h3>
        <button
          @click="$emit('close')"
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
        >
          <XMarkIcon class="h-6 w-6" />
        </button>
      </div>

      <!-- Content -->
      <div class="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
        <!-- Add Website Section -->
        <div class="mb-8 p-6 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <h4 class="text-md font-medium text-gray-900 dark:text-white mb-4">Add New Website</h4>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input
              v-model="newWebsite.name"
              type="text"
              placeholder="Website Name"
              class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
            />
            <input
              v-model="newWebsite.url"
              type="url"
              placeholder="https://example.com"
              class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white"
            />
            <button
              @click="addWebsite"
              :disabled="!newWebsite.name || !newWebsite.url"
              class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 text-white rounded-lg transition-colors flex items-center justify-center space-x-2"
            >
              <PlusIcon class="h-4 w-4" />
              <span>Add Website</span>
            </button>
          </div>
        </div>

        <!-- Websites List -->
        <div class="space-y-4">
          <div 
            v-for="website in websites" 
            :key="website.id"
            class="flex items-center justify-between p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
          >
            <div class="flex items-center space-x-4">
              <div 
                :class="[
                  'w-3 h-3 rounded-full',
                  website.status === 'active' ? 'bg-green-500' : 'bg-gray-400'
                ]"
              ></div>
              <div>
                <h5 class="font-medium text-gray-900 dark:text-white">{{ website.name }}</h5>
                <p class="text-sm text-gray-500 dark:text-gray-400">{{ website.url }}</p>
              </div>
            </div>
            
            <div class="flex items-center space-x-4">
              <div class="text-right">
                <div class="text-sm font-medium text-gray-900 dark:text-white">
                  {{ formatNumber(website.totalVerifications) }}
                </div>
                <div class="text-xs text-gray-500 dark:text-gray-400">verifications</div>
                <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Script: 
                  <span :class="getScriptStatusColor(website)">
                    {{ getScriptStatusText(website) }}
                  </span>
                </div>
              </div>
              
              <button
                @click="viewScriptIntegration(website)"
                class="px-3 py-1 rounded-lg text-xs font-medium transition-colors bg-indigo-100 text-indigo-800 hover:bg-indigo-200 dark:bg-indigo-900/20 dark:text-indigo-400"
              >
                <CodeBracketIcon class="h-4 w-4 inline mr-1" />
                Script
              </button>
              
              <button
                @click="toggleWebsiteStatus(website)"
                :class="[
                  'px-3 py-1 rounded-full text-xs font-medium transition-colors',
                  website.status === 'active' 
                    ? 'bg-red-100 text-red-800 hover:bg-red-200 dark:bg-red-900/20 dark:text-red-400'
                    : 'bg-green-100 text-green-800 hover:bg-green-200 dark:bg-green-900/20 dark:text-green-400'
                ]"
              >
                {{ website.status === 'active' ? 'Disable' : 'Enable' }}
              </button>
              
              <button
                @click="deleteWebsite(website.id)"
                class="p-1 text-red-400 hover:text-red-600 transition-colors"
              >
                <TrashIcon class="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="!websites.length" class="text-center py-8">
          <GlobeAltIcon class="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <p class="text-gray-500 dark:text-gray-400">No websites configured yet</p>
          <p class="text-sm text-gray-400 dark:text-gray-500 mt-1">Add your first website above to get started</p>
        </div>
      </div>
    </div>

    <!-- Script Integration Modal -->
    <div v-if="showScriptModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-60" @click="closeScriptModal">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-4xl mx-4 max-h-[90vh] overflow-hidden" @click.stop>
        <!-- Script Modal Header -->
        <div class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Script Integration - {{ selectedWebsiteForScript?.name }}
          </h3>
          <button
            @click="closeScriptModal"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <XMarkIcon class="h-6 w-6" />
          </button>
        </div>

        <!-- Script Modal Content -->
        <div class="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          <!-- No Script Token - Generate New -->
          <div v-if="!scriptTokenInfo" class="text-center py-8">
            <CodeBracketIcon class="mx-auto h-16 w-16 text-gray-400 mb-4" />
            <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No Script Token Generated
            </h3>
            <p class="text-gray-600 dark:text-gray-400 mb-6">
              Generate a one-time script token for {{ selectedWebsiteForScript?.name }} to start collecting passive data.
            </p>
            <button
              @click="generateScriptToken"
              :disabled="isGeneratingToken"
              class="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              <CodeBracketIcon class="h-5 w-5 mr-2" />
              {{ isGeneratingToken ? 'Generating...' : 'Generate Script Token' }}
            </button>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-3">
              This is a one-time operation. Once generated, the token cannot be edited, only deleted.
            </p>
          </div>

          <!-- Existing Script Token - View Only -->
          <div v-else class="space-y-6">
            <!-- Token Status -->
            <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
              <div class="flex items-center justify-between mb-3">
                <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300">Token Status</h4>
                <span 
                  :class="[
                    'inline-flex px-3 py-1 text-xs font-medium rounded-full',
                    getTokenStatusColor(scriptTokenInfo.status)
                  ]"
                >
                  {{ getTokenStatusText(scriptTokenInfo.status) }}
                </span>
              </div>
              <div class="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span class="text-gray-500 dark:text-gray-400">Created:</span>
                  <span class="ml-2 text-gray-900 dark:text-white">
                    {{ formatDate(scriptTokenInfo.created_at) }}
                  </span>
                </div>
                <div>
                  <span class="text-gray-500 dark:text-gray-400">Last Used:</span>
                  <span class="ml-2 text-gray-900 dark:text-white">
                    {{ scriptTokenInfo.last_used_at ? formatDate(scriptTokenInfo.last_used_at) : 'Never' }}
                  </span>
                </div>
                <div>
                  <span class="text-gray-500 dark:text-gray-400">Usage Count:</span>
                  <span class="ml-2 text-gray-900 dark:text-white">
                    {{ scriptTokenInfo.usage_count || 0 }} requests
                  </span>
                </div>
                <div>
                  <span class="text-gray-500 dark:text-gray-400">Version:</span>
                  <span class="ml-2 text-gray-900 dark:text-white">
                    {{ scriptTokenInfo.script_version }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Integration Code -->
            <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
              <div class="flex items-center justify-between mb-3">
                <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300">Integration Code</h4>
                <button
                  @click="copyIntegrationCode"
                  class="inline-flex items-center px-3 py-1 text-xs font-medium text-indigo-600 hover:text-indigo-500 transition-colors"
                >
                  <ClipboardDocumentIcon class="h-4 w-4 mr-1" />
                  Copy Code
                </button>
              </div>
              <pre class="text-xs text-gray-600 dark:text-gray-400 whitespace-pre-wrap bg-white dark:bg-gray-800 p-3 rounded border overflow-x-auto">{{ integrationCode }}</pre>
            </div>

            <!-- Instructions -->
            <div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
              <h4 class="text-sm font-medium text-blue-900 dark:text-blue-100 mb-3">
                <DocumentTextIcon class="h-4 w-4 inline mr-1" />
                Integration Instructions
              </h4>
              <ol class="text-sm text-blue-800 dark:text-blue-200 space-y-2 list-decimal list-inside">
                <li>Copy the integration code above</li>
                <li>Paste it in the &lt;head&gt; section of your website</li>
                <li>The script will automatically start collecting passive data</li>
                <li>Monitor this dashboard for real-time analytics</li>
              </ol>
            </div>

            <!-- Danger Zone -->
            <div class="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
              <h4 class="text-sm font-medium text-red-900 dark:text-red-100 mb-3">
                <ExclamationTriangleIcon class="h-4 w-4 inline mr-1" />
                Danger Zone
              </h4>
              <p class="text-sm text-red-800 dark:text-red-200 mb-3">
                Deleting the script token will permanently disable data collection for this website.
              </p>
              <button
                @click="deleteScriptToken"
                :disabled="isDeletingToken"
                class="inline-flex items-center px-4 py-2 border border-red-300 text-sm font-medium rounded-lg text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
              >
                <TrashIcon class="h-4 w-4 mr-2" />
                {{ isDeletingToken ? 'Deleting...' : 'Delete Script Token' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { useWebsiteStore } from '@/stores/websites'
import axios from 'axios'
import {
  XMarkIcon,
  PlusIcon,
  TrashIcon,
  GlobeAltIcon,
  CodeBracketIcon,
  ClipboardDocumentIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon
} from '@heroicons/vue/24/outline'

defineEmits<{
  close: []
}>()

// Stores
const appStore = useAppStore()

// State
const newWebsite = ref({
  name: '',
  url: ''
})

const websites = ref<any[]>([])

// Load websites from store
const websitesStore = useWebsiteStore()

// Watch for changes in the websites store
watch(() => websitesStore.websites, (newWebsites) => {
  websites.value = newWebsites.map(w => ({
    id: w.id,
    name: w.name,
    url: `https://${w.domain}`, // Reconstruct URL from domain
    status: w.status,
    totalVerifications: w.totalVerifications,
    integration_status: w.integration_status || 'not_integrated',
    has_script_token: w.has_script_token || false,
    script_token_info: w.script_token_info
  }))
}, { immediate: true })

// Script Integration State
const showScriptModal = ref(false)
const selectedWebsiteForScript = ref<any>(null)
const scriptTokenInfo = ref<any>(null)
const integrationCode = ref('')
const isGeneratingToken = ref(false)
const isDeletingToken = ref(false)

// Methods
const handleBackdropClick = (event: Event) => {
  if (event.target === event.currentTarget) {
    // Close modal when clicking on backdrop
  }
}

const addWebsite = async () => {
  if (!newWebsite.value.name || !newWebsite.value.url) return
  
  try {
    await websitesStore.addWebsite(newWebsite.value.name, newWebsite.value.url)
    
    // Success notification
    appStore.addNotification({
      type: 'success',
      title: 'Website Added',
      message: `${newWebsite.value.name} has been added successfully`
    })
    
    // Clear form
    newWebsite.value = { name: '', url: '' }
    
    // Refresh the websites list
    await websitesStore.fetchWebsites()
    
  } catch (error: any) {
    console.error('Error adding website:', error)
    appStore.addNotification({
      type: 'error',
      title: 'Failed to Add Website',
      message: error.message || 'Failed to add website'
    })
  }
}

const toggleWebsiteStatus = (website: any) => {
  website.status = website.status === 'active' ? 'inactive' : 'active'
}

const deleteWebsite = (id: string) => {
  if (confirm('Are you sure you want to delete this website?')) {
    const index = websites.value.findIndex(w => w.id === id)
    if (index > -1) {
      websites.value.splice(index, 1)
    }
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

// Script Integration Methods
const viewScriptIntegration = async (website: any) => {
  selectedWebsiteForScript.value = website
  showScriptModal.value = true
  
  // Load existing token if available
  if (website.has_script_token) {
    await loadScriptTokenInfo(website.id)
  } else {
    scriptTokenInfo.value = null
    integrationCode.value = ''
  }
}

const closeScriptModal = () => {
  showScriptModal.value = false
  selectedWebsiteForScript.value = null
  scriptTokenInfo.value = null
  integrationCode.value = ''
}

const loadScriptTokenInfo = async (websiteId: string) => {
  try {
    const response = await axios.get(`/admin/scripts/tokens/${websiteId}`)
    
    if (response.data.success) {
      scriptTokenInfo.value = response.data.data.token
      integrationCode.value = response.data.data.token.integration?.integration_code || ''
    }
  } catch (error) {
    // Token doesn't exist - that's fine
    scriptTokenInfo.value = null
    integrationCode.value = ''
  }
}

const generateScriptToken = async () => {
  if (!selectedWebsiteForScript.value) return
  
  isGeneratingToken.value = true
  try {
    const response = await axios.post(`/admin/scripts/generate`, {
      website_id: selectedWebsiteForScript.value.id,
      script_version: 'v2_enhanced'
    })
    
    if (response.data.success) {
      scriptTokenInfo.value = response.data.data.token
      integrationCode.value = response.data.data.integration.integration_code
      
      // Update website in list
      const website = websites.value.find(w => w.id === selectedWebsiteForScript.value.id)
      if (website) {
        website.has_script_token = true
        website.integration_status = 'pending'
      }
      
      appStore.addNotification({
        type: 'success',
        title: 'Script Token Generated',
        message: 'Integration code is ready to be added to your website'
      })
    }
  } catch (error: any) {
    console.error('Error generating token:', error)
    appStore.addNotification({
      type: 'error',
      title: 'Generation Failed',
      message: error.response?.data?.error?.message || 'Failed to generate script token'
    })
  } finally {
    isGeneratingToken.value = false
  }
}

const deleteScriptToken = async () => {
  if (!selectedWebsiteForScript.value || !scriptTokenInfo.value) return
  
  if (!confirm('Are you sure you want to delete this script token? This will permanently disable data collection for this website.')) {
    return
  }
  
  isDeletingToken.value = true
  try {
    const response = await axios.post(`/admin/scripts/tokens/${selectedWebsiteForScript.value.id}/revoke`)
    
    if (response.data.success) {
      // Update website in list
      const website = websites.value.find(w => w.id === selectedWebsiteForScript.value.id)
      if (website) {
        website.has_script_token = false
        website.integration_status = 'not_integrated'
      }
      
      // Clear token info
      scriptTokenInfo.value = null
      integrationCode.value = ''
      
      appStore.addNotification({
        type: 'success',
        title: 'Script Token Deleted',
        message: 'Script token has been permanently deleted'
      })
    }
  } catch (error: any) {
    console.error('Error deleting token:', error)
    appStore.addNotification({
      type: 'error',
      title: 'Deletion Failed',
      message: error.response?.data?.error?.message || 'Failed to delete script token'
    })
  } finally {
    isDeletingToken.value = false
  }
}

const copyIntegrationCode = async () => {
  try {
    await navigator.clipboard.writeText(integrationCode.value)
    appStore.addNotification({
      type: 'success',
      title: 'Copied!',
      message: 'Integration code copied to clipboard'
    })
  } catch (error) {
    console.error('Failed to copy:', error)
    appStore.addNotification({
      type: 'error',
      title: 'Copy Failed',
      message: 'Failed to copy integration code'
    })
  }
}

// Status helper methods
const getScriptStatusColor = (website: any) => {
  switch (website.integration_status) {
    case 'active':
      return 'text-green-600'
    case 'pending':
      return 'text-yellow-600'
    case 'inactive':
    case 'revoked':
      return 'text-red-600'
    case 'not_integrated':
    default:
      return 'text-gray-500'
  }
}

const getScriptStatusText = (website: any) => {
  switch (website.integration_status) {
    case 'active':
      return 'Active'
    case 'pending':
      return 'Pending'
    case 'inactive':
      return 'Inactive'
    case 'revoked':
      return 'Revoked'
    case 'not_integrated':
    default:
      return 'Not Generated'
  }
}

const getTokenStatusColor = (status: string) => {
  switch (status) {
    case 'active':
      return 'bg-green-100 text-green-800'
    case 'pending':
      return 'bg-yellow-100 text-yellow-800'
    case 'inactive':
    case 'revoked':
      return 'bg-red-100 text-red-800'
    case 'expired':
      return 'bg-gray-100 text-gray-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const getTokenStatusText = (status: string) => {
  switch (status) {
    case 'active':
      return 'Active'
    case 'pending':
      return 'Pending'
    case 'inactive':
      return 'Inactive'
    case 'revoked':
      return 'Revoked'
    case 'expired':
      return 'Expired'
    default:
      return 'Unknown'
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString() + ' ' + new Date(dateString).toLocaleTimeString()
}

// Load websites on component mount
onMounted(async () => {
  try {
    await websitesStore.fetchWebsites()
  } catch (error) {
    console.error('Failed to load websites:', error)
  }
})
</script>