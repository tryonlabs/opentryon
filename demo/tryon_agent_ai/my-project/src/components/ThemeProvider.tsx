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
      const initialTheme = savedTheme || 'dark'
      
      // Apply initial theme immediately before setting state
      const body = document.body
      const html = document.documentElement
      if (initialTheme === 'dark') {
        body.style.setProperty('background-color', '#1f2937', 'important')
        body.style.setProperty('color', '#ffffff', 'important')
        html.style.setProperty('background-color', '#1f2937', 'important')
      } else {
        body.style.setProperty('background-color', 'rgba(254, 242, 240, 1)', 'important')
        body.style.setProperty('color', '#171717', 'important')
        html.style.setProperty('background-color', 'rgba(254, 242, 240, 1)', 'important')
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
    
    const body = document.body
    const html = document.documentElement
    
    if (theme === 'dark') {
      body.style.setProperty('background-color', '#1f2937', 'important')
      body.style.setProperty('color', '#ffffff', 'important')
      html.style.setProperty('background-color', '#1f2937', 'important')
    } else {
      body.style.setProperty('background-color', 'rgba(254, 242, 240, 1)', 'important')
      body.style.setProperty('color', '#171717', 'important')
      html.style.setProperty('background-color', 'rgba(254, 242, 240, 1)', 'important')
    }
    
    // Save to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('theme', theme)
    }
  }, [theme, mounted])

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark'
    
    // Immediately apply theme change before state update
    if (typeof document !== 'undefined') {
      const body = document.body
      const html = document.documentElement
      
      if (newTheme === 'dark') {
        body.style.backgroundColor = '#1f2937'
        body.style.color = '#ffffff'
        html.style.backgroundColor = '#1f2937'
        // Force with setProperty as well
        body.style.setProperty('background-color', '#1f2937', 'important')
        body.style.setProperty('color', '#ffffff', 'important')
        html.style.setProperty('background-color', '#1f2937', 'important')
      } else {
        body.style.backgroundColor = 'rgba(254, 242, 240, 1)'
        body.style.color = '#171717'
        html.style.backgroundColor = 'rgba(254, 242, 240, 1)'
        // Force with setProperty as well
        body.style.setProperty('background-color', 'rgba(254, 242, 240, 1)', 'important')
        body.style.setProperty('color', '#171717', 'important')
        html.style.setProperty('background-color', 'rgba(254, 242, 240, 1)', 'important')
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

