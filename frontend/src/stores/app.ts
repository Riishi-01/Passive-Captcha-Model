import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  // State
  const isLoading = ref(false)
  const isDarkMode = ref(false)
  const isSidebarOpen = ref(true)
  const notifications = ref<Array<{
    id: string
    type: 'success' | 'error' | 'warning' | 'info'
    title: string
    message: string
    timestamp: Date
  }>>([])

  // Getters
  const loadingCount = ref(0)
  const isProcessing = computed(() => loadingCount.value > 0)

  // Actions
  function setLoading(loading: boolean) {
    if (loading) {
      loadingCount.value++
    } else {
      loadingCount.value = Math.max(0, loadingCount.value - 1)
    }
    isLoading.value = loadingCount.value > 0
  }

  function toggleDarkMode() {
    isDarkMode.value = !isDarkMode.value
    // Update DOM class for Tailwind
    if (isDarkMode.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    // Save preference
    localStorage.setItem('theme', isDarkMode.value ? 'dark' : 'light')
  }

  function initializeTheme() {
    const savedTheme = localStorage.getItem('theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    
    isDarkMode.value = savedTheme === 'dark' || (!savedTheme && prefersDark)
    
    if (isDarkMode.value) {
      document.documentElement.classList.add('dark')
    }
  }

  function toggleSidebar() {
    isSidebarOpen.value = !isSidebarOpen.value
    localStorage.setItem('sidebar-open', isSidebarOpen.value.toString())
  }

  function initializeSidebar() {
    const savedState = localStorage.getItem('sidebar-open')
    if (savedState !== null) {
      isSidebarOpen.value = savedState === 'true'
    }
  }

  function addNotification(notification: Omit<typeof notifications.value[0], 'id' | 'timestamp'>) {
    const id = Math.random().toString(36).substring(2, 15)
    notifications.value.push({
      ...notification,
      id,
      timestamp: new Date()
    })

    // Auto-remove after 5 seconds
    setTimeout(() => {
      removeNotification(id)
    }, 5000)

    return id
  }

  function removeNotification(id: string) {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }
  }

  function clearNotifications() {
    notifications.value = []
  }

  return {
    // State
    isLoading,
    isDarkMode,
    isSidebarOpen,
    notifications,
    
    // Getters
    isProcessing,
    
    // Actions
    setLoading,
    toggleDarkMode,
    initializeTheme,
    toggleSidebar,
    initializeSidebar,
    addNotification,
    removeNotification,
    clearNotifications
  }
}) 