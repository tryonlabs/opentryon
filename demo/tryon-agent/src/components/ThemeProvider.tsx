'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'

type Theme = 'dark' | 'light'

interface ThemeContextType {
  theme: Theme
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>('dark')
  const [mounted, setMounted] = useState(false)

  // Load theme from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem('theme') as Theme | null
      const initialTheme = savedTheme || 'light'
      
      // Apply initial theme using data-theme attribute
      const html = document.documentElement
      if (initialTheme === 'dark') {
        html.setAttribute('data-theme', 'dark')
      } else {
        html.removeAttribute('data-theme')
      }
      
      setTheme(initialTheme)
      setMounted(true)
      
      // Listen for storage changes (when theme changes in another tab/page)
      const handleStorageChange = (e: StorageEvent) => {
        if (e.key === 'theme' && e.newValue) {
          const newTheme = e.newValue as Theme
          setTheme(newTheme)
        }
      }
      
      window.addEventListener('storage', handleStorageChange)
      return () => window.removeEventListener('storage', handleStorageChange)
    }
  }, [])

  // Apply theme changes
  useEffect(() => {
    if (!mounted || typeof document === 'undefined') return
    
    const html = document.documentElement
    
    if (theme === 'dark') {
      html.setAttribute('data-theme', 'dark')
    } else {
      html.removeAttribute('data-theme')
    }
    
    // Save to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('theme', theme)
    }
  }, [theme, mounted])

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark'
    
    // Immediately apply theme change using data-theme attribute
    if (typeof document !== 'undefined') {
      const html = document.documentElement
      
      if (newTheme === 'dark') {
        html.setAttribute('data-theme', 'dark')
      } else {
        html.removeAttribute('data-theme')
      }
      
      // Save to localStorage immediately
      if (typeof window !== 'undefined') {
        localStorage.setItem('theme', newTheme)
      }
    }
    
    // Update state
    setTheme(newTheme)
  }

  // Always provide context, even when not mounted
  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

