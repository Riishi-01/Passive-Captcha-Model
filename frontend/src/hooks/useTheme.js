import { useEffect } from 'react'
import { useAppStore } from '../stores/app'

export function useTheme() {
  const { theme, setTheme } = useAppStore()

  useEffect(() => {
    // Check for saved theme preference or default to 'light'
    const savedTheme = localStorage.getItem('theme') || 'light'
    
    // Apply theme to document
    if (savedTheme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }

    // Update store if different
    if (savedTheme !== theme) {
      setTheme(savedTheme)
    }
  }, [theme, setTheme])

  useEffect(() => {
    // Save theme preference
    localStorage.setItem('theme', theme)
  }, [theme])

  return { theme, setTheme }
}
