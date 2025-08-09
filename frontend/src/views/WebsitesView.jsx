import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useWebsitesStore } from '../stores/websites'
import { useAppStore } from '../stores/app'
import WebsiteModal from '../components/WebsiteModal'
import { 
  Plus, 
  Globe, 
  Edit, 
  Trash2, 
  ExternalLink, 
  Shield, 
  ShieldOff,
  MoreVertical,
  Copy,
  Check,
  Code,
  Calendar,
  Activity
} from 'lucide-react'

export default function WebsitesView() {
  const { 
    websites, 
    loading, 
    error, 
    fetchWebsites, 
    deleteWebsite, 
    openModal, 
    clearError 
  } = useWebsitesStore()
  const { addNotification } = useAppStore()
  const [deleteConfirm, setDeleteConfirm] = useState(null)
  const [copiedScript, setCopiedScript] = useState('')

  useEffect(() => {
    const loadWebsites = async () => {
      try {
        await fetchWebsites()
      } catch (error) {
        addNotification({
          type: 'error',
          message: 'Failed to load websites'
        })
      }
    }

    loadWebsites()
  }, [fetchWebsites, addNotification])

  const generateScript = (domain, token) => {
    return `<!-- Passive CAPTCHA Integration -->
<script>
(function() {
    window.PassiveCaptcha = {
        domain: '${domain}',
        token: '${token}',
        apiUrl: '${window.location.origin}/api',
        excludePaths: ['/pages/*', '/admin/*', '/api/*'],
        
        init: function() {
            this.collectBehavioralData();
            this.setupEventListeners();
        },
        
        validateUser: function() {
            return fetch(\`\${this.apiUrl}/verify\`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Domain-Token': this.token
                },
                body: JSON.stringify({
                    domain: this.domain,
                    behavioralData: this.getBehavioralData(),
                    deviceFingerprint: this.getDeviceFingerprint()
                })
            }).then(response => response.json())
              .then(data => data.isHuman);
        }
    };
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            window.PassiveCaptcha.init();
        });
    } else {
        window.PassiveCaptcha.init();
    }
})();
</script>
<!-- End Passive CAPTCHA -->`
  }

  const copyScript = async (website) => {
    const domain = website.domain || website.url || website.website_url
    const token = website.token || website.api_key
    
    if (!domain || !token) {
      addNotification({
        type: 'error',
        message: 'Unable to generate script - missing domain or token'
      })
      return
    }
    
    const script = generateScript(domain, token)
    
    try {
      await navigator.clipboard.writeText(script)
      setCopiedScript(website.id)
      addNotification({
        type: 'success',
        message: 'Integration script copied to clipboard!'
      })
      setTimeout(() => setCopiedScript(''), 2000)
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to copy script to clipboard'
      })
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Never'
    const date = new Date(dateString)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const handleDelete = async (id) => {
    try {
      await deleteWebsite(id)
      addNotification({
        type: 'success',
        message: 'Website deleted successfully'
      })
      setDeleteConfirm(null)
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to delete website'
      })
    }
  }



  if (loading && websites.length === 0) {
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
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Websites</h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Manage websites protected by Passive CAPTCHA
          </p>
        </div>
        <button
          onClick={() => openModal()}
          className="btn btn-primary flex items-center"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Website
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
              <button
                onClick={clearError}
                className="mt-2 text-sm text-red-600 hover:text-red-500"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Websites Grid */}
      {websites.length === 0 ? (
        <div className="text-center py-12">
          <Globe className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No websites added yet
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Add your first website to start protecting it with Passive CAPTCHA
          </p>
          <button
            onClick={() => openModal()}
            className="btn btn-primary"
          >
            Add Website
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {websites.map((website) => (
            <div key={website.id} className="card">
              <div className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <Globe className="h-8 w-8 text-primary-600" />
                    </div>
                    <div className="ml-3">
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                        {website.name}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {website.url}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {website.status === 'active' ? (
                      <Shield className="h-5 w-5 text-green-500" title="Protection enabled" />
                    ) : (
                      <ShieldOff className="h-5 w-5 text-gray-400" title="Protection disabled" />
                    )}
                    <div className="relative">
                      <button className="p-1 rounded-md text-gray-400 hover:text-gray-500">
                        <MoreVertical className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Token Display */}
                <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Domain Token</p>
                      <code className="text-xs font-mono text-gray-900 dark:text-gray-100">
                        {website.token || website.api_key || 'Not generated'}
                      </code>
                    </div>
                    <button
                      onClick={() => copyScript(website)}
                      className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                      title="Copy integration script"
                    >
                      {copiedScript === website.id ? (
                        <Check className="h-4 w-4 text-green-500" />
                      ) : (
                        <Code className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>

                {website.description && (
                  <p className="mt-3 text-sm text-gray-600 dark:text-gray-400">
                    {website.description}
                  </p>
                )}

                {/* Stats & Status */}
                <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="flex items-center text-gray-500 dark:text-gray-400">
                      <Calendar className="h-4 w-4 mr-1" />
                      <span className="text-xs">Added</span>
                    </div>
                    <p className="text-gray-900 dark:text-gray-100 font-medium">
                      {formatDate(website.created_at)}
                    </p>
                  </div>
                  <div>
                    <div className="flex items-center text-gray-500 dark:text-gray-400">
                      <Activity className="h-4 w-4 mr-1" />
                      <span className="text-xs">Last Activity</span>
                    </div>
                    <p className="text-gray-900 dark:text-gray-100 font-medium">
                      {formatDate(website.last_activity)}
                    </p>
                  </div>
                </div>

                <div className="mt-4 flex items-center justify-between">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    website.status === 'active' 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                  }`}>
                    {website.status === 'active' ? 'Active' : 'Inactive'}
                  </span>
                  
                  <button
                    onClick={() => copyScript(website)}
                    className="inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-xs font-medium text-gray-700 bg-white hover:bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-600 transition-colors"
                  >
                    {copiedScript === website.id ? (
                      <>
                        <Check className="h-3 w-3 mr-1 text-green-500" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="h-3 w-3 mr-1" />
                        Copy Script
                      </>
                    )}
                  </button>
                </div>

                <div className="mt-6 flex items-center justify-between">
                  <div className="flex space-x-2">
                    <Link
                      to={`/dashboard/websites/${website.id}`}
                      className="text-primary-600 hover:text-primary-500 text-sm font-medium"
                    >
                      View Details
                    </Link>
                    <a
                      href={website.url.startsWith('http') ? website.url : `https://${website.url}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-gray-600 hover:text-gray-500 text-sm"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => openModal(website)}
                      className="p-1 text-gray-400 hover:text-gray-500"
                    >
                      <Edit className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => setDeleteConfirm(website.id)}
                      className="p-1 text-gray-400 hover:text-red-500"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 dark:bg-red-900 sm:mx-0 sm:h-10 sm:w-10">
                    <Trash2 className="h-6 w-6 text-red-600 dark:text-red-400" />
                  </div>
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                      Delete Website
                    </h3>
                    <div className="mt-2">
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Are you sure you want to delete this website? This action cannot be undone.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={() => handleDelete(deleteConfirm)}
                  className="btn btn-danger sm:ml-3"
                >
                  Delete
                </button>
                <button
                  type="button"
                  onClick={() => setDeleteConfirm(null)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <WebsiteModal />
    </div>
  )
}
