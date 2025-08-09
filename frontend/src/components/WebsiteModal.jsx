import { useState, useEffect } from 'react'
import { useWebsitesStore } from '../stores/websites'
import { useAppStore } from '../stores/app'
import { X, Globe } from 'lucide-react'

export default function WebsiteModal() {
  const { modalOpen, editingWebsite, loading, closeModal, createWebsite, updateWebsite } = useWebsitesStore()
  const { addNotification } = useAppStore()
  
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    description: '',
    enabled: true
  })

  const [errors, setErrors] = useState({})

  useEffect(() => {
    if (editingWebsite) {
      setFormData({
        name: editingWebsite.name || '',
        url: editingWebsite.url || '',
        description: editingWebsite.description || '',
        enabled: editingWebsite.status === 'active'
      })
    } else {
      setFormData({
        name: '',
        url: '',
        description: '',
        enabled: true
      })
    }
    setErrors({})
  }, [editingWebsite, modalOpen])

  const validateForm = () => {
    const newErrors = {}
    
    if (!formData.name.trim()) {
      newErrors.name = 'Website name is required'
    }
    
    if (!formData.url.trim()) {
      newErrors.url = 'URL is required'
    } else if (!/^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.\-~:]*)*\/?(\?[;&a-z\d%_.~+=-]*)?(\#[-a-z\d_]*)?$/i.test(formData.url)) {
      newErrors.url = 'Please enter a valid URL (e.g., https://example.com)'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    try {
      if (editingWebsite) {
        await updateWebsite(editingWebsite.id, formData)
        addNotification({
          type: 'success',
          message: 'Website updated successfully'
        })
      } else {
        await createWebsite(formData)
        addNotification({
          type: 'success',
          message: 'Website added successfully'
        })
      }
    } catch (error) {
      addNotification({
        type: 'error',
        message: error.response?.data?.detail || 'Operation failed'
      })
    }
  }

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }))
    }
  }

  if (!modalOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75" onClick={closeModal}></div>
        </div>

        <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <Globe className="h-6 w-6 text-primary-600 mr-2" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  {editingWebsite ? 'Edit Website' : 'Add Website'}
                </h3>
              </div>
              <button
                onClick={closeModal}
                className="text-gray-400 hover:text-gray-500"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Website Name
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  className={`mt-1 input ${errors.name ? 'border-red-500' : ''}`}
                  placeholder="My Website"
                />
                {errors.name && (
                  <p className="mt-1 text-sm text-red-600">{errors.name}</p>
                )}
              </div>

              <div>
                <label htmlFor="url" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Website URL
                </label>
                <input
                  type="text"
                  id="url"
                  name="url"
                  value={formData.url}
                  onChange={handleChange}
                  className={`mt-1 input ${errors.url ? 'border-red-500' : ''}`}
                  placeholder="https://example.com"
                />
                {errors.url && (
                  <p className="mt-1 text-sm text-red-600">{errors.url}</p>
                )}
              </div>

              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Description
                </label>
                <textarea
                  id="description"
                  name="description"
                  rows={3}
                  value={formData.description}
                  onChange={handleChange}
                  className="mt-1 input"
                  placeholder="Brief description of the website"
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="enabled"
                  name="enabled"
                  checked={formData.enabled}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label htmlFor="enabled" className="ml-2 block text-sm text-gray-900 dark:text-white">
                  Enable CAPTCHA protection
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={closeModal}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="btn btn-primary"
                >
                  {loading ? 'Saving...' : editingWebsite ? 'Update' : 'Add Website'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
