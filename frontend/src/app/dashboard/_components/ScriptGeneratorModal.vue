<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto">
    <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
      <!-- Background overlay -->
      <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="closeModal"></div>

      <!-- Modal panel -->
      <div class="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-6xl sm:w-full sm:p-6">
        <div class="sm:flex sm:items-start">
          <div class="w-full">
            <!-- Header -->
            <div class="flex justify-between items-center mb-6">
              <h3 class="text-lg font-medium text-gray-900">Script Generator & Token Management</h3>
              <button @click="closeModal" class="rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500">
                <XMarkIcon class="h-6 w-6" />
              </button>
            </div>

            <!-- Website Info -->
            <div class="bg-gray-50 rounded-lg p-4 mb-6">
              <div class="flex items-center justify-between">
                <div>
                  <h4 class="text-lg font-semibold">{{ props.website?.name || currentToken?.website_name || 'Website' }}</h4>
                  <p class="text-sm text-gray-600">{{ props.website?.url || currentToken?.website_url || 'No URL' }}</p>
                </div>
                <div v-if="currentToken" class="flex items-center space-x-2">
                  <span :class="statusClasses(currentToken.status)" class="px-3 py-1 rounded-full text-sm font-medium">
                    {{ currentToken.status }}
                  </span>
                  <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                    {{ currentToken.environment }}
                  </span>
                </div>
                <div v-else class="flex items-center space-x-2">
                  <span class="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm font-medium">
                    No Token
                  </span>
                </div>
              </div>
            </div>

            <!-- Tab Navigation -->
            <div class="border-b border-gray-200 mb-6">
              <nav class="-mb-px flex space-x-8">
                <button
                  v-for="tab in tabs"
                  :key="tab.id"
                  @click="activeTab = tab.id"
                  :class="[
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                    'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm'
                  ]"
                >
                  <component :is="tab.icon" class="h-5 w-5 mr-2 inline" />
                  {{ tab.name }}
                </button>
              </nav>
            </div>

            <!-- Tab Content -->
            <div class="tab-content">
              <!-- Generate Script Tab -->
              <div v-if="activeTab === 'generate'" class="space-y-6">
                <!-- Configuration Panel -->
                <div class="bg-white border rounded-lg p-6">
                  <h5 class="text-lg font-medium mb-4">Script Configuration</h5>
                  
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Script Settings -->
                    <div>
                      <h6 class="text-md font-medium mb-3">Script Settings</h6>
                      <div class="space-y-4">
                        <div>
                          <label class="block text-sm font-medium text-gray-700 mb-1">Script Version</label>
                          <select 
                            v-model="configForm.script_version" 
                            class="block w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                          >
                            <option value="v2_enhanced">v2 Enhanced (Recommended)</option>
                            <option value="v1_advanced">v1 Advanced</option>
                            <option value="v1_basic">v1 Basic</option>
                          </select>
                        </div>
                        <div>
                          <label class="block text-sm font-medium text-gray-700 mb-1">Environment</label>
                          <select 
                            v-model="advancedForm.environment" 
                            class="block w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                          >
                            <option value="development">Development</option>
                            <option value="staging">Staging</option>
                            <option value="production">Production</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    <!-- Data Collection -->
                    <div>
                      <h6 class="text-md font-medium mb-3">Data Collection</h6>
                      <div class="space-y-3">
                        <label class="flex items-center">
                          <input 
                            v-model="configForm.collect_mouse_movements" 
                            type="checkbox" 
                            class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span class="ml-2 text-sm">Mouse Movements</span>
                        </label>
                        <label class="flex items-center">
                          <input 
                            v-model="configForm.collect_keyboard_patterns" 
                            type="checkbox" 
                            class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span class="ml-2 text-sm">Keyboard Patterns</span>
                        </label>
                        <label class="flex items-center">
                          <input 
                            v-model="configForm.collect_scroll_behavior" 
                            type="checkbox" 
                            class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span class="ml-2 text-sm">Scroll Behavior</span>
                        </label>
                        <label class="flex items-center">
                          <input 
                            v-model="configForm.collect_timing_data" 
                            type="checkbox" 
                            class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span class="ml-2 text-sm">Timing Data</span>
                        </label>
                      </div>
                    </div>
                  </div>

                  <div class="mt-6 flex justify-center">
                    <button 
                      @click="generateScript" 
                      :disabled="loading || !websiteId"
                      class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <span v-if="loading">Generating...</span>
                      <span v-else>Generate Script</span>
                    </button>
                  </div>
                </div>

                <!-- Generated Script Display -->
                <div v-if="generatedScript" class="bg-white border rounded-lg p-6">
                  <h5 class="text-lg font-medium mb-4">Generated Integration Code</h5>
                  
                  <!-- Integration Tabs -->
                  <div class="border-b border-gray-200 mb-4">
                    <nav class="-mb-px flex space-x-8">
                      <button
                        v-for="tab in integrationTabs"
                        :key="tab.id"
                        @click="activeIntegrationTab = tab.id"
                        :class="[
                          activeIntegrationTab === tab.id
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                          'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm'
                        ]"
                      >
                        {{ tab.name }}
                      </button>
                    </nav>
                  </div>

                  <!-- Integration Code Display -->
                  <div class="space-y-4">
                    <div v-if="activeIntegrationTab === 'html'">
                      <div class="flex justify-between items-center mb-2">
                        <h6 class="font-medium">HTML Integration</h6>
                        <button @click="copyToClipboard(generatedScript.integration?.basic_html || '')" class="text-sm text-blue-600 hover:text-blue-800">
                          Copy Code
                        </button>
                      </div>
                      <pre class="bg-gray-100 p-4 rounded-lg text-sm overflow-x-auto"><code>{{ generatedScript.integration?.basic_html }}</code></pre>
                    </div>

                    <div v-if="activeIntegrationTab === 'react'">
                      <div class="flex justify-between items-center mb-2">
                        <h6 class="font-medium">React/Next.js Integration</h6>
                        <button @click="copyToClipboard(generatedScript.integration?.react_nextjs || '')" class="text-sm text-blue-600 hover:text-blue-800">
                          Copy Code
                        </button>
                      </div>
                      <pre class="bg-gray-100 p-4 rounded-lg text-sm overflow-x-auto"><code>{{ generatedScript.integration?.react_nextjs }}</code></pre>
                    </div>

                    <div v-if="activeIntegrationTab === 'wordpress'">
                      <div class="flex justify-between items-center mb-2">
                        <h6 class="font-medium">WordPress Integration</h6>
                        <button @click="copyToClipboard(generatedScript.integration?.wordpress_php || '')" class="text-sm text-blue-600 hover:text-blue-800">
                          Copy Code
                        </button>
                      </div>
                      <pre class="bg-gray-100 p-4 rounded-lg text-sm overflow-x-auto"><code>{{ generatedScript.integration?.wordpress_php }}</code></pre>
                    </div>

                    <div v-if="activeIntegrationTab === 'advanced'">
                      <div class="flex justify-between items-center mb-2">
                        <h6 class="font-medium">Advanced JavaScript</h6>
                        <button @click="copyToClipboard(generatedScript.integration?.advanced_javascript || '')" class="text-sm text-blue-600 hover:text-blue-800">
                          Copy Code
                        </button>
                      </div>
                      <pre class="bg-gray-100 p-4 rounded-lg text-sm overflow-x-auto"><code>{{ generatedScript.integration?.advanced_javascript }}</code></pre>
                    </div>
                  </div>

                  <!-- Quick Actions -->
                  <div class="mt-6 flex justify-between items-center">
                    <div class="text-sm text-gray-600">
                      Script URL: <span class="font-mono">{{ generatedScript.integration?.script_url }}</span>
                    </div>
                    <button @click="downloadIntegrationPackage" class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
                      Download Package
                    </button>
                  </div>
                </div>

                <!-- Success/Error Messages -->
                <div v-if="successMessage" class="bg-green-50 border border-green-200 rounded-lg p-4">
                  <p class="text-green-800">{{ successMessage }}</p>
                </div>
                <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p class="text-red-800">{{ error }}</p>
                </div>
              </div>

              <!-- Overview Tab -->
              <div v-if="activeTab === 'overview'" class="space-y-6">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <!-- Token Info Card -->
                  <div class="col-span-2 bg-white border rounded-lg p-6">
                    <h5 class="text-lg font-medium mb-4">Token Information</h5>
                    <dl class="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <dt class="font-medium text-gray-600">Token ID</dt>
                        <dd class="mt-1 text-gray-900 font-mono text-xs">{{ currentToken?.token_id }}</dd>
                      </div>
                      <div>
                        <dt class="font-medium text-gray-600">Script Version</dt>
                        <dd class="mt-1 text-gray-900">{{ currentToken?.script_version }}</dd>
                      </div>
                      <div>
                        <dt class="font-medium text-gray-600">Created</dt>
                        <dd class="mt-1 text-gray-900">{{ formatDate(currentToken?.created_at) }}</dd>
                      </div>
                      <div>
                        <dt class="font-medium text-gray-600">Last Used</dt>
                        <dd class="mt-1 text-gray-900">{{ formatDate(currentToken?.last_used_at) || 'Never' }}</dd>
                      </div>
                      <div>
                        <dt class="font-medium text-gray-600">Usage Count</dt>
                        <dd class="mt-1 text-gray-900">{{ currentToken?.usage_count?.toLocaleString() || 0 }}</dd>
                      </div>
                      <div>
                        <dt class="font-medium text-gray-600">Regenerations</dt>
                        <dd class="mt-1 text-gray-900">{{ currentToken?.regeneration_count || 0 }}</dd>
                      </div>
                    </dl>
                  </div>

                  <!-- Quick Actions Card -->
                  <div class="bg-white border rounded-lg p-6">
                    <h5 class="text-lg font-medium mb-4">Quick Actions</h5>
                    <div class="space-y-3">
                      <button @click="regenerateToken" class="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors">
                        <ArrowPathIcon class="h-4 w-4 mr-2 inline" />
                        Regenerate Token
                      </button>
                      <button @click="showRevokeDialog = true" class="w-full bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition-colors">
                        <XCircleIcon class="h-4 w-4 mr-2 inline" />
                        Revoke Token
                      </button>
                      <button @click="validateSecurity" class="w-full bg-yellow-600 text-white px-4 py-2 rounded-md hover:bg-yellow-700 transition-colors">
                        <ShieldCheckIcon class="h-4 w-4 mr-2 inline" />
                        Security Check
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Security Report -->
                <div v-if="securityReport" class="bg-white border rounded-lg p-6">
                  <h5 class="text-lg font-medium mb-4">Security Report</h5>
                  <div class="flex items-center mb-4">
                    <div class="mr-4">
                      <div :class="[
                        'text-2xl font-bold',
                        securityReport.security_score >= 80 ? 'text-green-600' : 
                        securityReport.security_score >= 60 ? 'text-yellow-600' : 'text-red-600'
                      ]">
                        {{ securityReport.security_score }}/100
                      </div>
                      <div class="text-sm text-gray-600">Security Score</div>
                    </div>
                    <div class="flex-1">
                      <div class="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          :class="[
                            'h-2 rounded-full',
                            securityReport.security_score >= 80 ? 'bg-green-500' : 
                            securityReport.security_score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                          ]"
                          :style="{ width: `${securityReport.security_score}%` }"
                        ></div>
                      </div>
                    </div>
                  </div>

                  <div v-if="securityReport.issues?.length" class="mb-4">
                    <h6 class="font-medium text-red-600 mb-2">Security Issues</h6>
                    <ul class="list-disc list-inside text-sm text-red-700 space-y-1">
                      <li v-for="issue in securityReport.issues" :key="issue">{{ issue }}</li>
                    </ul>
                  </div>

                  <div v-if="securityReport.recommendations?.length" class="mb-4">
                    <h6 class="font-medium text-yellow-600 mb-2">Recommendations</h6>
                    <ul class="list-disc list-inside text-sm text-yellow-700 space-y-1">
                      <li v-for="rec in securityReport.recommendations" :key="rec">{{ rec }}</li>
                    </ul>
                  </div>
                </div>
              </div>

              <!-- Configuration Tab -->
              <div v-if="activeTab === 'configuration'" class="space-y-6">
                <div class="bg-white border rounded-lg p-6">
                  <h5 class="text-lg font-medium mb-4">Script Configuration</h5>
                  
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Data Collection Settings -->
                    <div>
                      <h6 class="text-md font-medium mb-3">Data Collection</h6>
                      <div class="space-y-3">
                        <label class="flex items-center">
                          <input 
                            v-model="configForm.collect_mouse_movements" 
                            type="checkbox" 
                            class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span class="ml-2 text-sm">Mouse Movements</span>
                        </label>
                        <label class="flex items-center">
                          <input 
                            v-model="configForm.collect_keyboard_patterns" 
                            type="checkbox" 
                            class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span class="ml-2 text-sm">Keyboard Patterns</span>
                        </label>
                        <label class="flex items-center">
                          <input 
                            v-model="configForm.collect_scroll_behavior" 
                            type="checkbox" 
                            class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span class="ml-2 text-sm">Scroll Behavior</span>
                        </label>
                        <label class="flex items-center">
                          <input 
                            v-model="configForm.collect_timing_data" 
                            type="checkbox" 
                            class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span class="ml-2 text-sm">Timing Data</span>
                        </label>
                      </div>
                    </div>

                    <!-- Performance Settings -->
                    <div>
                      <h6 class="text-md font-medium mb-3">Performance</h6>
                      <div class="space-y-4">
                        <div>
                          <label class="block text-sm font-medium text-gray-700 mb-1">Sampling Rate</label>
                          <input 
                            v-model.number="configForm.sampling_rate" 
                            type="number" 
                            min="0" 
                            max="1" 
                            step="0.1"
                            class="block w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                          />
                          <p class="text-xs text-gray-500 mt-1">0.1 = 10%, 1.0 = 100%</p>
                        </div>
                        <div>
                          <label class="block text-sm font-medium text-gray-700 mb-1">Batch Size</label>
                          <input 
                            v-model.number="configForm.batch_size" 
                            type="number" 
                            min="1" 
                            max="100"
                            class="block w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                          />
                        </div>
                        <div>
                          <label class="block text-sm font-medium text-gray-700 mb-1">Send Interval (ms)</label>
                          <input 
                            v-model.number="configForm.send_interval" 
                            type="number" 
                            min="1000" 
                            max="60000" 
                            step="1000"
                            class="block w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div class="mt-6 flex justify-end space-x-3">
                    <button @click="resetConfigForm" class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50">
                      Reset
                    </button>
                    <button @click="updateConfig" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                      Update Configuration
                    </button>
                  </div>
                </div>
              </div>

              <!-- History Tab -->
              <div v-if="activeTab === 'history'" class="space-y-6">
                <div class="bg-white border rounded-lg p-6">
                  <h5 class="text-lg font-medium mb-4">Token History</h5>
                  
                  <div v-if="tokenHistory.length === 0" class="text-center py-8 text-gray-500">
                    <ClockIcon class="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>No token history available</p>
                  </div>

                  <div v-else class="space-y-4">
                    <div 
                      v-for="(historyItem, index) in tokenHistory" 
                      :key="historyItem.token.token_id"
                      class="border rounded-lg p-4"
                      :class="index === 0 ? 'border-blue-200 bg-blue-50' : 'border-gray-200'"
                    >
                      <div class="flex justify-between items-start">
                        <div>
                          <div class="flex items-center space-x-2">
                            <h6 class="font-medium">{{ historyItem.token.script_version }}</h6>
                            <span 
                              :class="statusClasses(historyItem.token.status)" 
                              class="px-2 py-1 rounded-full text-xs font-medium"
                            >
                              {{ historyItem.token.status }}
                            </span>
                            <span v-if="index === 0" class="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                              Current
                            </span>
                          </div>
                          <p class="text-sm text-gray-600 mt-1">
                            Created: {{ formatDate(historyItem.lifecycle_events.created) }}
                          </p>
                          <p v-if="historyItem.lifecycle_events.revoked" class="text-sm text-red-600 mt-1">
                            Revoked: {{ formatDate(historyItem.lifecycle_events.revoked) }}
                          </p>
                        </div>
                        <div class="text-right text-sm text-gray-600">
                          <p>Usage: {{ historyItem.performance_summary.usage_count.toLocaleString() }}</p>
                          <p>Active: {{ Math.round(historyItem.performance_summary.active_duration_hours) }}h</p>
                          <p>Regenerations: {{ historyItem.performance_summary.regeneration_count }}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Advanced Tab -->
              <div v-if="activeTab === 'advanced'" class="space-y-6">
                <div class="bg-white border rounded-lg p-6">
                  <h5 class="text-lg font-medium mb-4">Advanced Operations</h5>
                  
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Environment Management -->
                    <div>
                      <h6 class="text-md font-medium mb-3">Environment Management</h6>
                      <div class="space-y-3">
                        <div>
                          <label class="block text-sm font-medium text-gray-700 mb-1">Switch Environment</label>
                          <select 
                            v-model="advancedForm.environment" 
                            class="block w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                          >
                            <option value="development">Development</option>
                            <option value="staging">Staging</option>
                            <option value="production">Production</option>
                          </select>
                        </div>
                        <div>
                          <label class="block text-sm font-medium text-gray-700 mb-1">Script Version</label>
                          <select 
                            v-model="advancedForm.script_version" 
                            class="block w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                          >
                            <option value="v1_basic">v1 Basic</option>
                            <option value="v1_advanced">v1 Advanced</option>
                            <option value="v2_enhanced">v2 Enhanced</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    <!-- Bulk Operations -->
                    <div>
                      <h6 class="text-md font-medium mb-3">Bulk Operations</h6>
                      <div class="space-y-3">
                        <button @click="getRotationCandidates" class="w-full text-left px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50">
                          <ClockIcon class="h-4 w-4 mr-2 inline" />
                          Check Rotation Candidates
                        </button>
                        <button @click="exportTokenData" class="w-full text-left px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50">
                          <ArrowDownTrayIcon class="h-4 w-4 mr-2 inline" />
                          Export Token Data
                        </button>
                      </div>
                    </div>
                  </div>

                  <div class="mt-6">
                    <h6 class="text-md font-medium mb-3">Regenerate with Advanced Options</h6>
                    <div class="space-y-3">
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Regeneration Reason</label>
                        <input 
                          v-model="advancedForm.reason" 
                          type="text" 
                          placeholder="e.g., Security policy update, Configuration change"
                          class="block w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                        />
                      </div>
                      <button @click="regenerateTokenAdvanced" class="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700">
                        <ArrowPathIcon class="h-4 w-4 mr-2 inline" />
                        Regenerate with Advanced Options
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Rotation Candidates -->
                <div v-if="rotationCandidates.length > 0" class="bg-white border rounded-lg p-6">
                  <h5 class="text-lg font-medium mb-4">Rotation Candidates</h5>
                  <div class="space-y-3">
                    <div 
                      v-for="candidate in rotationCandidates.slice(0, 5)" 
                      :key="candidate.token.token_id"
                      class="flex justify-between items-center p-3 border rounded-lg"
                    >
                      <div>
                        <p class="font-medium">{{ candidate.token.website_name }}</p>
                        <p class="text-sm text-gray-600">Age: {{ candidate.age_days }} days</p>
                        <p class="text-sm text-red-600">{{ candidate.rotation_reasons.join(', ') }}</p>
                      </div>
                      <span 
                        :class="[
                          'px-2 py-1 rounded-full text-xs font-medium',
                          candidate.rotation_priority === 'high' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                        ]"
                      >
                        {{ candidate.rotation_priority }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Footer Actions -->
            <div class="mt-8 flex justify-end space-x-3">
              <button @click="closeModal" class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50">
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Revoke Confirmation Dialog -->
    <div v-if="showRevokeDialog" class="fixed inset-0 z-60 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
        <div class="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
          <div class="sm:flex sm:items-start">
            <div class="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
              <ExclamationTriangleIcon class="h-6 w-6 text-red-600" />
            </div>
            <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
              <h3 class="text-lg leading-6 font-medium text-gray-900">Revoke Script Token</h3>
              <div class="mt-2">
                <p class="text-sm text-gray-500">
                  Are you sure you want to revoke this script token? This action cannot be undone and the website will stop working immediately.
                </p>
                <div class="mt-3">
                  <label class="block text-sm font-medium text-gray-700 mb-1">Revocation Reason</label>
                  <input 
                    v-model="revokeReason" 
                    type="text" 
                    placeholder="e.g., Security concern, Website migration"
                    class="block w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>
          </div>
          <div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
            <button @click="confirmRevoke" class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm">
              Revoke Token
            </button>
            <button @click="showRevokeDialog = false" class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:w-auto sm:text-sm">
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { XMarkIcon, ArrowPathIcon, XCircleIcon, ShieldCheckIcon, ClockIcon, ArrowDownTrayIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import { CogIcon, IdentificationIcon, DocumentTextIcon, WrenchScrewdriverIcon } from '@heroicons/vue/24/solid'
import api from '@/services/api'

// Props
interface Props {
  website?: {
    id: string
    name: string
    url: string
  } | null
  websiteId?: string
  isOpen?: boolean
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  close: []
  success: [data: any]
  tokenUpdated: [token: any]
}>()

// State
const activeTab = ref('generate')
const currentToken = ref<any>(null)
const loading = ref(false)
const securityReport = ref<any>(null)
const tokenHistory = ref<any[]>([])
const rotationCandidates = ref<any[]>([])
const showRevokeDialog = ref(false)
const revokeReason = ref('')
const generatedScript = ref<any>(null)
const error = ref('')
const successMessage = ref('')
const activeIntegrationTab = ref('html')

// Computed website ID
const websiteId = computed(() => props.website?.id || props.websiteId)

// Integration tabs for the script generator
const integrationTabs = [
  { id: 'html', name: 'HTML' },
  { id: 'react', name: 'React/Next.js' },
  { id: 'wordpress', name: 'WordPress' },
  { id: 'advanced', name: 'Advanced JS' }
]

// Forms
const configForm = reactive({
  script_version: 'v2_enhanced',
  collect_mouse_movements: true,
  collect_keyboard_patterns: true,
  collect_scroll_behavior: true,
  collect_timing_data: true,
  collect_device_info: true,
  sampling_rate: 0.1,
  batch_size: 50,
  send_interval: 30000,
  debug_mode: false
})

const advancedForm = reactive({
  environment: 'production',
  script_version: 'v2_enhanced',
  reason: ''
})

// Tabs configuration
const tabs = [
  { id: 'generate', name: 'Generate Script', icon: CogIcon },
  { id: 'overview', name: 'Token Overview', icon: IdentificationIcon },
  { id: 'configuration', name: 'Configuration', icon: CogIcon },
  { id: 'history', name: 'History', icon: DocumentTextIcon },
  { id: 'advanced', name: 'Advanced', icon: WrenchScrewdriverIcon }
]

// Computed
const statusClasses = (status: string) => {
  switch (status) {
    case 'active':
      return 'bg-green-100 text-green-800'
    case 'pending':
      return 'bg-yellow-100 text-yellow-800'
    case 'revoked':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

// Methods
const closeModal = () => {
  emit('close')
}

const formatDate = (dateString: string | null) => {
  if (!dateString) return null
  return new Date(dateString).toLocaleString()
}

const loadTokenData = async () => {
  if (!websiteId.value) return
  
  loading.value = true
  try {
    // Load current token
    const tokenResponse = await api.getScriptTokenInfo(websiteId.value)
    if (tokenResponse.success) {
      currentToken.value = tokenResponse.data.token
      
      // Update forms with current config
      Object.assign(configForm, currentToken.value.config || {})
      advancedForm.environment = currentToken.value.environment || 'production'
      advancedForm.script_version = currentToken.value.script_version || 'v2_enhanced'
    }

    // Load token history
    const historyResponse = await api.getTokenHistory(websiteId.value)
    if (historyResponse.success) {
      tokenHistory.value = historyResponse.data.history
    }
  } catch (error) {
    console.error('Failed to load token data:', error)
  } finally {
    loading.value = false
  }
}

const generateScript = async () => {
  if (!websiteId.value) {
    error.value = 'Website ID is required'
    return
  }

  loading.value = true
  error.value = ''
  successMessage.value = ''

  try {
    const response = await api.generateScriptToken(websiteId.value, {
      script_version: advancedForm.script_version,
      environment: advancedForm.environment,
      config: configForm
    })
    
    if (response.success) {
      generatedScript.value = response.data
      currentToken.value = response.data.token
      successMessage.value = 'Script generated successfully!'
      emit('success', response.data)
      emit('tokenUpdated', currentToken.value)
      activeIntegrationTab.value = 'html'
    } else {
      throw new Error(response.error?.message || 'Failed to generate script')
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to generate script'
  } finally {
    loading.value = false
  }
}

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    successMessage.value = 'Copied to clipboard!'
    setTimeout(() => {
      successMessage.value = ''
    }, 2000)
  } catch (err) {
    error.value = 'Failed to copy to clipboard'
  }
}

const downloadIntegrationPackage = () => {
  if (!generatedScript.value) return

  const packageData = {
    website: props.website,
    token: generatedScript.value.token,
    integration: generatedScript.value.integration,
    analytics: generatedScript.value.analytics,
    configuration: configForm,
    generated_at: new Date().toISOString()
  }

  const blob = new Blob([JSON.stringify(packageData, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `passive-captcha-${(props.website?.name || 'website')?.toLowerCase().replace(/\s+/g, '-')}-integration.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const validateSecurity = async () => {
  if (!websiteId.value) return
  
  loading.value = true
  try {
    const response = await api.validateTokenSecurity(websiteId.value)
    if (response.success) {
      securityReport.value = response.data.security_report
    }
  } catch (error) {
    console.error('Failed to validate security:', error)
  } finally {
    loading.value = false
  }
}

const updateConfig = async () => {
  if (!websiteId.value) return
  
  loading.value = true
  try {
    const response = await api.updateTokenConfig(websiteId.value, configForm, 'admin_dashboard')
    if (response.success) {
      currentToken.value = response.data.token
      emit('tokenUpdated', currentToken.value)
      successMessage.value = 'Configuration updated successfully!'
    }
  } catch (error) {
    console.error('Failed to update config:', error)
    error.value = 'Failed to update configuration'
  } finally {
    loading.value = false
  }
}

const resetConfigForm = () => {
  if (currentToken.value?.config) {
    Object.assign(configForm, currentToken.value.config)
  }
}

const regenerateToken = async () => {
  if (!websiteId.value) return
  
  loading.value = true
  try {
    const response = await api.regenerateScriptTokenEnhanced(websiteId.value, {
      reason: 'Manual regeneration via enhanced token management'
    })
    if (response.success) {
      currentToken.value = response.data.token
      emit('tokenUpdated', currentToken.value)
      successMessage.value = 'Token regenerated successfully!'
      await loadTokenData() // Reload all data
    }
  } catch (error) {
    console.error('Failed to regenerate token:', error)
    error.value = 'Failed to regenerate token'
  } finally {
    loading.value = false
  }
}

const regenerateTokenAdvanced = async () => {
  if (!websiteId.value) return
  
  loading.value = true
  try {
    const response = await api.regenerateScriptTokenEnhanced(websiteId.value, {
      script_version: advancedForm.script_version,
      environment: advancedForm.environment,
      reason: advancedForm.reason || 'Advanced regeneration via token management',
      admin_user: 'admin_dashboard'
    })
    if (response.success) {
      currentToken.value = response.data.token
      emit('tokenUpdated', currentToken.value)
      successMessage.value = 'Token regenerated with advanced options!'
      await loadTokenData() // Reload all data
      advancedForm.reason = '' // Clear form
    }
  } catch (error) {
    console.error('Failed to regenerate token:', error)
    error.value = 'Failed to regenerate token'
  } finally {
    loading.value = false
  }
}

const confirmRevoke = async () => {
  if (!websiteId.value) return
  
  loading.value = true
  try {
    const response = await api.revokeScriptTokenEnhanced(
      websiteId.value, 
      revokeReason.value || 'Manual revocation via enhanced token management',
      'admin_dashboard'
    )
    if (response.success) {
      currentToken.value = response.data.token
      emit('tokenUpdated', currentToken.value)
      showRevokeDialog.value = false
      revokeReason.value = ''
      successMessage.value = 'Token revoked successfully!'
      await loadTokenData() // Reload all data
    }
  } catch (error) {
    console.error('Failed to revoke token:', error)
    error.value = 'Failed to revoke token'
  } finally {
    loading.value = false
  }
}

const getRotationCandidates = async () => {
  loading.value = true
  try {
    const response = await api.getRotationCandidates(90)
    if (response.success) {
      rotationCandidates.value = response.data.candidates
    }
  } catch (error) {
    console.error('Failed to get rotation candidates:', error)
  } finally {
    loading.value = false
  }
}

const exportTokenData = () => {
  if (!currentToken.value) return
  
  const data = {
    token: currentToken.value,
    history: tokenHistory.value,
    security_report: securityReport.value,
    export_timestamp: new Date().toISOString()
  }
  
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `token-data-${props.websiteId}-${new Date().toISOString().split('T')[0]}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// Watchers
watch(() => props.isOpen, (isOpen) => {
  if (isOpen && websiteId.value) {
    loadTokenData()
  }
})

watch(() => websiteId.value, () => {
  if (props.isOpen && websiteId.value) {
    loadTokenData()
  }
})

// Lifecycle
onMounted(() => {
  if (props.isOpen && websiteId.value) {
    loadTokenData()
  }
})
</script>

<style scoped>
.tab-content {
  min-height: 400px;
}
</style>