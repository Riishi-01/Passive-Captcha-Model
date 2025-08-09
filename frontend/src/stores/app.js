import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useAppStore = create(
  persist(
    (set, get) => ({
      theme: 'light',
      loading: false,
      notifications: [],
      sidebarCollapsed: false,

      toggleTheme: () => {
        const newTheme = get().theme === 'light' ? 'dark' : 'light'
        set({ theme: newTheme })
        
        // Apply theme to document
        if (newTheme === 'dark') {
          document.documentElement.classList.add('dark')
        } else {
          document.documentElement.classList.remove('dark')
        }
      },

      setTheme: (theme) => {
        set({ theme })
        if (theme === 'dark') {
          document.documentElement.classList.add('dark')
        } else {
          document.documentElement.classList.remove('dark')
        }
      },

      setLoading: (loading) => set({ loading }),

      addNotification: (notification) => {
        const id = Date.now().toString()
        const newNotification = {
          id,
          type: 'info',
          autoClose: true,
          duration: 5000,
          ...notification,
        }
        set((state) => ({
          notifications: [...state.notifications, newNotification]
        }))

        if (newNotification.autoClose) {
          setTimeout(() => {
            get().removeNotification(id)
          }, newNotification.duration)
        }

        return id
      },

      removeNotification: (id) => {
        set((state) => ({
          notifications: state.notifications.filter(n => n.id !== id)
        }))
      },

      clearNotifications: () => set({ notifications: [] }),

      toggleSidebar: () => {
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }))
      },

      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
    }),
    {
      name: 'app-store',
      partialize: (state) => ({ 
        theme: state.theme, 
        sidebarCollapsed: state.sidebarCollapsed 
      }),
    }
  )
)
