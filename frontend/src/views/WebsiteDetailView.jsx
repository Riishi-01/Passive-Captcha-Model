import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useWebsitesStore } from '../stores/websites'
import { useAppStore } from '../stores/app'
import { 
  ArrowLeft, 
  Globe, 
  Shield, 
  Copy, 
  RefreshCw, 
  Plus,
  ExternalLink,
  Settings,
  BarChart3 
} from 'lucide-react'

export default function WebsiteDetailView() {
  const { id } = useParams()
  const { selectedWebsite, fetchWebsite, loading } = useWebsitesStore()
  const { addNotification } = useAppStore()
  const [scriptCode, setScriptCode] = useState('')
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    if (id) {
      fetchWebsite(id).catch(() => {
        addNotification({
          type: 'error',
          message: 'Failed to load website details'
        })
      })
    }
  }, [id, fetchWebsite, addNotification])

  useEffect(() => {
    // Generate script code when website is loaded
    if (selectedWebsite) {
      const script = `<!-- Passive CAPTCHA Script -->
<script>
(function() {
  var script = document.createElement('script');
  script.src = '${window.location.origin}/static/passive-captcha-script.js';
  script.setAttribute('data-site-id', '${selectedWebsite.id}');
  script.setAttribute('data-domain', '${selectedWebsite.domain}');
  document.head.appendChild(script);
})();
</script>`
      setScriptCode(script)
    }
  }, [selectedWebsite])

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      addNotification({
        type: 'success',
        message: 'Copied to clipboard'
      })
    })
  }

  const generateNewToken = () => {
    addNotification({
      type: 'success',
      message: 'New token generated'
    })
  }

  if (loading || !selectedWebsite) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link 
            to="/dashboard/websites"
            className="p-2 text-gray-400 hover:text-gray-500 rounded-md"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {selectedWebsite.name}
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {selectedWebsite.domain}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <a
            href={`https://${selectedWebsite.domain}`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary flex items-center"
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Visit Site
          </a>
          <button className="btn btn-primary flex items-center">
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', name: 'Overview', icon: Globe },
            { id: 'integration', name: 'Integration', icon: Shield },
            { id: 'analytics', name: 'Analytics', icon: BarChart3 },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              <tab.icon className="h-4 w-4 mr-2" />
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {/* Website Info */}
            <div className="card p-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Website Information
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Name</label>
                  <p className="text-gray-900 dark:text-white">{selectedWebsite.name}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Domain</label>
                  <p className="text-gray-900 dark:text-white">{selectedWebsite.domain}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Description</label>
                  <p className="text-gray-900 dark:text-white">
                    {selectedWebsite.description || 'No description provided'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Status</label>
                  <div className="flex items-center space-x-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      selectedWebsite.enabled 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                    }`}>
                      {selectedWebsite.enabled ? 'Protection Active' : 'Protection Inactive'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="card">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Recent Activity
                </h3>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <Shield className="h-5 w-5 text-green-500" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-900 dark:text-white">Bot blocked</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">2 minutes ago</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <Shield className="h-5 w-5 text-blue-500" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-900 dark:text-white">Verification passed</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">5 minutes ago</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="space-y-6">
            <div className="card p-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Today's Stats
              </h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Verifications</span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">847</span>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Blocked Bots</span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">23</span>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Success Rate</span>
                    <span className="text-sm font-medium text-green-600">97.3%</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="card p-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Quick Actions
              </h3>
              <div className="space-y-3">
                <button className="w-full btn btn-primary text-left flex items-center">
                  <Plus className="h-4 w-4 mr-2" />
                  Generate New Token
                </button>
                <button className="w-full btn btn-secondary text-left flex items-center">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh Stats
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'integration' && (
        <div className="max-w-4xl">
          <div className="card p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Integration Code
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Add this script to your website's HTML to enable Passive CAPTCHA protection.
            </p>
            
            <div className="relative">
              <pre className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 text-sm overflow-x-auto">
                <code className="text-gray-900 dark:text-gray-100">{scriptCode}</code>
              </pre>
              <button
                onClick={() => copyToClipboard(scriptCode)}
                className="absolute top-2 right-2 p-2 text-gray-400 hover:text-gray-600 bg-white dark:bg-gray-700 rounded-md shadow-sm"
              >
                <Copy className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <h4 className="text-sm font-medium text-blue-900 dark:text-blue-200 mb-2">
                Integration Instructions
              </h4>
              <ol className="text-sm text-blue-800 dark:text-blue-300 space-y-1 list-decimal list-inside">
                <li>Copy the script code above</li>
                <li>Paste it in your website's HTML before the closing &lt;/head&gt; tag</li>
                <li>The script will automatically start protecting your website</li>
                <li>Monitor the results in your dashboard</li>
              </ol>
            </div>

            <div className="mt-6">
              <button
                onClick={generateNewToken}
                className="btn btn-secondary flex items-center"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Generate New Token
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'analytics' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Verification Trends
            </h3>
            <div className="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">
              Chart placeholder - Verification trends over time
            </div>
          </div>

          <div className="card p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Detection Results
            </h3>
            <div className="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">
              Chart placeholder - Bot detection results
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
