import { useState } from 'react'
import { useAppStore } from '../stores/app'
import { Save, Copy, Check, ExternalLink, Globe, Shield, Code } from 'lucide-react'
import apiService from '../services/api'

export default function SettingsView() {
  const { addNotification } = useAppStore()
  const [hostedUrl, setHostedUrl] = useState('')
  const [generatedToken, setGeneratedToken] = useState('')
  const [generatedScript, setGeneratedScript] = useState('')
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  const validateUrl = (url) => {
    try {
      const urlObj = new URL(url.startsWith('http') ? url : `https://${url}`)
      return urlObj.hostname
    } catch {
      return null
    }
  }

  const generateScript = (domain, token) => {
    return `<!-- Passive CAPTCHA Integration -->
<script>
(function() {
    // Passive CAPTCHA Configuration
    window.PassiveCaptcha = {
        domain: '${domain}',
        token: '${token}',
        apiUrl: '${window.location.origin}/api',
        excludePaths: ['/pages/*', '/admin/*', '/api/*'],
        
        init: function() {
            this.collectBehavioralData();
            this.setupEventListeners();
        },
        
        collectBehavioralData: function() {
            // Mouse movement tracking
            document.addEventListener('mousemove', this.trackMouseMovement.bind(this));
            
            // Keyboard behavior tracking
            document.addEventListener('keydown', this.trackKeystrokes.bind(this));
            
            // Scroll pattern tracking
            document.addEventListener('scroll', this.trackScrolling.bind(this));
            
            // Device fingerprinting
            this.collectDeviceFingerprint();
        },
        
        trackMouseMovement: function(e) {
            // Implementation for mouse tracking
        },
        
        trackKeystrokes: function(e) {
            // Implementation for keystroke dynamics
        },
        
        trackScrolling: function(e) {
            // Implementation for scroll pattern analysis
        },
        
        collectDeviceFingerprint: function() {
            // Implementation for device fingerprinting
        },
        
        setupEventListeners: function() {
            // Set up form submission handlers
            const forms = document.querySelectorAll('form');
            forms.forEach(form => {
                form.addEventListener('submit', this.handleFormSubmission.bind(this));
            });
        },
        
        handleFormSubmission: function(e) {
            // Validate with backend before allowing submission
            this.validateUser().then(isValid => {
                if (!isValid) {
                    e.preventDefault();
                    this.showCaptchaChallenge();
                }
            });
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
        },
        
        getBehavioralData: function() {
            // Return collected behavioral data
            return {};
        },
        
        getDeviceFingerprint: function() {
            // Return device fingerprint
            return {};
        },
        
        showCaptchaChallenge: function() {
            // Show additional verification if needed
            alert('Additional verification required. Please try again.');
        }
    };
    
    // Initialize when DOM is ready
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

  const handleSave = async () => {
    if (!hostedUrl.trim()) {
      addNotification({
        type: 'error',
        message: 'Please enter a hosted URL'
      })
      return
    }

    const domain = validateUrl(hostedUrl)
    if (!domain) {
      addNotification({
        type: 'error',
        message: 'Please enter a valid URL'
      })
      return
    }

    setLoading(true)
    try {
      // Create website entry with the domain
      const response = await apiService.createWebsite({
        name: domain,
        url: hostedUrl,
        description: `Hosted domain: ${domain}`
      })

      if (response.success) {
        const website = response.data.website
        const token = website.token || website.api_key
        
        setGeneratedToken(token)
        setGeneratedScript(generateScript(domain, token))
        
        addNotification({
          type: 'success',
          message: 'Domain registered and script generated successfully!'
        })
      }
    } catch (error) {
      addNotification({
        type: 'error',
        message: error.response?.data?.error?.message || 'Failed to register domain'
      })
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      addNotification({
        type: 'success',
        message: 'Script copied to clipboard!'
      })
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to copy to clipboard'
      })
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Settings</h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Configure your Passive CAPTCHA integration settings
        </p>
      </div>

      {/* Hosted URL Configuration */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center space-x-3 mb-4">
            <Globe className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
              Hosted URL Configuration
            </h3>
          </div>
          
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Enter your main domain where Passive CAPTCHA will be embedded. The system will automatically 
            exclude paths like /pages/*, /admin/*, and /api/* from verification.
          </p>

          <div className="space-y-4">
            <div>
              <label htmlFor="hosted-url" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Hosted URL
              </label>
              <div className="mt-1 flex rounded-md shadow-sm">
                <span className="inline-flex items-center px-3 rounded-l-md border border-r-0 border-gray-300 bg-gray-50 text-gray-500 text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-gray-400">
                  https://
                </span>
                <input
                  type="text"
                  id="hosted-url"
                  value={hostedUrl}
                  onChange={(e) => setHostedUrl(e.target.value)}
                  className="flex-1 min-w-0 block w-full px-3 py-2 rounded-none rounded-r-md border border-gray-300 focus:ring-blue-500 focus:border-blue-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  placeholder="example.com"
                />
              </div>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Enter your domain without the https:// prefix
              </p>
            </div>

            <button
              onClick={handleSave}
              disabled={loading}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Generating...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Generate Script
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Generated Token & Script */}
      {generatedToken && (
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex items-center space-x-3 mb-4">
              <Shield className="h-6 w-6 text-green-600 dark:text-green-400" />
              <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                Generated Configuration
              </h3>
            </div>

            <div className="space-y-4">
              {/* Token Display */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Domain Token
                </label>
                <div className="flex items-center space-x-2">
                  <code className="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-md text-sm font-mono text-gray-900 dark:text-gray-100">
                    {generatedToken}
                  </code>
                  <button
                    onClick={() => copyToClipboard(generatedToken)}
                    className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {/* Script Display */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Integration Script
                  </label>
                  <button
                    onClick={() => copyToClipboard(generatedScript)}
                    className="inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-xs font-medium text-gray-700 bg-white hover:bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-600"
                  >
                    {copied ? <Check className="h-3 w-3 mr-1" /> : <Copy className="h-3 w-3 mr-1" />}
                    Copy Script
                  </button>
                </div>
                <div className="relative">
                  <pre className="bg-gray-900 text-green-400 p-4 rounded-lg text-xs overflow-x-auto max-h-64">
                    <code>{generatedScript}</code>
                  </pre>
                </div>
                <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                  Add this script to the &lt;head&gt; section of your website
                </p>
              </div>
            </div>

            {/* Integration Instructions */}
            <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="flex items-start space-x-3">
                <Code className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100">
                    Integration Instructions
                  </h4>
                  <div className="mt-2 text-sm text-blue-700 dark:text-blue-300">
                    <ol className="list-decimal list-inside space-y-1">
                      <li>Copy the generated script above</li>
                      <li>Paste it in the &lt;head&gt; section of your website</li>
                      <li>The script will automatically exclude /pages/*, /admin/*, and /api/* paths</li>
                      <li>Monitor verification activity in the Dashboard</li>
                    </ol>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Additional Settings */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white mb-4">
            Additional Settings
          </h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">Real-time Monitoring</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Track verification events in real-time</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" defaultChecked className="sr-only peer" />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between py-2">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">Email Notifications</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Receive alerts for suspicious activity</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}